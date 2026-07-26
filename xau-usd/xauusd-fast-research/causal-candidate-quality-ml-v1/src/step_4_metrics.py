from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)


def weighted_mean_and_se(
    values: np.ndarray, weights: np.ndarray
) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    total = float(weights.sum())
    if not len(values) or total <= 0.0:
        return math.nan, math.nan
    mean = float(np.dot(values, weights) / total)
    denominator = float(np.square(weights).sum())
    effective = total * total / denominator if denominator > 0.0 else 0.0
    variance = float(np.dot(weights, np.square(values - mean)) / total)
    se = math.sqrt(variance / effective) if effective > 0.0 else math.nan
    return mean, se


def choose_threshold(
    calibration: pd.DataFrame, policy: Mapping[str, Any]
) -> tuple[float, list[dict[str, Any]]]:
    minimum = max(
        int(policy["minimum_selected_rows"]),
        int(math.ceil(len(calibration) * float(policy["minimum_selected_fraction"]))),
    )
    rows: list[dict[str, Any]] = []
    for threshold in policy["candidate_probability_thresholds"]:
        selected = calibration["probability"].ge(float(threshold))
        count = int(selected.sum())
        if count < minimum:
            rows.append(
                {
                    "threshold": float(threshold),
                    "selected_rows": count,
                    "selected_fraction": count / len(calibration),
                    "weighted_mean_stress_r": None,
                    "weighted_standard_error": None,
                    "utility": None,
                    "eligible": False,
                }
            )
            continue
        local = calibration.loc[selected]
        mean, se = weighted_mean_and_se(
            local["stress_net_r"].to_numpy(dtype=float),
            local["structural_weight"].to_numpy(dtype=float),
        )
        rows.append(
            {
                "threshold": float(threshold),
                "selected_rows": count,
                "selected_fraction": count / len(calibration),
                "weighted_mean_stress_r": mean,
                "weighted_standard_error": se,
                "utility": mean - se,
                "eligible": True,
            }
        )
    eligible = [row for row in rows if row["eligible"]]
    if not eligible:
        raise ValueError("No threshold satisfies the locked coverage constraints")
    chosen = max(
        eligible,
        key=lambda row: (
            float(row["utility"]),
            float(row["selected_fraction"]),
            -float(row["threshold"]),
        ),
    )
    return float(chosen["threshold"]), rows


def weighted_ece(
    target: np.ndarray,
    probability: np.ndarray,
    weights: np.ndarray,
    bins: int = 10,
) -> float:
    target = np.asarray(target, dtype=float)
    probability = np.asarray(probability, dtype=float)
    weights = np.asarray(weights, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    assignment = np.minimum(
        np.searchsorted(edges, probability, side="right") - 1, bins - 1
    )
    total = float(weights.sum())
    error = 0.0
    for index in range(bins):
        mask = assignment == index
        local_weight = float(weights[mask].sum())
        if local_weight <= 0.0:
            continue
        observed = float(np.dot(target[mask], weights[mask]) / local_weight)
        predicted = float(np.dot(probability[mask], weights[mask]) / local_weight)
        error += local_weight / total * abs(observed - predicted)
    return error


def probability_metrics(frame: pd.DataFrame) -> dict[str, float]:
    target = frame["target"].to_numpy(dtype=int)
    probability = frame["probability"].to_numpy(dtype=float)
    weights = frame["structural_weight"].to_numpy(dtype=float)
    return {
        "weighted_roc_auc": float(
            roc_auc_score(target, probability, sample_weight=weights)
        ),
        "weighted_average_precision": float(
            average_precision_score(target, probability, sample_weight=weights)
        ),
        "weighted_brier": float(
            brier_score_loss(target, probability, sample_weight=weights)
        ),
        "weighted_log_loss": float(
            log_loss(target, probability, sample_weight=weights, labels=[0, 1])
        ),
        "weighted_ece": weighted_ece(target, probability, weights),
    }


def weighted_max_drawdown(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    episodes = (
        frame.assign(weighted_r=frame["stress_net_r"] * frame["structural_weight"])
        .groupby("structural_episode_id", as_index=False)
        .agg(decision_time=("decision_time", "min"), weighted_r=("weighted_r", "sum"))
        .sort_values(["decision_time", "structural_episode_id"], kind="stable")
    )
    equity = episodes["weighted_r"].cumsum().to_numpy(dtype=float)
    equity = np.r_[0.0, equity]
    drawdown = np.maximum.accumulate(equity) - equity
    return float(np.max(drawdown))


def economic_metrics(
    frame: pd.DataFrame,
    selected: pd.Series | np.ndarray,
    *,
    weekdays: int,
) -> dict[str, float | int | None]:
    mask = np.asarray(selected, dtype=bool)
    local = frame.loc[mask].copy()
    if local.empty:
        return {
            "rows": 0,
            "episodes": 0,
            "selected_fraction": 0.0,
            "weighted_mean_stress_r": None,
            "weighted_profit_factor": None,
            "weighted_r_sum": 0.0,
            "weighted_max_drawdown_r": 0.0,
            "win_rate": None,
            "raw_candidates_per_weekday": 0.0,
            "structural_episodes_per_weekday": 0.0,
        }
    weights = local["structural_weight"].to_numpy(dtype=float)
    values = local["stress_net_r"].to_numpy(dtype=float)
    weighted = weights * values
    gains = float(weighted[weighted > 0.0].sum())
    losses = float(-weighted[weighted < 0.0].sum())
    return {
        "rows": len(local),
        "episodes": int(local["structural_episode_id"].nunique()),
        "selected_fraction": len(local) / len(frame),
        "weighted_mean_stress_r": weighted_mean_and_se(values, weights)[0],
        "weighted_profit_factor": gains / losses if losses > 0.0 else None,
        "weighted_r_sum": float(weighted.sum()),
        "weighted_max_drawdown_r": weighted_max_drawdown(local),
        "win_rate": float(local["target"].mean()),
        "raw_candidates_per_weekday": len(local) / weekdays,
        "structural_episodes_per_weekday": local["structural_episode_id"].nunique()
        / weekdays,
    }


def pooled_attribution(
    frame: pd.DataFrame, columns: Sequence[str]
) -> list[dict[str, Any]]:
    selected = frame.loc[frame["selected"]].copy()
    total_weight = float(selected["structural_weight"].sum())
    rows: list[dict[str, Any]] = []
    for column in columns:
        for value, local in selected.groupby(column, dropna=False, sort=True):
            weights = local["structural_weight"].to_numpy(dtype=float)
            outcome = local["stress_net_r"].to_numpy(dtype=float)
            rows.append(
                {
                    "dimension": column,
                    "value": str(value),
                    "rows": len(local),
                    "weight_fraction": float(weights.sum() / total_weight)
                    if total_weight > 0.0
                    else 0.0,
                    "weighted_mean_stress_r": weighted_mean_and_se(outcome, weights)[0],
                }
            )
    return rows

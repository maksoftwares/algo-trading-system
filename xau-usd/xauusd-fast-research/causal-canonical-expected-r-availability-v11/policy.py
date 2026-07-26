from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if hasattr(value, "item"):
        return json_ready(value.item())
    return value


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(dict(value)), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def resolve_inputs(repo_root: Path, config: Mapping[str, Any]) -> dict[str, Path]:
    result = {}
    for name, spec in config["inputs"].items():
        path = repo_root / str(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        if sha256_file(path) != str(spec["sha256"]):
            raise ValueError(f"Input hash mismatch: {name}")
        result[name] = path
    return result


def weighted_profit_factor(values: np.ndarray, weights: np.ndarray) -> float | None:
    positive = float(np.dot(np.clip(values, 0.0, None), weights))
    negative = float(np.dot(np.clip(-values, 0.0, None), weights))
    if negative == 0.0:
        return None if positive == 0.0 else float("inf")
    return positive / negative


def weighted_drawdown(frame: pd.DataFrame) -> float:
    episodes = (
        frame.assign(weighted_return=frame["stress_net_r"] * frame["structural_weight"])
        .groupby("structural_episode_id", sort=False)
        .agg(
            decision_time=("decision_time", "min"),
            weighted_return=("weighted_return", "sum"),
        )
        .sort_values("decision_time", kind="mergesort")
    )
    equity = episodes["weighted_return"].cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def business_days(start: pd.Timestamp, end: pd.Timestamp) -> int:
    first = pd.Timestamp(start).tz_localize(None).normalize()
    last = pd.Timestamp(end).tz_localize(None).normalize()
    return int(len(pd.date_range(first, last, freq="B")))


def economics(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    weights = frame["structural_weight"].to_numpy(dtype=float)
    values = frame["stress_net_r"].to_numpy(dtype=float)
    return {
        "rows": int(len(frame)),
        "episodes": int(frame["structural_episode_id"].nunique()),
        "weight": float(weights.sum()),
        "weighted_mean_r": float(np.dot(values, weights) / weights.sum()),
        "weighted_r_sum": float(np.dot(values, weights)),
        "weighted_profit_factor": weighted_profit_factor(values, weights),
        "weighted_max_drawdown_r": weighted_drawdown(frame),
        "weighted_win_rate": float(np.average(values > 0.0, weights=weights)),
        "candidates_per_weekday": float(len(frame) / business_days(start, end)),
    }


def comparison(frame: pd.DataFrame) -> dict[str, Any]:
    ordered = frame.sort_values(["decision_time", "candidate_id"], kind="mergesort")
    selected = ordered.loc[ordered["selected"]]
    start = ordered["decision_time"].min()
    end = ordered["decision_time"].max()
    baseline = economics(ordered, start, end)
    retained = economics(selected, start, end)
    weights = ordered["structural_weight"].to_numpy(dtype=float)
    target = ordered["stress_net_r_positive"].astype(int)
    return {
        "baseline": baseline,
        "selected": retained,
        "weighted_score_auc": float(
            roc_auc_score(target, ordered["model_score"], sample_weight=weights)
        ),
        "selected_weight_coverage": float(
            selected["structural_weight"].sum() / ordered["structural_weight"].sum()
        ),
        "selected_mean_lift_r": float(
            retained["weighted_mean_r"] - baseline["weighted_mean_r"]
        ),
        "drawdown_ratio_to_baseline": float(
            retained["weighted_max_drawdown_r"] / baseline["weighted_max_drawdown_r"]
        ),
    }


def bootstrap_statistics(frame: pd.DataFrame) -> np.ndarray:
    weights = frame["structural_weight"].to_numpy(dtype=float)
    values = frame["stress_net_r"].to_numpy(dtype=float)
    selected = frame["selected"].to_numpy(dtype=bool)
    selected_weights = weights[selected]
    selected_values = values[selected]
    selected_mean = float(
        np.dot(selected_values, selected_weights) / selected_weights.sum()
    )
    baseline_mean = float(np.dot(values, weights) / weights.sum())
    return np.asarray(
        [
            selected_mean,
            baseline_mean,
            selected_mean - baseline_mean,
            weighted_profit_factor(selected_values, selected_weights),
            selected_weights.sum() / weights.sum(),
        ],
        dtype=float,
    )


def weekly_bootstrap(
    frame: pd.DataFrame,
    *,
    resamples: int,
    confidence: float,
    seed: int,
) -> dict[str, Any]:
    source = frame.reset_index(drop=True).copy()
    source["utc_week"] = source["decision_time"].dt.strftime("%G-W%V")
    groups = [
        group.index.to_numpy() for _, group in source.groupby("utc_week", sort=True)
    ]
    rng = np.random.default_rng(seed)
    values = np.empty((int(resamples), 5), dtype=float)
    for index in range(int(resamples)):
        block_ids = rng.integers(0, len(groups), len(groups))
        sample = source.loc[np.concatenate([groups[block] for block in block_ids])]
        values[index] = bootstrap_statistics(sample)
    alpha = (1.0 - confidence) / 2.0
    names = [
        "selected_weighted_mean_r",
        "baseline_weighted_mean_r",
        "selected_mean_lift_r",
        "selected_profit_factor",
        "selected_weight_coverage",
    ]
    return {
        "schema_version": "xauusd_expected_r_availability_v11_bootstrap",
        "resamples": int(resamples),
        "confidence": float(confidence),
        "seed": int(seed),
        "weekly_blocks": int(len(groups)),
        "intervals": {
            name: {
                "lower": float(np.quantile(values[:, index], alpha)),
                "median": float(np.quantile(values[:, index], 0.5)),
                "upper": float(np.quantile(values[:, index], 1.0 - alpha)),
            }
            for index, name in enumerate(names)
        },
    }


def apply_availability(
    predictions: pd.DataFrame,
    fold_metrics: pd.DataFrame,
    minimum_fit_rows: int,
) -> pd.DataFrame:
    fit_rows = fold_metrics.set_index("fold_id")["fit_rows"].astype(int).to_dict()
    result = predictions.copy()
    result["v10_selected"] = result["selected"].astype(bool)
    result["model_available"] = result["fold_id"].map(
        {fold: rows >= minimum_fit_rows for fold, rows in fit_rows.items()}
    )
    if result["model_available"].isna().any():
        raise ValueError("Prediction fold has no fit-row evidence")
    result["selected"] = np.where(
        result["model_available"],
        result["v10_selected"],
        True,
    )
    result["availability_action"] = np.where(
        result["model_available"],
        "APPLY_FROZEN_V10_SELECTION",
        "ML_ABSTAIN_RETAIN_ALL",
    )
    return result

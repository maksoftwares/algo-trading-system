from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


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
    result: dict[str, Path] = {}
    for name, spec in config["inputs"].items():
        path = repo_root / str(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != str(spec["sha256"]):
            raise ValueError(f"Input hash mismatch for {name}: {actual}")
        result[name] = path
    return result


def require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def weighted_quantile(
    values: Sequence[float],
    weights: Sequence[float],
    quantile: float,
) -> float:
    value_array = np.asarray(values, dtype=float)
    weight_array = np.asarray(weights, dtype=float)
    if len(value_array) == 0 or len(value_array) != len(weight_array):
        raise ValueError("Weighted quantile requires equal nonempty arrays")
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("Quantile must be in [0, 1]")
    if np.any(weight_array < 0.0) or float(weight_array.sum()) <= 0.0:
        raise ValueError("Weighted quantile requires positive total weight")
    order = np.argsort(value_array, kind="mergesort")
    cumulative = np.cumsum(weight_array[order])
    index = int(
        np.searchsorted(cumulative, quantile * float(weight_array.sum()), side="left")
    )
    return float(value_array[order[min(index, len(order) - 1)]])


def weighted_profit_factor(values: np.ndarray, weights: np.ndarray) -> float | None:
    positive = float(np.dot(np.clip(values, 0.0, None), weights))
    negative = float(np.dot(np.clip(-values, 0.0, None), weights))
    if negative == 0.0:
        return None if positive == 0.0 else float("inf")
    return positive / negative


def weighted_drawdown(
    frame: pd.DataFrame,
    return_column: str = "stress_net_r",
) -> float:
    if frame.empty:
        return 0.0
    episodes = (
        frame.assign(
            weighted_return=frame[return_column] * frame["structural_weight"]
        )
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
    *,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "rows": 0,
            "episodes": 0,
            "weight": 0.0,
            "weighted_mean_r": 0.0,
            "weighted_r_sum": 0.0,
            "weighted_profit_factor": None,
            "weighted_max_drawdown_r": 0.0,
            "weighted_win_rate": 0.0,
            "normalized_weighted_usd_sum": 0.0,
            "normalized_weighted_profit_factor": None,
            "normalized_weighted_max_drawdown_usd": 0.0,
            "candidates_per_weekday": 0.0,
        }
    ordered = frame.sort_values(["decision_time", "candidate_id"], kind="mergesort")
    weights = ordered["structural_weight"].to_numpy(dtype=float)
    values = ordered["stress_net_r"].to_numpy(dtype=float)
    normalized_usd = (
        ordered["stress_net_r"] * ordered["initial_risk_usd_0p01"]
    ).to_numpy(dtype=float)
    date_start = pd.Timestamp(start if start is not None else ordered["decision_time"].min())
    date_end = pd.Timestamp(end if end is not None else ordered["decision_time"].max())
    return {
        "rows": int(len(ordered)),
        "episodes": int(ordered["structural_episode_id"].nunique()),
        "weight": float(weights.sum()),
        "weighted_mean_r": float(np.dot(values, weights) / weights.sum()),
        "weighted_r_sum": float(np.dot(values, weights)),
        "weighted_profit_factor": weighted_profit_factor(values, weights),
        "weighted_max_drawdown_r": weighted_drawdown(ordered),
        "weighted_win_rate": float(np.average(values > 0.0, weights=weights)),
        "normalized_weighted_usd_sum": float(np.dot(normalized_usd, weights)),
        "normalized_weighted_profit_factor": weighted_profit_factor(
            normalized_usd, weights
        ),
        "normalized_weighted_max_drawdown_usd": weighted_drawdown(
            ordered.assign(normalized_usd=normalized_usd),
            "normalized_usd",
        ),
        "candidates_per_weekday": float(
            len(ordered) / business_days(date_start, date_end)
        ),
    }


def comparison(frame: pd.DataFrame) -> dict[str, Any]:
    ordered = frame.sort_values(["decision_time", "candidate_id"], kind="mergesort")
    selected = ordered.loc[ordered["selected"].astype(bool)]
    start = ordered["decision_time"].min()
    end = ordered["decision_time"].max()
    baseline = economics(ordered, start=start, end=end)
    retained = economics(selected, start=start, end=end)
    return {
        "baseline": baseline,
        "selected": retained,
        "selected_weight_coverage": float(
            retained["weight"] / baseline["weight"]
        ),
        "selected_profit_delta_r": float(
            retained["weighted_r_sum"] - baseline["weighted_r_sum"]
        ),
        "selected_profit_delta_usd": float(
            retained["normalized_weighted_usd_sum"]
            - baseline["normalized_weighted_usd_sum"]
        ),
        "selected_mean_lift_r": float(
            retained["weighted_mean_r"] - baseline["weighted_mean_r"]
        ),
        "drawdown_ratio_to_baseline": float(
            retained["weighted_max_drawdown_r"]
            / baseline["weighted_max_drawdown_r"]
        ),
    }


def profit_factor_not_worse(
    selected: float | None,
    baseline: float | None,
) -> bool:
    if baseline is None:
        return True
    if selected is None:
        return False
    return float(selected) >= float(baseline)


def choose_profit_threshold(
    calibration: pd.DataFrame,
    policy: Mapping[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    require_columns(
        calibration,
        [
            "candidate_id",
            "decision_time",
            "structural_episode_id",
            "structural_weight",
            "stress_net_r",
            "initial_risk_usd_0p01",
            "model_score",
        ],
        "Calibration frame",
    )
    baseline_frame = calibration.copy()
    baseline_frame["selected"] = True
    baseline = comparison(baseline_frame)["baseline"]
    rows: list[dict[str, Any]] = []
    for quantile in policy["weighted_quantile_grid"]:
        threshold = weighted_quantile(
            calibration["model_score"],
            calibration["structural_weight"],
            float(quantile),
        )
        candidate = calibration.copy()
        candidate["selected"] = candidate["model_score"].ge(threshold)
        metrics = comparison(candidate)
        selected = metrics["selected"]
        constraints = {
            "coverage": metrics["selected_weight_coverage"]
            >= float(policy["minimum_selected_weight_coverage"]),
            "mean": (
                not bool(policy["require_mean_not_worse"])
                or selected["weighted_mean_r"] >= baseline["weighted_mean_r"]
            ),
            "profit_factor": (
                not bool(policy["require_profit_factor_not_worse"])
                or profit_factor_not_worse(
                    selected["weighted_profit_factor"],
                    baseline["weighted_profit_factor"],
                )
            ),
            "drawdown": (
                not bool(policy["require_drawdown_not_worse"])
                or selected["weighted_max_drawdown_r"]
                <= baseline["weighted_max_drawdown_r"]
            ),
        }
        rows.append(
            {
                "quantile": float(quantile),
                "threshold": float(threshold),
                "eligible": bool(all(constraints.values())),
                **{f"constraint_{key}": value for key, value in constraints.items()},
                "selected_rows": selected["rows"],
                "selected_weight": selected["weight"],
                "selected_weight_coverage": metrics["selected_weight_coverage"],
                "selected_weighted_mean_r": selected["weighted_mean_r"],
                "selected_weighted_r_sum": selected["weighted_r_sum"],
                "selected_weighted_profit_factor": selected[
                    "weighted_profit_factor"
                ],
                "selected_weighted_max_drawdown_r": selected[
                    "weighted_max_drawdown_r"
                ],
                "selected_normalized_weighted_usd_sum": selected[
                    "normalized_weighted_usd_sum"
                ],
                "selected_normalized_weighted_profit_factor": selected[
                    "normalized_weighted_profit_factor"
                ],
                "selected_normalized_weighted_max_drawdown_usd": selected[
                    "normalized_weighted_max_drawdown_usd"
                ],
                "profit_improvement_r": metrics["selected_profit_delta_r"],
                "profit_improvement_usd": metrics["selected_profit_delta_usd"],
            }
        )
    grid = pd.DataFrame(rows)
    eligible = grid.loc[grid["eligible"]].sort_values(
        ["selected_normalized_weighted_usd_sum", "quantile"],
        ascending=[False, True],
        kind="mergesort",
    )
    if eligible.empty:
        raise ValueError("Locked quantile grid has no eligible fallback")
    chosen = eligible.iloc[0].to_dict()
    if float(chosen["profit_improvement_usd"]) < float(
        policy["minimum_profit_improvement_usd"]
    ):
        fallback = grid.loc[
            grid["quantile"].eq(float(policy["fallback_quantile"]))
        ]
        if len(fallback) != 1:
            raise ValueError("Fallback quantile is missing or duplicated")
        chosen = fallback.iloc[0].to_dict()
        reason = "RETAIN_ALL_INSUFFICIENT_CALIBRATION_USD_IMPROVEMENT"
    else:
        reason = "MAXIMUM_ELIGIBLE_CALIBRATION_NORMALIZED_USD"
    chosen["selection_reason"] = reason
    return chosen, grid


def apply_profit_threshold(
    frame: pd.DataFrame,
    chosen: Mapping[str, Any],
    fallback_quantile: float,
) -> pd.DataFrame:
    result = frame.copy()
    if float(chosen["quantile"]) == float(fallback_quantile):
        result["selected"] = True
    else:
        result["selected"] = result["model_score"].ge(float(chosen["threshold"]))
    return result


def weekly_profit_bootstrap(
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
    if not groups:
        raise ValueError("Weekly bootstrap has no blocks")
    rng = np.random.default_rng(seed)
    values = np.empty((int(resamples), 7), dtype=float)
    for index in range(int(resamples)):
        sample = source.loc[
            np.concatenate(
                [groups[item] for item in rng.integers(0, len(groups), len(groups))]
            )
        ]
        metrics = comparison(sample)
        values[index] = [
            metrics["selected"]["weighted_r_sum"],
            metrics["baseline"]["weighted_r_sum"],
            metrics["selected_profit_delta_r"],
            metrics["selected"]["normalized_weighted_usd_sum"],
            metrics["baseline"]["normalized_weighted_usd_sum"],
            metrics["selected_profit_delta_usd"],
            metrics["selected"]["weighted_profit_factor"],
        ]
    alpha = (1.0 - confidence) / 2.0
    names = [
        "selected_weighted_r_sum",
        "baseline_weighted_r_sum",
        "selected_profit_delta_r",
        "selected_normalized_usd_sum",
        "baseline_normalized_usd_sum",
        "selected_profit_delta_usd",
        "selected_profit_factor",
    ]
    return {
        "schema_version": "xauusd_profit_policy_v12_weekly_bootstrap",
        "resamples": int(resamples),
        "confidence": float(confidence),
        "seed": int(seed),
        "weekly_blocks": int(len(groups)),
        "intervals": {
            name: {
                "lower": float(np.quantile(values[:, column], alpha)),
                "median": float(np.quantile(values[:, column], 0.5)),
                "upper": float(np.quantile(values[:, column], 1.0 - alpha)),
            }
            for column, name in enumerate(names)
        },
    }

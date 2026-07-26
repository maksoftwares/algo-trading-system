from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
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


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(json_ready(value), indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def resolve_inputs(repo_root: Path, config: dict[str, Any]) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for name, spec in config["inputs"].items():
        path = repo_root / str(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != str(spec["sha256"]):
            raise ValueError(f"Input hash mismatch for {name}: {actual}")
        paths[name] = path
    return paths


def require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def assign_model_lane(frame: pd.DataFrame, ownership: Mapping[str, Any]) -> pd.Series:
    priority = list(ownership["priority"])
    flags = dict(ownership["flag_columns"])
    result = pd.Series(pd.NA, index=frame.index, dtype="string")
    # Iterate from lowest to highest priority so higher-priority matches overwrite.
    for lane in reversed(priority):
        result.loc[frame[str(flags[lane])].eq(1.0)] = lane
    if result.isna().any():
        raise ValueError("A V3 event has no model-lane owner")
    return result.astype(str)


def prepare_dataset(
    dataset: pd.DataFrame,
    config: dict[str, Any],
    features: Sequence[str],
) -> pd.DataFrame:
    required = [
        "candidate_id",
        "event_id",
        "structural_episode_id",
        "signal_time",
        "label_end_time",
        "entry_time",
        "exit_time",
        "direction",
        "regime",
        "action_id",
        "stress_net_r",
        "stress_net_r_positive",
        "structural_weight",
        "resolved_events_in_structural_episode",
        *features,
        *config["lane_ownership"]["flag_columns"].values(),
    ]
    require_columns(dataset, required, "V3 action dataset")
    if len(dataset) != int(config["expected"]["action_rows"]):
        raise ValueError("V3 action row count changed")
    result = dataset.copy()
    for column in ("signal_time", "label_end_time", "entry_time", "exit_time"):
        result[column] = pd.to_datetime(result[column], utc=True)
    if result["candidate_id"].duplicated().any():
        raise ValueError("V3 candidate IDs are duplicated")
    numeric = result[list(features)].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("V3 model features contain non-finite values")
    result["model_lane"] = assign_model_lane(result, config["lane_ownership"])
    result["event_eval_weight"] = 1.0 / result[
        "resolved_events_in_structural_episode"
    ].astype(float)
    result["target_fit"] = result["stress_net_r"].clip(
        lower=float(config["target"]["clip_min_r"]),
        upper=float(config["target"]["clip_max_r"]),
    )
    result["action_tie_rank"] = result["action_id"].map(
        {action: index for index, action in enumerate(config["action_tie_order"])}
    )
    if result["action_tie_rank"].isna().any():
        raise ValueError("V3 dataset contains an unlocked action")
    excluded = set(config["exclusions"]["regimes"])
    result["model_eligible"] = ~result["regime"].isin(excluded)
    return result


def build_model(spec: Mapping[str, Any]) -> Any:
    kind = str(spec["kind"])
    parameters = dict(spec["parameters"])
    if kind == "RIDGE":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", Ridge(**parameters)),
            ]
        )
    if kind == "HIST_GRADIENT_BOOSTING":
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("model", HistGradientBoostingRegressor(**parameters)),
            ]
        )
    raise ValueError(f"Unknown model kind: {kind}")


def fit_model(
    frame: pd.DataFrame,
    *,
    features: Sequence[str],
    spec: Mapping[str, Any],
) -> Any:
    model = build_model(spec)
    model.fit(
        frame[list(features)],
        frame["target_fit"].to_numpy(dtype=float),
        model__sample_weight=frame["structural_weight"].to_numpy(dtype=float),
    )
    return model


def predict_model(
    model: Any, frame: pd.DataFrame, features: Sequence[str]
) -> np.ndarray:
    return np.asarray(model.predict(frame[list(features)]), dtype=float)


def choose_best_action(scored: pd.DataFrame) -> pd.DataFrame:
    ordered = scored.sort_values(
        ["event_id", "model_score", "action_tie_rank", "candidate_id"],
        ascending=[True, False, True, True],
        kind="mergesort",
    )
    return ordered.drop_duplicates("event_id", keep="first").sort_values(
        ["signal_time", "event_id"], kind="mergesort"
    )


def _weighted_mean_and_se(
    values: np.ndarray, weights: np.ndarray
) -> tuple[float, float]:
    total = float(weights.sum())
    if total <= 0:
        return 0.0, float("inf")
    mean = float(np.dot(values, weights) / total)
    variance = float(np.dot(weights, np.square(values - mean)) / total)
    effective = float(total * total / np.square(weights).sum())
    se = math.sqrt(max(0.0, variance) / max(1.0, effective))
    return mean, se


def fixed_action_ranking(
    calibration: pd.DataFrame, action_tie_order: Sequence[str]
) -> tuple[list[str], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    tie = {action: index for index, action in enumerate(action_tie_order)}
    for action in action_tie_order:
        group = calibration.loc[calibration["action_id"].eq(action)]
        values = group["stress_net_r"].to_numpy(dtype=float)
        weights = group["event_eval_weight"].to_numpy(dtype=float)
        mean, se = _weighted_mean_and_se(values, weights)
        rows.append(
            {
                "action_id": action,
                "events": int(group["event_id"].nunique()),
                "weighted_mean_stress_r": mean,
                "standard_error_r": se,
                "utility": mean - se,
                "tie_rank": tie[action],
            }
        )
    ordered = sorted(rows, key=lambda row: (-row["utility"], row["tie_rank"]))
    return [str(row["action_id"]) for row in ordered], ordered


def apply_fixed_action_cascade(
    frame: pd.DataFrame, action_ranking: Sequence[str]
) -> pd.DataFrame:
    rank = {action: index for index, action in enumerate(action_ranking)}
    result = frame.copy()
    result["fixed_action_rank"] = result["action_id"].map(rank)
    if result["fixed_action_rank"].isna().any():
        raise ValueError("Fixed-action cascade encountered an unknown action")
    return (
        result.sort_values(
            ["event_id", "fixed_action_rank", "candidate_id"], kind="mergesort"
        )
        .drop_duplicates("event_id", keep="first")
        .sort_values(["signal_time", "event_id"], kind="mergesort")
    )


def weighted_profit_factor(values: np.ndarray, weights: np.ndarray) -> float | None:
    positive = float(np.dot(np.clip(values, 0.0, None), weights))
    negative = float(np.dot(np.clip(-values, 0.0, None), weights))
    if negative == 0.0:
        return None if positive == 0.0 else float("inf")
    return positive / negative


def weighted_drawdown(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    episode = (
        frame.assign(weighted_return=frame["event_eval_weight"] * frame["stress_net_r"])
        .groupby("structural_episode_id", sort=False)
        .agg(
            signal_time=("signal_time", "min"),
            weighted_return=("weighted_return", "sum"),
        )
        .sort_values("signal_time", kind="mergesort")
    )
    equity = episode["weighted_return"].cumsum()
    return float((equity.cummax() - equity).max()) if len(equity) else 0.0


def business_days(start: pd.Timestamp, end: pd.Timestamp) -> int:
    first = pd.Timestamp(start).tz_localize(None).normalize()
    last = (
        pd.Timestamp(end).tz_localize(None) - pd.Timedelta(microseconds=1)
    ).normalize()
    return int(len(pd.date_range(first, last, freq="B")))


def economic_metrics(
    frame: pd.DataFrame,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    top_winners_removed: int,
) -> dict[str, Any]:
    if frame.empty:
        return {
            "events": 0,
            "episodes": 0,
            "events_per_weekday": 0.0,
            "weight_sum": 0.0,
            "weighted_mean_stress_r": 0.0,
            "weighted_r_sum": 0.0,
            "weighted_profit_factor": None,
            "weighted_max_drawdown_r": 0.0,
            "win_rate": 0.0,
            "top_winners_removed_weighted_r_sum": 0.0,
        }
    values = frame["stress_net_r"].to_numpy(dtype=float)
    weights = frame["event_eval_weight"].to_numpy(dtype=float)
    weight_sum = float(weights.sum())
    weighted_contribution = values * weights
    remove = min(int(top_winners_removed), len(frame))
    keep = np.ones(len(frame), dtype=bool)
    if remove:
        keep[np.argpartition(weighted_contribution, -remove)[-remove:]] = False
    return {
        "events": int(frame["event_id"].nunique()),
        "episodes": int(frame["structural_episode_id"].nunique()),
        "events_per_weekday": float(
            frame["event_id"].nunique() / business_days(start, end)
        ),
        "weight_sum": weight_sum,
        "weighted_mean_stress_r": float(np.dot(values, weights) / weight_sum),
        "weighted_r_sum": float(weighted_contribution.sum()),
        "weighted_profit_factor": weighted_profit_factor(values, weights),
        "weighted_max_drawdown_r": weighted_drawdown(frame),
        "win_rate": float(np.average(values > 0.0, weights=weights)),
        "top_winners_removed_weighted_r_sum": float(weighted_contribution[keep].sum()),
    }


def weighted_auc(frame: pd.DataFrame) -> float | None:
    target = frame["stress_net_r_positive"].astype(int)
    if target.nunique() < 2:
        return None
    return float(
        roc_auc_score(
            target,
            frame["model_score"],
            sample_weight=frame["structural_weight"],
        )
    )


def baseline_retention(selected_r_sum: float, baseline_r_sum: float) -> float | None:
    if baseline_r_sum <= 0.0:
        return None
    return float(selected_r_sum / baseline_r_sum)


def calibration_checks(
    selected_metrics: Mapping[str, Any],
    baseline_metrics: Mapping[str, Any],
    selected_fraction: float,
    gates: Mapping[str, Any],
) -> dict[str, bool]:
    selected_pf = selected_metrics["weighted_profit_factor"]
    retention = baseline_retention(
        float(selected_metrics["weighted_r_sum"]),
        float(baseline_metrics["weighted_r_sum"]),
    )
    retention_ok = (
        float(selected_metrics["weighted_r_sum"])
        >= float(baseline_metrics["weighted_r_sum"])
        if retention is None
        else retention >= float(gates["minimum_baseline_r_retention"])
    )
    return {
        "minimum_selected_events": int(selected_metrics["events"])
        >= int(gates["minimum_selected_events"]),
        "minimum_selected_fraction": selected_fraction
        >= float(gates["minimum_selected_fraction"]),
        "maximum_selected_fraction": selected_fraction
        <= float(gates["maximum_selected_fraction"]),
        "minimum_selected_mean_stress_r": float(
            selected_metrics["weighted_mean_stress_r"]
        )
        >= float(gates["minimum_selected_mean_stress_r"]),
        "minimum_selected_profit_factor": selected_pf is not None
        and float(selected_pf) >= float(gates["minimum_selected_profit_factor"]),
        "minimum_baseline_r_retention": retention_ok,
    }


def build_event_comparison(
    selected: pd.DataFrame,
    baseline: pd.DataFrame,
    *,
    lane: str,
    fold_id: str,
) -> pd.DataFrame:
    base = baseline[
        [
            "event_id",
            "structural_episode_id",
            "signal_time",
            "event_eval_weight",
            "action_id",
            "stress_net_r",
        ]
    ].rename(
        columns={
            "action_id": "baseline_action_id",
            "stress_net_r": "baseline_stress_r",
        }
    )
    chosen = selected[["event_id", "action_id", "stress_net_r", "model_score"]].rename(
        columns={
            "action_id": "selected_action_id",
            "stress_net_r": "selected_stress_r",
        }
    )
    result = base.merge(chosen, on="event_id", how="left", validate="one_to_one")
    result["selected"] = result["selected_action_id"].notna()
    result["baseline_return"] = (
        result["event_eval_weight"] * result["baseline_stress_r"]
    )
    result["selected_return"] = np.where(
        result["selected"],
        result["event_eval_weight"] * result["selected_stress_r"],
        0.0,
    )
    result["baseline_weight"] = result["event_eval_weight"]
    result["selected_weight"] = np.where(
        result["selected"], result["event_eval_weight"], 0.0
    )
    result["common_baseline_return"] = np.where(
        result["selected"], result["baseline_return"], 0.0
    )
    result["common_weight"] = result["selected_weight"]
    result["model_lane"] = lane
    result["fold_id"] = fold_id
    return result


def comparison_metrics(comparison: pd.DataFrame) -> dict[str, float | None]:
    selected_weight = float(comparison["selected_weight"].sum())
    common_weight = float(comparison["common_weight"].sum())
    baseline_weight = float(comparison["baseline_weight"].sum())
    selected_mean = (
        float(comparison["selected_return"].sum() / selected_weight)
        if selected_weight
        else 0.0
    )
    common_baseline_mean = (
        float(comparison["common_baseline_return"].sum() / common_weight)
        if common_weight
        else 0.0
    )
    total_delta = (
        float(
            (comparison["selected_return"].sum() - comparison["baseline_return"].sum())
            / baseline_weight
        )
        if baseline_weight
        else 0.0
    )
    return {
        "common_event_action_uplift_r": selected_mean - common_baseline_mean,
        "total_policy_delta_r_per_episode": total_delta,
        "baseline_r_retention": baseline_retention(
            float(comparison["selected_return"].sum()),
            float(comparison["baseline_return"].sum()),
        ),
    }


def _week_start(series: pd.Series) -> pd.Series:
    normalized = series.dt.tz_convert("UTC").dt.normalize()
    return normalized - pd.to_timedelta(normalized.dt.weekday, unit="D")


def bootstrap_comparison(
    comparison: pd.DataFrame,
    *,
    resamples: int,
    confidence: float,
    seed: int,
) -> dict[str, Any]:
    frame = comparison.copy()
    frame["week_start"] = _week_start(frame["signal_time"])
    weekly = frame.groupby("week_start", sort=True)[
        [
            "selected_return",
            "selected_weight",
            "common_baseline_return",
            "common_weight",
            "baseline_return",
            "baseline_weight",
        ]
    ].sum()
    values = weekly.to_numpy(dtype=float)
    if len(values) < 2:
        raise ValueError("Weekly bootstrap requires at least two blocks")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(values), size=(int(resamples), len(values)))
    sampled = values[indices].sum(axis=1)
    selected_mean = sampled[:, 0] / sampled[:, 1]
    common_baseline_mean = sampled[:, 2] / sampled[:, 3]
    quality_delta = selected_mean - common_baseline_mean
    total_delta = (sampled[:, 0] - sampled[:, 4]) / sampled[:, 5]
    alpha = (1.0 - float(confidence)) / 2.0

    def interval(sample: np.ndarray) -> dict[str, float]:
        return {
            "lower": float(np.quantile(sample, alpha)),
            "median": float(np.quantile(sample, 0.5)),
            "upper": float(np.quantile(sample, 1.0 - alpha)),
        }

    return {
        "blocks": int(len(weekly)),
        "resamples": int(resamples),
        "confidence": float(confidence),
        "seed": int(seed),
        "selected_mean_stress_r": interval(selected_mean),
        "common_event_action_uplift_r": interval(quality_delta),
        "total_policy_delta_r_per_episode": interval(total_delta),
    }

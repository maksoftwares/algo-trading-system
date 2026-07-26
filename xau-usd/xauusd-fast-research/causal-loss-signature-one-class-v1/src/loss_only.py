from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, roc_auc_score


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


def write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
        result[str(name)] = path
    return result


def require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def prepare_dataset(
    frame: pd.DataFrame, config: Mapping[str, Any], features: Sequence[str]
) -> pd.DataFrame:
    required = [
        "candidate_id",
        "structural_episode_id",
        "signal_time",
        "label_end_time",
        "stress_net_r",
        "stress_net_r_positive",
        "structural_weight",
        "current_account_feasible",
        "mechanism_signature",
        "direction",
        "regime",
        "action_id",
        *features,
    ]
    require_columns(frame, required, "Expanded V4 action dataset")
    expected = config["population"]
    if len(frame) != int(expected["rows"]):
        raise ValueError("Expanded V4 row count changed")
    result = frame.copy()
    if result["candidate_id"].duplicated().any():
        raise ValueError("Expanded V4 candidate IDs are duplicated")
    result["signal_time"] = pd.to_datetime(result["signal_time"], utc=True)
    result["label_end_time"] = pd.to_datetime(result["label_end_time"], utc=True)
    numeric = result[list(features)].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Loss-only model features contain non-finite values")
    if (result["structural_weight"].astype(float) <= 0.0).any():
        raise ValueError("Structural weights must be positive")
    failures = int((~result["stress_net_r_positive"].astype(bool)).sum())
    winners = int(result["stress_net_r_positive"].astype(bool).sum())
    if failures != int(expected["stressed_failures"]):
        raise ValueError("Expanded V4 failure count changed")
    if winners != int(expected["stressed_winners"]):
        raise ValueError("Expanded V4 winner count changed")
    return result


def partition_for(
    frame: pd.DataFrame,
    splits: pd.DataFrame,
    *,
    fold_id: str,
    partition: str,
) -> pd.DataFrame:
    local = splits.loc[
        splits["fold_id"].eq(fold_id)
        & splits["partition"].eq(partition)
        & splits["eligible"].astype(bool)
    ]
    episodes = set(local["structural_episode_id"].astype(str))
    result = frame.loc[frame["structural_episode_id"].isin(episodes)].copy()
    return result.sort_values(["signal_time", "candidate_id"], kind="mergesort")


def weighted_quantile(
    values: np.ndarray, weights: np.ndarray, quantile: float
) -> float:
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if len(values) == 0 or len(values) != len(weights):
        raise ValueError("Weighted quantile inputs are empty or misaligned")
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("Quantile must be between zero and one")
    if not np.isfinite(values).all() or not np.isfinite(weights).all():
        raise ValueError("Weighted quantile inputs must be finite")
    if (weights < 0.0).any() or float(weights.sum()) <= 0.0:
        raise ValueError("Weighted quantile weights must be nonnegative")
    order = np.argsort(values, kind="mergesort")
    ordered_values = values[order]
    cumulative = np.cumsum(weights[order])
    index = int(np.searchsorted(cumulative, quantile * cumulative[-1], side="left"))
    return float(ordered_values[min(index, len(ordered_values) - 1)])


def fit_loss_model(
    loss_rows: pd.DataFrame,
    *,
    features: Sequence[str],
    model_config: Mapping[str, Any],
) -> IsolationForest:
    if loss_rows["stress_net_r_positive"].astype(bool).any():
        raise ValueError("Winning rows reached loss-only model fitting")
    if len(loss_rows) == 0:
        raise ValueError("Loss-only fit population is empty")
    parameters = dict(model_config)
    parameters.pop("kind", None)
    model = IsolationForest(**parameters)
    model.fit(
        loss_rows[list(features)].to_numpy(dtype=float),
        sample_weight=loss_rows["structural_weight"].to_numpy(dtype=float),
    )
    return model


def loss_similarity(
    model: IsolationForest, frame: pd.DataFrame, features: Sequence[str]
) -> np.ndarray:
    return np.asarray(
        model.score_samples(frame[list(features)].to_numpy(dtype=float)), dtype=float
    )


def _ratio(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator > 0.0 else 0.0


def weighted_profit_factor(values: np.ndarray, weights: np.ndarray) -> float | None:
    gains = float(np.dot(weights, np.maximum(values, 0.0)))
    losses = float(-np.dot(weights, np.minimum(values, 0.0)))
    if losses <= 0.0:
        return None
    return gains / losses


def weighted_drawdown(frame: pd.DataFrame) -> float:
    if frame.empty:
        return 0.0
    ordered = frame.sort_values(["signal_time", "candidate_id"], kind="mergesort")
    increments = ordered["stress_net_r"].to_numpy(dtype=float) * ordered[
        "structural_weight"
    ].to_numpy(dtype=float)
    equity = np.cumsum(increments)
    peaks = np.maximum.accumulate(np.concatenate(([0.0], equity)))[:-1]
    return float(np.max(peaks - equity, initial=0.0))


def subset_economics(frame: pd.DataFrame, mask: np.ndarray) -> dict[str, Any]:
    local = frame.loc[np.asarray(mask, dtype=bool)]
    if local.empty:
        return {
            "rows": 0,
            "weighted_rows": 0.0,
            "weighted_mean_stress_r": 0.0,
            "weighted_profit_factor": None,
            "weighted_max_drawdown_r": 0.0,
        }
    values = local["stress_net_r"].to_numpy(dtype=float)
    weights = local["structural_weight"].to_numpy(dtype=float)
    return {
        "rows": len(local),
        "weighted_rows": float(weights.sum()),
        "weighted_mean_stress_r": float(np.dot(values, weights) / weights.sum()),
        "weighted_profit_factor": weighted_profit_factor(values, weights),
        "weighted_max_drawdown_r": weighted_drawdown(local),
    }


def loss_veto_metrics(frame: pd.DataFrame, flagged: np.ndarray) -> dict[str, Any]:
    flagged = np.asarray(flagged, dtype=bool)
    if len(frame) != len(flagged):
        raise ValueError("Flag mask does not align with evaluation rows")
    weights = frame["structural_weight"].to_numpy(dtype=float)
    losses = ~frame["stress_net_r_positive"].astype(bool).to_numpy()
    total_weight = float(weights.sum())
    loss_weight = float(weights[losses].sum())
    winner_weight = float(weights[~losses].sum())
    flagged_weight = float(weights[flagged].sum())
    flagged_loss_weight = float(weights[flagged & losses].sum())
    flagged_winner_weight = float(weights[flagged & ~losses].sum())
    baseline = subset_economics(frame, np.ones(len(frame), dtype=bool))
    vetoed = subset_economics(frame, flagged)
    retained = subset_economics(frame, ~flagged)
    baseline_loss_rate = _ratio(loss_weight, total_weight)
    flagged_loss_precision = _ratio(flagged_loss_weight, flagged_weight)
    retained_ev_lift = float(retained["weighted_mean_stress_r"]) - float(
        baseline["weighted_mean_stress_r"]
    )
    return {
        "weighted_loss_auc": float(
            roc_auc_score(
                losses.astype(int), frame["loss_similarity"], sample_weight=weights
            )
        ),
        "weighted_loss_average_precision": float(
            average_precision_score(
                losses.astype(int), frame["loss_similarity"], sample_weight=weights
            )
        ),
        "baseline_loss_rate": baseline_loss_rate,
        "flagged_loss_precision": flagged_loss_precision,
        "loss_precision_lift": flagged_loss_precision - baseline_loss_rate,
        "loss_recall": _ratio(flagged_loss_weight, loss_weight),
        "winner_collateral_rate": _ratio(flagged_winner_weight, winner_weight),
        "flagged_coverage": _ratio(flagged_weight, total_weight),
        "retained_coverage": _ratio(total_weight - flagged_weight, total_weight),
        "retained_ev_lift_r": retained_ev_lift,
        "baseline": baseline,
        "vetoed": vetoed,
        "retained": retained,
    }


def weekly_block_bootstrap(
    frame: pd.DataFrame, *, resamples: int, confidence: float, seed: int
) -> dict[str, Any]:
    local = frame.copy()
    local["week_block"] = local["signal_time"].dt.strftime("%G-W%V")
    local["loss_weight"] = (~local["stress_net_r_positive"].astype(bool)).astype(
        float
    ) * local["structural_weight"].astype(float)
    local["flagged_weight"] = local["flagged"].astype(float) * local[
        "structural_weight"
    ].astype(float)
    local["flagged_loss_weight"] = local["flagged"].astype(float) * local["loss_weight"]
    local["weighted_r"] = local["stress_net_r"].astype(float) * local[
        "structural_weight"
    ].astype(float)
    local["retained_weight"] = (~local["flagged"].astype(bool)).astype(float) * local[
        "structural_weight"
    ].astype(float)
    local["retained_weighted_r"] = (~local["flagged"].astype(bool)).astype(
        float
    ) * local["weighted_r"]
    columns = [
        "structural_weight",
        "loss_weight",
        "flagged_weight",
        "flagged_loss_weight",
        "weighted_r",
        "retained_weight",
        "retained_weighted_r",
    ]
    blocks = local.groupby("week_block", sort=True)[columns].sum().to_numpy(dtype=float)
    if len(blocks) < 2:
        raise ValueError("At least two weekly blocks are required")
    rng = np.random.default_rng(seed)
    precision_lifts = np.empty(resamples, dtype=float)
    ev_lifts = np.empty(resamples, dtype=float)
    for index in range(resamples):
        sampled = blocks[rng.integers(0, len(blocks), size=len(blocks))].sum(axis=0)
        (
            total_weight,
            loss_weight,
            flagged_weight,
            flagged_loss_weight,
            weighted_r,
            retained_weight,
            retained_weighted_r,
        ) = sampled
        precision_lifts[index] = _ratio(flagged_loss_weight, flagged_weight) - _ratio(
            loss_weight, total_weight
        )
        ev_lifts[index] = _ratio(retained_weighted_r, retained_weight) - _ratio(
            weighted_r, total_weight
        )
    alpha = (1.0 - confidence) / 2.0

    def interval(values: np.ndarray) -> dict[str, float]:
        return {
            "lower": float(np.quantile(values, alpha)),
            "median": float(np.quantile(values, 0.5)),
            "upper": float(np.quantile(values, 1.0 - alpha)),
        }

    return {
        "schema_version": "xauusd_loss_only_weekly_bootstrap_v1",
        "resamples": resamples,
        "confidence": confidence,
        "seed": seed,
        "weekly_blocks": len(blocks),
        "loss_precision_lift": interval(precision_lifts),
        "retained_ev_lift_r": interval(ev_lifts),
    }

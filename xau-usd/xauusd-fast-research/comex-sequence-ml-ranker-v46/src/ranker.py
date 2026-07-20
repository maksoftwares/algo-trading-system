from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score


MODEL_FEATURES = [
    "log_current_trade_count_5s",
    "log_prior_trade_count_30s",
    "log_current_volume_5s",
    "current_imbalance_5s",
    "same_side_transition_share_5s",
    "log_arrival_acceleration",
    "log_terminal_run_trades",
    "log_terminal_run_volume",
    "current_directional_impulse_ticks",
    "terminal_direction_sign",
    "session_progress",
]
REQUIRED_CANDIDATE_COLUMNS = {
    "candidate_id",
    "feature_time_utc",
    "direction",
    "current_trade_count_5s",
    "prior_trade_count_30s",
    "current_volume_5s",
    "current_imbalance_5s",
    "same_side_transition_share_5s",
    "arrival_acceleration",
    "terminal_run_trades",
    "terminal_run_volume",
    "current_directional_impulse_ticks",
    "terminal_run_sign",
}


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_matrix(candidates: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(REQUIRED_CANDIDATE_COLUMNS - set(candidates.columns))
    if missing:
        raise ValueError(f"Ranker candidates are missing columns: {missing}")
    frame = candidates.copy()
    timestamp = pd.to_datetime(frame["feature_time_utc"], utc=True)
    local = timestamp.dt.tz_convert("America/New_York")
    local_minutes = local.dt.hour * 60 + local.dt.minute + local.dt.second / 60.0
    matrix = pd.DataFrame(index=frame.index)
    matrix["log_current_trade_count_5s"] = np.log1p(
        frame["current_trade_count_5s"].clip(lower=0).astype(float)
    )
    matrix["log_prior_trade_count_30s"] = np.log1p(
        frame["prior_trade_count_30s"].clip(lower=0).astype(float)
    )
    matrix["log_current_volume_5s"] = np.log1p(
        frame["current_volume_5s"].clip(lower=0).astype(float)
    )
    matrix["current_imbalance_5s"] = frame["current_imbalance_5s"].astype(float)
    matrix["same_side_transition_share_5s"] = frame[
        "same_side_transition_share_5s"
    ].astype(float)
    matrix["log_arrival_acceleration"] = np.log1p(
        frame["arrival_acceleration"].clip(lower=0, upper=20).astype(float)
    )
    matrix["log_terminal_run_trades"] = np.log1p(
        frame["terminal_run_trades"].clip(lower=0).astype(float)
    )
    matrix["log_terminal_run_volume"] = np.log1p(
        frame["terminal_run_volume"].clip(lower=0).astype(float)
    )
    matrix["current_directional_impulse_ticks"] = (
        frame["current_directional_impulse_ticks"].clip(lower=0, upper=50).astype(float)
    )
    matrix["terminal_direction_sign"] = np.sign(
        frame["terminal_run_sign"].astype(float)
    )
    matrix["session_progress"] = ((local_minutes - 500.0) / 310.0).clip(0.0, 1.0)
    matrix = matrix[MODEL_FEATURES]
    values = matrix.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Ranker feature matrix contains non-finite values.")
    return matrix


def build_model(config: Mapping[str, Any]) -> HistGradientBoostingClassifier:
    settings = config["model"]
    return HistGradientBoostingClassifier(
        learning_rate=float(settings["learning_rate"]),
        max_iter=int(settings["max_iter"]),
        max_leaf_nodes=int(settings["max_leaf_nodes"]),
        min_samples_leaf=int(settings["min_samples_leaf"]),
        l2_regularization=float(settings["l2_regularization"]),
        early_stopping=bool(settings["early_stopping"]),
        random_state=int(settings["random_state"]),
    )


def merge_resolved(candidates: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
    if candidates["candidate_id"].duplicated().any():
        raise ValueError("Candidate IDs are not unique.")
    if labels["candidate_id"].duplicated().any():
        raise ValueError("Label IDs are not unique.")
    resolved = labels.loc[labels["status"] == "RESOLVED"].copy()
    merged = candidates.merge(
        resolved,
        on="candidate_id",
        how="inner",
        suffixes=("", "_label"),
        validate="one_to_one",
    )
    if merged.empty:
        raise ValueError("No resolved candidate labels are available.")
    return merged


def candidate_facts(
    candidates: pd.DataFrame, *, eligible_dates: Sequence[str]
) -> dict[str, Any]:
    count = len(candidates)
    if count:
        dates = pd.to_datetime(candidates["feature_time_utc"], utc=True).dt.date.astype(
            str
        )
        active_days = int(dates.nunique())
        long_count = int((candidates["direction"] == "LONG").sum())
        short_count = int((candidates["direction"] == "SHORT").sum())
    else:
        active_days = long_count = short_count = 0
    days = len(eligible_dates)
    return {
        "accepted_candidates": count,
        "eligible_full_weekdays": days,
        "candidates_per_full_weekday": count / days if days else 0.0,
        "active_days": active_days,
        "active_day_share": active_days / days if days else 0.0,
        "long_candidates": long_count,
        "short_candidates": short_count,
        "minority_direction_share": min(long_count, short_count) / count
        if count
        else 0.0,
    }


def select_threshold(
    candidates: pd.DataFrame,
    scores: np.ndarray,
    *,
    eligible_dates: Sequence[str],
    selection: Mapping[str, Any],
) -> tuple[float, dict[str, Any]] | None:
    if len(candidates) != len(scores):
        raise ValueError("Candidate and score lengths differ.")
    rows: list[tuple[float, dict[str, Any]]] = []
    score_values = np.asarray(scores, dtype=float)
    for threshold in np.unique(score_values):
        accepted = candidates.loc[score_values >= threshold]
        facts = candidate_facts(accepted, eligible_dates=eligible_dates)
        eligible = bool(
            float(selection["minimum_candidates_per_full_weekday"])
            <= facts["candidates_per_full_weekday"]
            <= float(selection["maximum_candidates_per_full_weekday"])
            and facts["active_day_share"]
            >= float(selection["minimum_active_day_share"])
            and facts["minority_direction_share"]
            >= float(selection["minimum_minority_direction_share"])
        )
        if eligible:
            rows.append((float(threshold), facts))
    if not rows:
        return None
    target = float(selection["target_candidates_per_full_weekday"])
    rows.sort(
        key=lambda item: (
            abs(item[1]["candidates_per_full_weekday"] - target),
            -item[0],
        )
    )
    return rows[0]


def rank_auc(labels: pd.Series, scores: np.ndarray) -> float | None:
    values = labels.astype(int).to_numpy()
    if np.unique(values).size != 2:
        return None
    return float(roc_auc_score(values, scores))


def eligible_dates_from_audit(
    audit: Mapping[str, Any], *, start: pd.Timestamp, end: pd.Timestamp
) -> list[str]:
    dates = []
    for row in audit["session_quality"]:
        if not row["eligible_full_weekday"]:
            continue
        date = pd.Timestamp(str(row["date_utc"]), tz="UTC")
        if start <= date < end:
            dates.append(str(row["date_utc"]))
    return dates

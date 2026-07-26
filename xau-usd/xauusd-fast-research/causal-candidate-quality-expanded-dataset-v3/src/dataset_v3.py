from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


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
    resolved: dict[str, Path] = {}
    for name, spec in config["inputs"].items():
        path = repo_root / str(spec["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256_file(path)
        if actual != str(spec["sha256"]):
            raise ValueError(f"Input hash mismatch for {name}: {actual}")
        resolved[name] = path
    return resolved


def _require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing columns: {missing}")


def _as_utc(frame: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        result[column] = pd.to_datetime(result[column], utc=True)
    return result


def mechanism_signature(frame: pd.DataFrame, mechanisms: list[str]) -> pd.Series:
    columns = {
        "BREAK_AND_RUN": "mechanism_break_and_run",
        "DOWNSIDE_IMPULSE_RETEST": "mechanism_downside_impulse_retest",
        "OPENING_RANGE_REVERSAL": "mechanism_opening_range_reversal",
    }
    unknown = sorted(set(mechanisms) - set(columns))
    if unknown:
        raise ValueError(f"Unknown mechanisms: {unknown}")

    def signature(row: pd.Series) -> str:
        active = [name for name in mechanisms if float(row[columns[name]]) == 1.0]
        if not active:
            raise ValueError("Candidate event has no mechanical source")
        return "+".join(active)

    return frame.apply(signature, axis=1)


def assign_structural_episodes(
    events: pd.DataFrame, *, gap_minutes: int
) -> pd.DataFrame:
    ordered = events.sort_values(["signal_time", "event_id"], kind="mergesort").copy()
    gap = ordered["signal_time"].diff().gt(pd.Timedelta(minutes=gap_minutes))
    episode_number = gap.fillna(True).cumsum().astype(int)
    starts = ordered.groupby(episode_number, sort=False)["signal_time"].transform("min")
    ordered["structural_episode_id"] = [
        f"HFV3_{number:06d}_{start.strftime('%Y%m%dT%H%M%SZ')}"
        for number, start in zip(episode_number, starts)
    ]
    ordered["events_in_structural_episode"] = ordered.groupby(
        "structural_episode_id", sort=False
    )["event_id"].transform("size")
    return ordered.sort_values(
        ["signal_time", "event_id"], kind="mergesort"
    ).reset_index(drop=True)


def build_primary_population(
    events: pd.DataFrame,
    actions: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = list(config["model_features"])
    mechanisms = list(config["mechanisms"])
    event_required = [
        "event_id",
        "signal_time",
        "feature_time",
        "direction",
        "regime",
        "signal_source_count",
        "mechanism_break_and_run",
        "mechanism_downside_impulse_retest",
        "mechanism_opening_range_reversal",
    ]
    action_required = [
        *event_required,
        "action_id",
        "entry_time",
        "exit_time",
        "stress_net_r",
        "net_r",
        "risk_usd",
        "mfe_r",
        "mae_r",
        "holding_minutes",
        "exit_reason",
        "ambiguous_m5",
        "current_account_feasible",
        *features,
    ]
    _require_columns(events, event_required, "HF events")
    _require_columns(actions, action_required, "HF actions")
    events = _as_utc(events, ["signal_time", "feature_time"])
    actions = _as_utc(
        actions, ["signal_time", "feature_time", "entry_time", "exit_time"]
    )
    expected = config["expected"]
    if len(events) != int(expected["hf_event_rows"]):
        raise ValueError("HF event row count changed")
    if len(actions) != int(expected["hf_action_rows"]):
        raise ValueError("HF action row count changed")
    if events["event_id"].duplicated().any():
        raise ValueError("HF event IDs are duplicated")
    if actions.duplicated(["event_id", "action_id"]).any():
        raise ValueError("HF event/action IDs are duplicated")
    if set(actions["event_id"]) - set(events["event_id"]):
        raise ValueError("HF action references an unknown event")
    if set(actions["action_id"]) - set(config["actions"]):
        raise ValueError("HF action contains an unlocked action ID")
    if (actions["entry_time"] < actions["signal_time"]).any():
        raise ValueError("An entry precedes its decision")
    if (actions["exit_time"] < actions["entry_time"]).any():
        raise ValueError("An exit precedes its entry")
    if not np.isfinite(actions[features].to_numpy(dtype=float)).all():
        raise ValueError("Primary model features contain a non-finite value")
    if not np.isfinite(
        actions[["stress_net_r", "net_r", "risk_usd", "mfe_r", "mae_r"]].to_numpy(
            dtype=float
        )
    ).all():
        raise ValueError("Primary economic labels contain a non-finite value")

    event_registry = events.copy()
    event_registry["mechanism_signature"] = mechanism_signature(
        event_registry, mechanisms
    )
    flag_count = event_registry[
        [
            "mechanism_break_and_run",
            "mechanism_downside_impulse_retest",
            "mechanism_opening_range_reversal",
        ]
    ].sum(axis=1)
    if not np.array_equal(
        flag_count.to_numpy(dtype=int),
        event_registry["signal_source_count"].to_numpy(dtype=int),
    ):
        raise ValueError("Mechanical source count does not match mechanism flags")
    event_registry = assign_structural_episodes(
        event_registry, gap_minutes=int(config["episode_gap_minutes"])
    )
    episode_columns = [
        "event_id",
        "mechanism_signature",
        "structural_episode_id",
        "events_in_structural_episode",
    ]
    drop_existing = [column for column in episode_columns[1:] if column in actions]
    result = actions.drop(columns=drop_existing).merge(
        event_registry[episode_columns],
        on="event_id",
        how="left",
        validate="many_to_one",
    )
    resolved_events = (
        result[["structural_episode_id", "event_id"]]
        .drop_duplicates()
        .groupby("structural_episode_id", sort=False)["event_id"]
        .size()
    )
    result["resolved_events_in_structural_episode"] = result[
        "structural_episode_id"
    ].map(resolved_events)
    result["actions_for_event"] = result.groupby("event_id", sort=False)[
        "action_id"
    ].transform("size")
    result["event_weight"] = 1.0 / result["actions_for_event"].astype(float)
    result["structural_weight"] = result["event_weight"] / result[
        "resolved_events_in_structural_episode"
    ].astype(float)
    result["mechanism_weight"] = 1.0 / result["signal_source_count"].astype(float)
    result["candidate_id"] = (
        result["event_id"].astype(str) + "__" + result["action_id"].astype(str)
    )
    result["population"] = "HF_PRIMARY"
    result["feature_cutoff_time"] = result["feature_time"]
    result["decision_time"] = result["signal_time"]
    result["entry_eligible_time"] = result["entry_time"]
    result["label_end_time"] = result["exit_time"]
    result["stress_net_r_positive"] = result["stress_net_r"].gt(0.0)
    result["label_status"] = "RESOLVED"
    if result["candidate_id"].duplicated().any():
        raise ValueError("V3 candidate IDs are duplicated")
    episode_weights = result.groupby("structural_episode_id", sort=False)[
        "structural_weight"
    ].sum()
    if not np.allclose(episode_weights.to_numpy(), 1.0, atol=1e-12):
        raise ValueError("Structural weights do not sum to one per episode")
    event_weights = result.groupby("event_id", sort=False)["event_weight"].sum()
    if not np.allclose(event_weights.to_numpy(), 1.0, atol=1e-12):
        raise ValueError("Event weights do not sum to one per event")
    event_action_counts = result.groupby("event_id", sort=False)["action_id"].size()
    event_registry["completed_action_rows"] = (
        event_registry["event_id"].map(event_action_counts).fillna(0).astype(int)
    )
    event_registry["resolved_for_training"] = event_registry[
        "completed_action_rows"
    ].gt(0)
    result = result.sort_values(
        ["signal_time", "direction", "action_id"], kind="mergesort"
    ).reset_index(drop=True)
    return event_registry, result


def build_split_assignments(
    dataset: pd.DataFrame, config: dict[str, Any]
) -> pd.DataFrame:
    episodes = (
        dataset.groupby("structural_episode_id", sort=False)
        .agg(
            episode_start=("signal_time", "min"),
            episode_end=("signal_time", "max"),
            label_end_time=("label_end_time", "max"),
            event_rows=("event_id", "nunique"),
            action_rows=("candidate_id", "size"),
            stressed_winners=("stress_net_r_positive", "sum"),
        )
        .reset_index()
    )
    rows: list[dict[str, Any]] = []
    for fold in config["folds"]:
        windows = {
            "FIT": tuple(pd.Timestamp(value) for value in fold["fit"]),
            "CALIBRATION": tuple(pd.Timestamp(value) for value in fold["calibration"]),
            "TEST": tuple(pd.Timestamp(value) for value in fold["test"]),
        }
        for episode in episodes.itertuples(index=False):
            partition = "OUTSIDE"
            partition_end: pd.Timestamp | None = None
            for name, (start, end) in windows.items():
                if episode.episode_start >= start and episode.episode_end < end:
                    partition = name
                    partition_end = end
                    break
                if episode.episode_start < end <= episode.episode_end:
                    partition = "PURGED_BOUNDARY_EPISODE"
                    break
            eligible = partition in {"FIT", "CALIBRATION", "TEST"}
            if eligible and episode.label_end_time >= partition_end:
                partition = "PURGED_LABEL_CROSSING"
                eligible = False
            rows.append(
                {
                    "fold_id": str(fold["fold_id"]),
                    "structural_episode_id": episode.structural_episode_id,
                    "partition": partition,
                    "eligible": bool(eligible),
                    "episode_start": episode.episode_start,
                    "episode_end": episode.episode_end,
                    "label_end_time": episode.label_end_time,
                    "event_rows": int(episode.event_rows),
                    "action_rows": int(episode.action_rows),
                    "stressed_winners": int(episode.stressed_winners),
                }
            )
    result = pd.DataFrame(rows).sort_values(
        ["fold_id", "episode_start", "structural_episode_id"], kind="mergesort"
    )
    duplicates = result.duplicated(["fold_id", "structural_episode_id"])
    if duplicates.any():
        raise ValueError("A structural episode has duplicate fold assignments")
    return result.reset_index(drop=True)


def _key_set(frame: pd.DataFrame, columns: list[str]) -> set[tuple[Any, ...]]:
    return set(frame[columns].itertuples(index=False, name=None))


def build_overlap_audit(
    events: pd.DataFrame,
    dataset: pd.DataFrame,
    canonical: pd.DataFrame,
    journey: pd.DataFrame,
) -> dict[str, Any]:
    canonical = _as_utc(canonical, ["decision_time"])
    journey = _as_utc(journey, ["entry_time"])
    canonical["direction"] = canonical["direction"].astype(str).str.upper()
    journey["direction"] = journey["direction"].astype(str).str.upper()
    event_keys = _key_set(events, ["signal_time", "direction"])
    canonical_keys = _key_set(canonical, ["decision_time", "direction"])
    action_entry_keys = _key_set(dataset, ["entry_time", "direction"])
    journey_entry_keys = _key_set(journey, ["entry_time", "direction"])
    action_exact_keys = _key_set(dataset, ["entry_time", "direction", "action_id"])
    journey_exact_keys = _key_set(journey, ["entry_time", "direction", "action_id"])
    return {
        "hf_event_keys": len(event_keys),
        "canonical_benchmark_keys": len(canonical_keys),
        "hf_event_keys_overlapping_canonical": len(event_keys & canonical_keys),
        "hf_action_entry_keys": len(action_entry_keys),
        "journey_entry_keys": len(journey_entry_keys),
        "hf_entry_keys_overlapping_journey": len(
            action_entry_keys & journey_entry_keys
        ),
        "hf_exact_action_keys": len(action_exact_keys),
        "journey_exact_action_keys": len(journey_exact_keys),
        "hf_exact_action_keys_overlapping_journey": len(
            action_exact_keys & journey_exact_keys
        ),
        "population_policy": {
            "hf_primary_enters_future_v3_fit": True,
            "canonical_benchmark_enters_future_v3_fit": False,
            "journey_quarantine_enters_future_v3_fit": False,
            "silent_pooling_forbidden": True,
        },
    }


def _category_summary(frame: pd.DataFrame, column: str) -> dict[str, int]:
    return {
        str(key): int(value)
        for key, value in frame[column].value_counts(dropna=False).sort_index().items()
    }


def _label_balance(frame: pd.DataFrame, column: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, group in frame.groupby(column, sort=True, dropna=False):
        winners = int(group["stress_net_r_positive"].sum())
        rows = int(len(group))
        result[str(key)] = {
            "rows": rows,
            "stressed_winners": winners,
            "stressed_failures": rows - winners,
            "stressed_win_rate": float(winners / rows),
            "structural_weight": float(group["structural_weight"].sum()),
        }
    return result


def build_population_audit(
    events: pd.DataFrame,
    dataset: pd.DataFrame,
    splits: pd.DataFrame,
    config: dict[str, Any],
) -> dict[str, Any]:
    winners = dataset["stress_net_r_positive"]
    fold_counts: dict[str, dict[str, dict[str, int]]] = {}
    for fold_id, fold in splits.groupby("fold_id", sort=True):
        fold_counts[str(fold_id)] = {}
        for partition, part in fold.groupby("partition", sort=True):
            fold_counts[str(fold_id)][str(partition)] = {
                "episodes": int(len(part)),
                "events": int(part["event_rows"].sum()),
                "actions": int(part["action_rows"].sum()),
                "stressed_winners": int(part["stressed_winners"].sum()),
            }
    return {
        "schema_version": config["schema_version"],
        "decision": "V3_EXPANDED_CANDIDATE_DATASET_COMPLETE_RESEARCH_ONLY",
        "population": "HF_PRIMARY",
        "event_rows": int(len(events)),
        "action_rows": int(len(dataset)),
        "events_with_resolved_actions": int(dataset["event_id"].nunique()),
        "events_without_resolved_actions": int(
            (~events["resolved_for_training"]).sum()
        ),
        "structural_episodes": int(dataset["structural_episode_id"].nunique()),
        "resolved_labels": int(dataset["label_status"].eq("RESOLVED").sum()),
        "stressed_winners": int(winners.sum()),
        "stressed_failures": int((~winners).sum()),
        "stressed_win_rate": float(winners.mean()),
        "structural_weight_sum": float(
            dataset.groupby("structural_episode_id")["structural_weight"].first().size
        ),
        "first_decision_time": dataset["signal_time"].min(),
        "last_decision_time": dataset["signal_time"].max(),
        "mechanism_signatures": _category_summary(dataset, "mechanism_signature"),
        "regimes": _category_summary(dataset, "regime"),
        "directions": _category_summary(dataset, "direction"),
        "actions": _category_summary(dataset, "action_id"),
        "label_balance": {
            "mechanism_signature": _label_balance(dataset, "mechanism_signature"),
            "regime": _label_balance(dataset, "regime"),
            "direction": _label_balance(dataset, "direction"),
            "action": _label_balance(dataset, "action_id"),
        },
        "exit_reasons": _category_summary(dataset, "exit_reason"),
        "ambiguous_m5_rows": int(dataset["ambiguous_m5"].sum()),
        "current_account_feasible_rows": int(dataset["current_account_feasible"].sum()),
        "fold_counts": fold_counts,
        "model_feature_count": len(config["model_features"]),
        "model_features": list(config["model_features"]),
        "forbidden_features_present": sorted(
            set(config["model_features"]) & set(config["forbidden_model_columns"])
        ),
        "historical_outcomes_already_exposed": bool(
            config["historical_outcomes_already_exposed"]
        ),
        "authorization": config["authorization"],
    }

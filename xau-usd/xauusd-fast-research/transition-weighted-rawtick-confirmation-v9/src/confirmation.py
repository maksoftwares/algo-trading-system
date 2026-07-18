from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import numpy as np
import pandas as pd


def candidate_id(origin_attempt: int, signal_time: pd.Timestamp) -> str:
    payload = f"{origin_attempt}|{signal_time.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def component_candidates(
    decisions: pd.DataFrame,
    execution_frame: pd.DataFrame,
    source_row: Any,
    campaign: Any,
    source_config: Mapping[str, Any],
    confirmation_config: Mapping[str, Any],
) -> pd.DataFrame:
    params = json.loads(str(source_row.parameters_json))
    mask, direction = campaign.signal_mask_direction(
        decisions, str(source_row.mechanic), params
    )
    raw_signals = int(mask.sum())
    if raw_signals != int(source_row.raw_signal_count):
        raise ValueError(
            f"Raw signal count changed for {source_row.attempt_no}: "
            f"{raw_signals} != {source_row.raw_signal_count}"
        )
    geometry = source_config["geometries"][str(source_row.regime_owner)][
        str(source_row.geometry_id)
    ]
    end = pd.Timestamp(confirmation_config["source"]["end_exclusive_utc"])
    hold = pd.Timedelta(hours=float(geometry["maximum_hold_hours"]))
    maximum_gap = float(
        confirmation_config["execution"]["maximum_entry_gap_minutes"]
    )
    rows: list[dict[str, Any]] = []
    for decision_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        signal = decisions.iloc[int(decision_index)]
        signal_index = int(signal["execution_index"])
        entry_index = signal_index + 1
        if entry_index >= len(execution_frame):
            continue
        signal_time = pd.Timestamp(signal["timestamp_utc"])
        scheduled = pd.Timestamp(execution_frame["bar_start_utc"].iat[entry_index])
        gap_minutes = (scheduled - signal_time).total_seconds() / 60.0
        if gap_minutes < 0.0 or gap_minutes > maximum_gap:
            continue
        if scheduled + hold >= end:
            continue
        sign = int(direction.iat[int(decision_index)])
        if sign not in (-1, 1):
            raise ValueError("Candidate direction is not executable")
        attempt = int(source_row.attempt_no)
        rows.append(
            {
                "candidate_id": candidate_id(attempt, signal_time),
                "origin_attempt": attempt,
                "origin_variant_id": str(source_row.variant_id),
                "regime_owner": str(source_row.regime_owner),
                "mechanic": str(source_row.mechanic),
                "geometry_id": str(source_row.geometry_id),
                "signal_time": signal_time,
                "scheduled_entry_time": scheduled,
                "direction_sign": sign,
                "direction": "LONG" if sign > 0 else "SHORT",
                "signal_atr": float(signal["atr14"]),
                "stop_atr": float(geometry["stop_atr"]),
                "target_r": float(geometry["target_r"]),
                "hold_hours": float(geometry["maximum_hold_hours"]),
                "parameters_json": str(source_row.parameters_json),
            }
        )
    if not rows:
        raise ValueError(f"No executable candidates for {source_row.attempt_no}")
    return pd.DataFrame(rows)


def combine_candidates(frames: list[pd.DataFrame]) -> pd.DataFrame:
    result = pd.concat(frames, ignore_index=True).sort_values(
        ["scheduled_entry_time", "origin_attempt"], kind="mergesort"
    ).reset_index(drop=True)
    if result["candidate_id"].duplicated().any():
        raise ValueError("Duplicate raw-tick candidate IDs")
    return result


def simulate_components(
    candidates: pd.DataFrame,
    tick_store: Any,
    quote_type: Any,
    execution: Mapping[str, Any],
    execute_candidate: Any,
) -> tuple[pd.DataFrame, dict[str, dict[str, int]]]:
    rows: list[dict[str, Any]] = []
    all_rejections: dict[str, dict[str, int]] = {}
    for attempt, group in candidates.groupby("origin_attempt", sort=True):
        position_until = pd.Timestamp.min.tz_localize("UTC")
        daily_count: dict[Any, int] = {}
        rejections: dict[str, int] = {}
        for candidate in group.sort_values(
            "scheduled_entry_time", kind="mergesort"
        ).itertuples(index=False):
            outcome, reason = execute_candidate(
                candidate, tick_store, quote_type, execution
            )
            if outcome is None:
                label = str(reason)
                rejections[label] = rejections.get(label, 0) + 1
                continue
            entry_time = pd.Timestamp(outcome["entry_time"])
            if entry_time < position_until:
                rejections["COMPONENT_POSITION_OVERLAP"] = (
                    rejections.get("COMPONENT_POSITION_OVERLAP", 0) + 1
                )
                continue
            day = entry_time.date()
            maximum = int(execution["maximum_trades_per_component_utc_day"])
            if daily_count.get(day, 0) >= maximum:
                rejections["COMPONENT_DAILY_CAP"] = (
                    rejections.get("COMPONENT_DAILY_CAP", 0) + 1
                )
                continue
            outcome["attempt_no"] = int(attempt)
            rows.append(outcome)
            position_until = pd.Timestamp(outcome["exit_time"])
            daily_count[day] = daily_count.get(day, 0) + 1
        all_rejections[str(int(attempt))] = dict(sorted(rejections.items()))
    result = pd.DataFrame(rows).sort_values(
        ["entry_time", "attempt_no"], kind="mergesort"
    ).reset_index(drop=True)
    return result, all_rejections


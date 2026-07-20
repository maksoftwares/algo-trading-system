from __future__ import annotations

import itertools
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


def select_source_events(
    features: pd.DataFrame, *, policy: Mapping[str, Any]
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    mask = features["horizon_ms"].eq(int(policy["horizon_ms"]))
    mask &= features["minimum_leg_move_bps"] >= float(
        policy["minimum_leg_move_bps"]
    )
    mask &= features["consensus_sum_bps"] >= float(
        policy["minimum_consensus_sum_bps"]
    )
    mask &= features["signed_xau_response_ratio"] <= float(
        policy["maximum_signed_xau_response_ratio"]
    )
    mask &= features["source_quote_count"] >= int(
        policy["minimum_source_quote_count"]
    )
    selected = features.loc[mask].copy()
    if selected.empty:
        return selected
    selected = selected.sort_values("feature_time_utc", kind="stable").reset_index(
        drop=True
    )
    selected["source_event_id"] = (
        "V80:SRC:"
        + selected["decision_timestamp_ms"].astype("int64").astype(str)
        + ":"
        + selected["direction"].astype(str)
    )
    if selected["source_event_id"].duplicated().any():
        raise ValueError("V80 source event IDs are not unique")
    return selected


def build_pattern_rows(
    source_events: pd.DataFrame,
    xau: pd.DataFrame,
    *,
    transmission_bps_grid: Sequence[float],
    retracement_fraction_grid: Sequence[float],
    maximum_pattern_seconds: int,
) -> pd.DataFrame:
    if source_events.empty or xau.empty:
        return pd.DataFrame()
    times = xau["timestamp_ms"].to_numpy(dtype=np.int64)
    mids = xau["mid"].to_numpy(dtype=float)
    output: list[dict[str, Any]] = []
    maximum_delay_ms = int(maximum_pattern_seconds) * 1000
    for row in source_events.to_dict(orient="records"):
        event_ms = int(row["decision_timestamp_ms"])
        current_i = int(np.searchsorted(times, event_ms, side="left") - 1)
        start_i = int(np.searchsorted(times, event_ms, side="right"))
        end_i = int(np.searchsorted(times, event_ms + maximum_delay_ms, side="right"))
        if current_i < 0 or start_i >= end_i:
            continue
        direction_sign = 1.0 if str(row["direction"]) == "LONG" else -1.0
        signed_moves = direction_sign * (mids[start_i:end_i] / mids[current_i] - 1.0) * 10_000.0
        running_peak = np.maximum.accumulate(signed_moves)
        for transmission, fraction in itertools.product(
            transmission_bps_grid, retracement_fraction_grid
        ):
            transmitted = np.flatnonzero(
                running_peak >= float(transmission) - 1e-12
            )
            if transmitted.size == 0:
                continue
            first_transmission = int(transmitted[0])
            positions = np.arange(len(signed_moves))
            retraced = (
                (positions > first_transmission)
                & (running_peak >= float(transmission) - 1e-12)
                & (
                    signed_moves
                    <= running_peak * (1.0 - float(fraction)) + 1e-12
                )
            )
            completed = np.flatnonzero(retraced)
            if completed.size == 0:
                continue
            completion = int(completed[0])
            completion_i = start_i + completion
            completion_ms = int(times[completion_i])
            output.append(
                {
                    "source_event_id": str(row["source_event_id"]),
                    "source_event_timestamp_ms": event_ms,
                    "decision_timestamp_ms": completion_ms,
                    "feature_time_utc": pd.to_datetime(
                        completion_ms, unit="ms", utc=True
                    ),
                    "direction": str(row["direction"]),
                    "transmission_bps": float(transmission),
                    "retracement_fraction": float(fraction),
                    "pattern_delay_ms": completion_ms - event_ms,
                    "transmission_delay_ms": int(times[start_i + first_transmission])
                    - event_ms,
                    "favorable_peak_bps": float(running_peak[completion]),
                    "completion_signed_move_bps": float(signed_moves[completion]),
                    "realized_retracement_bps": float(
                        running_peak[completion] - signed_moves[completion]
                    ),
                    "eurusd_move_bps": float(row["eurusd_move_bps"]),
                    "usdjpy_move_bps": float(row["usdjpy_move_bps"]),
                    "minimum_leg_move_bps": float(row["minimum_leg_move_bps"]),
                    "consensus_sum_bps": float(row["consensus_sum_bps"]),
                }
            )
    if not output:
        return pd.DataFrame()
    return pd.DataFrame(output).sort_values(
        ["feature_time_utc", "source_event_timestamp_ms", "transmission_bps"],
        kind="stable",
    )


def timing_policy_grid(calibration: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "transmission_bps": float(transmission),
            "retracement_fraction": float(fraction),
            "maximum_pattern_seconds": int(seconds),
        }
        for transmission, fraction, seconds in itertools.product(
            calibration["transmission_bps_grid"],
            calibration["retracement_fraction_grid"],
            calibration["maximum_pattern_seconds_grid"],
        )
    ]


def timing_policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"TR{int(round(float(policy['transmission_bps']) * 100)):03d}"
        f"__RF{int(round(float(policy['retracement_fraction']) * 100)):03d}"
        f"__MW{int(policy['maximum_pattern_seconds']):03d}"
    )


def generate_candidates(
    patterns: pd.DataFrame, *, policy: Mapping[str, Any], family: str
) -> pd.DataFrame:
    if patterns.empty:
        return pd.DataFrame()
    mask = np.isclose(
        patterns["transmission_bps"].to_numpy(dtype=float),
        float(policy["transmission_bps"]),
    )
    mask &= np.isclose(
        patterns["retracement_fraction"].to_numpy(dtype=float),
        float(policy["retracement_fraction"]),
    )
    mask &= patterns["pattern_delay_ms"].to_numpy(dtype=np.int64) <= int(
        policy["maximum_pattern_seconds"]
    ) * 1000
    selected = patterns.loc[mask].copy()
    if selected.empty:
        return selected
    selected["date_utc"] = selected["feature_time_utc"].dt.date.astype(str)
    selected = selected.sort_values(
        ["feature_time_utc", "source_event_timestamp_ms"], kind="stable"
    )
    selected = selected.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected["family"] = family
    selected["policy_id"] = timing_policy_id(policy)
    selected.insert(
        0,
        "candidate_id",
        "V80:"
        + selected["policy_id"]
        + ":"
        + selected["source_event_timestamp_ms"].astype("int64").astype(str)
        + ":"
        + selected["decision_timestamp_ms"].astype("int64").astype(str)
        + ":"
        + selected["direction"],
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V80 candidate IDs are not unique")
    return selected.reset_index(drop=True)


def summarize_candidate_facts(
    candidates: pd.DataFrame,
    *,
    eligible_dates: Sequence[str],
    policy: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> dict[str, Any]:
    trades = len(candidates)
    active_days = int(candidates["date_utc"].nunique()) if trades else 0
    longs = int((candidates["direction"] == "LONG").sum()) if trades else 0
    shorts = int((candidates["direction"] == "SHORT").sum()) if trades else 0
    days = len(eligible_dates)
    frequency = trades / days if days else 0.0
    minority = min(longs, shorts) / trades if trades else 0.0
    active_share = active_days / days if days else 0.0
    selectable = bool(
        float(calibration["minimum_candidates_per_full_weekday"])
        <= frequency
        <= float(calibration["maximum_candidates_per_full_weekday"])
        and active_share >= float(calibration["minimum_active_day_share"])
        and minority >= float(calibration["minimum_direction_share"])
    )
    return {
        "policy_id": timing_policy_id(policy),
        **dict(policy),
        "eligible_full_weekdays": days,
        "candidates": trades,
        "candidates_per_full_weekday": frequency,
        "active_days": active_days,
        "active_day_share": active_share,
        "long_candidates": longs,
        "short_candidates": shorts,
        "minority_direction_share": minority,
        "selection_eligible": selectable,
    }


def select_policy(
    rows: Iterable[Mapping[str, Any]], calibration: Mapping[str, Any]
) -> dict[str, Any] | None:
    eligible = [dict(row) for row in rows if bool(row["selection_eligible"])]
    if not eligible:
        return None
    target = float(calibration["target_candidates_per_full_weekday"])
    eligible.sort(
        key=lambda row: (
            abs(float(row["candidates_per_full_weekday"]) - target),
            -float(row["transmission_bps"]),
            -float(row["retracement_fraction"]),
            int(row["maximum_pattern_seconds"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "transmission_bps",
        "retracement_fraction",
        "maximum_pattern_seconds",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}

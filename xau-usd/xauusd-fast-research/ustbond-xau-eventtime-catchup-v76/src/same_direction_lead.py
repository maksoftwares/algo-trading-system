from __future__ import annotations

import itertools
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from catchup import clock_ms


def session_quality(
    date: pd.Timestamp,
    source: pd.DataFrame,
    xau: pd.DataFrame,
    rule: Mapping[str, Any],
) -> dict[str, Any]:
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    source_session = source.loc[
        source["timestamp_ms"].between(start_ms, end_ms - 1)
    ]
    xau_session = xau.loc[xau["timestamp_ms"].between(start_ms, end_ms - 1)]

    def coverage(frame: pd.DataFrame) -> float:
        if frame.empty:
            return 0.0
        elapsed = int(frame["timestamp_ms"].iloc[-1]) - int(
            frame["timestamp_ms"].iloc[0]
        )
        return elapsed / 60_000

    source_coverage = coverage(source_session)
    xau_coverage = coverage(xau_session)
    eligible = bool(
        date.weekday() < 5
        and len(source_session) >= int(rule["minimum_source_quotes"])
        and len(xau_session) >= int(rule["minimum_xau_quotes"])
        and source_coverage >= float(rule["minimum_session_coverage_minutes"])
        and xau_coverage >= float(rule["minimum_session_coverage_minutes"])
    )
    return {
        "date_utc": date.date().isoformat(),
        "weekday": int(date.weekday()),
        "source_quotes": int(len(source_session)),
        "xau_quotes": int(len(xau_session)),
        "source_coverage_minutes": source_coverage,
        "xau_coverage_minutes": xau_coverage,
        "eligible_full_weekday": eligible,
    }


def build_same_direction_features(
    date: pd.Timestamp,
    source: pd.DataFrame,
    xau: pd.DataFrame,
    *,
    horizons_ms: Sequence[int],
    rule: Mapping[str, Any],
    prefilter: Mapping[str, Any],
) -> pd.DataFrame:
    if source.empty or xau.empty:
        return pd.DataFrame()
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    source_times_all = source["timestamp_ms"].to_numpy(dtype=np.int64)
    source_mid_all = source["mid"].to_numpy(dtype=float)
    event_indices = np.flatnonzero(
        (source_times_all >= start_ms) & (source_times_all < end_ms)
    )
    if event_indices.size == 0:
        return pd.DataFrame()
    event_times = source_times_all[event_indices]
    event_mid = source_mid_all[event_indices]
    xau_times = xau["timestamp_ms"].to_numpy(dtype=np.int64)
    xau_mid = xau["mid"].to_numpy(dtype=float)
    max_staleness = int(rule["maximum_baseline_staleness_ms"])
    current_staleness = int(rule["maximum_current_xau_staleness_ms"])
    output: list[pd.DataFrame] = []
    for horizon in horizons_ms:
        targets = event_times - int(horizon)
        source_base_i = np.searchsorted(source_times_all, targets, side="right") - 1
        xau_base_i = np.searchsorted(xau_times, targets, side="right") - 1
        xau_current_i = np.searchsorted(xau_times, event_times, side="left") - 1
        valid = (source_base_i >= 0) & (xau_base_i >= 0) & (xau_current_i >= 0)
        safe_source = np.maximum(source_base_i, 0)
        safe_xau_base = np.maximum(xau_base_i, 0)
        safe_xau_current = np.maximum(xau_current_i, 0)
        valid &= targets - source_times_all[safe_source] <= max_staleness
        valid &= targets - xau_times[safe_xau_base] <= max_staleness
        valid &= event_times - xau_times[safe_xau_current] <= current_staleness
        source_move = (
            event_mid / source_mid_all[safe_source] - 1.0
        ) * 10_000.0
        xau_move = (
            xau_mid[safe_xau_current] / xau_mid[safe_xau_base] - 1.0
        ) * 10_000.0
        expected_sign = np.sign(source_move)
        absolute_source = np.abs(source_move)
        signed_xau = expected_sign * xau_move
        innovation = absolute_source - signed_xau
        response = np.divide(
            signed_xau,
            absolute_source,
            out=np.full_like(signed_xau, np.inf),
            where=absolute_source > 0,
        )
        quote_count = event_indices - source_base_i
        valid &= expected_sign != 0
        valid &= absolute_source >= float(
            prefilter["minimum_absolute_source_move_bps"]
        )
        valid &= innovation >= float(
            prefilter["minimum_directional_innovation_bps"]
        )
        valid &= response <= float(
            prefilter["maximum_signed_xau_response_ratio"]
        )
        valid &= quote_count >= int(prefilter["minimum_source_quote_count"])
        if not valid.any():
            continue
        chosen = np.flatnonzero(valid)
        output.append(
            pd.DataFrame(
                {
                    "feature_time_utc": pd.to_datetime(
                        event_times[chosen], unit="ms", utc=True
                    ),
                    "decision_timestamp_ms": event_times[chosen],
                    "horizon_ms": int(horizon),
                    "source_baseline_timestamp_ms": source_times_all[
                        safe_source[chosen]
                    ],
                    "xau_baseline_timestamp_ms": xau_times[
                        safe_xau_base[chosen]
                    ],
                    "xau_current_timestamp_ms": xau_times[
                        safe_xau_current[chosen]
                    ],
                    "source_move_bps": source_move[chosen],
                    "xau_move_bps": xau_move[chosen],
                    "directional_innovation_bps": innovation[chosen],
                    "signed_xau_response_ratio": response[chosen],
                    "source_quote_count": quote_count[chosen],
                    "direction": np.where(
                        expected_sign[chosen] > 0, "LONG", "SHORT"
                    ),
                }
            )
        )
    if not output:
        return pd.DataFrame()
    return (
        pd.concat(output, ignore_index=True)
        .sort_values(["feature_time_utc", "horizon_ms"], kind="stable")
        .reset_index(drop=True)
    )


def policy_grid(calibration: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for horizon, move, innovation, response, count in itertools.product(
        calibration["horizon_ms_grid"],
        calibration["minimum_absolute_source_move_bps_grid"],
        calibration["minimum_directional_innovation_bps_grid"],
        calibration["maximum_signed_xau_response_ratio_grid"],
        calibration["minimum_source_quote_count_grid"],
    ):
        rows.append(
            {
                "horizon_ms": int(horizon),
                "minimum_absolute_source_move_bps": float(move),
                "minimum_directional_innovation_bps": float(innovation),
                "maximum_signed_xau_response_ratio": float(response),
                "minimum_source_quote_count": int(count),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"H{int(policy['horizon_ms']):05d}"
        f"__BM{int(round(float(policy['minimum_absolute_source_move_bps']) * 10)):03d}"
        f"__IN{int(round(float(policy['minimum_directional_innovation_bps']) * 10)):03d}"
        f"__RR{int(round(float(policy['maximum_signed_xau_response_ratio']) * 100)):03d}"
        f"__QC{int(policy['minimum_source_quote_count']):02d}"
    )


def generate_candidates(
    features: pd.DataFrame, *, policy: Mapping[str, Any], family: str
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    mask = features["horizon_ms"].eq(int(policy["horizon_ms"]))
    mask &= features["source_move_bps"].abs() >= float(
        policy["minimum_absolute_source_move_bps"]
    )
    mask &= features["directional_innovation_bps"] >= float(
        policy["minimum_directional_innovation_bps"]
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
    selected["date_utc"] = selected["feature_time_utc"].dt.date.astype(str)
    selected = selected.sort_values(["feature_time_utc", "horizon_ms"], kind="stable")
    selected = selected.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected["family"] = family
    selected["policy_id"] = policy_id(policy)
    selected.insert(
        0,
        "candidate_id",
        "V76:"
        + selected["policy_id"]
        + ":"
        + selected["decision_timestamp_ms"].astype(str)
        + ":"
        + selected["direction"],
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V76 candidate IDs are not unique")
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
        "policy_id": policy_id(policy),
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
            -float(row["minimum_absolute_source_move_bps"]),
            -float(row["minimum_directional_innovation_bps"]),
            float(row["maximum_signed_xau_response_ratio"]),
            -int(row["minimum_source_quote_count"]),
            int(row["horizon_ms"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "horizon_ms",
        "minimum_absolute_source_move_bps",
        "minimum_directional_innovation_bps",
        "maximum_signed_xau_response_ratio",
        "minimum_source_quote_count",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}


def calibration_prefilter(calibration: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "minimum_absolute_source_move_bps": min(
            calibration["minimum_absolute_source_move_bps_grid"]
        ),
        "minimum_directional_innovation_bps": min(
            calibration["minimum_directional_innovation_bps_grid"]
        ),
        "maximum_signed_xau_response_ratio": max(
            calibration["maximum_signed_xau_response_ratio_grid"]
        ),
        "minimum_source_quote_count": min(
            calibration["minimum_source_quote_count_grid"]
        ),
    }

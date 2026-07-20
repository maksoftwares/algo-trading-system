from __future__ import annotations

import itertools
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from catchup import clock_ms


def session_quality(
    date: pd.Timestamp,
    eurusd: pd.DataFrame,
    usdjpy: pd.DataFrame,
    xau: pd.DataFrame,
    rule: Mapping[str, Any],
) -> dict[str, Any]:
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    sessions = {
        "eurusd": eurusd.loc[
            eurusd["timestamp_ms"].between(start_ms, end_ms - 1)
        ],
        "usdjpy": usdjpy.loc[
            usdjpy["timestamp_ms"].between(start_ms, end_ms - 1)
        ],
        "xau": xau.loc[xau["timestamp_ms"].between(start_ms, end_ms - 1)],
    }

    def coverage(frame: pd.DataFrame) -> float:
        if frame.empty:
            return 0.0
        elapsed = int(frame["timestamp_ms"].iloc[-1]) - int(
            frame["timestamp_ms"].iloc[0]
        )
        return elapsed / 60_000

    coverage_minutes = {key: coverage(frame) for key, frame in sessions.items()}
    eligible = bool(
        date.weekday() < 5
        and len(sessions["eurusd"]) >= int(rule["minimum_eurusd_quotes"])
        and len(sessions["usdjpy"]) >= int(rule["minimum_usdjpy_quotes"])
        and len(sessions["xau"]) >= int(rule["minimum_xau_quotes"])
        and all(
            value >= float(rule["minimum_session_coverage_minutes"])
            for value in coverage_minutes.values()
        )
    )
    return {
        "date_utc": date.date().isoformat(),
        "weekday": int(date.weekday()),
        "eurusd_quotes": int(len(sessions["eurusd"])),
        "usdjpy_quotes": int(len(sessions["usdjpy"])),
        "xau_quotes": int(len(sessions["xau"])),
        "eurusd_coverage_minutes": coverage_minutes["eurusd"],
        "usdjpy_coverage_minutes": coverage_minutes["usdjpy"],
        "xau_coverage_minutes": coverage_minutes["xau"],
        "eligible_full_weekday": eligible,
    }


def build_consensus_features(
    date: pd.Timestamp,
    eurusd: pd.DataFrame,
    usdjpy: pd.DataFrame,
    xau: pd.DataFrame,
    *,
    horizons_ms: Sequence[int],
    rule: Mapping[str, Any],
    prefilter: Mapping[str, Any],
) -> pd.DataFrame:
    if eurusd.empty or usdjpy.empty or xau.empty:
        return pd.DataFrame()
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    eur_times_all = eurusd["timestamp_ms"].to_numpy(dtype=np.int64)
    eur_mid_all = eurusd["mid"].to_numpy(dtype=float)
    event_indices = np.flatnonzero(
        (eur_times_all >= start_ms) & (eur_times_all < end_ms)
    )
    if event_indices.size == 0:
        return pd.DataFrame()
    event_times = eur_times_all[event_indices]
    event_eur_mid = eur_mid_all[event_indices]
    jpy_times = usdjpy["timestamp_ms"].to_numpy(dtype=np.int64)
    jpy_mid = usdjpy["mid"].to_numpy(dtype=float)
    xau_times = xau["timestamp_ms"].to_numpy(dtype=np.int64)
    xau_mid = xau["mid"].to_numpy(dtype=float)
    baseline_staleness = int(rule["maximum_baseline_staleness_ms"])
    source_staleness = int(rule["maximum_current_source_staleness_ms"])
    xau_staleness = int(rule["maximum_current_xau_staleness_ms"])
    output: list[pd.DataFrame] = []
    for horizon in horizons_ms:
        targets = event_times - int(horizon)
        eur_base_i = np.searchsorted(eur_times_all, targets, side="right") - 1
        jpy_base_i = np.searchsorted(jpy_times, targets, side="right") - 1
        jpy_current_i = np.searchsorted(jpy_times, event_times, side="right") - 1
        xau_base_i = np.searchsorted(xau_times, targets, side="right") - 1
        xau_current_i = np.searchsorted(xau_times, event_times, side="left") - 1
        valid = (
            (eur_base_i >= 0)
            & (jpy_base_i >= 0)
            & (jpy_current_i >= 0)
            & (xau_base_i >= 0)
            & (xau_current_i >= 0)
        )
        safe_eur_base = np.maximum(eur_base_i, 0)
        safe_jpy_base = np.maximum(jpy_base_i, 0)
        safe_jpy_current = np.maximum(jpy_current_i, 0)
        safe_xau_base = np.maximum(xau_base_i, 0)
        safe_xau_current = np.maximum(xau_current_i, 0)
        valid &= targets - eur_times_all[safe_eur_base] <= baseline_staleness
        valid &= targets - jpy_times[safe_jpy_base] <= baseline_staleness
        valid &= targets - xau_times[safe_xau_base] <= baseline_staleness
        valid &= event_times - jpy_times[safe_jpy_current] <= source_staleness
        valid &= event_times - xau_times[safe_xau_current] <= xau_staleness
        eur_move = (
            event_eur_mid / eur_mid_all[safe_eur_base] - 1.0
        ) * 10_000.0
        jpy_move = (
            jpy_mid[safe_jpy_current] / jpy_mid[safe_jpy_base] - 1.0
        ) * 10_000.0
        xau_move = (
            xau_mid[safe_xau_current] / xau_mid[safe_xau_base] - 1.0
        ) * 10_000.0
        eur_sign = np.sign(eur_move)
        jpy_sign = np.sign(jpy_move)
        consensus = (eur_sign != 0) & (eur_sign == -jpy_sign)
        leg_min = np.minimum(np.abs(eur_move), np.abs(jpy_move))
        consensus_sum = np.abs(eur_move) + np.abs(jpy_move)
        signed_xau = eur_sign * xau_move
        response = np.divide(
            signed_xau,
            leg_min,
            out=np.full_like(signed_xau, np.inf),
            where=leg_min > 0,
        )
        eur_quote_count = event_indices - eur_base_i
        jpy_quote_count = jpy_current_i - jpy_base_i
        source_quote_count = np.minimum(eur_quote_count, jpy_quote_count)
        valid &= consensus
        valid &= leg_min >= float(prefilter["minimum_leg_move_bps"])
        valid &= consensus_sum >= float(
            prefilter["minimum_consensus_sum_bps"]
        )
        valid &= response <= float(
            prefilter["maximum_signed_xau_response_ratio"]
        )
        valid &= source_quote_count >= int(
            prefilter["minimum_source_quote_count"]
        )
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
                    "eurusd_baseline_timestamp_ms": eur_times_all[
                        safe_eur_base[chosen]
                    ],
                    "usdjpy_baseline_timestamp_ms": jpy_times[
                        safe_jpy_base[chosen]
                    ],
                    "usdjpy_current_timestamp_ms": jpy_times[
                        safe_jpy_current[chosen]
                    ],
                    "xau_baseline_timestamp_ms": xau_times[
                        safe_xau_base[chosen]
                    ],
                    "xau_current_timestamp_ms": xau_times[
                        safe_xau_current[chosen]
                    ],
                    "eurusd_move_bps": eur_move[chosen],
                    "usdjpy_move_bps": jpy_move[chosen],
                    "minimum_leg_move_bps": leg_min[chosen],
                    "consensus_sum_bps": consensus_sum[chosen],
                    "xau_move_bps": xau_move[chosen],
                    "signed_xau_response_ratio": response[chosen],
                    "source_quote_count": source_quote_count[chosen],
                    "direction": np.where(eur_sign[chosen] > 0, "LONG", "SHORT"),
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
    for horizon, leg, total, response, count in itertools.product(
        calibration["horizon_ms_grid"],
        calibration["minimum_leg_move_bps_grid"],
        calibration["minimum_consensus_sum_bps_grid"],
        calibration["maximum_signed_xau_response_ratio_grid"],
        calibration["minimum_source_quote_count_grid"],
    ):
        rows.append(
            {
                "horizon_ms": int(horizon),
                "minimum_leg_move_bps": float(leg),
                "minimum_consensus_sum_bps": float(total),
                "maximum_signed_xau_response_ratio": float(response),
                "minimum_source_quote_count": int(count),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"H{int(policy['horizon_ms']):05d}"
        f"__LM{int(round(float(policy['minimum_leg_move_bps']) * 100)):03d}"
        f"__CS{int(round(float(policy['minimum_consensus_sum_bps']) * 100)):03d}"
        f"__RR{int(round(float(policy['maximum_signed_xau_response_ratio']) * 100)):03d}"
        f"__QC{int(policy['minimum_source_quote_count']):02d}"
    )


def generate_candidates(
    features: pd.DataFrame, *, policy: Mapping[str, Any], family: str
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
    selected["date_utc"] = selected["feature_time_utc"].dt.date.astype(str)
    selected = selected.sort_values(["feature_time_utc", "horizon_ms"], kind="stable")
    selected = selected.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected["family"] = family
    selected["policy_id"] = policy_id(policy)
    selected.insert(
        0,
        "candidate_id",
        "V78:"
        + selected["policy_id"]
        + ":"
        + selected["decision_timestamp_ms"].astype(str)
        + ":"
        + selected["direction"],
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V78 candidate IDs are not unique")
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
            -float(row["minimum_consensus_sum_bps"]),
            -float(row["minimum_leg_move_bps"]),
            float(row["maximum_signed_xau_response_ratio"]),
            -int(row["minimum_source_quote_count"]),
            int(row["horizon_ms"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "horizon_ms",
        "minimum_leg_move_bps",
        "minimum_consensus_sum_bps",
        "maximum_signed_xau_response_ratio",
        "minimum_source_quote_count",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}


def calibration_prefilter(calibration: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "minimum_leg_move_bps": min(calibration["minimum_leg_move_bps_grid"]),
        "minimum_consensus_sum_bps": min(
            calibration["minimum_consensus_sum_bps_grid"]
        ),
        "maximum_signed_xau_response_ratio": max(
            calibration["maximum_signed_xau_response_ratio_grid"]
        ),
        "minimum_source_quote_count": min(
            calibration["minimum_source_quote_count_grid"]
        ),
    }

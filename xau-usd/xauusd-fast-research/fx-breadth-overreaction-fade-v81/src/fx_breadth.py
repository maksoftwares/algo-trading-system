from __future__ import annotations

import itertools
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from catchup import clock_ms


def session_quality(
    date: pd.Timestamp,
    eurusd: pd.DataFrame,
    gbpusd: pd.DataFrame,
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
        "gbpusd": gbpusd.loc[
            gbpusd["timestamp_ms"].between(start_ms, end_ms - 1)
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
    minimum_quotes = int(rule["minimum_quotes_per_symbol"])
    eligible = bool(
        date.weekday() < 5
        and all(len(frame) >= minimum_quotes for frame in sessions.values())
        and all(
            value >= float(rule["minimum_session_coverage_minutes"])
            for value in coverage_minutes.values()
        )
    )
    result: dict[str, Any] = {
        "date_utc": date.date().isoformat(),
        "weekday": int(date.weekday()),
        "eligible_full_weekday": eligible,
    }
    for key, frame in sessions.items():
        result[f"{key}_quotes"] = int(len(frame))
        result[f"{key}_coverage_minutes"] = coverage_minutes[key]
    return result


def _aligned_indices(
    times: np.ndarray,
    targets: np.ndarray,
    *,
    side: str = "right",
) -> np.ndarray:
    return np.searchsorted(times, targets, side=side) - 1


def build_breadth_features(
    date: pd.Timestamp,
    eurusd: pd.DataFrame,
    gbpusd: pd.DataFrame,
    usdjpy: pd.DataFrame,
    xau: pd.DataFrame,
    *,
    horizons_ms: Sequence[int],
    rule: Mapping[str, Any],
    prefilter: Mapping[str, Any],
) -> pd.DataFrame:
    if any(frame.empty for frame in (eurusd, gbpusd, usdjpy, xau)):
        return pd.DataFrame()
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    frames = {
        "eurusd": eurusd,
        "gbpusd": gbpusd,
        "usdjpy": usdjpy,
        "xau": xau,
    }
    times = {
        key: frame["timestamp_ms"].to_numpy(dtype=np.int64)
        for key, frame in frames.items()
    }
    mids = {
        key: frame["mid"].to_numpy(dtype=float) for key, frame in frames.items()
    }
    event_indices = np.flatnonzero(
        (times["eurusd"] >= start_ms) & (times["eurusd"] < end_ms)
    )
    if event_indices.size == 0:
        return pd.DataFrame()
    event_times = times["eurusd"][event_indices]
    event_eur_mid = mids["eurusd"][event_indices]
    baseline_staleness = int(rule["maximum_baseline_staleness_ms"])
    source_staleness = int(rule["maximum_current_source_staleness_ms"])
    xau_staleness = int(rule["maximum_current_xau_staleness_ms"])
    output: list[pd.DataFrame] = []
    for horizon in horizons_ms:
        targets = event_times - int(horizon)
        base_indices = {
            key: _aligned_indices(value, targets) for key, value in times.items()
        }
        current_indices = {
            "gbpusd": _aligned_indices(times["gbpusd"], event_times),
            "usdjpy": _aligned_indices(times["usdjpy"], event_times),
            "xau": _aligned_indices(times["xau"], event_times, side="left"),
        }
        valid = np.ones(len(event_times), dtype=bool)
        for index in base_indices.values():
            valid &= index >= 0
        for index in current_indices.values():
            valid &= index >= 0
        safe_base = {key: np.maximum(value, 0) for key, value in base_indices.items()}
        safe_current = {
            key: np.maximum(value, 0) for key, value in current_indices.items()
        }
        for key in frames:
            valid &= (
                targets - times[key][safe_base[key]] <= baseline_staleness
            )
        for key in ("gbpusd", "usdjpy"):
            valid &= (
                event_times - times[key][safe_current[key]] <= source_staleness
            )
        valid &= (
            event_times - times["xau"][safe_current["xau"]] <= xau_staleness
        )
        eur_move = (
            event_eur_mid / mids["eurusd"][safe_base["eurusd"]] - 1.0
        ) * 10_000.0
        gbp_move = (
            mids["gbpusd"][safe_current["gbpusd"]]
            / mids["gbpusd"][safe_base["gbpusd"]]
            - 1.0
        ) * 10_000.0
        jpy_move = (
            mids["usdjpy"][safe_current["usdjpy"]]
            / mids["usdjpy"][safe_base["usdjpy"]]
            - 1.0
        ) * 10_000.0
        xau_move = (
            mids["xau"][safe_current["xau"]]
            / mids["xau"][safe_base["xau"]]
            - 1.0
        ) * 10_000.0
        usd_moves = np.column_stack((-eur_move, -gbp_move, jpy_move))
        usd_signs = np.sign(usd_moves)
        dollar_sign = usd_signs[:, 0]
        unanimous = (dollar_sign != 0) & np.all(
            usd_signs == dollar_sign[:, None], axis=1
        )
        leg_min = np.min(np.abs(usd_moves), axis=1)
        breadth_sum = np.sum(np.abs(usd_moves), axis=1)
        expected_xau_sign = -dollar_sign
        signed_xau_move = expected_xau_sign * xau_move
        response = np.divide(
            signed_xau_move,
            leg_min,
            out=np.full_like(signed_xau_move, -np.inf),
            where=leg_min > 0,
        )
        quote_counts = np.column_stack(
            (
                event_indices - base_indices["eurusd"],
                current_indices["gbpusd"] - base_indices["gbpusd"],
                current_indices["usdjpy"] - base_indices["usdjpy"],
            )
        )
        source_quote_count = np.min(quote_counts, axis=1)
        valid &= unanimous
        valid &= leg_min >= float(prefilter["minimum_leg_move_bps"])
        valid &= breadth_sum >= float(prefilter["minimum_breadth_sum_bps"])
        valid &= response >= float(
            prefilter["minimum_signed_xau_response_ratio"]
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
                    "eurusd_baseline_timestamp_ms": times["eurusd"][
                        safe_base["eurusd"][chosen]
                    ],
                    "gbpusd_baseline_timestamp_ms": times["gbpusd"][
                        safe_base["gbpusd"][chosen]
                    ],
                    "gbpusd_current_timestamp_ms": times["gbpusd"][
                        safe_current["gbpusd"][chosen]
                    ],
                    "usdjpy_baseline_timestamp_ms": times["usdjpy"][
                        safe_base["usdjpy"][chosen]
                    ],
                    "usdjpy_current_timestamp_ms": times["usdjpy"][
                        safe_current["usdjpy"][chosen]
                    ],
                    "xau_baseline_timestamp_ms": times["xau"][
                        safe_base["xau"][chosen]
                    ],
                    "xau_current_timestamp_ms": times["xau"][
                        safe_current["xau"][chosen]
                    ],
                    "eurusd_move_bps": eur_move[chosen],
                    "gbpusd_move_bps": gbp_move[chosen],
                    "usdjpy_move_bps": jpy_move[chosen],
                    "minimum_leg_move_bps": leg_min[chosen],
                    "breadth_sum_bps": breadth_sum[chosen],
                    "xau_move_bps": xau_move[chosen],
                    "signed_xau_response_ratio": response[chosen],
                    "source_quote_count": source_quote_count[chosen],
                    "dollar_direction": np.where(
                        dollar_sign[chosen] > 0, "STRENGTH", "WEAKNESS"
                    ),
                    "direction": np.where(
                        dollar_sign[chosen] > 0, "LONG", "SHORT"
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
    return [
        {
            "horizon_ms": int(horizon),
            "minimum_leg_move_bps": float(leg),
            "minimum_breadth_sum_bps": float(total),
            "minimum_signed_xau_response_ratio": float(response),
            "minimum_source_quote_count": int(count),
        }
        for horizon, leg, total, response, count in itertools.product(
            calibration["horizon_ms_grid"],
            calibration["minimum_leg_move_bps_grid"],
            calibration["minimum_breadth_sum_bps_grid"],
            calibration["minimum_signed_xau_response_ratio_grid"],
            calibration["minimum_source_quote_count_grid"],
        )
    ]


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"H{int(policy['horizon_ms']):05d}"
        f"__LM{int(round(float(policy['minimum_leg_move_bps']) * 100)):03d}"
        f"__BS{int(round(float(policy['minimum_breadth_sum_bps']) * 100)):03d}"
        f"__RR{int(round(float(policy['minimum_signed_xau_response_ratio']) * 100)):03d}"
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
    mask &= features["breadth_sum_bps"] >= float(
        policy["minimum_breadth_sum_bps"]
    )
    mask &= features["signed_xau_response_ratio"] >= float(
        policy["minimum_signed_xau_response_ratio"]
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
        "V81:"
        + selected["policy_id"]
        + ":"
        + selected["decision_timestamp_ms"].astype("int64").astype(str)
        + ":"
        + selected["direction"],
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V81 candidate IDs are not unique")
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
            -float(row["minimum_breadth_sum_bps"]),
            -float(row["minimum_leg_move_bps"]),
            -float(row["minimum_signed_xau_response_ratio"]),
            -int(row["minimum_source_quote_count"]),
            int(row["horizon_ms"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "horizon_ms",
        "minimum_leg_move_bps",
        "minimum_breadth_sum_bps",
        "minimum_signed_xau_response_ratio",
        "minimum_source_quote_count",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}


def calibration_prefilter(calibration: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "minimum_leg_move_bps": min(calibration["minimum_leg_move_bps_grid"]),
        "minimum_breadth_sum_bps": min(
            calibration["minimum_breadth_sum_bps_grid"]
        ),
        "minimum_signed_xau_response_ratio": min(
            calibration["minimum_signed_xau_response_ratio_grid"]
        ),
        "minimum_source_quote_count": min(
            calibration["minimum_source_quote_count_grid"]
        ),
    }

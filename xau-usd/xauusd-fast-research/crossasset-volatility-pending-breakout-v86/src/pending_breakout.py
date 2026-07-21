from __future__ import annotations

import itertools
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from catchup import clock_ms


def session_quality(
    date: pd.Timestamp,
    dxy: pd.DataFrame,
    xag: pd.DataFrame,
    xau: pd.DataFrame,
    rule: Mapping[str, Any],
) -> dict[str, Any]:
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    sessions = {
        "dxy": dxy.loc[dxy["timestamp_ms"].between(start_ms, end_ms - 1)],
        "xag": xag.loc[xag["timestamp_ms"].between(start_ms, end_ms - 1)],
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
    minimum_quotes = rule["minimum_quotes_by_symbol"]
    eligible = bool(
        date.weekday() < 5
        and all(
            len(frame) >= int(minimum_quotes[key])
            for key, frame in sessions.items()
        )
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
    times: np.ndarray, targets: np.ndarray, *, side: str = "right"
) -> np.ndarray:
    return np.searchsorted(times, targets, side=side) - 1


def _breakout_rows(
    *,
    event_positions: np.ndarray,
    event_times: np.ndarray,
    xau_times: np.ndarray,
    xau_mids: np.ndarray,
    anchor_indices: np.ndarray,
    thresholds_bps: Sequence[float],
    trigger_window_ms: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for position in event_positions:
        event_time = int(event_times[position])
        start = int(np.searchsorted(xau_times, event_time, side="right"))
        end = int(
            np.searchsorted(
                xau_times, event_time + trigger_window_ms, side="right"
            )
        )
        if start >= end:
            continue
        anchor = float(xau_mids[int(anchor_indices[position])])
        moves = (xau_mids[start:end] / anchor - 1.0) * 10_000.0
        for threshold in thresholds_bps:
            crossing = np.flatnonzero(np.abs(moves) >= float(threshold))
            if crossing.size == 0:
                continue
            trigger_index = start + int(crossing[0])
            trigger_move = float(moves[int(crossing[0])])
            rows.append(
                {
                    "event_position": int(position),
                    "breakout_threshold_bps": float(threshold),
                    "trigger_index": trigger_index,
                    "trigger_timestamp_ms": int(xau_times[trigger_index]),
                    "breakout_move_bps": trigger_move,
                    "direction": "LONG" if trigger_move > 0 else "SHORT",
                }
            )
    return rows


def build_pending_breakout_features(
    date: pd.Timestamp,
    dxy: pd.DataFrame,
    xag: pd.DataFrame,
    xau: pd.DataFrame,
    *,
    horizons_ms: Sequence[int],
    breakout_thresholds_bps: Sequence[float],
    rule: Mapping[str, Any],
    prefilter: Mapping[str, Any],
) -> pd.DataFrame:
    if any(frame.empty for frame in (dxy, xag, xau)):
        return pd.DataFrame()
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    frames = {"dxy": dxy, "xag": xag, "xau": xau}
    times = {
        key: frame["timestamp_ms"].to_numpy(dtype=np.int64)
        for key, frame in frames.items()
    }
    mids = {
        key: frame["mid"].to_numpy(dtype=float) for key, frame in frames.items()
    }
    event_indices = np.flatnonzero(
        (times["dxy"] >= start_ms) & (times["dxy"] < end_ms)
    )
    if event_indices.size == 0:
        return pd.DataFrame()
    event_times = times["dxy"][event_indices]
    event_dxy_mid = mids["dxy"][event_indices]
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
            "xag": _aligned_indices(times["xag"], event_times),
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
            valid &= targets - times[key][safe_base[key]] <= baseline_staleness
        valid &= (
            event_times - times["xag"][safe_current["xag"]] <= source_staleness
        )
        valid &= (
            event_times - times["xau"][safe_current["xau"]] <= xau_staleness
        )
        dxy_move = (
            event_dxy_mid / mids["dxy"][safe_base["dxy"]] - 1.0
        ) * 10_000.0
        xag_move = (
            mids["xag"][safe_current["xag"]]
            / mids["xag"][safe_base["xag"]]
            - 1.0
        ) * 10_000.0
        initial_xau_move = (
            mids["xau"][safe_current["xau"]]
            / mids["xau"][safe_base["xau"]]
            - 1.0
        ) * 10_000.0
        dxy_magnitude = np.abs(dxy_move)
        xag_magnitude = np.abs(xag_move)
        initial_xau_magnitude = np.abs(initial_xau_move)
        quote_counts = np.column_stack(
            (
                event_indices - base_indices["dxy"],
                current_indices["xag"] - base_indices["xag"],
            )
        )
        source_quote_count = np.min(quote_counts, axis=1)
        valid &= dxy_magnitude >= float(prefilter["minimum_dxy_move_bps"])
        valid &= xag_magnitude >= float(prefilter["minimum_xag_move_bps"])
        valid &= initial_xau_magnitude <= float(
            prefilter["maximum_initial_xau_move_bps"]
        )
        valid &= source_quote_count >= int(prefilter["minimum_source_quote_count"])
        chosen = np.flatnonzero(valid)
        if chosen.size == 0:
            continue
        triggers = _breakout_rows(
            event_positions=chosen,
            event_times=event_times,
            xau_times=times["xau"],
            xau_mids=mids["xau"],
            anchor_indices=safe_current["xau"],
            thresholds_bps=breakout_thresholds_bps,
            trigger_window_ms=int(rule["trigger_window_ms"]),
        )
        if not triggers:
            continue
        trigger = pd.DataFrame(triggers)
        position = trigger["event_position"].to_numpy(dtype=np.int64)
        trigger_index = trigger["trigger_index"].to_numpy(dtype=np.int64)
        output.append(
            pd.DataFrame(
                {
                    "feature_time_utc": pd.to_datetime(
                        trigger["trigger_timestamp_ms"], unit="ms", utc=True
                    ),
                    "decision_timestamp_ms": trigger["trigger_timestamp_ms"],
                    "source_event_timestamp_ms": event_times[position],
                    "horizon_ms": int(horizon),
                    "breakout_threshold_bps": trigger["breakout_threshold_bps"],
                    "dxy_baseline_timestamp_ms": times["dxy"][
                        safe_base["dxy"][position]
                    ],
                    "xag_baseline_timestamp_ms": times["xag"][
                        safe_base["xag"][position]
                    ],
                    "xag_current_timestamp_ms": times["xag"][
                        safe_current["xag"][position]
                    ],
                    "xau_baseline_timestamp_ms": times["xau"][
                        safe_base["xau"][position]
                    ],
                    "xau_anchor_timestamp_ms": times["xau"][
                        safe_current["xau"][position]
                    ],
                    "xau_trigger_timestamp_ms": times["xau"][trigger_index],
                    "dxy_move_bps": dxy_move[position],
                    "xag_move_bps": xag_move[position],
                    "initial_xau_move_bps": initial_xau_move[position],
                    "dxy_magnitude_bps": dxy_magnitude[position],
                    "xag_magnitude_bps": xag_magnitude[position],
                    "initial_xau_magnitude_bps": initial_xau_magnitude[position],
                    "breakout_move_bps": trigger["breakout_move_bps"],
                    "source_quote_count": source_quote_count[position],
                    "direction": trigger["direction"],
                }
            )
        )
    if not output:
        return pd.DataFrame()
    return (
        pd.concat(output, ignore_index=True)
        .sort_values(
            ["feature_time_utc", "source_event_timestamp_ms", "horizon_ms"],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def policy_grid(calibration: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "horizon_ms": int(horizon),
            "minimum_dxy_move_bps": float(dxy),
            "minimum_xag_move_bps": float(xag),
            "maximum_initial_xau_move_bps": float(initial_xau),
            "breakout_move_bps": float(breakout),
        }
        for horizon, dxy, xag, initial_xau, breakout in itertools.product(
            calibration["horizon_ms_grid"],
            calibration["minimum_dxy_move_bps_grid"],
            calibration["minimum_xag_move_bps_grid"],
            calibration["maximum_initial_xau_move_bps_grid"],
            calibration["breakout_move_bps_grid"],
        )
    ]


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"H{int(policy['horizon_ms']):05d}"
        f"__DX{int(round(float(policy['minimum_dxy_move_bps']) * 100)):03d}"
        f"__AG{int(round(float(policy['minimum_xag_move_bps']) * 100)):03d}"
        f"__XI{int(round(float(policy['maximum_initial_xau_move_bps']) * 100)):03d}"
        f"__BO{int(round(float(policy['breakout_move_bps']) * 100)):03d}"
    )


def generate_candidates(
    features: pd.DataFrame,
    *,
    policy: Mapping[str, Any],
    family: str,
    minimum_source_quote_count: int,
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    mask = features["horizon_ms"].eq(int(policy["horizon_ms"]))
    mask &= features["breakout_threshold_bps"].eq(
        float(policy["breakout_move_bps"])
    )
    mask &= features["dxy_magnitude_bps"] >= float(
        policy["minimum_dxy_move_bps"]
    )
    mask &= features["xag_magnitude_bps"] >= float(
        policy["minimum_xag_move_bps"]
    )
    mask &= features["initial_xau_magnitude_bps"] <= float(
        policy["maximum_initial_xau_move_bps"]
    )
    mask &= features["source_quote_count"] >= int(minimum_source_quote_count)
    selected = features.loc[mask].copy()
    if selected.empty:
        return selected
    selected["date_utc"] = selected["feature_time_utc"].dt.date.astype(str)
    selected = selected.sort_values(
        ["feature_time_utc", "source_event_timestamp_ms", "horizon_ms"],
        kind="stable",
    )
    selected = selected.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected["family"] = family
    selected["policy_id"] = policy_id(policy)
    selected.insert(
        0,
        "candidate_id",
        "V86:"
        + selected["policy_id"]
        + ":"
        + selected["decision_timestamp_ms"].astype("int64").astype(str)
        + ":"
        + selected["direction"],
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V86 candidate IDs are not unique")
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
            -float(row["minimum_dxy_move_bps"]),
            -float(row["minimum_xag_move_bps"]),
            float(row["maximum_initial_xau_move_bps"]),
            -float(row["breakout_move_bps"]),
            int(row["horizon_ms"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "horizon_ms",
        "minimum_dxy_move_bps",
        "minimum_xag_move_bps",
        "maximum_initial_xau_move_bps",
        "breakout_move_bps",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}


def calibration_prefilter(
    calibration: Mapping[str, Any], rule: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "minimum_dxy_move_bps": min(calibration["minimum_dxy_move_bps_grid"]),
        "minimum_xag_move_bps": min(calibration["minimum_xag_move_bps_grid"]),
        "maximum_initial_xau_move_bps": max(
            calibration["maximum_initial_xau_move_bps_grid"]
        ),
        "minimum_source_quote_count": int(rule["minimum_source_quote_count"]),
    }

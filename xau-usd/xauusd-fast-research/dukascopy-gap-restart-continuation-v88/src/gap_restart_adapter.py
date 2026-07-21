from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
V26_SRC = ROOT.parent / "capital-gap-restart-forward-v26" / "src"
sys.path.insert(0, str(V26_SRC))

from gap_restart import generate_candidates as generate_v26_candidates  # noqa: E402
from catchup import clock_ms  # noqa: E402


def _ordered_quotes(quotes: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp_ms", "bid", "ask", "mid"}
    missing = sorted(required - set(quotes.columns))
    if missing:
        raise ValueError(f"V88 quotes are missing columns: {missing}")
    ordered = (
        quotes.sort_values("timestamp_ms", kind="stable")
        .drop_duplicates("timestamp_ms", keep="last")
        .reset_index(drop=True)
    )
    if not ordered.empty:
        timestamps = ordered["timestamp_ms"].to_numpy(dtype=np.int64)
        if np.any(np.diff(timestamps) <= 0):
            raise ValueError("V88 quote timestamps are not strictly increasing")
        if bool((ordered["ask"] < ordered["bid"]).any()):
            raise ValueError("V88 found crossed quotes")
    return ordered


def session_quality(
    date: pd.Timestamp, quotes: pd.DataFrame, rule: Mapping[str, Any]
) -> dict[str, Any]:
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    ordered = _ordered_quotes(quotes)
    session = ordered.loc[ordered["timestamp_ms"].between(start_ms, end_ms - 1)]
    if session.empty:
        coverage = 0.0
    else:
        coverage = (
            int(session["timestamp_ms"].iloc[-1])
            - int(session["timestamp_ms"].iloc[0])
        ) / 60_000
    eligible = bool(
        date.weekday() < 5
        and len(session) >= int(rule["minimum_session_quotes"])
        and coverage >= float(rule["minimum_session_coverage_minutes"])
    )
    return {
        "date_utc": date.date().isoformat(),
        "weekday": int(date.weekday()),
        "eligible_full_weekday": eligible,
        "xau_quotes": int(len(session)),
        "xau_coverage_minutes": coverage,
    }


def v26_candidate_config(rule: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "feature": {
            key: rule[key]
            for key in (
                "minimum_preceding_gap_ms",
                "maximum_preceding_gap_ms",
                "restart_observation_ms",
                "minimum_nonzero_mid_updates",
                "minimum_absolute_update_imbalance",
                "minimum_absolute_displacement_price",
                "maximum_spread_price",
            )
        },
        "episode": {
            "utc_block_hours": int(rule["utc_block_hours"]),
            "maximum_candidates_per_utc_day": int(
                rule["maximum_candidates_per_utc_day"]
            ),
        },
    }


def generate_candidates(
    date: pd.Timestamp,
    quotes: pd.DataFrame,
    *,
    rule: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    ordered = _ordered_quotes(quotes)
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    session = ordered.loc[ordered["timestamp_ms"].between(start_ms, end_ms - 1)].copy()
    if session.empty:
        return pd.DataFrame(), {"restart_episode_count": 0, "raw_candidate_count": 0}
    ticks = session.rename(columns={"timestamp_ms": "tick_time_msc"})
    ticks["spread_price"] = ticks["ask"] - ticks["bid"]
    candidates, audit = generate_v26_candidates(ticks, v26_candidate_config(rule))
    if candidates.empty:
        return pd.DataFrame(), audit
    candidates = candidates.copy()
    candidates["feature_time_utc"] = pd.to_datetime(
        candidates["tick_time_msc"], unit="ms", utc=True
    )
    candidates["decision_timestamp_ms"] = candidates["tick_time_msc"].astype(
        "int64"
    )
    candidates["direction"] = candidates["candidate_side"]
    candidates["family"] = str(rule["family"])
    candidates.insert(
        0,
        "candidate_id",
        "V88:"
        + candidates["decision_timestamp_ms"].astype(str)
        + ":"
        + candidates["direction"],
    )
    if candidates["candidate_id"].duplicated().any():
        raise ValueError("V88 candidate IDs are not unique")
    return candidates.reset_index(drop=True), audit


def summarize_candidate_facts(
    candidates: pd.DataFrame,
    *,
    eligible_dates: Sequence[str],
    calibration: Mapping[str, Any],
) -> dict[str, Any]:
    trades = len(candidates)
    days = len(eligible_dates)
    active_days = int(candidates["date_utc"].nunique()) if trades else 0
    longs = int((candidates["direction"] == "LONG").sum()) if trades else 0
    shorts = int((candidates["direction"] == "SHORT").sum()) if trades else 0
    frequency = trades / days if days else 0.0
    active_share = active_days / days if days else 0.0
    minority = min(longs, shorts) / trades if trades else 0.0
    passed = bool(
        float(calibration["minimum_candidates_per_full_weekday"])
        <= frequency
        <= float(calibration["maximum_candidates_per_full_weekday"])
        and active_share >= float(calibration["minimum_active_day_share"])
        and minority >= float(calibration["minimum_direction_share"])
    )
    return {
        "eligible_full_weekdays": days,
        "candidates": trades,
        "candidates_per_full_weekday": frequency,
        "active_days": active_days,
        "active_day_share": active_share,
        "long_candidates": longs,
        "short_candidates": shorts,
        "minority_direction_share": minority,
        "density_gate_passed": passed,
    }


def label_candidates(
    candidates: pd.DataFrame,
    *,
    quotes: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    columns = [
        "candidate_id",
        "status",
        "direction",
        "decision_time_utc",
        "entry_time_utc",
        "exit_time_utc",
        "observed_move_usd",
        "baseline_net_pnl_usd",
        "stress_net_pnl_usd",
    ]
    if candidates.empty:
        return pd.DataFrame(columns=columns)
    ordered = _ordered_quotes(quotes)
    times = ordered["timestamp_ms"].to_numpy(dtype=np.int64)
    execution = config["execution"]
    hold_ms = int(execution["hold_seconds"]) * 1000
    ounces = float(execution["ounces"])
    ticket = float(execution["ticket_cost_usd"])
    rows: list[dict[str, Any]] = []
    for candidate in candidates.to_dict("records"):
        decision_ms = int(candidate["decision_timestamp_ms"])
        row: dict[str, Any] = {
            "candidate_id": str(candidate["candidate_id"]),
            "status": "NO_ENTRY",
            "direction": str(candidate["direction"]),
            "decision_time_utc": pd.to_datetime(decision_ms, unit="ms", utc=True),
            "entry_time_utc": pd.NaT,
            "exit_time_utc": pd.NaT,
            "observed_move_usd": np.nan,
            "baseline_net_pnl_usd": np.nan,
            "stress_net_pnl_usd": np.nan,
        }
        entry_index = int(np.searchsorted(times, decision_ms, side="right"))
        if entry_index >= len(ordered):
            rows.append(row)
            continue
        entry_ms = int(times[entry_index])
        if entry_ms - decision_ms > int(execution["maximum_entry_delay_ms"]):
            rows.append(row)
            continue
        target_exit_ms = entry_ms + hold_ms
        exit_index = int(np.searchsorted(times, target_exit_ms, side="left"))
        row["entry_time_utc"] = pd.to_datetime(entry_ms, unit="ms", utc=True)
        row["status"] = "NO_EXIT"
        if exit_index >= len(ordered):
            rows.append(row)
            continue
        exit_ms = int(times[exit_index])
        if exit_ms - target_exit_ms > int(execution["maximum_exit_delay_ms"]):
            rows.append(row)
            continue
        entry = ordered.iloc[entry_index]
        exit_quote = ordered.iloc[exit_index]
        if row["direction"] == "LONG":
            observed = float(exit_quote["bid"]) - float(entry["ask"])
        elif row["direction"] == "SHORT":
            observed = float(entry["bid"]) - float(exit_quote["ask"])
        else:
            raise ValueError(f"Unknown V88 direction: {row['direction']}")
        row["status"] = "RESOLVED"
        row["exit_time_utc"] = pd.to_datetime(exit_ms, unit="ms", utc=True)
        row["observed_move_usd"] = observed * ounces
        row["baseline_net_pnl_usd"] = (
            observed * ounces
            - 2.0 * float(execution["base_slippage_per_side_usd"]) * ounces
            - ticket
        )
        row["stress_net_pnl_usd"] = (
            observed * ounces
            - 2.0 * float(execution["stress_slippage_per_side_usd"]) * ounces
            - ticket
        )
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)

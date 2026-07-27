from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .campaign import PIP_SIZE, sha256_file


TRADE_COLUMNS = [
    "specialist", "symbol", "signal_time_utc", "entry_time_utc", "exit_time_utc",
    "side", "entry_price", "stop_price", "target_price", "exit_price",
    "exit_reason", "risk_distance", "r", "extra_half_pip_stress_r",
]


def verify_seed_lock(package_root: Path) -> dict[str, str]:
    lock_path = package_root / "FOREX_SESSION_SEED_REGIME_DECOMPOSITION_PREREG_2026_07_27.sha256.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("locked_before_regime_outcome_join") is not True:
        raise RuntimeError("Seed decomposition was not locked before the regime/outcome join")
    checked = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(package_root / relative)
        if actual != expected:
            raise RuntimeError(f"Seed decomposition hash mismatch: {relative}")
        checked[relative] = actual
    return checked


def wilder_atr(frame: pd.DataFrame, period: int) -> pd.Series:
    previous = frame["close"].shift(1)
    tr = pd.concat(
        [
            frame["high"] - frame["low"],
            (frame["high"] - previous).abs(),
            (frame["low"] - previous).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def midpoint_resample(m5: pd.DataFrame, rule: str) -> pd.DataFrame:
    mid = pd.DataFrame(index=m5.index)
    mid["open"] = (m5["bid_open"] + m5["ask_open"]) / 2.0
    mid["high"] = (m5["bid_high"] + m5["ask_high"]) / 2.0
    mid["low"] = (m5["bid_low"] + m5["ask_low"]) / 2.0
    mid["close"] = (m5["bid_close"] + m5["ask_close"]) / 2.0
    return (
        mid.resample(rule, label="left", closed="left")
        .agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
        .dropna()
    )


def generate_seed_signals(m5: pd.DataFrame, seed: dict[str, Any]) -> pd.DataFrame:
    m15 = midpoint_resample(m5, f"{seed['signal_timeframe_minutes']}min")
    d1 = midpoint_resample(m5, "1D")
    m15["atr"] = wilder_atr(m15, seed["atr_period_m15"])
    d1["atr"] = wilder_atr(d1, seed["d1_atr_period"])
    rows: list[dict[str, Any]] = []
    point = float(seed["point"])
    for bar_time, bar in m15.iterrows():
        if pd.isna(bar["atr"]) or not (seed["trade_start_hour_utc"] <= bar_time.hour < seed["trade_end_hour_utc"]):
            continue
        day = bar_time.floor("D")
        previous_day = day - pd.Timedelta(days=1)
        if previous_day not in d1.index or pd.isna(d1.at[previous_day, "atr"]) or d1.at[previous_day, "atr"] <= 0:
            continue
        range_start = day + pd.Timedelta(hours=seed["range_start_hour_utc"])
        range_end = range_start + pd.Timedelta(minutes=seed["range_minutes"])
        range_bars = m15.loc[(m15.index >= range_start) & (m15.index < range_end)]
        expected_bars = seed["range_minutes"] // seed["signal_timeframe_minutes"]
        if len(range_bars) < expected_bars:
            continue
        range_high = float(range_bars["high"].max())
        range_low = float(range_bars["low"].min())
        session_range = range_high - range_low
        atr = float(bar["atr"])
        range_atr = session_range / atr
        if not (seed["range_atr_min"] <= range_atr <= seed["range_atr_max"]):
            continue
        if session_range / float(d1.at[previous_day, "atr"]) < seed["daily_range_atr_min"]:
            continue
        bar_range = max(float(bar["high"]) - float(bar["low"]), point)
        body_fraction = abs(float(bar["close"]) - float(bar["open"])) / bar_range
        if body_fraction < seed["body_fraction_min"]:
            continue
        close_location = (float(bar["close"]) - float(bar["low"])) / bar_range
        buffer = seed["break_buffer_atr"] * atr
        side = ""
        if float(bar["close"]) > range_high + buffer and close_location >= seed["long_close_location_min"]:
            side = "LONG"
        elif float(bar["close"]) < range_low - buffer and close_location <= seed["short_close_location_max"]:
            side = "SHORT"
        if side:
            rows.append(
                {
                    "signal_time_utc": bar_time,
                    "signal_complete_utc": bar_time + pd.Timedelta(minutes=seed["signal_timeframe_minutes"]),
                    "side": side,
                    "atr": atr,
                    "range_high": range_high,
                    "range_low": range_low,
                    "session_range": session_range,
                }
            )
    return pd.DataFrame(rows)


def assign_regime_ownership(signals: pd.DataFrame, state: pd.DataFrame) -> pd.DataFrame:
    result = signals.copy()
    ownership: list[str] = []
    state_times: list[pd.Timestamp | None] = []
    for _, signal in result.iterrows():
        completion = signal["signal_complete_utc"]
        latest_allowed = completion.floor("h") - pd.Timedelta(hours=1)
        position = int(state.index.searchsorted(latest_allowed, side="right")) - 1
        if position < 0:
            ownership.append("CASH_NO_STATE")
            state_times.append(None)
            continue
        row = state.iloc[position]
        state_time = state.index[position]
        state_times.append(state_time)
        if bool(row["shock"]):
            ownership.append("SHOCK_CASH")
            continue
        if bool(row["DXY_compressed"]) and bool(row["USDJPY_compressed"]):
            ownership.append("s3_compression_release_breakout")
            continue
        aligned = (
            (row["direction"] == "USD_UP" and signal["side"] == "LONG")
            or (row["direction"] == "USD_DOWN" and signal["side"] == "SHORT")
        )
        if row["phase"] == "ESTABLISHED" and aligned:
            ownership.append("s1_established_aligned_breakout")
        elif row["phase"] == "TRANSITION" and aligned:
            ownership.append("s2_transition_aligned_breakout")
        elif row["direction"] == "NEUTRAL" and row["phase"] == "UNRESOLVED":
            ownership.append("s4_neutral_normal_breakout")
        else:
            ownership.append("DIRECTION_CONFLICT_CASH")
    result["state_time_utc"] = state_times
    result["ownership"] = ownership
    return result


def simulate_owned_signals(
    signals: pd.DataFrame,
    m5: pd.DataFrame,
    specialist: str,
    seed: dict[str, Any],
    execution: dict[str, Any],
) -> pd.DataFrame:
    owned = signals[signals["ownership"] == specialist].sort_values("signal_complete_utc")
    records: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    daily_counts: dict[Any, int] = {}
    pip = PIP_SIZE["USDJPY"]
    slip = execution["extra_slippage_pips_per_side"] * pip
    quarantine_start = pd.Timestamp(execution["quarantine_start_utc"])
    quarantine_end = pd.Timestamp(execution["quarantine_end_utc"])
    for _, signal in owned.iterrows():
        position = int(m5.index.searchsorted(signal["signal_complete_utc"], side="left"))
        if position >= len(m5):
            continue
        entry_time = m5.index[position]
        if quarantine_start <= entry_time <= quarantine_end:
            continue
        if open_until is not None and entry_time < open_until:
            continue
        day_key = entry_time.date()
        if daily_counts.get(day_key, 0) >= seed["max_trades_per_day"]:
            continue
        entry_bar = m5.iloc[position]
        side = signal["side"]
        base_distance = max(
            seed["stop_atr_multiple"] * signal["atr"],
            seed["stop_range_multiple"] * signal["session_range"],
            seed["stop_floor_points"] * seed["point"],
        )
        if side == "LONG":
            entry = float(entry_bar["ask_open"]) + slip
            stop = min(float(signal["range_low"]), entry - base_distance)
            risk_distance = entry - stop
            target = entry + seed["risk_reward"] * risk_distance
        else:
            entry = float(entry_bar["bid_open"]) - slip
            stop = max(float(signal["range_high"]), entry + base_distance)
            risk_distance = stop - entry
            target = entry - seed["risk_reward"] * risk_distance
        if risk_distance / seed["point"] > seed["stop_ceiling_points"]:
            continue
        exit_time, exit_price, reason = walk_seed_exit(m5, position, side, stop, target, slip)
        pnl = exit_price - entry if side == "LONG" else entry - exit_price
        r_value = pnl / risk_distance
        records.append(
            {
                "specialist": specialist,
                "symbol": "USDJPY",
                "signal_time_utc": signal["signal_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "side": side,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk_distance,
                "r": r_value,
                "extra_half_pip_stress_r": r_value - (0.5 * pip / risk_distance),
            }
        )
        open_until = exit_time
        daily_counts[day_key] = daily_counts.get(day_key, 0) + 1
    return pd.DataFrame(records, columns=TRADE_COLUMNS)


def walk_seed_exit(
    m5: pd.DataFrame,
    start_position: int,
    side: str,
    stop: float,
    target: float,
    slip: float,
) -> tuple[pd.Timestamp, float, str]:
    for position in range(start_position, len(m5)):
        bar = m5.iloc[position]
        timestamp = m5.index[position]
        if side == "LONG":
            if float(bar["bid_low"]) <= stop:
                return timestamp, min(float(bar["bid_open"]), stop) - slip, "STOP"
            if float(bar["bid_high"]) >= target:
                return timestamp, max(float(bar["bid_open"]), target) - slip, "TARGET"
        else:
            if float(bar["ask_high"]) >= stop:
                return timestamp, max(float(bar["ask_open"]), stop) + slip, "STOP"
            if float(bar["ask_low"]) <= target:
                return timestamp, min(float(bar["ask_open"]), target) + slip, "TARGET"
    final = m5.iloc[-1]
    price = float(final["bid_close"]) - slip if side == "LONG" else float(final["ask_close"]) + slip
    return m5.index[-1], price, "DATA_END"

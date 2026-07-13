from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from regime import atr


STRATEGY_IDS = (
    "CHOP_ROBUST_EQUILIBRIUM_REVERSION_V1",
    "CHOP_IMPULSE_EXHAUSTION_REVERSION_V1",
    "CHOP_RANGE_ROTATION_CONTINUATION_V1",
)


@dataclass(frozen=True)
class ClockBars:
    day: int
    atr: int
    impulse: int
    confirmation: int
    memory: int
    hold_standard: int
    hold_impulse: int
    cooldown: int


def clock_bars(timeframe_minutes: int) -> ClockBars:
    if 1440 % timeframe_minutes or 180 % timeframe_minutes or 120 % timeframe_minutes or 360 % timeframe_minutes:
        raise ValueError("Timeframe must divide all frozen economic horizons exactly")
    return ClockBars(
        day=1440 // timeframe_minutes,
        atr=840 // timeframe_minutes,
        impulse=180 // timeframe_minutes,
        confirmation=120 // timeframe_minutes,
        memory=360 // timeframe_minutes,
        hold_standard=720 // timeframe_minutes,
        hold_impulse=540 // timeframe_minutes,
        cooldown=360 // timeframe_minutes,
    )


def rolling_exact_mad(values: pd.Series, window: int, chunk_size: int = 20_000) -> pd.Series:
    array = values.to_numpy(dtype=float)
    result = np.full(len(array), np.nan)
    if len(array) < window:
        return pd.Series(result, index=values.index)
    from numpy.lib.stride_tricks import sliding_window_view

    windows = sliding_window_view(array, window)
    for start in range(0, len(windows), chunk_size):
        block = windows[start : start + chunk_size]
        medians = np.median(block, axis=1)
        result[start + window - 1 : start + window - 1 + len(block)] = np.median(
            np.abs(block - medians[:, None]), axis=1
        )
    return pd.Series(result, index=values.index)


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def _clv(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    width = (frame["mid_high"] - frame["mid_low"]).replace(0.0, np.nan)
    return (frame["mid_close"] - frame["mid_low"]) / width, (frame["mid_high"] - frame["mid_close"]) / width


def _base_signal(frame: pd.DataFrame, mask: pd.Series, strategy_id: str, direction: str) -> pd.DataFrame:
    rows = frame.loc[mask].copy()
    rows["strategy_id"] = strategy_id
    rows["direction"] = direction
    rows["signal_time"] = rows["timestamp_utc"]
    return rows


def _equilibrium_setup_ids(frame: pd.DataFrame, z: pd.Series, threshold: float) -> tuple[pd.Series, pd.Series]:
    ids = {"LONG": np.zeros(len(frame), dtype=int), "SHORT": np.zeros(len(frame), dtype=int)}
    counters = {"LONG": 0, "SHORT": 0}
    active = {"LONG": False, "SHORT": False}
    for i, (value, regime_active) in enumerate(zip(z, frame["chop_active"], strict=True)):
        if not regime_active or not np.isfinite(value):
            active = {"LONG": False, "SHORT": False}
            continue
        for direction, beyond in (("LONG", value <= -threshold), ("SHORT", value >= threshold)):
            if beyond and not active[direction]:
                counters[direction] += 1
                active[direction] = True
            if active[direction]:
                ids[direction][i] = counters[direction]
            if active[direction] and ((direction == "LONG" and value >= 0) or (direction == "SHORT" and value <= 0)):
                active[direction] = False
    return pd.Series(ids["LONG"], index=frame.index), pd.Series(ids["SHORT"], index=frame.index)


def equilibrium_signals(frame: pd.DataFrame, cb: ClockBars, settings: dict[str, Any]) -> pd.DataFrame:
    work = frame.copy()
    typical = (work["mid_high"] + work["mid_low"] + work["mid_close"]) / 3.0
    median = typical.rolling(cb.day, min_periods=cb.day).median()
    mad = rolling_exact_mad(typical, cb.day)
    scale = 1.4826 * mad
    spread_price = (work["ask_close"] - work["bid_close"]).abs()
    z = (work["mid_close"] - median) / scale.where(scale >= spread_price)
    atr_value = atr(work, cb.atr)
    long_clv, short_clv = _clv(work)
    threshold = float(settings["z"])
    long_trigger = (z.shift(1) <= -threshold) & (z > -threshold)
    short_trigger = (z.shift(1) >= threshold) & (z < threshold)
    long_ids, short_ids = _equilibrium_setup_ids(work, z, threshold)
    common = work["chop_active"] & np.isfinite(z) & np.isfinite(atr_value) & (atr_value > 0)
    long_ok = common & long_trigger & (work["mid_close"] > work["mid_open"]) & (long_clv >= 0.60) & (work["mid_close"] < median)
    short_ok = common & short_trigger & (work["mid_close"] < work["mid_open"]) & (short_clv >= 0.60) & (work["mid_close"] > median)
    candidates = []
    for direction, trigger, accepted, setup_ids in (("LONG", long_trigger, long_ok, long_ids), ("SHORT", short_trigger, short_ok, short_ids)):
        rows = _base_signal(work, trigger.fillna(False), STRATEGY_IDS[0], direction)
        idx = rows.index
        rows["setup_episode_id"] = setup_ids.loc[idx].astype(int)
        starts = work.loc[setup_ids > 0].groupby(setup_ids.loc[setup_ids > 0])["timestamp_utc"].min()
        rows["setup_start_time"] = rows["setup_episode_id"].map(starts)
        rows["signal_accepted_pre_execution"] = accepted.loc[idx].astype(bool)
        rows["rejection_reason"] = np.where(rows["signal_accepted_pre_execution"], "", "EQUILIBRIUM_SIGNAL_CONDITION_FAILED")
        rows["atr"] = atr_value.loc[idx]
        rows["target_frozen"] = median.loc[idx]
        rows["stop_kind"] = "ENTRY_ATR"
        rows["stop_value"] = float(settings["stop_atr"])
        rows["max_hold_bars"] = cb.hold_standard
        rows["raw_z"] = z.loc[idx]
        rows["raw_center"] = median.loc[idx]
        rows["raw_scale"] = scale.loc[idx]
        candidates.append(rows)
    return pd.concat(candidates, ignore_index=False).sort_values("signal_time").reset_index(drop=True)


def _group_impulse_setups(times: pd.Series, directions: pd.Series) -> pd.Series:
    ids = np.zeros(len(times), dtype=int)
    counters = {"LONG": 0, "SHORT": 0}
    last: dict[str, pd.Timestamp | None] = {"LONG": None, "SHORT": None}
    for i, (time, direction) in enumerate(zip(times, directions, strict=True)):
        prior = last[direction]
        if prior is None or time - prior >= pd.Timedelta(hours=6):
            counters[direction] += 1
        ids[i] = counters[direction]
        last[direction] = time
    return pd.Series(ids, index=times.index)


def impulse_signals(frame: pd.DataFrame, cb: ClockBars, settings: dict[str, Any]) -> pd.DataFrame:
    work = frame.copy()
    log_close = np.log(work["mid_close"])
    returns = log_close.diff()
    std = returns.rolling(cb.day, min_periods=cb.day).std(ddof=1)
    impulse_return = returns.rolling(cb.impulse, min_periods=cb.impulse).sum()
    denominator = std * np.sqrt(cb.impulse)
    impulse_z = impulse_return / denominator.replace(0.0, np.nan)
    impulse_start = work["mid_open"].shift(cb.impulse - 1)
    impulse_low = work["mid_low"].rolling(cb.impulse, min_periods=cb.impulse).min()
    impulse_high = work["mid_high"].rolling(cb.impulse, min_periods=cb.impulse).max()
    atr_value = atr(work, cb.atr)
    long_clv, short_clv = _clv(work)
    threshold = float(settings["z"])
    common = work["chop_active"] & np.isfinite(impulse_z) & np.isfinite(atr_value) & (atr_value > 0)
    long_trigger = impulse_z <= -threshold
    short_trigger = impulse_z >= threshold
    long_ok = common & long_trigger & (work["mid_close"] > work["mid_close"].shift(1)) & (work["mid_close"] > work["mid_open"]) & (long_clv >= 0.60)
    short_ok = common & short_trigger & (work["mid_close"] < work["mid_close"].shift(1)) & (work["mid_close"] < work["mid_open"]) & (short_clv >= 0.60)
    candidates = []
    for direction, trigger, accepted in (("LONG", long_trigger, long_ok), ("SHORT", short_trigger, short_ok)):
        event = trigger & ((work["mid_close"] > work["mid_close"].shift(1)) if direction == "LONG" else (work["mid_close"] < work["mid_close"].shift(1)))
        rows = _base_signal(work, event.fillna(False), STRATEGY_IDS[1], direction)
        idx = rows.index
        rows["signal_accepted_pre_execution"] = accepted.loc[idx].astype(bool)
        rows["rejection_reason"] = np.where(rows["signal_accepted_pre_execution"], "", "IMPULSE_CONFIRMATION_FAILED")
        rows["atr"] = atr_value.loc[idx]
        rows["target_frozen"] = np.where(
            direction == "LONG",
            work.loc[idx, "mid_close"] + 0.50 * (impulse_start.loc[idx] - work.loc[idx, "mid_close"]),
            work.loc[idx, "mid_close"] - 0.50 * (work.loc[idx, "mid_close"] - impulse_start.loc[idx]),
        )
        rows["stop_kind"] = "ABSOLUTE"
        rows["stop_value"] = np.where(
            direction == "LONG", impulse_low.loc[idx] - float(settings["stop_buffer_atr"]) * atr_value.loc[idx],
            impulse_high.loc[idx] + float(settings["stop_buffer_atr"]) * atr_value.loc[idx],
        )
        rows["max_hold_bars"] = cb.hold_impulse
        rows["raw_z"] = impulse_z.loc[idx]
        rows["raw_center"] = impulse_start.loc[idx]
        rows["raw_scale"] = std.loc[idx]
        candidates.append(rows)
    result = pd.concat(candidates, ignore_index=True).sort_values("signal_time").reset_index(drop=True)
    result["setup_episode_id"] = _group_impulse_setups(result["signal_time"], result["direction"])
    result["setup_start_time"] = result.groupby(["direction", "setup_episode_id"])["signal_time"].transform("min") - pd.Timedelta(hours=3)
    return result


def _rotation_memory(z: pd.Series, active: pd.Series, memory_bars: int, side: str) -> tuple[pd.Series, pd.Series]:
    condition = z <= -1.5 if side == "LONG" else z >= 1.5
    recent = condition.shift(1).rolling(memory_bars, min_periods=1).max().fillna(0).astype(bool) & active
    episode_ids = np.zeros(len(z), dtype=int)
    counter = 0
    memory_active = False
    last_excursion = -10**9
    for i, (is_excursion, regime_active) in enumerate(zip(condition.fillna(False), active, strict=True)):
        if not regime_active or i - last_excursion > memory_bars:
            memory_active = False
        if is_excursion:
            if not memory_active:
                counter += 1
            memory_active = True
            last_excursion = i
        if memory_active:
            episode_ids[i] = counter
    return recent, pd.Series(episode_ids, index=z.index)


def rotation_signals(frame: pd.DataFrame, cb: ClockBars, settings: dict[str, Any]) -> pd.DataFrame:
    work = frame.copy()
    typical = (work["mid_high"] + work["mid_low"] + work["mid_close"]) / 3.0
    center = _ema(typical, cb.day)
    std = typical.rolling(cb.day, min_periods=cb.day).std(ddof=1)
    z = (work["mid_close"] - center) / std.replace(0.0, np.nan)
    atr_value = atr(work, cb.atr)
    two_hour_return = np.log(work["mid_close"] / work["mid_close"].shift(cb.confirmation))
    long_memory, long_ids = _rotation_memory(z, work["chop_active"], cb.memory, "LONG")
    short_memory, short_ids = _rotation_memory(z, work["chop_active"], cb.memory, "SHORT")
    long_cross = (work["mid_close"].shift(1) < center.shift(1)) & (work["mid_close"] > center)
    short_cross = (work["mid_close"].shift(1) > center.shift(1)) & (work["mid_close"] < center)
    common = work["chop_active"] & np.isfinite(z) & np.isfinite(atr_value) & (atr_value > 0)
    long_trigger = long_memory & long_cross
    short_trigger = short_memory & short_cross
    long_ok = common & long_trigger & (two_hour_return > 0) & (work["mid_close"] > work["mid_open"])
    short_ok = common & short_trigger & (two_hour_return < 0) & (work["mid_close"] < work["mid_open"])
    candidates = []
    for direction, trigger, accepted, setup_ids in (("LONG", long_trigger, long_ok, long_ids), ("SHORT", short_trigger, short_ok, short_ids)):
        rows = _base_signal(work, trigger.fillna(False), STRATEGY_IDS[2], direction)
        idx = rows.index
        rows["setup_episode_id"] = setup_ids.loc[idx].astype(int)
        starts = work.loc[setup_ids > 0].groupby(setup_ids.loc[setup_ids > 0])["timestamp_utc"].min()
        rows["setup_start_time"] = rows["setup_episode_id"].map(starts)
        rows["signal_accepted_pre_execution"] = accepted.loc[idx].astype(bool)
        rows["rejection_reason"] = np.where(rows["signal_accepted_pre_execution"], "", "ROTATION_CONFIRMATION_FAILED")
        rows["atr"] = atr_value.loc[idx]
        rows["target_frozen"] = np.where(direction == "LONG", center.loc[idx] + 1.25 * std.loc[idx], center.loc[idx] - 1.25 * std.loc[idx])
        rows["stop_kind"] = "ENTRY_ATR"
        rows["stop_value"] = float(settings["stop_atr"])
        rows["max_hold_bars"] = cb.hold_standard
        rows["raw_z"] = z.loc[idx]
        rows["raw_center"] = center.loc[idx]
        rows["raw_scale"] = std.loc[idx]
        candidates.append(rows)
    return pd.concat(candidates, ignore_index=False).sort_values("signal_time").reset_index(drop=True)


def generate_signals(frame: pd.DataFrame, timeframe_minutes: int, config: dict[str, Any]) -> pd.DataFrame:
    cb = clock_bars(timeframe_minutes)
    frames = [
        equilibrium_signals(frame, cb, config["strategies"]["equilibrium"]),
        impulse_signals(frame, cb, config["strategies"]["impulse"]),
        rotation_signals(frame, cb, config["strategies"]["rotation"]),
    ]
    result = pd.concat(frames, ignore_index=True).sort_values(["signal_time", "strategy_id", "direction"], kind="mergesort").reset_index(drop=True)
    return result

"""Preregistered strategy families.

Design constraint driven by ``outputs/REFERENCE_SPREAD_STRESS.json``: the
inherited EURUSD fade used ~157-point stops and died at a 1-pip spread. Every
family here therefore carries a **stop floor** so realistic retail cost stays a
small fraction of risk, and frequency is bought with more pairs and more
sessions rather than tighter stops.

Each family is split in two so a parameter sweep stays cheap and honest:

* ``candidates_*`` decides *which* bars trade. It reads completed bars only and
  returns the M5 bar whose open is the fill.
* :func:`build_signals` turns candidates into stop/target geometry. Sweeping
  stop and target parameters never changes the trigger set, so a sweep cannot
  smuggle in extra trigger tuning.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .engine import Signals
from .fxdata import INSTRUMENTS, add_time_columns, mid, resample_from_m5
from .indicators import atr, decision_to_execution, rolling_max, rolling_min, shift

# Session boundaries in UTC. Fixed by market structure, never swept.
ASIA_START, ASIA_END = 0, 7
LONDON_BREAK_END = 12
FLATTEN_HOUR = 20


@dataclass
class Candidates:
    """Trigger set plus the context needed to size a stop."""

    entry_index: np.ndarray
    direction: np.ndarray
    atr_points: np.ndarray
    context_points: np.ndarray  # range width, channel width, or excursion
    family: str

    def __len__(self) -> int:
        return int(self.entry_index.size)


def build_signals(
    candidates: Candidates,
    *,
    stop_floor_points: float,
    context_mult: float,
    atr_mult: float,
    rr: float,
    stop_cap_points: float,
) -> Signals:
    """Compose stop geometry: the widest of floor, context and ATR terms."""
    stop_from_context = candidates.context_points * context_mult
    stop_from_atr = candidates.atr_points * atr_mult
    stop_points = np.maximum(stop_from_context, stop_from_atr)
    stop_points = np.maximum(stop_points, stop_floor_points)
    count = len(candidates)
    return Signals(
        entry_index=candidates.entry_index,
        direction=candidates.direction,
        stop_min_points=stop_points,
        stop_atr_points=np.zeros(count),
        stop_ref_price=np.full(count, np.nan),
        rr=np.full(count, rr),
        stop_cap_points=np.full(count, stop_cap_points),
        tag=np.full(count, candidates.family),
    )


def _points(symbol: str) -> float:
    return float(INSTRUMENTS[symbol]["point_size"])


def _m5_atr_points(m5: pd.DataFrame, symbol: str, timeframe_minutes: int, length: int) -> np.ndarray:
    """ATR of a higher timeframe, expressed in points and mapped onto M5 bars."""
    frame = resample_from_m5(m5, timeframe_minutes)
    values = shift(atr(mid(frame, "high"), mid(frame, "low"), mid(frame, "close"), length), 1)
    slot = frame["timestamp_ms"].to_numpy()
    index = np.searchsorted(slot, m5["timestamp_ms"].to_numpy(), side="right") - 1
    index = np.clip(index, 0, slot.size - 1)
    return values[index] / _points(symbol)


# --------------------------------------------------------------------------
# Family A: Asia-range London breakout (liquidity-arrival expansion)
# --------------------------------------------------------------------------
def candidates_london_breakout(m5: pd.DataFrame, symbol: str) -> Candidates:
    """Break of the Asia range once London liquidity arrives.

    Triggers on a *completed* M5 close beyond the Asia extreme, fills at the
    next M5 open, and takes at most the first break of each side per day.
    """
    point = _points(symbol)
    timed = add_time_columns(m5)
    hour = timed["hour"].to_numpy()
    date = timed["date"].to_numpy()
    high = mid(m5, "high")
    low = mid(m5, "low")
    close = mid(m5, "close")

    asia = (hour >= ASIA_START) & (hour < ASIA_END)
    frame = pd.DataFrame({"date": date, "high": high, "low": low, "asia": asia})
    asia_high = frame.loc[asia].groupby("date")["high"].max()
    asia_low = frame.loc[asia].groupby("date")["low"].min()
    level_high = frame["date"].map(asia_high).to_numpy(dtype=float)
    level_low = frame["date"].map(asia_low).to_numpy(dtype=float)
    range_points = (level_high - level_low) / point

    window = (hour >= ASIA_END) & (hour < LONDON_BREAK_END)
    long_break = window & np.isfinite(level_high) & (close > level_high)
    short_break = window & np.isfinite(level_low) & (close < level_low)

    picks: list[tuple[int, int]] = []
    triggers = pd.DataFrame({"date": date, "long": long_break, "short": short_break})
    for direction, column in ((1, "long"), (-1, "short")):
        first = triggers.loc[triggers[column]].groupby("date").apply(
            lambda block: block.index[0], include_groups=False
        )
        picks.extend((int(index), direction) for index in first.to_numpy())

    if not picks:
        return Candidates(*(np.empty(0) for _ in range(4)), family="london_breakout")

    picks.sort()
    signal_index = np.array([index for index, _ in picks], dtype=np.int64)
    direction = np.array([value for _, value in picks], dtype=np.int64)
    entry_index = signal_index + 1
    keep = entry_index < len(m5)

    atr_points = _m5_atr_points(m5, symbol, 60, 14)
    return Candidates(
        entry_index=entry_index[keep],
        direction=direction[keep],
        atr_points=atr_points[signal_index[keep]],
        context_points=range_points[signal_index[keep]],
        family="london_breakout",
    )


# --------------------------------------------------------------------------
# Family B: H4 Donchian channel breakout (multi-day trend persistence)
# --------------------------------------------------------------------------
def candidates_donchian(m5: pd.DataFrame, symbol: str, channel_bars: int = 30) -> Candidates:
    """Completed H4 close beyond the prior ``channel_bars`` H4 extreme."""
    point = _points(symbol)
    h4 = resample_from_m5(m5, 240)
    close = mid(h4, "close")
    high = mid(h4, "high")
    low = mid(h4, "low")

    signal_close = shift(close, 1)
    upper = shift(rolling_max(high, channel_bars), 2)
    lower = shift(rolling_min(low, channel_bars), 2)
    atr_points = shift(atr(high, low, close, 14), 1) / point

    long_break = np.isfinite(upper) & np.isfinite(signal_close) & (signal_close > upper)
    short_break = np.isfinite(lower) & np.isfinite(signal_close) & (signal_close < lower)
    trigger = long_break | short_break

    execution = decision_to_execution(
        h4["timestamp_ms"].to_numpy(), m5["timestamp_ms"].to_numpy(), 240 * 60_000
    )
    keep = trigger & (execution >= 0) & np.isfinite(atr_points)
    picked = np.flatnonzero(keep)
    channel_points = (upper[picked] - lower[picked]) / point

    return Candidates(
        entry_index=execution[picked],
        direction=np.where(long_break[picked], 1, -1).astype(np.int64),
        atr_points=atr_points[picked],
        context_points=channel_points,
        family="donchian_h4",
    )


# --------------------------------------------------------------------------
# Family C: Asia-session excursion fade (thin-liquidity mean reversion)
# --------------------------------------------------------------------------
def candidates_asia_fade(m5: pd.DataFrame, symbol: str, lookback_bars: int = 24) -> Candidates:
    """Fade an M30 excursion during the thin Asia session.

    Rationale: overnight moves without fundamental flow tend to retrace when
    London prices the session. Trades only inside Asia hours.
    """
    point = _points(symbol)
    m30 = resample_from_m5(m5, 30)
    close = mid(m30, "close")
    high = mid(m30, "high")
    low = mid(m30, "low")

    signal_close = shift(close, 1)
    reference = shift(pd.Series(close).rolling(lookback_bars).mean().to_numpy(), 1)
    atr_points = shift(atr(high, low, close, 14), 1) / point
    excursion_points = (signal_close - reference) / point

    hour = pd.to_datetime(m30["timestamp_ms"], unit="ms", utc=True).dt.hour.to_numpy()
    in_asia = (hour >= ASIA_START) & (hour < ASIA_END)

    stretched = np.isfinite(excursion_points) & np.isfinite(atr_points) & (atr_points > 0)
    magnitude = np.abs(excursion_points) / np.where(atr_points > 0, atr_points, np.nan)
    trigger = in_asia & stretched & (magnitude >= 1.5)

    execution = decision_to_execution(
        m30["timestamp_ms"].to_numpy(), m5["timestamp_ms"].to_numpy(), 30 * 60_000
    )
    keep = trigger & (execution >= 0)
    picked = np.flatnonzero(keep)

    return Candidates(
        entry_index=execution[picked],
        # fade: sell an up-excursion, buy a down-excursion
        direction=np.where(excursion_points[picked] > 0, -1, 1).astype(np.int64),
        atr_points=atr_points[picked],
        context_points=np.abs(excursion_points[picked]),
        family="asia_fade",
    )


FAMILIES = {
    "london_breakout": candidates_london_breakout,
    "donchian_h4": candidates_donchian,
    "asia_fade": candidates_asia_fade,
}

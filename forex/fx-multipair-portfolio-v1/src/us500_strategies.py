"""US500 intraday strategy families, keyed to the US cash session.

The FX families in ``strategies.py`` are keyed to Asia/London, which is
meaningless for an equity index. These are the index analogues, each an
established effect rather than a mined pattern:

* ``opening_range``   — the US cash open is the day's liquidity and
  information event; a break of the first 30 minutes is the classic index
  expansion trade.
* ``overnight_fade``  — the overnight session is thin and gaps often retrace
  once the cash session prices them.
* ``session_trend``   — H1 Donchian continuation inside the cash session,
  included as a deliberate control: it failed on FX majors, so if it also fails
  here that is consistent, and if it passes on an instrument with 2x the
  range/cost ratio that is informative about *why* FX failed.

Session boundaries are UTC and fixed by market structure, never swept. The US
cash session is 13:30–20:00 UTC in summer and 14:30–21:00 in winter; the DST
shift is handled by deriving the open from the exchange calendar rather than
hard-coding one clock.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .fxdata import INSTRUMENTS, add_time_columns, mid, resample_from_m5
from .indicators import atr, decision_to_execution, rolling_max, rolling_min, shift
from .strategies import Candidates

# US cash session in UTC, by DST state.
SUMMER_OPEN, SUMMER_CLOSE = 13 * 60 + 30, 20 * 60
WINTER_OPEN, WINTER_CLOSE = 14 * 60 + 30, 21 * 60
OPENING_RANGE_MINUTES = 30


def _session_minutes(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Minutes-since-midnight plus the session open/close for each bar's date.

    US DST runs from the second Sunday in March to the first Sunday in November.
    Deriving it beats hard-coding because a one-hour error would silently move
    every opening-range trade.
    """
    stamps = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    minutes = (stamps.dt.hour * 60 + stamps.dt.minute).to_numpy()
    month = stamps.dt.month.to_numpy()
    day = stamps.dt.day.to_numpy()
    weekday = stamps.dt.weekday.to_numpy()

    # second Sunday in March .. first Sunday in November
    after_march = (month > 3) | ((month == 3) & (day - weekday_offset(day, weekday) >= 8))
    before_november = (month < 11) | ((month == 11) & (day - weekday_offset(day, weekday) < 1))
    summer = after_march & before_november
    open_minutes = np.where(summer, SUMMER_OPEN, WINTER_OPEN)
    close_minutes = np.where(summer, SUMMER_CLOSE, WINTER_CLOSE)
    return minutes, open_minutes, close_minutes


def weekday_offset(day: np.ndarray, weekday: np.ndarray) -> np.ndarray:
    """Days since the most recent Sunday, used to locate the nth Sunday."""
    return (weekday + 1) % 7


def _points(symbol: str) -> float:
    return float(INSTRUMENTS[symbol]["point_size"])


def _atr_points(m5: pd.DataFrame, symbol: str, timeframe_minutes: int, length: int) -> np.ndarray:
    frame = resample_from_m5(m5, timeframe_minutes)
    values = shift(atr(mid(frame, "high"), mid(frame, "low"), mid(frame, "close"), length), 1)
    slot = frame["timestamp_ms"].to_numpy()
    index = np.clip(np.searchsorted(slot, m5["timestamp_ms"].to_numpy(), side="right") - 1, 0, slot.size - 1)
    return values[index] / _points(symbol)


def candidates_opening_range(m5: pd.DataFrame, symbol: str = "US500") -> Candidates:
    """Break of the first 30 minutes of the US cash session."""
    point = _points(symbol)
    timed = add_time_columns(m5)
    date = timed["date"].to_numpy()
    minutes, open_minutes, close_minutes = _session_minutes(m5)
    high, low, close = mid(m5, "high"), mid(m5, "low"), mid(m5, "close")

    in_range = (minutes >= open_minutes) & (minutes < open_minutes + OPENING_RANGE_MINUTES)
    frame = pd.DataFrame({"date": date, "high": high, "low": low})
    range_high = frame["date"].map(frame.loc[in_range].groupby("date")["high"].max()).to_numpy(float)
    range_low = frame["date"].map(frame.loc[in_range].groupby("date")["low"].min()).to_numpy(float)
    width_points = (range_high - range_low) / point

    tradable = (
        (minutes >= open_minutes + OPENING_RANGE_MINUTES)
        & (minutes < close_minutes - 30)
        & np.isfinite(range_high)
        & np.isfinite(range_low)
    )
    long_break = tradable & (close > range_high)
    short_break = tradable & (close < range_low)

    picks: list[tuple[int, int]] = []
    triggers = pd.DataFrame({"date": date, "long": long_break, "short": short_break})
    for direction, column in ((1, "long"), (-1, "short")):
        hits = triggers.loc[triggers[column]]
        if hits.empty:
            continue
        first = hits.groupby("date").apply(lambda block: block.index[0], include_groups=False)
        picks.extend((int(i), direction) for i in first.to_numpy())
    if not picks:
        return Candidates(*(np.empty(0) for _ in range(4)), family="opening_range")

    picks.sort()
    signal_index = np.array([i for i, _ in picks], dtype=np.int64)
    direction = np.array([d for _, d in picks], dtype=np.int64)
    entry = signal_index + 1
    keep = entry < len(m5)
    atr_points = _atr_points(m5, symbol, 60, 14)
    return Candidates(
        entry_index=entry[keep],
        direction=direction[keep],
        atr_points=atr_points[signal_index[keep]],
        context_points=width_points[signal_index[keep]],
        family="opening_range",
    )


def candidates_overnight_fade(m5: pd.DataFrame, symbol: str = "US500") -> Candidates:
    """Fade the overnight excursion once the cash session opens.

    Direction is set by the gap: a gap up is sold, a gap down is bought, entered
    on the first bar after the opening range completes.
    """
    point = _points(symbol)
    timed = add_time_columns(m5)
    date = timed["date"].to_numpy()
    minutes, open_minutes, close_minutes = _session_minutes(m5)
    close = mid(m5, "close")

    frame = pd.DataFrame({"date": date, "close": close, "minutes": minutes})
    session_close = frame.loc[minutes >= close_minutes - 5].groupby("date")["close"].last()
    session_open = frame.loc[minutes >= open_minutes].groupby("date")["close"].first()
    previous_close = session_close.shift(1)
    gap_points = ((session_open - previous_close) / point).rename("gap")

    entry_mask = (minutes == open_minutes + OPENING_RANGE_MINUTES)
    rows = np.flatnonzero(entry_mask)
    if rows.size == 0:
        return Candidates(*(np.empty(0) for _ in range(4)), family="overnight_fade")
    gaps = pd.Series(date[rows]).map(gap_points).to_numpy(float)
    valid = np.isfinite(gaps) & (np.abs(gaps) > 0)
    rows, gaps = rows[valid], gaps[valid]

    atr_points = _atr_points(m5, symbol, 60, 14)
    entry = rows + 1
    keep = entry < len(m5)
    return Candidates(
        entry_index=entry[keep],
        direction=np.where(gaps[keep] > 0, -1, 1).astype(np.int64),
        atr_points=atr_points[rows[keep]],
        context_points=np.abs(gaps[keep]),
        family="overnight_fade",
    )


def candidates_session_trend(m5: pd.DataFrame, symbol: str = "US500", channel_bars: int = 20) -> Candidates:
    """H1 Donchian continuation, restricted to the cash session."""
    point = _points(symbol)
    h1 = resample_from_m5(m5, 60)
    close, high, low = mid(h1, "close"), mid(h1, "high"), mid(h1, "low")
    signal_close = shift(close, 1)
    upper = shift(rolling_max(high, channel_bars), 2)
    lower = shift(rolling_min(low, channel_bars), 2)
    atr_points = shift(atr(high, low, close, 14), 1) / point

    long_break = np.isfinite(upper) & (signal_close > upper)
    short_break = np.isfinite(lower) & (signal_close < lower)
    trigger = long_break | short_break

    execution = decision_to_execution(
        h1["timestamp_ms"].to_numpy(), m5["timestamp_ms"].to_numpy(), 60 * 60_000
    )
    minutes, open_minutes, close_minutes = _session_minutes(m5)
    in_session = np.zeros(len(m5), dtype=bool)
    in_session[(minutes >= open_minutes) & (minutes < close_minutes - 30)] = True

    keep = trigger & (execution >= 0) & np.isfinite(atr_points)
    picked = np.flatnonzero(keep)
    picked = picked[in_session[execution[picked]]]
    return Candidates(
        entry_index=execution[picked],
        direction=np.where(long_break[picked], 1, -1).astype(np.int64),
        atr_points=atr_points[picked],
        context_points=(upper[picked] - lower[picked]) / point,
        family="session_trend",
    )


US500_FAMILIES = {
    "opening_range": candidates_opening_range,
    "overnight_fade": candidates_overnight_fade,
    "session_trend": candidates_session_trend,
}

"""Entry families for the mega-search.

Each family returns M5 execution indices, so the engine always simulates the
full 24-hour path. Every family reads **completed** decision bars only and
enters on the next M5 open; the offset is enforced centrally by
``decision_to_execution`` rather than trusted to each family.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .fxdata import mid, resample_from_m5
from .indicators import (
    atr,
    bollinger,
    decision_to_execution,
    rolling_max,
    rolling_min,
    rsi,
    shift,
)

SESSIONS = {"all": None, "us": (13 * 60 + 30, 20 * 60), "non_us": "outside_us"}


def timeframe_frame(m5: pd.DataFrame, minutes: int) -> dict:
    """Precompute everything the families need for one decision timeframe."""
    frame = resample_from_m5(m5, minutes)
    close, high, low = mid(frame, "close"), mid(frame, "high"), mid(frame, "low")
    stamps = pd.to_datetime(frame["timestamp_ms"], unit="ms", utc=True)
    return {
        "minutes": minutes,
        "timestamp_ms": frame["timestamp_ms"].to_numpy(),
        "close": close, "high": high, "low": low,
        "signal_close": shift(close, 1),
        "signal_high": shift(high, 1),
        "signal_low": shift(low, 1),
        "atr": shift(atr(high, low, close, 14), 1),
        "rsi": shift(rsi(close, 14), 1),
        "minute_of_day": (stamps.dt.hour * 60 + stamps.dt.minute).to_numpy(),
        "execution": None,  # filled by prepare()
    }


def prepare(data: dict, m5_timestamps: np.ndarray) -> dict:
    data["execution"] = decision_to_execution(
        data["timestamp_ms"], m5_timestamps, data["minutes"] * 60_000
    )
    return data


def _session_mask(data: dict, session: str) -> np.ndarray:
    if session == "all":
        return np.ones(data["close"].size, dtype=bool)
    minute = data["minute_of_day"]
    inside = (minute >= SESSIONS["us"][0]) & (minute < SESSIONS["us"][1])
    return inside if session == "us" else ~inside


def signals_for(family: str, data: dict, param: int, direction: int) -> np.ndarray:
    """Boolean trigger array on decision bars, for one family/parameter/side."""
    close, high, low = data["close"], data["high"], data["low"]
    sig_close, sig_high, sig_low = data["signal_close"], data["signal_high"], data["signal_low"]
    atr_values, rsi_values = data["atr"], data["rsi"]
    long = direction > 0

    if family == "rsi_extreme":
        return (sig_rsi_lo(rsi_values, param) if long else sig_rsi_hi(rsi_values, param))

    if family == "bollinger":
        _, upper, lower = bollinger(close, param, 2.0)
        band = shift(lower if long else upper, 1)
        return np.isfinite(band) & ((sig_close <= band) if long else (sig_close >= band))

    if family == "breakout":
        extreme = shift(rolling_max(high, param) if long else rolling_min(low, param), 2)
        return np.isfinite(extreme) & ((sig_close > extreme) if long else (sig_close < extreme))

    if family == "fade":
        extreme = shift(rolling_min(low, param) if long else rolling_max(high, param), 2)
        return np.isfinite(extreme) & ((sig_close < extreme) if long else (sig_close > extreme))

    if family == "ma_reversion":
        mean = shift(pd.Series(close).rolling(param).mean().to_numpy(), 1)
        distance = (sig_close - mean) / np.where(atr_values > 0, atr_values, np.nan)
        return np.isfinite(distance) & ((distance <= -1.0) if long else (distance >= 1.0))

    if family == "consecutive":
        step = np.r_[np.nan, np.diff(close)]
        mask = np.ones(close.size, dtype=bool)
        for k in range(param):
            shifted = shift(step, k + 1)
            mask &= (shifted < 0) if long else (shifted > 0)
        return mask & np.isfinite(shift(step, param))

    if family == "vol_expansion":
        short_vol = shift(pd.Series(close).pct_change().rolling(param).std().to_numpy(), 1)
        long_vol = shift(pd.Series(close).pct_change().rolling(param * 4).std().to_numpy(), 1)
        expanding = np.isfinite(short_vol) & np.isfinite(long_vol) & (short_vol > 1.5 * long_vol)
        step = shift(np.r_[np.nan, np.diff(close)], 1)
        return expanding & ((step > 0) if long else (step < 0))

    if family == "range_break":
        span = shift(rolling_max(high, param) - rolling_min(low, param), 2)
        reference = shift(rolling_max(high, param) if long else rolling_min(low, param), 2)
        wide = np.isfinite(span) & (span > 0)
        return wide & ((sig_close > reference) if long else (sig_close < reference))

    raise ValueError(f"unknown family: {family}")


def sig_rsi_lo(values: np.ndarray, level: int) -> np.ndarray:
    return np.isfinite(values) & (values <= level)


def sig_rsi_hi(values: np.ndarray, level: int) -> np.ndarray:
    return np.isfinite(values) & (values >= 100 - level)


FAMILY_PARAMS = {
    "rsi_extreme": (20, 25, 30, 35),
    "bollinger": (14, 20, 30),
    "breakout": (10, 20, 40),
    "fade": (10, 20, 40),
    "ma_reversion": (20, 50, 100),
    "consecutive": (2, 3, 4),
    "vol_expansion": (10, 20),
    "range_break": (12, 24, 48),
}

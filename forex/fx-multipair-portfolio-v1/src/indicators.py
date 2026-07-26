"""Indicators and decision-timeframe plumbing.

Every indicator here returns values aligned to the bar that *produced* them.
Strategies must shift before use so a decision only ever reads completed bars;
:func:`decision_to_execution` then maps a completed decision bar to the first
M5 execution bar that opens after it, which is the earliest legitimate fill.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rma(values: np.ndarray, length: int) -> np.ndarray:
    """Wilder's smoothing, as used by MT5 RSI and ATR."""
    out = np.full(values.size, np.nan, dtype=np.float64)
    if values.size < length:
        return out
    seed = float(np.mean(values[:length]))
    out[length - 1] = seed
    alpha = 1.0 / length
    previous = seed
    for index in range(length, values.size):
        previous = previous + alpha * (values[index] - previous)
        out[index] = previous
    return out


def rsi(close: np.ndarray, length: int = 14) -> np.ndarray:
    delta = np.diff(close, prepend=close[0])
    delta[0] = 0.0
    gain = rma(np.clip(delta, 0.0, None), length)
    loss = rma(np.clip(-delta, 0.0, None), length)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = np.where(loss > 0, gain / loss, np.inf)
    return np.where(np.isfinite(rs), 100.0 - 100.0 / (1.0 + rs), 100.0)


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, length: int = 14) -> np.ndarray:
    previous_close = np.roll(close, 1)
    previous_close[0] = close[0]
    true_range = np.maximum(
        high - low, np.maximum(np.abs(high - previous_close), np.abs(low - previous_close))
    )
    return rma(true_range, length)


def bollinger(close: np.ndarray, length: int = 20, deviations: float = 2.0):
    series = pd.Series(close)
    middle = series.rolling(length).mean()
    # MT5 Bollinger uses the population standard deviation.
    spread = series.rolling(length).std(ddof=0)
    return (
        middle.to_numpy(),
        (middle + deviations * spread).to_numpy(),
        (middle - deviations * spread).to_numpy(),
    )


def rolling_min(values: np.ndarray, length: int) -> np.ndarray:
    return pd.Series(values).rolling(length).min().to_numpy()


def rolling_max(values: np.ndarray, length: int) -> np.ndarray:
    return pd.Series(values).rolling(length).max().to_numpy()


def shift(values: np.ndarray, periods: int = 1) -> np.ndarray:
    """Shift forward so index i holds the value from i-periods."""
    out = np.full_like(values, np.nan, dtype=np.float64)
    if periods <= 0:
        return values.astype(np.float64)
    out[periods:] = values[:-periods]
    return out


def decision_to_execution(decision_ms: np.ndarray, execution_ms: np.ndarray, width_ms: int) -> np.ndarray:
    """First execution-bar index that opens at or after each decision bar closes.

    A decision bar stamped ``T`` spans ``[T, T + width)`` and is only complete at
    ``T + width``; that instant is the earliest honest fill. Returns -1 where no
    execution bar exists (end of series).
    """
    close_ms = decision_ms.astype(np.int64) + int(width_ms)
    index = np.searchsorted(execution_ms.astype(np.int64), close_ms, side="left")
    return np.where(index >= execution_ms.size, -1, index).astype(np.int64)

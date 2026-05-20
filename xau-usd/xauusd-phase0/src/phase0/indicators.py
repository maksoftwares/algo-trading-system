from __future__ import annotations

import numpy as np
import pandas as pd

from phase0.config import ConfigError


def ema(close: pd.Series, period: int) -> pd.Series:
    """Standard EMA with SMA initialization and NaN values before the seed period."""

    _validate_period(period)
    close = pd.Series(close, dtype="float64")
    result = pd.Series(np.nan, index=close.index, dtype="float64")
    if len(close) < period:
        return result

    seed = close.iloc[:period]
    if seed.isna().any():
        return result

    alpha = 2.0 / (period + 1.0)
    result.iloc[period - 1] = seed.mean()
    for position in range(period, len(close)):
        current = close.iloc[position]
        previous_ema = result.iloc[position - 1]
        if np.isnan(current) or np.isnan(previous_ema):
            result.iloc[position] = np.nan
        else:
            result.iloc[position] = alpha * current + (1.0 - alpha) * previous_ema
    return result


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    high = pd.Series(high, dtype="float64")
    low = pd.Series(low, dtype="float64")
    close = pd.Series(close, dtype="float64")
    previous_close = close.shift(1)
    ranges = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder ATR with a simple-average seed over the first period true ranges."""

    _validate_period(period)
    tr = true_range(high, low, close)
    result = pd.Series(np.nan, index=tr.index, dtype="float64")
    if len(tr) < period:
        return result

    seed = tr.iloc[:period]
    if seed.isna().any():
        return result

    result.iloc[period - 1] = seed.mean()
    for position in range(period, len(tr)):
        current_tr = tr.iloc[position]
        previous_atr = result.iloc[position - 1]
        if np.isnan(current_tr) or np.isnan(previous_atr):
            result.iloc[position] = np.nan
        else:
            result.iloc[position] = ((previous_atr * (period - 1)) + current_tr) / period
    return result


def adx_components(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.DataFrame:
    """Wilder ADX component table: DM, smoothed values, DI, DX, and ADX."""

    _validate_period(period)
    high = pd.Series(high, dtype="float64")
    low = pd.Series(low, dtype="float64")
    close = pd.Series(close, dtype="float64")

    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = pd.Series(
        np.where((up_move > down_move) & (up_move > 0), up_move, 0.0),
        index=high.index,
        dtype="float64",
    )
    minus_dm = pd.Series(
        np.where((down_move > up_move) & (down_move > 0), down_move, 0.0),
        index=high.index,
        dtype="float64",
    )
    tr = true_range(high, low, close)
    smoothed_tr = wilder_sum(tr, period)
    smoothed_plus_dm = wilder_sum(plus_dm, period)
    smoothed_minus_dm = wilder_sum(minus_dm, period)

    plus_di = 100.0 * smoothed_plus_dm / smoothed_tr
    minus_di = 100.0 * smoothed_minus_dm / smoothed_tr
    denominator = plus_di + minus_di
    dx = 100.0 * (plus_di - minus_di).abs() / denominator.replace(0.0, np.nan)
    adx_series = _adx_from_dx(dx, period)

    return pd.DataFrame(
        {
            "true_range": tr,
            "plus_dm": plus_dm,
            "minus_dm": minus_dm,
            "smoothed_tr": smoothed_tr,
            "smoothed_plus_dm": smoothed_plus_dm,
            "smoothed_minus_dm": smoothed_minus_dm,
            "plus_di": plus_di,
            "minus_di": minus_di,
            "dx": dx,
            "adx": adx_series,
        },
        index=high.index,
    )


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    return adx_components(high, low, close, period)["adx"]


def slope(series: pd.Series, lookback: int) -> pd.Series:
    _validate_period(lookback)
    values = pd.Series(series, dtype="float64")
    return values - values.shift(lookback)


def wilder_sum(values: pd.Series, period: int) -> pd.Series:
    """Wilder smoothing used for ADX DM/TR sums."""

    _validate_period(period)
    values = pd.Series(values, dtype="float64")
    result = pd.Series(np.nan, index=values.index, dtype="float64")
    if len(values) < period:
        return result

    seed = values.iloc[:period]
    if seed.isna().any():
        return result

    result.iloc[period - 1] = seed.sum()
    for position in range(period, len(values)):
        current = values.iloc[position]
        previous = result.iloc[position - 1]
        if np.isnan(current) or np.isnan(previous):
            result.iloc[position] = np.nan
        else:
            result.iloc[position] = previous - (previous / period) + current
    return result


def _adx_from_dx(dx: pd.Series, period: int) -> pd.Series:
    result = pd.Series(np.nan, index=dx.index, dtype="float64")
    first_position = (period - 1) + (period - 1)
    if len(dx) <= first_position:
        return result

    seed = dx.iloc[period - 1 : first_position + 1]
    if seed.isna().any():
        return result

    result.iloc[first_position] = seed.mean()
    for position in range(first_position + 1, len(dx)):
        current = dx.iloc[position]
        previous = result.iloc[position - 1]
        if np.isnan(current) or np.isnan(previous):
            result.iloc[position] = np.nan
        else:
            result.iloc[position] = ((previous * (period - 1)) + current) / period
    return result


def _validate_period(period: int) -> None:
    if period <= 0:
        raise ConfigError(f"Indicator period must be positive, got {period}.")

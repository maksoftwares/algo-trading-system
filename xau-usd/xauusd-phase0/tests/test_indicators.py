from __future__ import annotations

import math

import pandas as pd
import pytest

from phase0.indicators import adx, adx_components, atr, ema, slope, true_range


def test_ema_uses_sma_seed():
    close = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])

    result = ema(close, period=3)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2] == pytest.approx(2.0)
    assert result.iloc[3] == pytest.approx(3.0)
    assert result.iloc[4] == pytest.approx(4.0)


def test_atr_uses_wilder_smoothing():
    high = pd.Series([10.0, 12.0, 13.0, 15.0])
    low = pd.Series([9.0, 10.0, 11.0, 12.0])
    close = pd.Series([9.5, 11.0, 12.0, 14.0])

    tr = true_range(high, low, close)
    result = atr(high, low, close, period=3)

    assert tr.tolist() == pytest.approx([1.0, 2.5, 2.0, 3.0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2] == pytest.approx((1.0 + 2.5 + 2.0) / 3.0)
    assert result.iloc[3] == pytest.approx((((1.0 + 2.5 + 2.0) / 3.0) * 2.0 + 3.0) / 3.0)


def test_adx_components_on_monotonic_trend():
    close = pd.Series([float(i) for i in range(1, 41)])
    high = close + 0.5
    low = close - 0.5

    components = adx_components(high, low, close, period=14)
    result = adx(high, low, close, period=14)

    assert set(
        [
            "true_range",
            "plus_dm",
            "minus_dm",
            "smoothed_tr",
            "smoothed_plus_dm",
            "smoothed_minus_dm",
            "plus_di",
            "minus_di",
            "dx",
            "adx",
        ]
    ).issubset(components.columns)
    assert components["plus_di"].iloc[20] > components["minus_di"].iloc[20]
    assert result.iloc[26] == pytest.approx(100.0)


def test_slope_is_difference_from_lookback():
    values = pd.Series([10.0, 11.0, 14.0, 13.0])

    result = slope(values, lookback=2)

    assert math.isnan(result.iloc[0])
    assert math.isnan(result.iloc[1])
    assert result.iloc[2] == pytest.approx(4.0)
    assert result.iloc[3] == pytest.approx(2.0)

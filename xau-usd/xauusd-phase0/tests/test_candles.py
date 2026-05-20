from __future__ import annotations

import pandas as pd
import pytest

from phase0.candles import (
    bearish_engulfing,
    bearish_pin_bar,
    bullish_engulfing,
    bullish_pin_bar,
    candle_components,
)


def test_candle_components():
    candles = pd.DataFrame(
        [
            {"open": 10.0, "high": 10.5, "low": 9.0, "close": 10.0},
            {"open": 10.0, "high": 11.0, "low": 9.5, "close": 10.8},
        ]
    )

    components = candle_components(candles, point_size=0.01)

    assert components.loc[0, "body"] == 0
    assert components.loc[0, "body_for_ratio"] == 0.01
    assert bool(components.loc[0, "doji"]) is True
    assert components.loc[1, "upper_wick"] == pytest.approx(0.2)
    assert bool(components.loc[1, "bullish"]) is True


def test_engulfing_patterns():
    candles = pd.DataFrame(
        [
            {"open": 10.0, "high": 10.2, "low": 8.8, "close": 9.0},
            {"open": 8.9, "high": 10.4, "low": 8.7, "close": 10.3},
            {"open": 10.0, "high": 10.7, "low": 9.4, "close": 10.2},
            {"open": 10.4, "high": 10.6, "low": 8.8, "close": 9.2},
        ]
    )

    assert bool(bullish_engulfing(candles).iloc[1]) is True
    assert bool(bearish_engulfing(candles).iloc[3]) is True


def test_pin_bars():
    candles = pd.DataFrame(
        [
            {"open": 10.0, "high": 10.15, "low": 9.5, "close": 10.1},
            {"open": 10.0, "high": 10.6, "low": 9.95, "close": 9.9},
        ]
    )

    assert bool(bullish_pin_bar(candles, point_size=0.01).iloc[0]) is True
    assert bool(bearish_pin_bar(candles, point_size=0.01).iloc[1]) is True

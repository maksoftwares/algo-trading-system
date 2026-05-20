from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.breakout_retest import BreakoutRetestStrategy
from phase0.strategies.range_mr import RangeMeanReversionStrategy
from phase0.strategies.trend_pullback import TrendPullbackStrategy


def test_trend_pullback_generates_long_signal_and_plan():
    strategy = TrendPullbackStrategy()
    context = _trend_context()

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert len(signals) == 1
    assert signals[0].direction == "LONG"
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_breakout_retest_generates_long_stop_plan():
    strategy = BreakoutRetestStrategy()
    context = _breakout_context()

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[0], context)

    assert len(signals) == 1
    assert signals[0].direction == "LONG"
    assert signals[0].metadata["level_kind"] == "previous_daily_high"
    assert plan.entry_type == "STOP"
    assert plan.entry_price == pytest.approx(100.41)
    assert plan.stop_loss == pytest.approx(99.93)
    assert plan.take_profit > plan.entry_price


def test_range_mr_generates_long_limit_plan():
    strategy = RangeMeanReversionStrategy()
    context = _range_context()

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[0], context)

    assert len(signals) == 1
    assert signals[0].direction == "LONG"
    assert plan.entry_type == "LIMIT"
    assert plan.entry_price == pytest.approx(100.0)
    assert plan.stop_loss == pytest.approx(99.4)
    assert plan.take_profit == pytest.approx(110.0)
    assert plan.risk_reward > 1.0


def test_strategies_ignore_when_open_position_exists():
    strategy = TrendPullbackStrategy()
    context = _trend_context()
    context["open_position_exists"] = True

    assert strategy.generate_signals(context) == []


def _trend_context() -> dict:
    m5_times = pd.date_range("2016-01-04T10:00:00Z", periods=10, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "open": [100.0] * 9 + [100.0],
            "high": [100.2] * 9 + [100.3],
            "low": [99.8] * 9 + [99.4],
            "close": [100.0] * 9 + [100.2],
            "bullish_engulfing": [False] * 10,
            "bearish_engulfing": [False] * 10,
            "bullish_pin_bar": [False] * 9 + [True],
            "bearish_pin_bar": [False] * 10,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-04T10:45:00Z"],
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.2],
            "ema21": [100.0],
            "atr14": [2.0],
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-04T10:00:00Z"],
            "open": [100.0],
            "high": [102.0],
            "low": [98.0],
            "close": [101.0],
            "ema50": [110.0],
            "ema200": [100.0],
            "ema50_slope20": [1.0],
            "atr14": [2.0],
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _breakout_context() -> dict:
    times = pd.date_range("2016-01-05T10:00:00Z", periods=24, freq="5min")
    open_values = [99.5] * 24
    high_values = [99.8] * 24
    low_values = [99.2] * 24
    close_values = [99.6] * 24

    open_values[18] = 100.0
    high_values[18] = 100.8
    low_values[18] = 99.8
    close_values[18] = 100.4

    open_values[19] = 100.8
    high_values[19] = 100.9
    low_values[19] = 100.7
    close_values[19] = 100.8

    open_values[20] = 100.2
    high_values[20] = 100.4
    low_values[20] = 100.03
    close_values[20] = 100.1

    open_values[21] = 100.1
    high_values[21] = 100.5
    low_values[21] = 100.0
    close_values[21] = 100.3

    open_values[22] = 99.6
    high_values[22] = 99.8
    low_values[22] = 99.1
    close_values[22] = 99.5

    m5 = pd.DataFrame(
        {
            "timestamp_utc": times,
            "open": open_values,
            "high": high_values,
            "low": low_values,
            "close": close_values,
            "atr14": [1.0] * 24,
            "previous_daily_high": [100.0] * 24,
            "previous_daily_low": [90.0] * 24,
            "previous_weekly_high": [pd.NA] * 24,
            "previous_weekly_low": [pd.NA] * 24,
            "latest_swing_high": [pd.NA] * 24,
            "latest_swing_high_time_utc": [pd.NaT] * 24,
            "latest_swing_low": [pd.NA] * 24,
            "latest_swing_low_time_utc": [pd.NaT] * 24,
        }
    )
    return {"M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


def _range_context() -> dict:
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2016-01-04T00:00:00Z", periods=30, freq="1h"),
            "open": [105.0] * 30,
            "high": [106.0] * 30,
            "low": [104.0] * 30,
            "close": [105.0] * 30,
            "adx14": [10.0] * 30,
        }
    )
    m15_times = pd.date_range("2016-01-04T00:00:00Z", periods=50, freq="15min")
    highs = [106.0] * 50
    lows = [104.0] * 50
    for index in (0, 10, 20):
        highs[index] = 110.0
    for index in (5, 15, 25):
        lows[index] = 100.0
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [105.0] * 50,
            "high": highs,
            "low": lows,
            "close": [105.0] * 50,
            "atr14": [2.0] * 50,
        }
    )
    m5 = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-05T05:00:00Z"],
            "open": [100.2],
            "high": [100.4],
            "low": [100.1],
            "close": [100.3],
            "bullish_pin_bar": [True],
            "bearish_pin_bar": [False],
        }
    )
    return {"H1": h1, "M15": m15, "M5": m5, "symbol": "XAUUSD", "point_size": 0.01}

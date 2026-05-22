from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.ny_london_overlap_compression_break_v0 import (
    NyLondonOverlapCompressionBreakV0Strategy,
)


def test_ny_london_overlap_compression_break_v0_generates_long_market_plan():
    strategy = NyLondonOverlapCompressionBreakV0Strategy()
    context = _overlap_context("LONG")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["session_window_utc"] == "13:00-16:00"
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_ny_london_overlap_compression_break_v0_generates_short_market_plan():
    strategy = NyLondonOverlapCompressionBreakV0Strategy()
    context = _overlap_context("SHORT")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "SHORT"
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_ny_london_overlap_compression_break_v0_ignores_outside_overlap():
    strategy = NyLondonOverlapCompressionBreakV0Strategy()
    context = _overlap_context("LONG")
    context["M5"]["bar_start_utc"] = context["M5"]["bar_start_utc"] - pd.Timedelta(hours=5)
    context["M5"]["timestamp_utc"] = context["M5"]["timestamp_utc"] - pd.Timedelta(hours=5)

    assert strategy.generate_signals(context) == []


def _overlap_context(direction: str) -> dict:
    m15_times = pd.date_range("2024-10-01T00:15:00Z", periods=180, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 180,
            "high": [102.0] * 130 + [100.12] * 50,
            "low": [98.0] * 130 + [99.88] * 50,
            "close": [100.0] * 180,
        }
    )

    m5_times = pd.date_range("2024-10-01T00:05:00Z", periods=500, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 500,
            "high": [100.10] * 500,
            "low": [99.90] * 500,
            "close": [100.0] * 500,
            "atr14": [1.0] * 448 + [0.35] * 52,
            "mid_open": [100.0] * 500,
            "mid_close": [100.0] * 500,
            "bid_open": [99.9] * 500,
            "ask_open": [100.1] * 500,
            "bid_close": [99.9] * 500,
            "ask_close": [100.1] * 500,
        }
    )
    if direction == "LONG":
        m5.loc[450, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.58, 99.96, 100.50, 0.35]
    else:
        m5.loc[450, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.04, 99.42, 99.50, 0.35]
    m5.loc[450, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        m5.loc[450, "open"],
        m5.loc[450, "close"],
        m5.loc[450, "open"] - 0.1,
        m5.loc[450, "open"] + 0.1,
        m5.loc[450, "close"] - 0.1,
        m5.loc[450, "close"] + 0.1,
    ]

    if direction == "LONG":
        h1_close = 101.0
        h1_ema = 100.0
        h1_slope = 0.1
    else:
        h1_close = 99.0
        h1_ema = 100.0
        h1_slope = -0.1
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T00:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [102.0] * 60,
            "low": [98.0] * 60,
            "close": [h1_close] * 60,
            "ema50": [h1_ema] * 60,
            "ema50_slope12": [h1_slope] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}

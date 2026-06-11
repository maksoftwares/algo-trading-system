from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.w1_d1_momentum_m5_continuation_experimental import (
    W1D1MomentumM5ContinuationExperimentalStrategy,
)


def test_w1_d1_momentum_m5_continuation_generates_long_market_plan():
    strategy = W1D1MomentumM5ContinuationExperimentalStrategy()
    context = _context_with_bull_bias()
    m5 = context["M5"].copy()
    _set_long_trigger(m5, 90)
    context["M5"] = m5

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[0], context)

    assert signals
    assert signals[0].direction == "LONG"
    assert signals[0].metadata["bias_reason"] == "bull"
    assert signals[0].metadata["trigger_type"] == "pullback"
    assert signals[0].metadata["m5_body_fraction"] >= 0.35
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_w1_d1_momentum_m5_continuation_ignores_without_w1_d1_bias():
    strategy = W1D1MomentumM5ContinuationExperimentalStrategy()
    context = _context_with_bull_bias()
    d1 = context["D1"].copy()
    d1["close"] = 100.0
    d1["open"] = 100.0
    d1["high"] = 101.0
    d1["low"] = 99.0
    context["D1"] = d1
    m5 = context["M5"].copy()
    _set_long_trigger(m5, 90)
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_w1_d1_momentum_m5_continuation_generates_impulse_signal():
    strategy = W1D1MomentumM5ContinuationExperimentalStrategy()
    strategy.enable_impulse_trigger = True
    context = _context_with_bull_bias()
    m5 = context["M5"].copy()
    _set_long_impulse_trigger(m5, 90)
    context["M5"] = m5

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[0].direction == "LONG"
    assert signals[0].metadata["trigger_type"] == "impulse"


def test_w1_d1_momentum_m5_continuation_respects_daily_signal_cap():
    strategy = W1D1MomentumM5ContinuationExperimentalStrategy()
    context = _context_with_bull_bias()
    m5 = context["M5"].copy()
    for position in range(90, 180, 3):
        _set_long_trigger(m5, position)
    context["M5"] = m5

    signals = strategy.generate_signals(context)

    assert len(signals) == strategy.max_signals_per_day
    assert {pd.Timestamp(signal.timestamp_utc).strftime("%Y-%m-%d") for signal in signals} == {
        "2024-03-20"
    }


def _context_with_bull_bias() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=100, freq="1D")
    d1_closes = [100.0 + 0.55 * index for index in range(len(d1_times))]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.25 for close in d1_closes],
            "high": [close + 1.0 for close in d1_closes],
            "low": [close - 1.0 for close in d1_closes],
            "close": d1_closes,
        }
    )

    m5_times = pd.date_range("2024-03-20T00:05:00Z", periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [150.0] * len(m5_times),
            "high": [150.3] * len(m5_times),
            "low": [149.7] * len(m5_times),
            "close": [150.0] * len(m5_times),
            "mid_open": [150.0] * len(m5_times),
            "mid_close": [150.0] * len(m5_times),
            "bid_open": [149.9] * len(m5_times),
            "ask_open": [150.1] * len(m5_times),
            "bid_close": [149.9] * len(m5_times),
            "ask_close": [150.1] * len(m5_times),
        }
    )
    return {"M5": m5, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _set_long_trigger(m5: pd.DataFrame, position: int) -> None:
    m5.loc[position, ["open", "high", "low", "close"]] = [149.8, 151.0, 149.5, 150.8]
    m5.loc[position, ["mid_open", "mid_close"]] = [149.8, 150.8]
    m5.loc[position, ["bid_open", "bid_close"]] = [149.7, 150.7]
    m5.loc[position, ["ask_open", "ask_close"]] = [149.9, 150.9]


def _set_long_impulse_trigger(m5: pd.DataFrame, position: int) -> None:
    m5.loc[position - 1, ["open", "high", "low", "close"]] = [150.0, 150.2, 149.8, 150.0]
    m5.loc[position, ["open", "high", "low", "close"]] = [150.4, 151.6, 150.3, 151.4]
    m5.loc[position, ["mid_open", "mid_close"]] = [150.4, 151.4]
    m5.loc[position, ["bid_open", "bid_close"]] = [150.3, 151.3]
    m5.loc[position, ["ask_open", "ask_close"]] = [150.5, 151.5]

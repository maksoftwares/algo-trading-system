from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.w1_d1_momentum_continuation_v0 import W1D1MomentumContinuationV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_w1_d1_momentum_continuation_v0_generates_long_market_plan():
    strategy = W1D1MomentumContinuationV0Strategy()
    context = synthetic_context_for_expert("w1_d1_momentum_continuation_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["d1_momentum20"] > 0
    assert signals[-1].metadata["signal_body_ratio"] > 0.35
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_w1_d1_momentum_continuation_v0_ignores_without_long_momentum():
    strategy = W1D1MomentumContinuationV0Strategy()
    context = synthetic_context_for_expert("w1_d1_momentum_continuation_v0")
    d1 = context["D1"].copy()
    d1["close"] = [100.0] * len(d1)
    d1["open"] = [100.0] * len(d1)
    d1["high"] = [101.0] * len(d1)
    d1["low"] = [99.0] * len(d1)
    context["D1"] = d1

    assert strategy.generate_signals(context) == []


def test_w1_d1_momentum_continuation_v0_ignores_without_signal_candle():
    strategy = W1D1MomentumContinuationV0Strategy()
    context = synthetic_context_for_expert("w1_d1_momentum_continuation_v0")
    d1 = context["D1"].copy()
    d1.loc[70, ["open", "high", "low", "close"]] = [125.0, 125.2, 124.8, 125.0]
    context["D1"] = d1

    assert strategy.generate_signals(context) == []


def test_w1_d1_momentum_continuation_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("w1_d1_momentum_continuation_v0")

    assert pd.to_datetime(context["D1"]["timestamp_utc"], utc=True).is_monotonic_increasing
    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

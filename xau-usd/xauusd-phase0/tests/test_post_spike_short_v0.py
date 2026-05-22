from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.post_spike_short_v0 import PostSpikeShortV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_post_spike_short_v0_generates_short_market_plan():
    strategy = PostSpikeShortV0Strategy()
    context = synthetic_context_for_expert("post_spike_short_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "SHORT"
    assert signals[-1].metadata["spike_high"] == pytest.approx(101.55)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_post_spike_short_v0_ignores_when_h1_context_fails():
    strategy = PostSpikeShortV0Strategy()
    context = synthetic_context_for_expert("post_spike_short_v0")
    h1 = context["H1"].copy()
    h1["ema50_slope12"] = 0.2
    context["H1"] = h1

    assert strategy.generate_signals(context) == []


def test_post_spike_short_v0_ignores_without_fresh_high():
    strategy = PostSpikeShortV0Strategy()
    context = synthetic_context_for_expert("post_spike_short_v0")
    m5 = context["M5"].copy()
    m5.loc[50, "high"] = 102.0
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_post_spike_short_v0_ignores_bullish_rejection_candle():
    strategy = PostSpikeShortV0Strategy()
    context = synthetic_context_for_expert("post_spike_short_v0")
    m5 = context["M5"].copy()
    m5.loc[123, ["open", "close"]] = [100.8, 101.2]
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_post_spike_short_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("post_spike_short_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

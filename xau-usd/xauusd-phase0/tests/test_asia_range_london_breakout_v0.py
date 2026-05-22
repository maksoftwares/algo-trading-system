from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.asia_range_london_breakout_v0 import AsiaRangeLondonBreakoutV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_asia_range_london_breakout_v0_generates_long_market_plan():
    strategy = AsiaRangeLondonBreakoutV0Strategy()
    context = synthetic_context_for_expert("asia_range_london_breakout_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["asia_high"] == pytest.approx(101.0)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_asia_range_london_breakout_v0_ignores_when_not_london_window():
    strategy = AsiaRangeLondonBreakoutV0Strategy()
    context = synthetic_context_for_expert("asia_range_london_breakout_v0")
    m5 = context["M5"].copy()
    m5.loc[90, "bar_start_utc"] = pd.Timestamp("2024-08-01T06:30:00Z")
    m5.loc[90, "timestamp_utc"] = pd.Timestamp("2024-08-01T06:35:00Z")
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_asia_range_london_breakout_v0_ignores_without_breakout_close():
    strategy = AsiaRangeLondonBreakoutV0Strategy()
    context = synthetic_context_for_expert("asia_range_london_breakout_v0")
    m5 = context["M5"].copy()
    m5.loc[90, "close"] = 101.05
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_asia_range_london_breakout_v0_supports_short_breakdown_plan():
    strategy = AsiaRangeLondonBreakoutV0Strategy()
    context = synthetic_context_for_expert("asia_range_london_breakout_v0")
    m5 = context["M5"].copy()
    m5.loc[90, ["open", "high", "low", "close"]] = [99.20, 99.40, 98.30, 98.50]
    context["M5"] = m5

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals[-1].direction == "SHORT"
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]


def test_asia_range_london_breakout_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("asia_range_london_breakout_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.london_fix_continuation_v0 import LondonFixContinuationV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_london_fix_continuation_v0_generates_long_market_plan():
    strategy = LondonFixContinuationV0Strategy()
    context = synthetic_context_for_expert("london_fix_continuation_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["pre_fix_high"] == pytest.approx(101.0)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_london_fix_continuation_v0_ignores_when_not_post_fix_window():
    strategy = LondonFixContinuationV0Strategy()
    context = synthetic_context_for_expert("london_fix_continuation_v0")
    m5 = context["M5"].copy()
    m5.loc[36, "bar_start_utc"] = pd.Timestamp("2024-06-03T13:00:00Z")
    m5.loc[36, "timestamp_utc"] = pd.Timestamp("2024-06-03T13:05:00Z")
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_london_fix_continuation_v0_ignores_without_breakout_close():
    strategy = LondonFixContinuationV0Strategy()
    context = synthetic_context_for_expert("london_fix_continuation_v0")
    m5 = context["M5"].copy()
    m5.loc[36, "close"] = 101.05
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_london_fix_continuation_v0_supports_short_breakdown_plan():
    strategy = LondonFixContinuationV0Strategy()
    context = synthetic_context_for_expert("london_fix_continuation_v0")
    m5 = context["M5"].copy()
    m5.loc[36, ["open", "high", "low", "close"]] = [99.20, 99.30, 98.40, 98.60]
    context["M5"] = m5

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals[-1].direction == "SHORT"
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]


def test_london_fix_continuation_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("london_fix_continuation_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

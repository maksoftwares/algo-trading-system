from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_daily_range_extension_reversal_v0_generates_short_market_plan():
    strategy = get_strategy("h4_daily_range_extension_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_daily_range_extension_reversal_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].expert == "h4_daily_range_extension_reversal_v0"
    assert signals[-1].direction == "SHORT"
    assert signals[-1].reason_code == "H4_DAILY_RANGE_EXTENSION_REVERSAL_V0_SHORT"
    assert signals[-1].metadata["extension_direction"] == "UP"
    assert signals[-1].metadata["day_extension_prior_range"] >= strategy.min_day_extension_prior_range
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.25)
    assert plan.metadata["planned_time_stop_h4_bars"] == 6
    assert plan.metadata["max_holding_bars"] == 288


def test_h4_daily_range_extension_reversal_v0_ignores_non_decision_hour():
    strategy = get_strategy("h4_daily_range_extension_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_daily_range_extension_reversal_v0")
    h4 = context["H4"].copy()
    h4.loc[40, "timestamp_utc"] = pd.Timestamp("2024-05-07T18:00:00Z")
    context["H4"] = h4

    assert strategy.generate_signals(context) == []


def test_h4_daily_range_extension_reversal_v0_ignores_without_close_back():
    strategy = get_strategy("h4_daily_range_extension_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_daily_range_extension_reversal_v0")
    h4 = context["H4"].copy()
    h4.loc[40, ["open", "high", "low", "close"]] = [101.80, 102.20, 100.80, 101.90]
    context["H4"] = h4

    assert strategy.generate_signals(context) == []

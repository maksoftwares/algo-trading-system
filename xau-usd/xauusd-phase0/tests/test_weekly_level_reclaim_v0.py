from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.weekly_level_reclaim_v0 import WeeklyLevelReclaimV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_weekly_level_reclaim_v0_generates_long_market_plan():
    strategy = WeeklyLevelReclaimV0Strategy()
    context = synthetic_context_for_expert("weekly_level_reclaim_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["level"] == pytest.approx(99.0)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_weekly_level_reclaim_v0_ignores_without_reclaim_close():
    strategy = WeeklyLevelReclaimV0Strategy()
    context = synthetic_context_for_expert("weekly_level_reclaim_v0")
    m5 = context["M5"].copy()
    m5.loc[2100, "close"] = 98.95
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_weekly_level_reclaim_v0_ignores_without_sweep():
    strategy = WeeklyLevelReclaimV0Strategy()
    context = synthetic_context_for_expert("weekly_level_reclaim_v0")
    m5 = context["M5"].copy()
    m5.loc[2100, "low"] = 98.90
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_weekly_level_reclaim_v0_ignores_first_week_without_previous_levels():
    strategy = WeeklyLevelReclaimV0Strategy()
    context = synthetic_context_for_expert("weekly_level_reclaim_v0")
    m5 = context["M5"].copy().iloc[:2016].reset_index(drop=True)
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_weekly_level_reclaim_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("weekly_level_reclaim_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

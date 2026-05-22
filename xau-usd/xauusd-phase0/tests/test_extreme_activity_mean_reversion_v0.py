from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.extreme_activity_mean_reversion_v0 import ExtremeActivityMeanReversionV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_extreme_activity_mean_reversion_v0_generates_short_market_plan():
    strategy = ExtremeActivityMeanReversionV0Strategy()
    context = synthetic_context_for_expert("extreme_activity_mean_reversion_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "SHORT"
    assert signals[-1].metadata["spike_high"] == pytest.approx(103.0)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_extreme_activity_mean_reversion_v0_ignores_without_extreme_range():
    strategy = ExtremeActivityMeanReversionV0Strategy()
    context = synthetic_context_for_expert("extreme_activity_mean_reversion_v0")
    m5 = context["M5"].copy()
    m5.loc[320, ["high", "low"]] = [100.4, 99.8]
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_extreme_activity_mean_reversion_v0_ignores_without_reclaim_inside_prior_high():
    strategy = ExtremeActivityMeanReversionV0Strategy()
    context = synthetic_context_for_expert("extreme_activity_mean_reversion_v0")
    m5 = context["M5"].copy()
    m5.loc[320, "close"] = 100.25
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_extreme_activity_mean_reversion_v0_supports_long_spike_plan():
    strategy = ExtremeActivityMeanReversionV0Strategy()
    context = synthetic_context_for_expert("extreme_activity_mean_reversion_v0")
    m5 = context["M5"].copy()
    m5.loc[320, ["open", "high", "low", "close"]] = [97.50, 100.20, 97.00, 99.95]
    context["M5"] = m5

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals[-1].direction == "LONG"
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]


def test_extreme_activity_mean_reversion_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("extreme_activity_mean_reversion_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

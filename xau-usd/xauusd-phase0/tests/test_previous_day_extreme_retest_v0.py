from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.previous_day_extreme_retest_v0 import PreviousDayExtremeRetestV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_previous_day_extreme_retest_v0_generates_long_market_plan():
    strategy = PreviousDayExtremeRetestV0Strategy()
    context = synthetic_context_for_expert("previous_day_extreme_retest_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["level"] == pytest.approx(101.0)
    assert signals[-1].metadata["breakout_index"] == 400
    assert signals[-1].metadata["retest_index"] == 403
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_previous_day_extreme_retest_v0_ignores_without_retest():
    strategy = PreviousDayExtremeRetestV0Strategy()
    context = synthetic_context_for_expert("previous_day_extreme_retest_v0")
    m5 = context["M5"].copy()
    m5.loc[403, "low"] = 101.40
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_previous_day_extreme_retest_v0_ignores_without_confirmation():
    strategy = PreviousDayExtremeRetestV0Strategy()
    context = synthetic_context_for_expert("previous_day_extreme_retest_v0")
    m5 = context["M5"].copy()
    m5.loc[405, ["open", "close"]] = [101.60, 101.05]
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_previous_day_extreme_retest_v0_ignores_first_day_without_previous_levels():
    strategy = PreviousDayExtremeRetestV0Strategy()
    context = synthetic_context_for_expert("previous_day_extreme_retest_v0")
    m5 = context["M5"].copy().iloc[:288].reset_index(drop=True)
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_previous_day_extreme_retest_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("previous_day_extreme_retest_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

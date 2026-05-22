from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.emr_inactivity_long_v0 import EmrInactivityLongV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_emr_inactivity_long_v0_generates_long_market_plan():
    strategy = EmrInactivityLongV0Strategy()
    context = synthetic_context_for_expert("emr_inactivity_long_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["sweep_low"] == pytest.approx(98.75)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_emr_inactivity_long_v0_ignores_when_h1_context_fails():
    strategy = EmrInactivityLongV0Strategy()
    context = synthetic_context_for_expert("emr_inactivity_long_v0")
    h1 = context["H1"].copy()
    h1["ema50_slope12"] = -2.0
    context["H1"] = h1

    assert strategy.generate_signals(context) == []


def test_emr_inactivity_long_v0_ignores_without_m5_inactivity():
    strategy = EmrInactivityLongV0Strategy()
    context = synthetic_context_for_expert("emr_inactivity_long_v0")
    m5 = context["M5"].copy()
    m5["atr14"] = 1.0
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_emr_inactivity_long_v0_ignores_without_bullish_reclaim():
    strategy = EmrInactivityLongV0Strategy()
    context = synthetic_context_for_expert("emr_inactivity_long_v0")
    m5 = context["M5"].copy()
    m5.loc[413, ["open", "close"]] = [99.30, 98.95]
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_emr_inactivity_long_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("emr_inactivity_long_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

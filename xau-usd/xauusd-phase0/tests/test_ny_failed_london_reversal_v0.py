from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.ny_failed_london_reversal_v0 import NyFailedLondonReversalV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_ny_failed_london_reversal_v0_generates_short_market_plan():
    strategy = NyFailedLondonReversalV0Strategy()
    context = synthetic_context_for_expert("ny_failed_london_reversal_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "SHORT"
    assert signals[-1].metadata["london_high"] == pytest.approx(101.0)
    assert signals[-1].metadata["sweep_high"] == pytest.approx(101.6)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_ny_failed_london_reversal_v0_ignores_when_not_ny_window():
    strategy = NyFailedLondonReversalV0Strategy()
    context = synthetic_context_for_expert("ny_failed_london_reversal_v0")
    m5 = context["M5"].copy()
    m5.loc[90, "bar_start_utc"] = pd.Timestamp("2024-04-01T12:00:00Z")
    m5.loc[90, "timestamp_utc"] = pd.Timestamp("2024-04-01T12:05:00Z")
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_ny_failed_london_reversal_v0_ignores_without_failed_high_close_back_inside():
    strategy = NyFailedLondonReversalV0Strategy()
    context = synthetic_context_for_expert("ny_failed_london_reversal_v0")
    m5 = context["M5"].copy()
    m5.loc[90, "close"] = 101.15
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_ny_failed_london_reversal_v0_supports_failed_low_long_plan():
    strategy = NyFailedLondonReversalV0Strategy()
    context = synthetic_context_for_expert("ny_failed_london_reversal_v0")
    m5 = context["M5"].copy()
    m5.loc[90, ["open", "high", "low", "close"]] = [98.50, 99.60, 98.40, 99.40]
    context["M5"] = m5

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals[-1].direction == "LONG"
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]


def test_ny_failed_london_reversal_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("ny_failed_london_reversal_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

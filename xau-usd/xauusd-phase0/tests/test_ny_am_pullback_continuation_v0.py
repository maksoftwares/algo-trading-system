from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.ny_am_pullback_continuation_v0 import NyAmPullbackContinuationV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_ny_am_pullback_continuation_v0_generates_long_market_plan():
    strategy = NyAmPullbackContinuationV0Strategy()
    context = synthetic_context_for_expert("ny_am_pullback_continuation_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["opening_drive_close"] == pytest.approx(101.30)
    assert signals[-1].metadata["pullback_index"] == 24
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_ny_am_pullback_continuation_v0_ignores_without_opening_drive():
    strategy = NyAmPullbackContinuationV0Strategy()
    context = synthetic_context_for_expert("ny_am_pullback_continuation_v0")
    m5 = context["M5"].copy()
    m5.loc[6:11, "close"] = 100.0
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_ny_am_pullback_continuation_v0_ignores_without_pullback():
    strategy = NyAmPullbackContinuationV0Strategy()
    context = synthetic_context_for_expert("ny_am_pullback_continuation_v0")
    m5 = context["M5"].copy()
    m5.loc[24, "low"] = 101.20
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_ny_am_pullback_continuation_v0_ignores_without_confirmation():
    strategy = NyAmPullbackContinuationV0Strategy()
    context = synthetic_context_for_expert("ny_am_pullback_continuation_v0")
    m5 = context["M5"].copy()
    m5.loc[26, ["open", "close"]] = [101.20, 100.85]
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_ny_am_pullback_continuation_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("ny_am_pullback_continuation_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

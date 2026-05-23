from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.h4_inside_bar_d1_momentum_breakout_v0 import (
    H4InsideBarD1MomentumBreakoutV0Strategy,
)
from phase0.synthetic import synthetic_context_for_expert


def test_h4_inside_bar_d1_momentum_breakout_v0_generates_long_market_plan():
    strategy = H4InsideBarD1MomentumBreakoutV0Strategy()
    context = synthetic_context_for_expert("h4_inside_bar_d1_momentum_breakout_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["d1_momentum5"] > 0
    assert signals[-1].metadata["mother_high"] == pytest.approx(131.2)
    assert signals[-1].metadata["inside_high"] == pytest.approx(130.8)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_h4_inside_bar_d1_momentum_breakout_v0_ignores_without_inside_bar():
    strategy = H4InsideBarD1MomentumBreakoutV0Strategy()
    context = synthetic_context_for_expert("h4_inside_bar_d1_momentum_breakout_v0")
    h4 = context["H4"].copy()
    h4.loc[119, ["open", "high", "low", "close"]] = [130.3, 131.4, 128.6, 130.2]
    context["H4"] = h4

    assert strategy.generate_signals(context) == []


def test_h4_inside_bar_d1_momentum_breakout_v0_ignores_without_d1_momentum():
    strategy = H4InsideBarD1MomentumBreakoutV0Strategy()
    context = synthetic_context_for_expert("h4_inside_bar_d1_momentum_breakout_v0")
    d1 = context["D1"].copy()
    d1["close"] = [100.0] * len(d1)
    d1["open"] = [100.0] * len(d1)
    d1["high"] = [101.0] * len(d1)
    d1["low"] = [99.0] * len(d1)
    context["D1"] = d1

    assert strategy.generate_signals(context) == []


def test_h4_inside_bar_d1_momentum_breakout_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("h4_inside_bar_d1_momentum_breakout_v0")

    assert pd.to_datetime(context["D1"]["timestamp_utc"], utc=True).is_monotonic_increasing
    assert pd.to_datetime(context["H4"]["timestamp_utc"], utc=True).is_monotonic_increasing

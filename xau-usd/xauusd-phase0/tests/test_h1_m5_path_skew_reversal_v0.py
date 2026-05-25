from __future__ import annotations

import pytest

from phase0.strategies.h1_m5_path_skew_reversal_v0 import H1M5PathSkewReversalV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h1_m5_path_skew_reversal_v0_generates_long_market_plan():
    strategy = H1M5PathSkewReversalV0Strategy()
    context = synthetic_context_for_expert("h1_m5_path_skew_reversal_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["m5_count"] >= 10
    assert signals[-1].metadata["m5_first_third_return_atr"] <= -0.20
    assert signals[-1].metadata["m5_last_third_return_atr"] >= 0.16
    assert signals[-1].metadata["h1_close_position"] >= 0.28
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.45)
    assert plan.metadata["max_holding_bars"] == 288


def test_h1_m5_path_skew_reversal_v0_requires_m5_path():
    strategy = H1M5PathSkewReversalV0Strategy()
    context = synthetic_context_for_expert("h1_m5_path_skew_reversal_v0")
    context["M5"] = context["M5"].iloc[0:0].copy()

    assert strategy.generate_signals(context) == []

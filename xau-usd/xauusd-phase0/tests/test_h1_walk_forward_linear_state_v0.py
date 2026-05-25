from __future__ import annotations

import pytest

from phase0.strategies.h1_walk_forward_linear_state_v0 import (
    H1WalkForwardLinearStateV0Strategy,
)
from phase0.synthetic import synthetic_context_for_expert


def test_h1_walk_forward_linear_state_v0_generates_long_market_plan():
    strategy = H1WalkForwardLinearStateV0Strategy()
    context = synthetic_context_for_expert("h1_walk_forward_linear_state_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["model_score"] >= strategy.score_threshold
    assert signals[-1].metadata["realized_vol_ratio"] >= 0.35
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.55)
    assert plan.metadata["max_holding_bars"] == 288


def test_h1_walk_forward_linear_state_v0_requires_training_history():
    strategy = H1WalkForwardLinearStateV0Strategy()
    context = synthetic_context_for_expert("h1_walk_forward_linear_state_v0")
    context["H1"] = context["H1"].iloc[: strategy.min_training_rows].copy()

    assert strategy.generate_signals(context) == []

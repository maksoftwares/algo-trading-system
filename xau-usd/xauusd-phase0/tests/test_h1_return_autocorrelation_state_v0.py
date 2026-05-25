from __future__ import annotations

import pytest

from phase0.strategies.h1_return_autocorrelation_state_v0 import (
    H1ReturnAutocorrelationStateV0Strategy,
)
from phase0.synthetic import synthetic_context_for_expert


def test_h1_return_autocorrelation_state_v0_generates_long_market_plan():
    strategy = H1ReturnAutocorrelationStateV0Strategy()
    context = synthetic_context_for_expert("h1_return_autocorrelation_state_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["return_autocorr_72h"] >= 0.02
    assert signals[-1].metadata["momentum_6h_atr"] >= 0.45
    assert signals[-1].metadata["momentum_24h_atr"] >= 0.80
    assert signals[-1].metadata["model_state_score"] >= 0.75
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.70)
    assert plan.metadata["max_holding_bars"] == 432


def test_h1_return_autocorrelation_state_v0_ignores_without_state_score():
    strategy = H1ReturnAutocorrelationStateV0Strategy()
    context = synthetic_context_for_expert("h1_return_autocorrelation_state_v0")
    h1 = context["H1"].copy()
    h1["close"] = 2000.0
    context["H1"] = h1

    assert strategy.generate_signals(context) == []

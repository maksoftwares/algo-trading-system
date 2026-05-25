from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_d1_w1_momentum_h4_pullback_synthetic_smoke():
    strategy = get_strategy("d1_w1_momentum_h4_pullback_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("d1_w1_momentum_h4_pullback_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].reason_code == "D1_W1_MOMENTUM_H4_PULLBACK_V0_LONG"
    assert signals[-1].metadata["d1_momentum20"] > signals[-1].metadata["d1_atr14"]

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.expert == "d1_w1_momentum_h4_pullback_v0"
    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.75

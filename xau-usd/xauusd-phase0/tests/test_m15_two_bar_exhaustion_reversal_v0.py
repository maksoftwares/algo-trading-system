from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_m15_two_bar_exhaustion_reversal_synthetic_smoke():
    strategy = get_strategy("m15_two_bar_exhaustion_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("m15_two_bar_exhaustion_reversal_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].reason_code == "M15_TWO_BAR_EXHAUSTION_REVERSAL_V0_LONG"
    assert signals[-1].metadata["impulse_move_atr"] < -1.55

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.expert == "m15_two_bar_exhaustion_reversal_v0"
    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.35
    assert plan.metadata["max_holding_bars"] == 96

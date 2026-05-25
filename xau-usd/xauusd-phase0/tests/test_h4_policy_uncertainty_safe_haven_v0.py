from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_policy_uncertainty_safe_haven_synthetic_smoke():
    strategy = get_strategy("h4_policy_uncertainty_safe_haven_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_policy_uncertainty_safe_haven_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h4_policy_uncertainty_safe_haven_v0"
    assert signals[-1].direction == "LONG"
    assert (
        signals[-1].metadata["policy_uncertainty_ratio_5d_120d"] >= 1.35
        or signals[-1].metadata["policy_uncertainty_change_z252"] >= 0.75
    )

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.65
    assert plan.metadata["max_holding_bars"] == 432

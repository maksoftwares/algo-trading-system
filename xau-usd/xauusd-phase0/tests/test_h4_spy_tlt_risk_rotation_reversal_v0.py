from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_spy_tlt_risk_rotation_reversal_v0_generates_synthetic_trade_plan() -> None:
    strategy = get_strategy(
        "h4_spy_tlt_risk_rotation_reversal_v0",
        allow_research_candidate=True,
    )
    context = synthetic_context_for_expert("h4_spy_tlt_risk_rotation_reversal_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h4_spy_tlt_risk_rotation_reversal_v0"
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["risk_rotation_5d"] >= 0.0120
    assert signals[-1].metadata["close_location"] >= 0.60

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.expert == "h4_spy_tlt_risk_rotation_reversal_v0"
    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.55
    assert plan.metadata["max_holding_bars"] == 336

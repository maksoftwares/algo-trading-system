from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_weekend_gap_reversion_v0_generates_synthetic_trade_plan() -> None:
    strategy = get_strategy("weekend_gap_reversion_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("weekend_gap_reversion_v0")

    signals = strategy.generate_signals(context)

    assert signals
    signal = signals[-1]
    assert signal.expert == "weekend_gap_reversion_v0"
    assert signal.direction == "SHORT"
    assert signal.metadata["market_break_hours"] >= 24.0
    assert signal.metadata["gap_atr"] > 0.35

    plan = strategy.build_trade_plan(signal, context)

    assert plan.entry_type == "MARKET"
    assert plan.stop_loss > signal.metadata["estimated_entry_price"]
    assert plan.take_profit == signal.metadata["pre_gap_close"]
    assert plan.risk_reward >= 1.15

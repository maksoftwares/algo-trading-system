from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h1_real_yield_inflation_mix_followthrough_synthetic_generates_signal() -> None:
    expert = "h1_real_yield_inflation_mix_followthrough_v0"
    strategy = get_strategy(expert, allow_research_candidate=True)
    context = synthetic_context_for_expert(expert)

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[0].expert == expert
    assert signals[0].direction in {"LONG", "SHORT"}


def test_h1_real_yield_inflation_mix_followthrough_trade_plan_has_valid_risk() -> None:
    expert = "h1_real_yield_inflation_mix_followthrough_v0"
    strategy = get_strategy(expert, allow_research_candidate=True)
    context = synthetic_context_for_expert(expert)
    signal = strategy.generate_signals(context)[0]

    plan = strategy.build_trade_plan(signal, context)

    assert plan.entry_type == "MARKET"
    assert plan.risk_reward == strategy.risk_reward
    assert plan.stop_loss != plan.take_profit
    assert plan.metadata["planned_time_stop_h1_bars"] == 14

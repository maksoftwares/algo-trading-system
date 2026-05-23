from __future__ import annotations

import pytest

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


@pytest.mark.parametrize(
    "expert",
    [
        "d1_inside_day_breakout_v0",
        "d1_outside_day_followthrough_v0",
        "weekly_open_reversion_v0",
    ],
)
def test_new_independent_research_candidate_synthetic_smoke(expert: str):
    strategy = get_strategy(expert, allow_research_candidate=True)
    context = synthetic_context_for_expert(expert)

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == expert

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.expert == expert
    assert plan.entry_type == "MARKET"
    assert plan.stop_loss != plan.take_profit
    assert plan.risk_reward > 0

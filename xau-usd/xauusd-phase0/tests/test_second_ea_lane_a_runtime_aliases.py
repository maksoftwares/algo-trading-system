from __future__ import annotations

from phase0.strategies.registry import get_research_strategy, research_strategy_names
from phase0.synthetic import synthetic_context_for_expert


ALIASES = (
    ("d1_momentum_h4_pullback_v0", "d1_momentum_h4_pullback_v1_fullhist"),
    ("w1_d1_momentum_continuation_v0", "w1_d1_momentum_continuation_v1_fullhist"),
    ("h4_inside_bar_d1_momentum_breakout_v0", "h4_inside_bar_d1_momentum_breakout_v1_fullhist"),
)


def test_second_ea_lane_a_v1_aliases_are_research_only():
    names = set(research_strategy_names())

    for _, alias in ALIASES:
        assert alias in names


def test_second_ea_lane_a_v1_aliases_preserve_synthetic_signal_and_plan():
    for source, alias in ALIASES:
        source_strategy = get_research_strategy(source)
        alias_strategy = get_research_strategy(alias)
        source_context = synthetic_context_for_expert(source)
        alias_context = synthetic_context_for_expert(alias)

        source_signal = source_strategy.generate_signals(source_context)[-1]
        alias_signal = alias_strategy.generate_signals(alias_context)[-1]
        source_plan = source_strategy.build_trade_plan(source_signal, source_context)
        alias_plan = alias_strategy.build_trade_plan(alias_signal, alias_context)

        assert alias_signal.direction == source_signal.direction
        assert alias_signal.timestamp_utc == source_signal.timestamp_utc
        assert alias_signal.reason_code == source_signal.reason_code
        assert alias_plan.direction == source_plan.direction
        assert alias_plan.entry_type == source_plan.entry_type
        assert alias_plan.stop_loss == source_plan.stop_loss
        assert alias_plan.take_profit == source_plan.take_profit
        assert alias_plan.risk_reward == source_plan.risk_reward

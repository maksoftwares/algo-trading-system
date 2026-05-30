from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h1_gld_spy_safe_haven_rotation_followthrough_synthetic_smoke() -> None:
    strategy = get_strategy(
        "h1_gld_spy_safe_haven_rotation_followthrough_v0",
        allow_research_candidate=True,
    )
    context = synthetic_context_for_expert("h1_gld_spy_safe_haven_rotation_followthrough_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h1_gld_spy_safe_haven_rotation_followthrough_v0"
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["gld_spy_rotation_5d"] >= strategy.rotation_threshold
    assert signals[-1].metadata["gld_spy_rotation_abs_percentile252"] >= strategy.rotation_percentile_threshold

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"] < plan.take_profit
    assert plan.risk_reward == 1.50
    assert plan.metadata["max_holding_bars"] == 120

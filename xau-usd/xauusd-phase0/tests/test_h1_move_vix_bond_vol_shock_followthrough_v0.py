from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h1_move_vix_bond_vol_shock_followthrough_generates_synthetic_trade_plan() -> None:
    strategy = get_strategy(
        "h1_move_vix_bond_vol_shock_followthrough_v0",
        allow_research_candidate=True,
    )
    context = synthetic_context_for_expert("h1_move_vix_bond_vol_shock_followthrough_v0")

    signals = strategy.generate_signals(context)

    assert signals
    signal = signals[-1]
    assert signal.expert == "h1_move_vix_bond_vol_shock_followthrough_v0"
    assert signal.direction == "LONG"
    assert signal.metadata["move_return_5d"] > signal.metadata["vix_return_5d"]
    assert signal.metadata["move_vix_ratio_z252"] >= 0.35

    plan = strategy.build_trade_plan(signal, context)

    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signal.metadata["estimated_entry_price"]
    assert plan.take_profit > signal.metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.50
    assert plan.metadata["planned_time_stop_h1_bars"] == 18

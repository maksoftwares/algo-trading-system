from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h1_volatility_squeeze_breakout_synthetic_smoke():
    strategy = get_strategy("h1_volatility_squeeze_breakout_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h1_volatility_squeeze_breakout_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h1_volatility_squeeze_breakout_v0"
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["bb_width_percentile240"] <= 0.25
    assert signals[-1].metadata["signal_body_ratio"] >= 0.45

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.60
    assert plan.metadata["max_holding_bars"] == 144

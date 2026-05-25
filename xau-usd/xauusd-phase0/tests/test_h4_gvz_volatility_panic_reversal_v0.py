from __future__ import annotations

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_gvz_volatility_panic_reversal_synthetic_smoke():
    strategy = get_strategy("h4_gvz_volatility_panic_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_gvz_volatility_panic_reversal_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h4_gvz_volatility_panic_reversal_v0"
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["gvz_percentile252"] >= 0.70
    assert (
        signals[-1].metadata["gvz_return_5d"] >= 0.06
        or signals[-1].metadata["gvz_return_5d_z126"] >= 0.65
    )

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.60
    assert plan.metadata["max_holding_bars"] == 288

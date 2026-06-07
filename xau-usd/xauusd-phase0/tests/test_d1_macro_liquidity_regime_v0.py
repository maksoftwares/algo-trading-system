from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_d1_macro_liquidity_regime_v0_generates_synthetic_trade_plan() -> None:
    strategy = get_strategy("d1_macro_liquidity_regime_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("d1_macro_liquidity_regime_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "d1_macro_liquidity_regime_v0"
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["fed_assets_return_13w"] >= 0.012
    assert signals[-1].metadata["dollar_return_20d"] <= -0.004
    plan = strategy.build_trade_plan(signals[-1], context)
    assert plan.expert == "d1_macro_liquidity_regime_v0"
    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.70

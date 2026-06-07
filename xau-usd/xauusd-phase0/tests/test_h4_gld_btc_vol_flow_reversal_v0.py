from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_gld_btc_vol_flow_reversal_v0_generates_synthetic_trade_plan() -> None:
    strategy = get_strategy("h4_gld_btc_vol_flow_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_gld_btc_vol_flow_reversal_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h4_gld_btc_vol_flow_reversal_v0"
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["gld_return_1d"] <= -0.0035
    assert signals[-1].metadata["btc_vol_ratio_10_40"] >= 1.10
    plan = strategy.build_trade_plan(signals[-1], context)
    assert plan.expert == "h4_gld_btc_vol_flow_reversal_v0"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.55

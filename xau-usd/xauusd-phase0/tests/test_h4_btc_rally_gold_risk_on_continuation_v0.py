from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_btc_rally_gold_risk_on_continuation_v0_generates_synthetic_trade_plan() -> None:
    strategy = get_strategy(
        "h4_btc_rally_gold_risk_on_continuation_v0",
        allow_research_candidate=True,
    )
    context = synthetic_context_for_expert("h4_btc_rally_gold_risk_on_continuation_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h4_btc_rally_gold_risk_on_continuation_v0"
    assert signals[-1].direction == "SHORT"
    plan = strategy.build_trade_plan(signals[-1], context)
    assert plan.expert == "h4_btc_rally_gold_risk_on_continuation_v0"
    assert plan.risk_reward == 1.35
    assert plan.take_profit < plan.stop_loss

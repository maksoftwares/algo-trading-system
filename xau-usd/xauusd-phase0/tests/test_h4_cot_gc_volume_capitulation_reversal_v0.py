from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_cot_gc_volume_capitulation_reversal_v0_generates_synthetic_trade_plan() -> None:
    strategy = get_strategy(
        "h4_cot_gc_volume_capitulation_reversal_v0",
        allow_research_candidate=True,
    )
    context = synthetic_context_for_expert("h4_cot_gc_volume_capitulation_reversal_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h4_cot_gc_volume_capitulation_reversal_v0"
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["gc_volume_percentile252"] >= 0.78
    assert signals[-1].metadata["mm_net_percentile156"] <= 0.35
    plan = strategy.build_trade_plan(signals[-1], context)
    assert plan.expert == "h4_cot_gc_volume_capitulation_reversal_v0"
    assert plan.risk_reward == 1.55
    assert plan.stop_loss < plan.take_profit

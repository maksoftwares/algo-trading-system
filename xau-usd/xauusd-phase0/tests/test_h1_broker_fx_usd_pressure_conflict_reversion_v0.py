from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h1_broker_fx_usd_pressure_conflict_reversion_v0_generates_synthetic_trade_plan() -> None:
    strategy = get_strategy(
        "h1_broker_fx_usd_pressure_conflict_reversion_v0",
        allow_research_candidate=True,
    )
    context = synthetic_context_for_expert("h1_broker_fx_usd_pressure_conflict_reversion_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h1_broker_fx_usd_pressure_conflict_reversion_v0"
    plan = strategy.build_trade_plan(signals[-1], context)
    assert plan.expert == "h1_broker_fx_usd_pressure_conflict_reversion_v0"
    assert plan.risk_reward == 1.50
    assert plan.stop_loss != plan.take_profit

from __future__ import annotations

from phase0.strategies.h1_macro_composite_pullback_v0 import H1MacroCompositePullbackV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h1_macro_composite_pullback_smoke_signal() -> None:
    strategy = H1MacroCompositePullbackV0Strategy()

    signals = strategy.generate_signals(synthetic_context_for_expert("h1_macro_composite_pullback_v0"))

    assert len(signals) >= 1
    assert signals[0].expert == "h1_macro_composite_pullback_v0"
    assert signals[0].direction == "LONG"
    assert signals[0].metadata["macro_composite_score"] >= 3
    assert signals[0].metadata["macro_bull_votes"] >= 4


def test_h1_macro_composite_pullback_builds_valid_plan() -> None:
    strategy = H1MacroCompositePullbackV0Strategy()
    context = synthetic_context_for_expert("h1_macro_composite_pullback_v0")
    signal = strategy.generate_signals(context)[0]

    plan = strategy.build_trade_plan(signal, context)

    assert plan.direction == "LONG"
    assert plan.stop_loss < signal.metadata["estimated_entry_price"] < plan.take_profit
    assert plan.risk_reward == strategy.risk_reward


def test_h1_macro_composite_pullback_requires_macro_context() -> None:
    strategy = H1MacroCompositePullbackV0Strategy()
    context = synthetic_context_for_expert("h1_macro_composite_pullback_v0")
    context.pop("macro_proxy")

    try:
        strategy.generate_signals(context)
    except Exception as exc:
        assert "macro" in str(exc).lower()
    else:
        raise AssertionError("Expected missing macro context to fail.")

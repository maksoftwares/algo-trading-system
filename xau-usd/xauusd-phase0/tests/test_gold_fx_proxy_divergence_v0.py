from __future__ import annotations

import pytest

from phase0.config import ConfigError
from phase0.strategies.gold_fx_proxy_divergence_v0 import GoldFxProxyDivergenceV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_gold_fx_proxy_divergence_v0_generates_long_market_plan():
    strategy = GoldFxProxyDivergenceV0Strategy()
    context = synthetic_context_for_expert("gold_fx_proxy_divergence_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["usd_proxy_z"] >= 1.0
    assert signals[-1].metadata["xau_residual_z"] >= 0.75
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.8)
    assert plan.metadata["max_holding_bars"] == 144


def test_gold_fx_proxy_divergence_v0_requires_proxy_context():
    strategy = GoldFxProxyDivergenceV0Strategy()
    context = synthetic_context_for_expert("gold_fx_proxy_divergence_v0")
    context.pop("intermarket_proxy")

    with pytest.raises(ConfigError, match="intermarket_proxy"):
        strategy.generate_signals(context)

from __future__ import annotations

import pytest

from phase0.config import ConfigError
from phase0.strategies.xau_xag_relative_value_v0 import XauXagRelativeValueV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_xau_xag_relative_value_v0_generates_long_market_plan():
    strategy = XauXagRelativeValueV0Strategy()
    context = synthetic_context_for_expert("xau_xag_relative_value_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["xau_xag_ratio_z"] <= -0.50
    assert signals[-1].metadata["relative_momentum_6h"] > 0.0
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.65)
    assert plan.metadata["max_holding_bars"] == 288


def test_xau_xag_relative_value_v0_requires_relative_context():
    strategy = XauXagRelativeValueV0Strategy()
    context = synthetic_context_for_expert("xau_xag_relative_value_v0")
    context.pop("relative_value")

    with pytest.raises(ConfigError, match="relative_value"):
        strategy.generate_signals(context)

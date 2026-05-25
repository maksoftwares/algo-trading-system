from __future__ import annotations

import pytest

from phase0.strategies.h1_smooth_trend_exhaustion_reversal_v0 import (
    H1SmoothTrendExhaustionReversalV0Strategy,
)
from phase0.synthetic import synthetic_context_for_expert


def test_h1_smooth_trend_exhaustion_reversal_v0_generates_long_market_plan():
    strategy = H1SmoothTrendExhaustionReversalV0Strategy()
    context = synthetic_context_for_expert("h1_smooth_trend_exhaustion_reversal_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["trend_move_24h_atr"] <= -2.20
    assert signals[-1].metadata["trend_efficiency_24h"] >= 0.58
    assert signals[-1].metadata["ema50_stretch_atr"] <= -1.00
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.4)
    assert plan.metadata["max_holding_bars"] == 576

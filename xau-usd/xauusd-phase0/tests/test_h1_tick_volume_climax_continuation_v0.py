from __future__ import annotations

import pytest

from phase0.strategies.h1_tick_volume_climax_continuation_v0 import (
    H1TickVolumeClimaxContinuationV0Strategy,
)
from phase0.synthetic import synthetic_context_for_expert


def test_h1_tick_volume_climax_continuation_v0_generates_long_market_plan() -> None:
    strategy = H1TickVolumeClimaxContinuationV0Strategy()
    context = synthetic_context_for_expert("h1_tick_volume_climax_continuation_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["tick_count_z"] >= 1.10
    assert signals[-1].metadata["tick_count_ratio"] >= 1.18
    assert signals[-1].metadata["h1_range_atr"] >= 0.80
    assert signals[-1].metadata["h1_move_atr"] >= 0.45
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.45)
    assert plan.metadata["max_holding_bars"] == 144


def test_h1_tick_volume_climax_continuation_v0_requires_volume_climax() -> None:
    strategy = H1TickVolumeClimaxContinuationV0Strategy()
    context = synthetic_context_for_expert("h1_tick_volume_climax_continuation_v0")
    h1 = context["H1"].copy()
    h1["tick_count"] = 100.0
    h1["volume_sum"] = 100.0
    context["H1"] = h1

    assert strategy.generate_signals(context) == []

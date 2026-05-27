from __future__ import annotations

import pandas as pd

from phase0.gc_futures_volume_data import GC_FUTURES_VOLUME_FRAME_KEY
from phase0.strategies.h4_gold_futures_volume_climax_v0 import (
    H4GoldFuturesVolumeClimaxV0Strategy,
)
from phase0.synthetic import synthetic_context_for_expert


def test_h4_gold_futures_volume_climax_smoke_signal() -> None:
    strategy = H4GoldFuturesVolumeClimaxV0Strategy()

    signals = strategy.generate_signals(
        synthetic_context_for_expert("h4_gold_futures_volume_climax_v0")
    )

    assert len(signals) == 1
    assert signals[0].expert == "h4_gold_futures_volume_climax_v0"
    assert signals[0].direction == "LONG"
    assert signals[0].metadata["gc_volume_percentile252"] >= strategy.volume_percentile_threshold


def test_h4_gold_futures_volume_climax_builds_valid_plan() -> None:
    strategy = H4GoldFuturesVolumeClimaxV0Strategy()
    context = synthetic_context_for_expert("h4_gold_futures_volume_climax_v0")
    signal = strategy.generate_signals(context)[0]

    plan = strategy.build_trade_plan(signal, context)

    assert plan.direction == "LONG"
    assert plan.stop_loss < signal.metadata["estimated_entry_price"] < plan.take_profit
    assert plan.risk_reward == strategy.risk_reward


def test_h4_gold_futures_volume_climax_requires_context() -> None:
    strategy = H4GoldFuturesVolumeClimaxV0Strategy()
    context = synthetic_context_for_expert("h4_gold_futures_volume_climax_v0")
    context.pop(GC_FUTURES_VOLUME_FRAME_KEY)

    try:
        strategy.generate_signals(context)
    except Exception as exc:
        assert "gc_futures_volume" in str(exc)
    else:
        raise AssertionError("Expected missing GC futures volume context to fail.")


def test_h4_gold_futures_volume_climax_no_unshifted_same_day_volume() -> None:
    strategy = H4GoldFuturesVolumeClimaxV0Strategy()
    context = synthetic_context_for_expert("h4_gold_futures_volume_climax_v0")
    gc = context[GC_FUTURES_VOLUME_FRAME_KEY].copy()
    gc.loc[gc.index[-1], "volume"] = 99_999_999
    context[GC_FUTURES_VOLUME_FRAME_KEY] = gc

    signals = strategy.generate_signals(context)

    assert len(signals) == 1
    assert pd.Timestamp(signals[0].timestamp_utc) < pd.Timestamp(gc.iloc[-1]["timestamp_utc"])

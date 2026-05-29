from __future__ import annotations

import pandas as pd

from phase0.gdx_gld_relative_data import GDX_GLD_RELATIVE_FRAME_KEY
from phase0.strategies.h4_gdx_gld_miner_divergence_v0 import H4GdxGldMinerDivergenceV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_gdx_gld_miner_divergence_smoke_signal() -> None:
    strategy = H4GdxGldMinerDivergenceV0Strategy()

    signals = strategy.generate_signals(synthetic_context_for_expert("h4_gdx_gld_miner_divergence_v0"))

    assert len(signals) == 1
    assert signals[0].expert == "h4_gdx_gld_miner_divergence_v0"
    assert signals[0].direction == "LONG"
    assert signals[0].metadata["miner_relative_return_1d"] >= strategy.relative_return_threshold
    assert signals[0].metadata["miner_relative_z126"] >= strategy.relative_z_threshold


def test_h4_gdx_gld_miner_divergence_builds_valid_plan() -> None:
    strategy = H4GdxGldMinerDivergenceV0Strategy()
    context = synthetic_context_for_expert("h4_gdx_gld_miner_divergence_v0")
    signal = strategy.generate_signals(context)[0]

    plan = strategy.build_trade_plan(signal, context)

    assert plan.direction == "LONG"
    assert plan.stop_loss < signal.metadata["estimated_entry_price"] < plan.take_profit
    assert plan.risk_reward == strategy.risk_reward


def test_h4_gdx_gld_miner_divergence_requires_context() -> None:
    strategy = H4GdxGldMinerDivergenceV0Strategy()
    context = synthetic_context_for_expert("h4_gdx_gld_miner_divergence_v0")
    context.pop(GDX_GLD_RELATIVE_FRAME_KEY)

    try:
        strategy.generate_signals(context)
    except Exception as exc:
        assert "gdx_gld_relative_flow" in str(exc)
    else:
        raise AssertionError("Expected missing GDX/GLD relative context to fail.")


def test_h4_gdx_gld_miner_divergence_no_unshifted_same_day_data() -> None:
    strategy = H4GdxGldMinerDivergenceV0Strategy()
    context = synthetic_context_for_expert("h4_gdx_gld_miner_divergence_v0")
    relative = context[GDX_GLD_RELATIVE_FRAME_KEY].copy()
    relative.loc[relative.index[-1], "gdx_close"] = 999.0
    context[GDX_GLD_RELATIVE_FRAME_KEY] = relative

    signals = strategy.generate_signals(context)

    assert len(signals) == 1
    assert pd.Timestamp(signals[0].timestamp_utc) < pd.Timestamp(relative.iloc[-1]["timestamp_utc"])

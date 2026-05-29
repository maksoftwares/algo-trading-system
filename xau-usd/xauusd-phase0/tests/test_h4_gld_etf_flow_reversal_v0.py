from __future__ import annotations

import pandas as pd

from phase0.gld_etf_flow_data import GLD_ETF_FLOW_FRAME_KEY
from phase0.strategies.h4_gld_etf_flow_reversal_v0 import H4GldEtfFlowReversalV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_gld_etf_flow_reversal_smoke_signal() -> None:
    strategy = H4GldEtfFlowReversalV0Strategy()

    signals = strategy.generate_signals(synthetic_context_for_expert("h4_gld_etf_flow_reversal_v0"))

    assert len(signals) == 1
    assert signals[0].expert == "h4_gld_etf_flow_reversal_v0"
    assert signals[0].direction == "LONG"
    assert signals[0].metadata["gld_volume_percentile252"] >= strategy.volume_percentile_threshold
    assert signals[0].metadata["gld_return_1d"] <= -strategy.gld_return_threshold


def test_h4_gld_etf_flow_reversal_builds_valid_plan() -> None:
    strategy = H4GldEtfFlowReversalV0Strategy()
    context = synthetic_context_for_expert("h4_gld_etf_flow_reversal_v0")
    signal = strategy.generate_signals(context)[0]

    plan = strategy.build_trade_plan(signal, context)

    assert plan.direction == "LONG"
    assert plan.stop_loss < signal.metadata["estimated_entry_price"] < plan.take_profit
    assert plan.risk_reward == strategy.risk_reward


def test_h4_gld_etf_flow_reversal_requires_context() -> None:
    strategy = H4GldEtfFlowReversalV0Strategy()
    context = synthetic_context_for_expert("h4_gld_etf_flow_reversal_v0")
    context.pop(GLD_ETF_FLOW_FRAME_KEY)

    try:
        strategy.generate_signals(context)
    except Exception as exc:
        assert "gld_etf_flow" in str(exc)
    else:
        raise AssertionError("Expected missing GLD ETF flow context to fail.")


def test_h4_gld_etf_flow_reversal_no_unshifted_same_day_volume() -> None:
    strategy = H4GldEtfFlowReversalV0Strategy()
    context = synthetic_context_for_expert("h4_gld_etf_flow_reversal_v0")
    gld = context[GLD_ETF_FLOW_FRAME_KEY].copy()
    gld.loc[gld.index[-1], "volume"] = 999_999_999
    context[GLD_ETF_FLOW_FRAME_KEY] = gld

    signals = strategy.generate_signals(context)

    assert len(signals) == 1
    assert pd.Timestamp(signals[0].timestamp_utc) < pd.Timestamp(gld.iloc[-1]["timestamp_utc"])

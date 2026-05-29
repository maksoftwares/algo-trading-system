from __future__ import annotations

from phase0.strategies.h4_gld_etf_flow_reversal_v1 import H4GldEtfFlowReversalV1Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_gld_etf_flow_reversal_v1_smoke_signal() -> None:
    strategy = H4GldEtfFlowReversalV1Strategy()

    signals = strategy.generate_signals(synthetic_context_for_expert("h4_gld_etf_flow_reversal_v1"))

    assert len(signals) == 1
    assert signals[0].expert == "h4_gld_etf_flow_reversal_v1"
    assert signals[0].direction == "LONG"
    assert signals[0].reason_code == "H4_GLD_ETF_FLOW_REVERSAL_V1_LONG"
    assert signals[0].metadata["gld_volume_percentile252"] >= strategy.volume_percentile_threshold


def test_h4_gld_etf_flow_reversal_v1_thresholds_are_broader_than_v0() -> None:
    strategy = H4GldEtfFlowReversalV1Strategy()

    assert strategy.volume_percentile_threshold == 0.75
    assert strategy.volume_z_threshold == 0.80
    assert strategy.gld_return_threshold == 0.003
    assert strategy.h4_return_threshold == 0.0025
    assert 8 in strategy.decision_hours_utc

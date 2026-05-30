from __future__ import annotations

from phase0.strategies.h4_gld_etf_flow_reversal_v0 import H4GldEtfFlowReversalV0Strategy
from phase0.strategies.h4_gld_etf_flow_reversal_v2 import H4GldEtfFlowReversalV2Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_gld_etf_flow_reversal_v2_smoke_signal() -> None:
    strategy = H4GldEtfFlowReversalV2Strategy()

    signals = strategy.generate_signals(synthetic_context_for_expert("h4_gld_etf_flow_reversal_v2"))

    assert len(signals) == 1
    assert signals[0].expert == "h4_gld_etf_flow_reversal_v2"
    assert signals[0].direction == "LONG"
    assert signals[0].reason_code == "H4_GLD_ETF_FLOW_REVERSAL_V2_LONG"
    assert signals[0].metadata["gld_volume_percentile252"] >= strategy.volume_percentile_threshold


def test_h4_gld_etf_flow_reversal_v2_preserves_v0_thresholds() -> None:
    baseline = H4GldEtfFlowReversalV0Strategy()
    strategy = H4GldEtfFlowReversalV2Strategy()

    assert strategy.volume_percentile_threshold == baseline.volume_percentile_threshold
    assert strategy.volume_z_threshold == baseline.volume_z_threshold
    assert strategy.gld_return_threshold == baseline.gld_return_threshold
    assert strategy.h4_return_threshold == baseline.h4_return_threshold
    assert 8 in strategy.decision_hours_utc

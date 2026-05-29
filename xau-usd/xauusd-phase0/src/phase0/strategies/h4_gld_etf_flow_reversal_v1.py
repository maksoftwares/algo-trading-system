from __future__ import annotations

from phase0.strategies.h4_gld_etf_flow_reversal_v0 import H4GldEtfFlowReversalV0Strategy


class H4GldEtfFlowReversalV1Strategy(H4GldEtfFlowReversalV0Strategy):
    """Result-informed GLD ETF flow-stress reversal candidate."""

    name = "h4_gld_etf_flow_reversal_v1"
    version = "0.1-result-informed-research-disabled"

    volume_percentile_threshold = 0.75
    volume_z_threshold = 0.80
    gld_return_threshold = 0.003
    h4_return_threshold = 0.0025
    decision_hours_utc = {8, 12, 16, 20}

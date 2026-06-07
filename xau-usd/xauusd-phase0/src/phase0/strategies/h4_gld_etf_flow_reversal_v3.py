from __future__ import annotations

from phase0.strategies.h4_gld_etf_flow_reversal_v2 import H4GldEtfFlowReversalV2Strategy


class H4GldEtfFlowReversalV3Strategy(H4GldEtfFlowReversalV2Strategy):
    """Result-focused timing expansion for GLD ETF flow-stress reversal."""

    name = "h4_gld_etf_flow_reversal_v3"
    version = "0.3-result-focused-timing-v3"

    decision_hours_utc = {0, 4, 8, 12, 16, 20}
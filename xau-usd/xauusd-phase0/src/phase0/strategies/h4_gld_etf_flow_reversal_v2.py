from __future__ import annotations

from phase0.strategies.h4_gld_etf_flow_reversal_v0 import H4GldEtfFlowReversalV0Strategy


class H4GldEtfFlowReversalV2Strategy(H4GldEtfFlowReversalV0Strategy):
    """Research-only narrow GLD ETF flow-stress timing variant."""

    name = "h4_gld_etf_flow_reversal_v2"
    version = "0.2-narrow-timing-research-disabled"

    decision_hours_utc = {8, 12, 16, 20}

from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.strategies.liquidity_sweep_reversal_v0 import LiquiditySweepReversalV0Strategy


class LiquiditySweepContinuationV0Strategy(LiquiditySweepReversalV0Strategy):
    """Disabled research strategy for the locked liquidity sweep continuation v0 hypothesis."""

    name = "liquidity_sweep_continuation_v0"
    version = "0.1-research-disabled"
    reason_prefix = "LIQUIDITY_SWEEP_CONTINUATION_V0"

    def _short_setup(
        self,
        row: pd.Series,
        high: float,
        low: float,
        open_price: float,
        close: float,
        m5_atr: float,
        body: float,
        upper_wick: float,
        close_position: float,
    ) -> dict[str, Any] | None:
        del low, upper_wick
        if close <= open_price or close_position < 0.70 or body < 0.30 * m5_atr:
            return None
        for level_kind, level in self._high_levels(row):
            if high >= level + 0.20 * m5_atr and close >= level + 0.10 * m5_atr:
                return {
                    "direction": "LONG",
                    "level_kind": level_kind,
                    "level": level,
                    "sweep_distance_atr": (high - level) / m5_atr,
                    "acceptance_distance_atr": (close - level) / m5_atr,
                    "continuation_body_atr": body / m5_atr,
                }
        return None

    def _long_setup(
        self,
        row: pd.Series,
        high: float,
        low: float,
        open_price: float,
        close: float,
        m5_atr: float,
        body: float,
        lower_wick: float,
        close_position: float,
    ) -> dict[str, Any] | None:
        del high, lower_wick
        if close >= open_price or close_position > 0.30 or body < 0.30 * m5_atr:
            return None
        for level_kind, level in self._low_levels(row):
            if low <= level - 0.20 * m5_atr and close <= level - 0.10 * m5_atr:
                return {
                    "direction": "SHORT",
                    "level_kind": level_kind,
                    "level": level,
                    "sweep_distance_atr": (level - low) / m5_atr,
                    "acceptance_distance_atr": (level - close) / m5_atr,
                    "continuation_body_atr": body / m5_atr,
                }
        return None

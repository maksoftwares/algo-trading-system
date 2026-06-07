from __future__ import annotations

import pandas as pd

from phase0.strategies.base import value_available
from phase0.strategies.h4_macro_momentum_confluence_v0 import (
    H4MacroMomentumConfluenceV0Strategy,
    _setup_metadata,
)


class H4MacroPullbackReclaimV0Strategy(H4MacroMomentumConfluenceV0Strategy):
    """Research-only strict macro-state H4 EMA50 pullback/reclaim candidate."""

    name = "h4_macro_pullback_reclaim_v0"
    version = "0.1-research-disabled"
    throttle_days = 1

    def _setup_at_row(self, row: pd.Series) -> dict | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema50"],
            row["h4_return_3"],
            row["h4_return_12"],
            row["macro_composite_score"],
            row["macro_bull_votes"],
            row["macro_bear_votes"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema50 = float(row["h4_ema50"])
        h4_return_3 = float(row["h4_return_3"])
        h4_return_12 = float(row["h4_return_12"])
        composite_score = float(row["macro_composite_score"])
        bull_votes = float(row["macro_bull_votes"])
        bear_votes = float(row["macro_bear_votes"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema50_distance_atr = (close - h4_ema50) / h4_atr

        if (
            composite_score >= 2.0
            and bull_votes >= 3.0
            and bear_votes <= 1.0
            and low <= h4_ema50 + 1.10 * h4_atr
            and close >= h4_ema50 - 0.10 * h4_atr
            and close > open_price
            and h4_return_3 >= -0.0008
            and h4_return_12 >= -0.0200
            and close_location >= 0.52
            and ema50_distance_atr <= 3.20
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema50_distance_atr)

        if (
            composite_score <= -2.0
            and bear_votes >= 3.0
            and bull_votes <= 1.0
            and high >= h4_ema50 - 1.10 * h4_atr
            and close <= h4_ema50 + 0.10 * h4_atr
            and close < open_price
            and h4_return_3 <= 0.0008
            and h4_return_12 <= 0.0200
            and close_location <= 0.48
            and ema50_distance_atr >= -3.20
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema50_distance_atr)

        return None

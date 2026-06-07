from __future__ import annotations

import pandas as pd

from phase0.strategies.base import value_available
from phase0.strategies.h4_macro_momentum_confluence_v0 import (
    H4MacroMomentumConfluenceV0Strategy,
    _setup_metadata,
)


class H4MacroMomentumConfluenceV1Strategy(H4MacroMomentumConfluenceV0Strategy):
    """Research-only broader macro/D1/H4 confluence candidate."""

    name = "h4_macro_momentum_confluence_v1"
    version = "0.1-research-disabled"

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
            row["d1_close"],
            row["d1_ema20"],
            row["d1_return_5"],
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
        d1_close = float(row["d1_close"])
        d1_ema20 = float(row["d1_ema20"])
        d1_return_5 = float(row["d1_return_5"])
        composite_score = float(row["macro_composite_score"])
        bull_votes = float(row["macro_bull_votes"])
        bear_votes = float(row["macro_bear_votes"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema50_distance_atr = (close - h4_ema50) / h4_atr

        if (
            composite_score >= 1.0
            and bull_votes >= 2.0
            and bear_votes <= 1.0
            and d1_close > d1_ema20
            and d1_return_5 >= 0.0
            and low <= h4_ema50 + 1.20 * h4_atr
            and close >= h4_ema50 - 0.15 * h4_atr
            and close > open_price
            and h4_return_3 >= 0.0
            and h4_return_12 >= -0.0180
            and close_location >= 0.52
            and ema50_distance_atr <= 3.25
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema50_distance_atr)

        if (
            composite_score <= -1.0
            and bear_votes >= 2.0
            and bull_votes <= 1.0
            and d1_close < d1_ema20
            and d1_return_5 <= 0.0
            and high >= h4_ema50 - 1.20 * h4_atr
            and close <= h4_ema50 + 0.15 * h4_atr
            and close < open_price
            and h4_return_3 <= 0.0
            and h4_return_12 <= 0.0180
            and close_location <= 0.48
            and ema50_distance_atr >= -3.25
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema50_distance_atr)

        return None

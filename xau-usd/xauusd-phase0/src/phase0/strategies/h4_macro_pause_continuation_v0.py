from __future__ import annotations

import pandas as pd

from phase0.strategies.base import value_available
from phase0.strategies.h4_macro_momentum_confluence_v0 import (
    H4MacroMomentumConfluenceV0Strategy,
    _setup_metadata,
)


class H4MacroPauseContinuationV0Strategy(H4MacroMomentumConfluenceV0Strategy):
    """Research-only strict macro-state H4 pause/continuation candidate."""

    name = "h4_macro_pause_continuation_v0"
    version = "0.1-research-disabled"
    throttle_days = 1
    risk_reward = 1.55

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
            and close > h4_ema50
            and close > open_price
            and h4_return_12 >= 0.0020
            and -0.0040 <= h4_return_3 <= 0.0100
            and 0.45 <= close_location <= 0.82
            and 0.05 <= ema50_distance_atr <= 3.60
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema50_distance_atr)

        if (
            composite_score <= -2.0
            and bear_votes >= 3.0
            and bull_votes <= 1.0
            and close < h4_ema50
            and close < open_price
            and h4_return_12 <= -0.0020
            and -0.0100 <= h4_return_3 <= 0.0040
            and 0.18 <= close_location <= 0.55
            and -3.60 <= ema50_distance_atr <= -0.05
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema50_distance_atr)

        return None

from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.strategies.base import value_available
from phase0.strategies.h1_move_vix_bond_vol_shock_reversal_v0 import (
    H1MoveVixBondVolShockReversalV0Strategy,
    _setup_metadata,
)


class H1MoveVixBondVolShockFollowthroughV0Strategy(H1MoveVixBondVolShockReversalV0Strategy):
    """Research-only H1 XAU follow-through candidate using MOVE/VIX rates-volatility stress."""

    name = "h1_move_vix_bond_vol_shock_followthrough_v0"
    version = "0.1-research-disabled"
    reason_code_prefix = "H1_MOVE_VIX_BOND_VOL_SHOCK_FOLLOWTHROUGH_V0"

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h1_atr14"],
            row["h1_ema40"],
            row["h1_return_6"],
            row["h1_return_24"],
            row["move_close"],
            row["vix_close"],
            row["move_return_5d"],
            row["vix_return_5d"],
            row["move_vix_ratio_z252"],
            row["move_vix_ratio_change_5d"],
            row["move_vix_ratio_change_z126"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema40 = float(row["h1_ema40"])
        h1_return_6 = float(row["h1_return_6"])
        h1_return_24 = float(row["h1_return_24"])
        move_return_5d = float(row["move_return_5d"])
        vix_return_5d = float(row["vix_return_5d"])
        ratio_z = float(row["move_vix_ratio_z252"])
        ratio_change = float(row["move_vix_ratio_change_5d"])
        ratio_change_z = float(row["move_vix_ratio_change_z126"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        bond_vol_shock = (
            move_return_5d >= 0.060
            and move_return_5d > vix_return_5d + 0.015
            and ratio_z >= 0.35
            and (ratio_change >= 0.035 or ratio_change_z >= 0.40)
        )
        if not bond_vol_shock:
            return None

        if (
            h1_return_6 >= 0.0025
            and h1_return_24 <= 0.0300
            and close > open_price
            and close_location >= 0.60
            and close >= h1_ema40 - 0.70 * h1_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            h1_return_6 <= -0.0025
            and h1_return_24 >= -0.0300
            and close < open_price
            and close_location <= 0.40
            and close <= h1_ema40 + 0.70 * h1_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None

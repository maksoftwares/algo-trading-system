from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.strategies.base import value_available
from phase0.strategies.h1_hg_gc_copper_gold_rotation_followthrough_v0 import (
    H1HgGcCopperGoldRotationFollowthroughV0Strategy,
    _setup_metadata,
)


class H1HgGcCopperGoldRotationReversalV0Strategy(H1HgGcCopperGoldRotationFollowthroughV0Strategy):
    """Research-only H1 XAU reversal candidate using HG/GC futures rotation pressure."""

    name = "h1_hg_gc_copper_gold_rotation_reversal_v0"
    version = "0.1-research-disabled"

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        timestamp = pd.Timestamp(row["timestamp_utc"])
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        if timestamp.hour not in self.decision_hours_utc:
            return None

        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h1_atr14"],
            row["h1_ema21"],
            row["h1_ema50"],
            row["h1_return_6"],
            row["h1_return_12"],
            row["h1_return_24"],
            row["copper_gold_pressure_5d"],
            row["copper_gold_pressure_z126"],
            row["copper_gold_pressure_abs_percentile252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        ema21 = float(row["h1_ema21"])
        ema50 = float(row["h1_ema50"])
        h1_return_6 = float(row["h1_return_6"])
        h1_return_12 = float(row["h1_return_12"])
        h1_return_24 = float(row["h1_return_24"])
        pressure = float(row["copper_gold_pressure_5d"])
        pressure_z = float(row["copper_gold_pressure_z126"])
        pressure_percentile = float(row["copper_gold_pressure_abs_percentile252"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        pressure_active = (
            abs(pressure) >= self.pressure_threshold
            and abs(pressure_z) >= self.pressure_z_threshold
            and pressure_percentile >= self.pressure_percentile_threshold
        )
        if not pressure_active:
            return None

        if (
            pressure >= self.pressure_threshold
            and pressure_z >= self.pressure_z_threshold
            and close > ema50
            and ema21 >= ema50
            and h1_return_12 >= 0.0025
            and h1_return_6 >= 0.0005
            and h1_return_24 <= 0.0300
            and close < open_price
            and close_location <= 0.35
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        if (
            pressure <= -self.pressure_threshold
            and pressure_z <= -self.pressure_z_threshold
            and close < ema50
            and ema21 <= ema50
            and h1_return_12 <= -0.0025
            and h1_return_6 <= -0.0005
            and h1_return_24 >= -0.0300
            and close > open_price
            and close_location >= 0.65
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        return None

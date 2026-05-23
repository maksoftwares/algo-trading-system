from __future__ import annotations

from typing import Any

import math
import pandas as pd

from phase0.indicators import atr
from phase0.strategies.base import copy_context, require_frame
from phase0.strategies.breakout_retest import BreakoutRetestStrategy


class RoundNumberRetestV0Strategy(BreakoutRetestStrategy):
    """Disabled research strategy for the locked round-number retest v0 hypothesis."""

    name = "round_number_retest_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        context["M5"] = m5
        return context

    def _bar_arrays(self, m5: pd.DataFrame) -> dict[str, Any]:
        return {
            "timestamp": m5["timestamp_utc"].to_numpy(),
            "open": m5["open"].to_numpy(),
            "high": m5["high"].to_numpy(),
            "low": m5["low"].to_numpy(),
            "close": m5["close"].to_numpy(),
            "atr14": m5["atr14"].to_numpy(),
        }

    def _candidate_levels_from_arrays(
        self,
        arrays: dict[str, Any],
        position: int,
        direction: str,
        point_size: float,
    ) -> list[dict[str, Any]]:
        close = float(arrays["close"][position])
        if close <= 0:
            return []

        timestamp = arrays["timestamp"][position]
        levels: list[dict[str, Any]] = []
        for increment in (10.0, 25.0, 50.0):
            if direction == "LONG":
                price = math.floor(close / increment) * increment
                if price <= 0 or price >= close:
                    continue
            else:
                price = math.ceil(close / increment) * increment
                if price <= close:
                    continue
            levels.append(
                {
                    "level_kind": f"round_number_{increment:g}",
                    "level_price": float(price),
                    "level_time_utc": timestamp,
                }
            )

        tolerance = 10.0 * point_size
        kept: list[dict[str, Any]] = []
        kept_prices: list[float] = []
        for level in sorted(levels, key=lambda item: abs(close - float(item["level_price"]))):
            price = float(level["level_price"])
            if all(abs(price - kept_price) > tolerance for kept_price in kept_prices):
                kept.append(level)
                kept_prices.append(price)
        return kept

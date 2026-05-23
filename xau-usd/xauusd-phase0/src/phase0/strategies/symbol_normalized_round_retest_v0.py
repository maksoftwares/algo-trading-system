from __future__ import annotations

from typing import Any

import math

from phase0.strategies.round_number_retest_v0 import RoundNumberRetestV0Strategy


class SymbolNormalizedRoundRetestV0Strategy(RoundNumberRetestV0Strategy):
    """Disabled research strategy for symbol-scaled round-number retests."""

    name = "symbol_normalized_round_retest_v0"
    version = "0.1-research-disabled"

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
        for increment in self._increments_for_point_size(point_size):
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
                    "level_kind": f"symbol_round_{increment:g}",
                    "level_price": round(float(price), self._digits_for_point_size(point_size)),
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

    def _increments_for_point_size(self, point_size: float) -> tuple[float, float, float]:
        if point_size <= 0.0001:
            return (0.0050, 0.0100, 0.0250)
        if point_size < 0.005:
            return (0.50, 1.00, 2.50)
        return (10.0, 25.0, 50.0)

    def _digits_for_point_size(self, point_size: float) -> int:
        if point_size <= 0:
            return 5
        return max(0, min(8, int(round(-math.log10(point_size)))))

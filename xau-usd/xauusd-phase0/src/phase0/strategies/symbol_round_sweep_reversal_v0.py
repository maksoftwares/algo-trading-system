from __future__ import annotations

from typing import Any

import math
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import (
    StrategyBase,
    context_point_size,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)
from phase0.strategies.symbol_normalized_round_retest_v0 import SymbolNormalizedRoundRetestV0Strategy


class SymbolRoundSweepReversalV0Strategy(StrategyBase):
    """Disabled research strategy for symbol-scaled round-number sweep reversals."""

    name = "symbol_round_sweep_reversal_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        context["M5"] = m5
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        symbol = context_symbol(context)
        point_size = context_point_size(context)
        levels = SymbolNormalizedRoundRetestV0Strategy()
        increments = levels._increments_for_point_size(point_size)
        digits = levels._digits_for_point_size(point_size)
        signals: list[Signal] = []

        for position in range(14, len(m5)):
            row = m5.iloc[position]
            setup = self._setup_at_position(row, increments, digits, point_size)
            if setup is None:
                continue
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=pd.Timestamp(row["timestamp_utc"]).to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"SYMBOL_ROUND_SWEEP_REVERSAL_V0_{direction}",
                    metadata={
                        **setup,
                        "m5_index": int(position),
                        "point_size": point_size,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m5_atr = float(signal.metadata["m5_atr14"])
        if direction == "LONG":
            stop_loss = float(signal.metadata["sweep_low"]) - 0.10 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["sweep_high"]) + 0.10 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported symbol round sweep reversal direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid symbol round sweep reversal v0 trade plan risk.")
        return TradePlan(
            expert=self.name,
            symbol=signal.symbol,
            direction=direction,
            signal_time_utc=signal.timestamp_utc,
            entry_type="MARKET",
            entry_price=None,
            stop_loss=stop_loss,
            take_profit=take_profit,
            invalidation_level=stop_loss,
            risk_reward=1.5,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry},
        )

    def _setup_at_position(
        self,
        row: pd.Series,
        increments: tuple[float, float, float],
        digits: int,
        point_size: float,
    ) -> dict[str, Any] | None:
        m5_atr = float(row["atr14"])
        if not value_available(m5_atr) or m5_atr <= 0:
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body = abs(close - open_price)
        if body <= 0:
            return None
        body_ratio = body / candle_range
        if body_ratio < 0.20:
            return None
        close_position = (close - low) / candle_range
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low

        long_setup = self._long_setup(
            increments, digits, point_size, open_price, high, low, close, m5_atr, body, lower_wick, close_position
        )
        if long_setup is not None:
            return long_setup

        short_setup = self._short_setup(
            increments, digits, point_size, open_price, high, low, close, m5_atr, body, upper_wick, close_position
        )
        return short_setup

    def _long_setup(
        self,
        increments: tuple[float, float, float],
        digits: int,
        point_size: float,
        open_price: float,
        high: float,
        low: float,
        close: float,
        m5_atr: float,
        body: float,
        lower_wick: float,
        close_position: float,
    ) -> dict[str, Any] | None:
        if close <= open_price or close_position < 0.60 or lower_wick < 1.25 * body:
            return None
        for level in self._candidate_low_sweep_levels(low, close, increments, digits):
            if low <= level - 0.20 * m5_atr and close >= level + 0.05 * m5_atr:
                return {
                    "direction": "LONG",
                    "level_kind": self._level_kind(level, increments, point_size),
                    "level_price": level,
                    "sweep_distance_atr": (level - low) / m5_atr,
                    "reclaim_distance_atr": (close - level) / m5_atr,
                    "m5_atr14": m5_atr,
                    "sweep_high": high,
                    "sweep_low": low,
                    "estimated_entry_price": close,
                    "rejection_body_ratio": body / max(high - low, body),
                    "rejection_close_position": close_position,
                }
        return None

    def _short_setup(
        self,
        increments: tuple[float, float, float],
        digits: int,
        point_size: float,
        open_price: float,
        high: float,
        low: float,
        close: float,
        m5_atr: float,
        body: float,
        upper_wick: float,
        close_position: float,
    ) -> dict[str, Any] | None:
        if close >= open_price or close_position > 0.40 or upper_wick < 1.25 * body:
            return None
        for level in self._candidate_high_sweep_levels(high, close, increments, digits):
            if high >= level + 0.20 * m5_atr and close <= level - 0.05 * m5_atr:
                return {
                    "direction": "SHORT",
                    "level_kind": self._level_kind(level, increments, point_size),
                    "level_price": level,
                    "sweep_distance_atr": (high - level) / m5_atr,
                    "reclaim_distance_atr": (level - close) / m5_atr,
                    "m5_atr14": m5_atr,
                    "sweep_high": high,
                    "sweep_low": low,
                    "estimated_entry_price": close,
                    "rejection_body_ratio": body / max(high - low, body),
                    "rejection_close_position": close_position,
                }
        return None

    def _candidate_low_sweep_levels(
        self,
        low: float,
        close: float,
        increments: tuple[float, float, float],
        digits: int,
    ) -> list[float]:
        levels: set[float] = set()
        for increment in increments:
            start = math.floor(low / increment) - 1
            end = math.ceil(close / increment) + 1
            for handle in range(start, end + 1):
                level = round(handle * increment, digits)
                if low < level < close:
                    levels.add(level)
        return sorted(levels, key=lambda level: abs(close - level))

    def _candidate_high_sweep_levels(
        self,
        high: float,
        close: float,
        increments: tuple[float, float, float],
        digits: int,
    ) -> list[float]:
        levels: set[float] = set()
        for increment in increments:
            start = math.floor(close / increment) - 1
            end = math.ceil(high / increment) + 1
            for handle in range(start, end + 1):
                level = round(handle * increment, digits)
                if close < level < high:
                    levels.add(level)
        return sorted(levels, key=lambda level: abs(close - level))

    def _level_kind(
        self,
        level: float,
        increments: tuple[float, float, float],
        point_size: float,
    ) -> str:
        tolerance = 10.0 * point_size
        for increment in increments:
            nearest = round(level / increment) * increment
            if abs(level - nearest) <= tolerance:
                return f"symbol_round_sweep_{increment:g}"
        return "symbol_round_sweep"

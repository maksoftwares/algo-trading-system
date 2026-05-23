from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    latest_completed_position,
    require_frame,
    value_available,
)


class D1InsideDayBreakoutV0Strategy(StrategyBase):
    """Disabled research strategy for the locked D1 inside-day breakout v0 hypothesis."""

    name = "d1_inside_day_breakout_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        if "atr14" not in h4:
            h4["atr14"] = atr(h4["high"], h4["low"], h4["close"], 14)
        if "atr14" not in d1:
            d1["atr14"] = atr(d1["high"], d1["low"], d1["close"], 14)

        d1_high = pd.to_numeric(d1["high"], errors="coerce")
        d1_low = pd.to_numeric(d1["low"], errors="coerce")
        prev_high = d1_high.shift(1)
        prev_low = d1_low.shift(1)
        prev_range = prev_high - prev_low
        current_range = d1_high - d1_low
        d1["inside_mother_high"] = prev_high
        d1["inside_mother_low"] = prev_low
        d1["inside_mother_range"] = prev_range
        d1["inside_day_range"] = current_range
        d1["is_inside_day"] = (
            (d1_high <= prev_high)
            & (d1_low >= prev_low)
            & (current_range <= 0.70 * prev_range)
            & (prev_range >= 0.75 * pd.to_numeric(d1["atr14"], errors="coerce").shift(1))
        )

        context["H4"] = h4
        context["D1"] = d1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        d1 = context["D1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_inside_days: set[tuple[int, str]] = set()

        for h4_position in range(30, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            inside_day = self._inside_day_at_timestamp(d1, timestamp)
            if inside_day is None:
                continue

            setup = self._setup_at_position(h4, h4_position, inside_day)
            if setup is None:
                continue

            inside_key = (int(setup["inside_d1_index"]), str(setup["direction"]))
            if inside_key in used_inside_days:
                continue
            used_inside_days.add(inside_key)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"D1_INSIDE_DAY_BREAKOUT_V0_{direction}",
                    metadata={**setup, "h4_index": int(h4_position)},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = float(signal.metadata["inside_day_low"]) - 0.25 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["inside_day_high"]) + 0.25 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported D1 inside-day breakout direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid D1 inside-day breakout v0 trade plan risk.")

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

    def _inside_day_at_timestamp(self, d1: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, Any] | None:
        d1_position = latest_completed_position(d1, timestamp)
        if d1_position is None or d1_position < 20:
            return None

        row = d1.iloc[d1_position]
        if not bool(row["is_inside_day"]):
            return None

        d1_timestamp = pd.Timestamp(row["timestamp_utc"])
        if d1_timestamp.tzinfo is None:
            d1_timestamp = d1_timestamp.tz_localize("UTC")
        timestamp = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
        hours_after_close = (timestamp - d1_timestamp).total_seconds() / 3600.0
        if hours_after_close <= 0 or hours_after_close > 48:
            return None

        required = (
            row["high"],
            row["low"],
            row["inside_mother_high"],
            row["inside_mother_low"],
            row["inside_mother_range"],
            row["inside_day_range"],
            row["atr14"],
        )
        if not value_available(*required):
            return None

        return {
            "inside_d1_index": int(d1_position),
            "inside_day_timestamp": d1_timestamp.isoformat(),
            "hours_after_inside_day_close": hours_after_close,
            "inside_day_high": float(row["high"]),
            "inside_day_low": float(row["low"]),
            "mother_high": float(row["inside_mother_high"]),
            "mother_low": float(row["inside_mother_low"]),
            "mother_range": float(row["inside_mother_range"]),
            "inside_day_range": float(row["inside_day_range"]),
            "d1_atr14": float(row["atr14"]),
        }

    def _setup_at_position(
        self,
        h4: pd.DataFrame,
        h4_position: int,
        inside_day: dict[str, Any],
    ) -> dict[str, Any] | None:
        row = h4.iloc[h4_position]
        required = (row["open"], row["high"], row["low"], row["close"], row["atr14"])
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["atr14"])
        if h4_atr <= 0:
            return None

        candle_range = high - low
        if candle_range <= 0 or candle_range > 3.0 * h4_atr:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.35:
            return None

        mother_high = float(inside_day["mother_high"])
        mother_low = float(inside_day["mother_low"])

        if close >= mother_high + 0.05 * h4_atr and close > open_price and close_position >= 0.65:
            return {
                **inside_day,
                "direction": "LONG",
                "h4_atr14": h4_atr,
                "breakout_high": high,
                "breakout_low": low,
                "estimated_entry_price": close,
                "breakout_body_ratio": body_ratio,
                "breakout_close_position": close_position,
            }

        if close <= mother_low - 0.05 * h4_atr and close < open_price and close_position <= 0.35:
            return {
                **inside_day,
                "direction": "SHORT",
                "h4_atr14": h4_atr,
                "breakout_high": high,
                "breakout_low": low,
                "estimated_entry_price": close,
                "breakout_body_ratio": body_ratio,
                "breakout_close_position": close_position,
            }

        return None

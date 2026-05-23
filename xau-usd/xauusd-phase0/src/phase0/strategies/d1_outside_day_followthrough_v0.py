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


class D1OutsideDayFollowthroughV0Strategy(StrategyBase):
    """Disabled research strategy for the locked D1 outside-day follow-through v0 hypothesis."""

    name = "d1_outside_day_followthrough_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        if "atr14" not in h4:
            h4["atr14"] = atr(h4["high"], h4["low"], h4["close"], 14)
        if "atr14" not in d1:
            d1["atr14"] = atr(d1["high"], d1["low"], d1["close"], 14)

        d1_open = pd.to_numeric(d1["open"], errors="coerce")
        d1_high = pd.to_numeric(d1["high"], errors="coerce")
        d1_low = pd.to_numeric(d1["low"], errors="coerce")
        d1_close = pd.to_numeric(d1["close"], errors="coerce")
        d1_range = d1_high - d1_low
        d1_body = (d1_close - d1_open).abs()
        d1_close_position = (d1_close - d1_low) / d1_range.replace(0.0, pd.NA)
        prev_high = d1_high.shift(1)
        prev_low = d1_low.shift(1)

        d1["outside_day_range"] = d1_range
        d1["outside_day_body"] = d1_body
        d1["outside_day_close_position"] = d1_close_position
        d1["is_outside_day"] = (
            (d1_high >= prev_high)
            & (d1_low <= prev_low)
            & (d1_range >= 1.00 * pd.to_numeric(d1["atr14"], errors="coerce"))
            & (d1_body >= 0.35 * d1_range)
        )
        d1["outside_direction"] = pd.NA
        d1.loc[
            d1["is_outside_day"] & (d1_close > d1_open) & (d1_close_position >= 0.70),
            "outside_direction",
        ] = "LONG"
        d1.loc[
            d1["is_outside_day"] & (d1_close < d1_open) & (d1_close_position <= 0.30),
            "outside_direction",
        ] = "SHORT"

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
        used_outside_days: set[int] = set()

        for h4_position in range(30, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            outside_day = self._outside_day_at_timestamp(d1, timestamp)
            if outside_day is None:
                continue
            outside_key = int(outside_day["outside_d1_index"])
            if outside_key in used_outside_days:
                continue

            setup = self._setup_at_position(h4, h4_position, outside_day)
            if setup is None:
                continue

            used_outside_days.add(outside_key)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"D1_OUTSIDE_DAY_FOLLOWTHROUGH_V0_{direction}",
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
            stop_loss = float(signal.metadata["confirmation_low"]) - 0.25 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["confirmation_high"]) + 0.25 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported D1 outside-day follow-through direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid D1 outside-day follow-through v0 trade plan risk.")

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

    def _outside_day_at_timestamp(self, d1: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, Any] | None:
        d1_position = latest_completed_position(d1, timestamp)
        if d1_position is None or d1_position < 20:
            return None

        row = d1.iloc[d1_position]
        if not bool(row["is_outside_day"]) or not value_available(row["outside_direction"]):
            return None

        d1_timestamp = pd.Timestamp(row["timestamp_utc"])
        if d1_timestamp.tzinfo is None:
            d1_timestamp = d1_timestamp.tz_localize("UTC")
        timestamp = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
        hours_after_close = (timestamp - d1_timestamp).total_seconds() / 3600.0
        if hours_after_close <= 0 or hours_after_close > 24:
            return None

        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["outside_day_range"],
            row["outside_day_body"],
            row["outside_day_close_position"],
        )
        if not value_available(*required):
            return None

        return {
            "outside_d1_index": int(d1_position),
            "outside_day_timestamp": d1_timestamp.isoformat(),
            "hours_after_outside_day_close": hours_after_close,
            "direction": str(row["outside_direction"]),
            "outside_day_open": float(row["open"]),
            "outside_day_high": float(row["high"]),
            "outside_day_low": float(row["low"]),
            "outside_day_close": float(row["close"]),
            "d1_atr14": float(row["atr14"]),
            "outside_day_range": float(row["outside_day_range"]),
            "outside_day_body": float(row["outside_day_body"]),
            "outside_day_close_position": float(row["outside_day_close_position"]),
        }

    def _setup_at_position(
        self,
        h4: pd.DataFrame,
        h4_position: int,
        outside_day: dict[str, Any],
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
        if body_ratio < 0.30:
            return None

        direction = str(outside_day["direction"])
        outside_close = float(outside_day["outside_day_close"])
        if (
            direction == "LONG"
            and close >= outside_close + 0.05 * h4_atr
            and close > open_price
            and close_position >= 0.60
        ):
            return {
                **outside_day,
                "h4_atr14": h4_atr,
                "confirmation_high": high,
                "confirmation_low": low,
                "estimated_entry_price": close,
                "confirmation_body_ratio": body_ratio,
                "confirmation_close_position": close_position,
            }

        if (
            direction == "SHORT"
            and close <= outside_close - 0.05 * h4_atr
            and close < open_price
            and close_position <= 0.40
        ):
            return {
                **outside_day,
                "h4_atr14": h4_atr,
                "confirmation_high": high,
                "confirmation_low": low,
                "estimated_entry_price": close,
                "confirmation_body_ratio": body_ratio,
                "confirmation_close_position": close_position,
            }

        return None

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


class D1VolatilityExpansionReversalV0Strategy(StrategyBase):
    """Disabled research strategy for the locked D1 volatility expansion reversal v0 hypothesis."""

    name = "d1_volatility_expansion_reversal_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        if "atr14" not in h4:
            h4["atr14"] = atr(h4["high"], h4["low"], h4["close"], 14)
        if "atr14" not in d1:
            d1["atr14"] = atr(d1["high"], d1["low"], d1["close"], 14)
        if "range" not in d1:
            d1["range"] = pd.to_numeric(d1["high"], errors="coerce") - pd.to_numeric(
                d1["low"], errors="coerce"
            )
        if "body" not in d1:
            d1["body"] = (
                pd.to_numeric(d1["close"], errors="coerce")
                - pd.to_numeric(d1["open"], errors="coerce")
            ).abs()
        if "close_position" not in d1:
            d1_range = pd.to_numeric(d1["range"], errors="coerce").replace(0.0, pd.NA)
            d1["close_position"] = (
                pd.to_numeric(d1["close"], errors="coerce") - pd.to_numeric(d1["low"], errors="coerce")
            ) / d1_range
        if "momentum3" not in d1:
            d1["momentum3"] = pd.to_numeric(d1["close"], errors="coerce") - pd.to_numeric(
                d1["close"], errors="coerce"
            ).shift(3)

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
        used_expansions: set[tuple[int, str]] = set()

        for h4_position in range(30, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            expansion = self._d1_expansion_at_timestamp(d1, timestamp)
            if expansion is None:
                continue

            expansion_key = (int(expansion["d1_index"]), str(expansion["direction"]))
            if expansion_key in used_expansions:
                continue

            setup = self._setup_at_position(h4, h4_position, expansion)
            if setup is None:
                continue

            used_expansions.add(expansion_key)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"D1_VOL_EXPANSION_REVERSAL_V0_{direction}",
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
            stop_loss = float(signal.metadata["reversal_low"]) - 0.30 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.75 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["reversal_high"]) + 0.30 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.75 * risk_price
        else:
            raise ConfigError(f"Unsupported D1 volatility expansion reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid D1 volatility expansion reversal v0 trade plan risk.")

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
            risk_reward=1.75,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry},
        )

    def _d1_expansion_at_timestamp(self, d1: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, Any] | None:
        d1_position = latest_completed_position(d1, timestamp)
        if d1_position is None or d1_position < 20:
            return None

        row = d1.iloc[d1_position]
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
            row["range"],
            row["body"],
            row["close_position"],
            row["momentum3"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        d1_atr = float(row["atr14"])
        d1_range = float(row["range"])
        body = float(row["body"])
        close_position = float(row["close_position"])
        momentum3 = float(row["momentum3"])
        if d1_atr <= 0 or d1_range <= 0:
            return None

        range_expanded = d1_range >= 1.25 * d1_atr
        body_expanded = body >= 0.55 * d1_range
        if not range_expanded or not body_expanded:
            return None

        if close > open_price and close_position >= 0.75 and momentum3 >= 0.75 * d1_atr:
            return {
                "direction": "SHORT",
                "expansion_direction": "UP",
                "d1_index": int(d1_position),
                "d1_close_timestamp": d1_timestamp.isoformat(),
                "hours_after_d1_close": hours_after_close,
                "d1_atr14": d1_atr,
                "d1_range": d1_range,
                "d1_body": body,
                "d1_close_position": close_position,
                "d1_momentum3": momentum3,
            }

        if close < open_price and close_position <= 0.25 and momentum3 <= -0.75 * d1_atr:
            return {
                "direction": "LONG",
                "expansion_direction": "DOWN",
                "d1_index": int(d1_position),
                "d1_close_timestamp": d1_timestamp.isoformat(),
                "hours_after_d1_close": hours_after_close,
                "d1_atr14": d1_atr,
                "d1_range": d1_range,
                "d1_body": body,
                "d1_close_position": close_position,
                "d1_momentum3": momentum3,
            }

        return None

    def _setup_at_position(
        self,
        h4: pd.DataFrame,
        h4_position: int,
        expansion: dict[str, Any],
    ) -> dict[str, Any] | None:
        row = h4.iloc[h4_position]
        h4_atr_raw = row["atr14"]
        if not value_available(h4_atr_raw):
            return None

        h4_atr = float(h4_atr_raw)
        if h4_atr <= 0:
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None

        body = abs(close - open_price)
        body_ratio = body / candle_range
        close_position = (close - low) / candle_range
        upper_wick_ratio = (high - max(open_price, close)) / candle_range
        lower_wick_ratio = (min(open_price, close) - low) / candle_range
        if body_ratio < 0.25:
            return None

        direction = str(expansion["direction"])
        if direction == "SHORT":
            if close < open_price and close_position <= 0.35 and upper_wick_ratio >= 0.20:
                return {
                    **expansion,
                    "direction": "SHORT",
                    "h4_atr14": h4_atr,
                    "reversal_high": high,
                    "reversal_low": low,
                    "estimated_entry_price": close,
                    "reversal_body_ratio": body_ratio,
                    "reversal_close_position": close_position,
                    "reversal_upper_wick_ratio": upper_wick_ratio,
                    "reversal_lower_wick_ratio": lower_wick_ratio,
                }

        if direction == "LONG":
            if close > open_price and close_position >= 0.65 and lower_wick_ratio >= 0.20:
                return {
                    **expansion,
                    "direction": "LONG",
                    "h4_atr14": h4_atr,
                    "reversal_high": high,
                    "reversal_low": low,
                    "estimated_entry_price": close,
                    "reversal_body_ratio": body_ratio,
                    "reversal_close_position": close_position,
                    "reversal_upper_wick_ratio": upper_wick_ratio,
                    "reversal_lower_wick_ratio": lower_wick_ratio,
                }

        return None

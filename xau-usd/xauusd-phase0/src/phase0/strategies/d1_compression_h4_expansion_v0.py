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


class D1CompressionH4ExpansionV0Strategy(StrategyBase):
    """Disabled research strategy for the locked D1 compression / H4 expansion v0 hypothesis."""

    name = "d1_compression_h4_expansion_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        if "atr14" not in h4:
            h4["atr14"] = atr(h4["high"], h4["low"], h4["close"], 14)
        if "range" not in h4:
            h4["range"] = pd.to_numeric(h4["high"], errors="coerce") - pd.to_numeric(
                h4["low"], errors="coerce"
            )
        if "body" not in h4:
            h4["body"] = (
                pd.to_numeric(h4["close"], errors="coerce")
                - pd.to_numeric(h4["open"], errors="coerce")
            ).abs()
        if "close_position" not in h4:
            h4_range = pd.to_numeric(h4["range"], errors="coerce").replace(0.0, pd.NA)
            h4["close_position"] = (
                pd.to_numeric(h4["close"], errors="coerce") - pd.to_numeric(h4["low"], errors="coerce")
            ) / h4_range

        if "atr14" not in d1:
            d1["atr14"] = atr(d1["high"], d1["low"], d1["close"], 14)
        if "range" not in d1:
            d1["range"] = pd.to_numeric(d1["high"], errors="coerce") - pd.to_numeric(
                d1["low"], errors="coerce"
            )
        if "range5_width" not in d1:
            d1_high = pd.to_numeric(d1["high"], errors="coerce")
            d1_low = pd.to_numeric(d1["low"], errors="coerce")
            d1["range5_width"] = d1_high.rolling(5, min_periods=5).max() - d1_low.rolling(
                5, min_periods=5
            ).min()
        if "range20_median_width" not in d1:
            d1["range20_median_width"] = d1["range5_width"].shift(1).rolling(
                20, min_periods=20
            ).median()
        if "atr20_median" not in d1:
            d1["atr20_median"] = d1["atr14"].shift(1).rolling(20, min_periods=20).median()

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
        used_compressions: set[tuple[int, str]] = set()

        for h4_position in range(30, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            compression = self._d1_compression_at_timestamp(d1, timestamp)
            if compression is None:
                continue

            setup = self._setup_at_position(h4, h4_position, compression)
            if setup is None:
                continue

            compression_key = (int(setup["d1_index"]), str(setup["direction"]))
            if compression_key in used_compressions:
                continue
            used_compressions.add(compression_key)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"D1_COMPRESSION_H4_EXPANSION_V0_{direction}",
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
            stop_loss = float(signal.metadata["expansion_low"]) - 0.25 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.75 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["expansion_high"]) + 0.25 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.75 * risk_price
        else:
            raise ConfigError(f"Unsupported D1 compression H4 expansion direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid D1 compression H4 expansion v0 trade plan risk.")

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

    def _d1_compression_at_timestamp(self, d1: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, Any] | None:
        d1_position = latest_completed_position(d1, timestamp)
        if d1_position is None or d1_position < 30:
            return None

        row = d1.iloc[d1_position]
        required = (
            row["atr14"],
            row["range5_width"],
            row["range20_median_width"],
            row["atr20_median"],
        )
        if not value_available(*required):
            return None

        d1_atr = float(row["atr14"])
        range5_width = float(row["range5_width"])
        range20_median_width = float(row["range20_median_width"])
        atr20_median = float(row["atr20_median"])
        if d1_atr <= 0 or range5_width <= 0 or range20_median_width <= 0 or atr20_median <= 0:
            return None

        compression_ratio = range5_width / range20_median_width
        atr_ratio = d1_atr / atr20_median
        if compression_ratio > 0.85 or atr_ratio > 1.05:
            return None

        return {
            "d1_index": int(d1_position),
            "d1_close_timestamp": pd.Timestamp(row["timestamp_utc"]).isoformat(),
            "d1_atr14": d1_atr,
            "d1_range5_width": range5_width,
            "d1_range20_median_width": range20_median_width,
            "d1_atr20_median": atr20_median,
            "d1_compression_ratio": compression_ratio,
            "d1_atr_ratio": atr_ratio,
        }

    def _setup_at_position(
        self,
        h4: pd.DataFrame,
        h4_position: int,
        compression: dict[str, Any],
    ) -> dict[str, Any] | None:
        row = h4.iloc[h4_position]
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["range"],
            row["body"],
            row["close_position"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["atr14"])
        candle_range = float(row["range"])
        body = float(row["body"])
        close_position = float(row["close_position"])
        if h4_atr <= 0 or candle_range <= 0:
            return None

        body_ratio = body / candle_range
        if candle_range < 1.35 * h4_atr or body_ratio < 0.55:
            return None

        if close > open_price and close_position >= 0.75:
            return {
                **compression,
                "direction": "LONG",
                "h4_atr14": h4_atr,
                "expansion_high": high,
                "expansion_low": low,
                "estimated_entry_price": close,
                "expansion_range": candle_range,
                "expansion_body_ratio": body_ratio,
                "expansion_close_position": close_position,
            }

        if close < open_price and close_position <= 0.25:
            return {
                **compression,
                "direction": "SHORT",
                "h4_atr14": h4_atr,
                "expansion_high": high,
                "expansion_low": low,
                "estimated_entry_price": close,
                "expansion_range": candle_range,
                "expansion_body_ratio": body_ratio,
                "expansion_close_position": close_position,
            }

        return None

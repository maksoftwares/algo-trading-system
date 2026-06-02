from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import (
    StrategyBase,
    context_point_size,
    context_symbol,
    copy_context,
    latest_completed_position,
    require_frame,
    value_available,
)


class H4D1VolatilityContractionExpansionV0Strategy(StrategyBase):
    """Disabled research strategy for the locked H4/D1 volatility contraction expansion v0 hypothesis."""

    name = "h4_d1_volatility_contraction_expansion_v0"
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
        if "close_position" not in h4:
            h4_range = pd.to_numeric(h4["range"], errors="coerce").replace(0.0, pd.NA)
            h4["close_position"] = (
                pd.to_numeric(h4["close"], errors="coerce") - pd.to_numeric(h4["low"], errors="coerce")
            ) / h4_range

        if "atr14" not in d1:
            d1["atr14"] = atr(d1["high"], d1["low"], d1["close"], 14)
        if "range3_width" not in d1:
            d1_high = pd.to_numeric(d1["high"], errors="coerce")
            d1_low = pd.to_numeric(d1["low"], errors="coerce")
            d1["range3_width"] = d1_high.rolling(3, min_periods=3).max() - d1_low.rolling(
                3, min_periods=3
            ).min()
        if "prior60_atr35" not in d1:
            d1["prior60_atr35"] = d1["atr14"].shift(1).rolling(60, min_periods=60).quantile(0.35)
        if "prior40_range3_median" not in d1:
            d1["prior40_range3_median"] = d1["range3_width"].shift(1).rolling(
                40, min_periods=40
            ).median()

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
        point_size = context_point_size(context)
        signals: list[Signal] = []
        used_contraction_states: set[tuple[int, str]] = set()

        for h4_position in range(30, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            contraction = self._d1_contraction_at_timestamp(d1, timestamp)
            if contraction is None:
                continue

            setup = self._setup_at_position(h4, h4_position, contraction, point_size)
            if setup is None:
                continue

            contraction_key = (int(setup["d1_index"]), str(setup["direction"]))
            if contraction_key in used_contraction_states:
                continue
            used_contraction_states.add(contraction_key)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_D1_VOLATILITY_CONTRACTION_EXPANSION_V0_{direction}",
                    metadata={**setup, "h4_index": int(h4_position)},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        point_size = context_point_size(data_context)
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = float(signal.metadata["expansion_low"]) - 0.35 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.60 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["expansion_high"]) + 0.35 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.60 * risk_price
        else:
            raise ConfigError(f"Unsupported H4/D1 volatility expansion direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4/D1 volatility contraction expansion v0 trade plan risk.")
        if risk_price / point_size < 300.0:
            raise ConfigError("H4/D1 volatility contraction expansion v0 stop is below 300 points.")

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
            risk_reward=1.60,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry},
        )

    def _d1_contraction_at_timestamp(self, d1: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, Any] | None:
        d1_position = latest_completed_position(d1, timestamp)
        if d1_position is None or d1_position < 65:
            return None

        row = d1.iloc[d1_position]
        required = (
            row["atr14"],
            row["range3_width"],
            row["prior60_atr35"],
            row["prior40_range3_median"],
        )
        if not value_available(*required):
            return None

        d1_atr = float(row["atr14"])
        range3_width = float(row["range3_width"])
        prior60_atr35 = float(row["prior60_atr35"])
        prior40_range3_median = float(row["prior40_range3_median"])
        if d1_atr <= 0 or range3_width <= 0 or prior60_atr35 <= 0 or prior40_range3_median <= 0:
            return None
        if d1_atr > prior60_atr35:
            return None
        if range3_width >= prior40_range3_median:
            return None

        return {
            "d1_index": int(d1_position),
            "d1_close_timestamp": pd.Timestamp(row["timestamp_utc"]).isoformat(),
            "d1_atr14": d1_atr,
            "d1_prior60_atr35": prior60_atr35,
            "d1_range3_width": range3_width,
            "d1_prior40_range3_median": prior40_range3_median,
            "d1_atr_percentile_gate": 0.35,
        }

    def _setup_at_position(
        self,
        h4: pd.DataFrame,
        h4_position: int,
        contraction: dict[str, Any],
        point_size: float,
    ) -> dict[str, Any] | None:
        row = h4.iloc[h4_position]
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["range"],
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
        close_position = float(row["close_position"])
        if h4_atr <= 0 or candle_range <= 0:
            return None
        if candle_range < 1.20 * h4_atr:
            return None

        if close > open_price and close_position >= 0.70:
            stop_loss = low - 0.35 * h4_atr
            stop_distance_points = (close - stop_loss) / point_size
            if stop_distance_points < 300.0:
                return None
            return {
                **contraction,
                "direction": "LONG",
                "h4_atr14": h4_atr,
                "expansion_high": high,
                "expansion_low": low,
                "estimated_entry_price": close,
                "expansion_range": candle_range,
                "expansion_close_position": close_position,
                "stop_distance_points": stop_distance_points,
            }

        if close < open_price and close_position <= 0.30:
            stop_loss = high + 0.35 * h4_atr
            stop_distance_points = (stop_loss - close) / point_size
            if stop_distance_points < 300.0:
                return None
            return {
                **contraction,
                "direction": "SHORT",
                "h4_atr14": h4_atr,
                "expansion_high": high,
                "expansion_low": low,
                "estimated_entry_price": close,
                "expansion_range": candle_range,
                "expansion_close_position": close_position,
                "stop_distance_points": stop_distance_points,
            }

        return None

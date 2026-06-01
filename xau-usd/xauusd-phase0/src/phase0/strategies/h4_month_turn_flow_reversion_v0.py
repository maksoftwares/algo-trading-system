from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H4MonthTurnFlowReversionV0Strategy(StrategyBase):
    """Research-only H4 month-turn flow unwind/reversion candidate."""

    name = "h4_month_turn_flow_reversion_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_ema80"] = ema(close, 80)
        h4["h4_return_3"] = np.log(close / close.shift(3))
        h4["h4_return_6"] = np.log(close / close.shift(6))
        h4["h4_return_12"] = np.log(close / close.shift(12))
        timestamps = pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce")
        h4["month_day"] = timestamps.dt.day
        h4["month_turn_window"] = (h4["month_day"] <= 4) | (h4["month_day"] >= 25)
        context["H4"] = h4
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(120, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            signal_day = timestamp.strftime("%Y-%m-%d")
            direction = str(setup["direction"])
            key = (signal_day, direction)
            if key in used_day_direction:
                continue
            used_day_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_MONTH_TURN_FLOW_REVERSION_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_day": signal_day},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.10 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.10 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H4 month-turn flow reversion direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4 month-turn flow reversion trade plan risk.")

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
            risk_reward=self.risk_reward,
            reason_code=signal.reason_code,
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 576,
                "planned_time_stop_h4_bars": 12,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_ema80"],
            row["h4_return_3"],
            row["h4_return_6"],
            row["h4_return_12"],
            row["month_day"],
            row["month_turn_window"],
        )
        if not value_available(*required) or not bool(row["month_turn_window"]):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        ema40_value = float(row["h4_ema40"])
        ema80_value = float(row["h4_ema80"])
        h4_return_3 = float(row["h4_return_3"])
        h4_return_6 = float(row["h4_return_6"])
        h4_return_12 = float(row["h4_return_12"])
        month_day = int(row["month_day"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - ema40_value) / h4_atr
        ema80_distance_atr = (close - ema80_value) / h4_atr

        if (
            h4_return_6 <= -0.0040
            and h4_return_3 >= -0.0015
            and h4_return_12 >= -0.0550
            and ema40_distance_atr >= -2.75
            and ema80_distance_atr >= -3.50
            and close > open_price
            and close_location >= 0.58
        ):
            return _setup_metadata(
                row,
                "LONG",
                close,
                close_location,
                ema40_distance_atr,
                ema80_distance_atr,
                month_day,
            )

        if (
            h4_return_6 >= 0.0040
            and h4_return_3 <= 0.0015
            and h4_return_12 <= 0.0550
            and ema40_distance_atr <= 2.75
            and ema80_distance_atr <= 3.50
            and close < open_price
            and close_location <= 0.42
        ):
            return _setup_metadata(
                row,
                "SHORT",
                close,
                close_location,
                ema40_distance_atr,
                ema80_distance_atr,
                month_day,
            )

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema40_distance_atr: float,
    ema80_distance_atr: float,
    month_day: int,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_ema80": float(row["h4_ema80"]),
        "h4_return_3": float(row["h4_return_3"]),
        "h4_return_6": float(row["h4_return_6"]),
        "h4_return_12": float(row["h4_return_12"]),
        "close_location": float(close_location),
        "ema40_distance_atr": float(ema40_distance_atr),
        "ema80_distance_atr": float(ema80_distance_atr),
        "month_day": month_day,
        "month_turn_window": bool(row["month_turn_window"]),
    }

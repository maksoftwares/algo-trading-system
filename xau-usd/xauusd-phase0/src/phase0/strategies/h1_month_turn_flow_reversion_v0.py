from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H1MonthTurnFlowReversionV0Strategy(StrategyBase):
    """Research-only month-turn flow unwind/reversion candidate."""

    name = "h1_month_turn_flow_reversion_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.35
    decision_hours_utc = {7, 11, 15, 19}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["h1_ema21"] = ema(close, 21)
        h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_6"] = np.log(close / close.shift(6))
        h1["h1_return_24"] = np.log(close / close.shift(24))
        timestamps = pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce")
        h1["month_day"] = timestamps.dt.day
        h1["month_turn_window"] = (h1["month_day"] <= 4) | (h1["month_day"] >= 25)
        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(80, len(h1)):
            row = h1.iloc[position]
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
                    reason_code=f"H1_MONTH_TURN_FLOW_REVERSION_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": signal_day},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["h1_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 0.95 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 0.95 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported month-turn flow reversion direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid month-turn flow reversion trade plan risk.")

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
                "max_holding_bars": 96,
                "planned_time_stop_h1_bars": 8,
            },
        )

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
            row["h1_return_24"],
            row["month_day"],
            row["month_turn_window"],
        )
        if not value_available(*required) or not bool(row["month_turn_window"]):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        ema21_value = float(row["h1_ema21"])
        ema50_value = float(row["h1_ema50"])
        h1_return_6 = float(row["h1_return_6"])
        h1_return_24 = float(row["h1_return_24"])
        month_day = int(row["month_day"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        ema21_distance_atr = (close - ema21_value) / h1_atr
        ema50_distance_atr = (close - ema50_value) / h1_atr

        if (
            h1_return_24 <= -0.0030
            and h1_return_6 <= -0.0010
            and ema21_distance_atr <= -0.25
            and ema50_distance_atr >= -2.75
            and close < open_price
            and close_location <= 0.38
        ):
            return _setup_metadata(
                row,
                "LONG",
                close,
                close_location,
                ema21_distance_atr,
                ema50_distance_atr,
                month_day,
            )

        if (
            h1_return_24 >= 0.0030
            and h1_return_6 >= 0.0010
            and ema21_distance_atr >= 0.25
            and ema50_distance_atr <= 2.75
            and close > open_price
            and close_location >= 0.62
        ):
            return _setup_metadata(
                row,
                "SHORT",
                close,
                close_location,
                ema21_distance_atr,
                ema50_distance_atr,
                month_day,
            )

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema21_distance_atr: float,
    ema50_distance_atr: float,
    month_day: int,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema21": float(row["h1_ema21"]),
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_6": float(row["h1_return_6"]),
        "h1_return_24": float(row["h1_return_24"]),
        "close_location": close_location,
        "ema21_distance_atr": ema21_distance_atr,
        "ema50_distance_atr": ema50_distance_atr,
        "month_day": month_day,
        "month_turn_window": bool(row["month_turn_window"]),
    }

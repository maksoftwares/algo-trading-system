from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.macro_real_yield_data import MACRO_FRAME_KEY
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)
from phase0.strategies.h4_real_yield_proxy_momentum_v0 import _macro_features_for_h4


class H4RealYieldDollarStressReversalV0Strategy(StrategyBase):
    """Research-only H4 reversal candidate after real-yield and dollar stress."""

    name = "h4_real_yield_dollar_stress_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.65

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        macro = data_context.get(MACRO_FRAME_KEY)
        if not isinstance(macro, pd.DataFrame):
            raise ConfigError(
                "h4_real_yield_dollar_stress_reversal_v0 requires data_context['macro_proxy'] "
                "with FRED DFII10 and DTWEXBGS observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))
        h4["h4_return_12"] = np.log(close / close.shift(12))
        h4["h4_return_24"] = np.log(close / close.shift(24))

        macro_features = _macro_features_for_h4(h4, macro)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                macro_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
        )
        context["H4"] = h4
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_week_direction: set[tuple[str, str]] = set()

        for position in range(180, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            iso = timestamp.isocalendar()
            direction = str(setup["direction"])
            week_direction = (f"{iso.year}-W{iso.week:02d}", direction)
            if week_direction in used_week_direction:
                continue
            used_week_direction.add(week_direction)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_REAL_YIELD_DOLLAR_STRESS_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_week": week_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.25 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.25 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H4 real-yield stress direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4 real-yield stress reversal trade plan risk.")

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
                "max_holding_bars": 384,
                "planned_time_stop_h4_bars": 8,
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
            row["h4_return_6"],
            row["h4_return_12"],
            row["h4_return_24"],
            row["real_yield_change_20d"],
            row["dollar_return_20d"],
            row["real_yield_change_z252"],
            row["dollar_return_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        h4_return_12 = float(row["h4_return_12"])
        h4_return_24 = float(row["h4_return_24"])
        real_yield_change_20d = float(row["real_yield_change_20d"])
        dollar_return_20d = float(row["dollar_return_20d"])
        real_yield_z = float(row["real_yield_change_z252"])
        dollar_z = float(row["dollar_return_z252"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - h4_ema40) / h4_atr

        macro_bearish_gold = (
            real_yield_change_20d >= 0.16
            and dollar_return_20d >= 0.0050
            and max(real_yield_z, dollar_z) >= 0.50
        )
        macro_bullish_gold = (
            real_yield_change_20d <= -0.16
            and dollar_return_20d <= -0.0050
            and min(real_yield_z, dollar_z) <= -0.50
        )

        if (
            macro_bearish_gold
            and h4_return_12 <= -0.0050
            and h4_return_24 >= -0.0450
            and h4_return_6 <= 0.0010
            and close > open_price
            and close_location >= 0.60
            and ema40_distance_atr >= -2.50
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema40_distance_atr)

        if (
            macro_bullish_gold
            and h4_return_12 >= 0.0050
            and h4_return_24 <= 0.0450
            and h4_return_6 >= -0.0010
            and close < open_price
            and close_location <= 0.40
            and ema40_distance_atr <= 2.50
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema40_distance_atr)

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema40_distance_atr: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_6": float(row["h4_return_6"]),
        "h4_return_12": float(row["h4_return_12"]),
        "h4_return_24": float(row["h4_return_24"]),
        "close_location": close_location,
        "ema40_distance_atr": ema40_distance_atr,
        "real_yield_10y": float(row["real_yield_10y"]),
        "dollar_index_broad": float(row["dollar_index_broad"]),
        "real_yield_change_20d": float(row["real_yield_change_20d"]),
        "dollar_return_20d": float(row["dollar_return_20d"]),
        "real_yield_change_z252": float(row["real_yield_change_z252"]),
        "dollar_return_z252": float(row["dollar_return_z252"]),
    }

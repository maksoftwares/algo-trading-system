from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h4_macro_composite_risk_state_v0 import (
    _macro_features_for_h4,
    _require_macro_inputs,
)


class H1MacroCompositeStateReversionV0Strategy(StrategyBase):
    """Research-only H1 exhaustion reversion under fixed macro composite extremes."""

    name = "h1_macro_composite_state_reversion_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.35
    decision_hours_utc = {7, 9, 11, 13, 15, 17, 19, 21}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        macro_inputs = _require_macro_inputs(data_context)

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["h1_ema21"] = ema(close, 21)
        h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_6"] = np.log(close / close.shift(6))
        h1["h1_return_12"] = np.log(close / close.shift(12))
        h1["h1_return_24"] = np.log(close / close.shift(24))

        macro_features = _macro_features_for_h4(h1, macro_inputs)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                macro_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
        )
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

        for position in range(140, len(h1)):
            row = h1.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            direction = str(setup["direction"])
            key = (timestamp.strftime("%Y-%m-%d"), direction)
            if key in used_day_direction:
                continue
            used_day_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_MACRO_COMPOSITE_STATE_REVERSION_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["h1_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.00 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.00 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H1 macro state reversion direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 macro state reversion trade plan risk.")

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
            row["h1_ema50"],
            row["h1_return_6"],
            row["h1_return_12"],
            row["h1_return_24"],
            row["macro_composite_score"],
            row["macro_bull_votes"],
            row["macro_bear_votes"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        ema50 = float(row["h1_ema50"])
        h1_return_6 = float(row["h1_return_6"])
        h1_return_12 = float(row["h1_return_12"])
        h1_return_24 = float(row["h1_return_24"])
        composite_score = float(row["macro_composite_score"])
        bull_votes = float(row["macro_bull_votes"])
        bear_votes = float(row["macro_bear_votes"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        ema50_distance_atr = (close - ema50) / h1_atr

        if (
            composite_score >= 3.0
            and bull_votes >= 4.0
            and h1_return_24 >= 0.0040
            and h1_return_12 >= 0.0020
            and h1_return_6 >= -0.0005
            and 0.50 <= ema50_distance_atr <= 3.50
            and close < open_price
            and close_location <= 0.42
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema50_distance_atr)

        if (
            composite_score <= -3.0
            and bear_votes >= 4.0
            and h1_return_24 <= -0.0040
            and h1_return_12 <= -0.0020
            and h1_return_6 <= 0.0005
            and -3.50 <= ema50_distance_atr <= -0.50
            and close > open_price
            and close_location >= 0.58
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema50_distance_atr)

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema50_distance_atr: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema21": float(row["h1_ema21"]),
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_6": float(row["h1_return_6"]),
        "h1_return_12": float(row["h1_return_12"]),
        "h1_return_24": float(row["h1_return_24"]),
        "close_location": close_location,
        "ema50_distance_atr": ema50_distance_atr,
        "macro_bull_votes": int(row["macro_bull_votes"]),
        "macro_bear_votes": int(row["macro_bear_votes"]),
        "macro_composite_score": int(row["macro_composite_score"]),
        "real_yield_change_20d": float(row["real_yield_change_20d"]),
        "dollar_change_20d": float(row["dollar_change_20d"]),
        "breakeven_5y_change_20d": float(row["breakeven_5y_change_20d"]),
        "dgs2_change_20d": float(row["dgs2_change_20d"]),
        "treasury_10y2y_change_20d": float(row["treasury_10y2y_change_20d"]),
        "baa10y_change_20d": float(row["baa10y_change_20d"]),
        "vix_change_20d": float(row["vix_change_20d"]),
        "gvz_change_20d": float(row["gvz_change_20d"]),
        "nfci_change_4obs": float(row["nfci_change_4obs"]),
    }

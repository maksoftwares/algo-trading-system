from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h1_treasury_curve_shock_reversal_v0 import _treasury_features_for_h1
from phase0.treasury_curve_data import TREASURY_CURVE_FRAME_KEY


class H1TreasuryCurveShockFollowthroughV0Strategy(StrategyBase):
    """Research-only H1 Treasury curve/rates shock follow-through candidate."""

    name = "h1_treasury_curve_shock_followthrough_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.45
    decision_hours_utc = frozenset({7, 9, 11, 13, 15, 17, 19, 21})

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        treasury = data_context.get(TREASURY_CURVE_FRAME_KEY)
        if not isinstance(treasury, pd.DataFrame):
            raise ConfigError(
                "h1_treasury_curve_shock_followthrough_v0 requires "
                "data_context['treasury_curve'] with shifted FRED DGS2/DGS10/T10Y2Y observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_8"] = np.log(close / close.shift(8))
        h1["h1_return_24"] = np.log(close / close.shift(24))

        treasury_features = _treasury_features_for_h1(h1, treasury)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                treasury_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(100, len(h1)):
            row = h1.iloc[position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            if timestamp.hour not in self.decision_hours_utc:
                continue

            setup = self._setup_at_row(row)
            if setup is None:
                continue

            day_direction = (timestamp.strftime("%Y-%m-%d"), str(setup["direction"]))
            if day_direction in used_day_direction:
                continue
            used_day_direction.add(day_direction)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_TREASURY_CURVE_SHOCK_FOLLOWTHROUGH_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": day_direction[0]},
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
            raise ConfigError(f"Unsupported Treasury curve shock follow-through direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid Treasury curve shock follow-through trade plan risk.")

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
                "max_holding_bars": 216,
                "planned_time_stop_h1_bars": 18,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h1_atr14"],
            row["h1_ema50"],
            row["h1_return_8"],
            row["h1_return_24"],
            row["dgs2"],
            row["dgs10"],
            row["treasury_10y2y"],
            row["dgs2_change_10d"],
            row["dgs10_change_10d"],
            row["treasury_10y2y_change_10d"],
            row["dgs2_change_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema50 = float(row["h1_ema50"])
        h1_return_8 = float(row["h1_return_8"])
        h1_return_24 = float(row["h1_return_24"])
        dgs2_change = float(row["dgs2_change_10d"])
        dgs10_change = float(row["dgs10_change_10d"])
        curve_change = float(row["treasury_10y2y_change_10d"])
        dgs2_change_z = float(row["dgs2_change_z252"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        easing_shock = (
            dgs2_change <= -0.12 and dgs10_change <= -0.07 and curve_change >= 0.03
        ) or dgs2_change_z <= -0.75
        tightening_shock = (
            dgs2_change >= 0.12 and dgs10_change >= 0.07 and curve_change <= -0.03
        ) or dgs2_change_z >= 0.75

        if (
            easing_shock
            and h1_return_24 >= 0.004
            and h1_return_8 >= -0.001
            and close > open_price
            and close_location >= 0.58
            and close >= h1_ema50 * 0.985
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            tightening_shock
            and h1_return_24 <= -0.004
            and h1_return_8 <= 0.001
            and close < open_price
            and close_location <= 0.42
            and close <= h1_ema50 * 1.015
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_8": float(row["h1_return_8"]),
        "h1_return_24": float(row["h1_return_24"]),
        "close_location": close_location,
        "dgs2": float(row["dgs2"]),
        "dgs10": float(row["dgs10"]),
        "treasury_10y2y": float(row["treasury_10y2y"]),
        "dgs2_change_10d": float(row["dgs2_change_10d"]),
        "dgs10_change_10d": float(row["dgs10_change_10d"]),
        "treasury_10y2y_change_10d": float(row["treasury_10y2y_change_10d"]),
        "dgs2_change_z252": float(row["dgs2_change_z252"]),
    }

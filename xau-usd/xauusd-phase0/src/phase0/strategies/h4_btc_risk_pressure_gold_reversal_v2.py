from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.btc_risk_pressure_data import BTC_RISK_PRESSURE_FRAME_KEY
from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h4_btc_risk_pressure_gold_reversal_v0 import _btc_features_for_h4


class H4BtcRiskPressureGoldReversalV2Strategy(StrategyBase):
    """Research-only stricter H4 XAU reversal candidate after shifted BTC stress."""

    name = "h4_btc_risk_pressure_gold_reversal_v2"
    version = "0.1-research-disabled"

    risk_reward = 1.45
    pressure_threshold = 0.080
    pressure_z_threshold = 0.40
    pressure_percentile_threshold = 0.60
    pressure_volume_z_threshold = 0.00

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        btc = data_context.get(BTC_RISK_PRESSURE_FRAME_KEY)
        if not isinstance(btc, pd.DataFrame):
            raise ConfigError(
                "h4_btc_risk_pressure_gold_reversal_v2 requires "
                "data_context['btc_risk_pressure'] with shifted BTC-USD daily observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_3"] = np.log(close / close.shift(3))
        h4["h4_return_6"] = np.log(close / close.shift(6))

        btc_features = _btc_features_for_h4(h4, btc)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                btc_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(160, len(h4)):
            row = h4.iloc[position]
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
                    reason_code=f"H4_BTC_RISK_PRESSURE_GOLD_REVERSAL_V2_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_day": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.35 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.35 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported BTC H4 reversal v2 direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid BTC H4 reversal v2 trade plan risk.")

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
                "max_holding_bars": 288,
                "planned_time_stop_h4_bars": 6,
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
            row["h4_return_3"],
            row["h4_return_6"],
            row["btc_return_5d"],
            row["btc_return_20d"],
            row["btc_return_z126"],
            row["btc_abs_return_percentile252"],
            row["btc_volume_z126"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_3 = float(row["h4_return_3"])
        h4_return_6 = float(row["h4_return_6"])
        btc_return = float(row["btc_return_5d"])
        btc_z = float(row["btc_return_z126"])
        btc_percentile = float(row["btc_abs_return_percentile252"])
        btc_volume_z = float(row["btc_volume_z126"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - h4_ema40) / h4_atr

        pressure_active = (
            abs(btc_return) >= self.pressure_threshold
            and abs(btc_z) >= self.pressure_z_threshold
            and btc_percentile >= self.pressure_percentile_threshold
            and btc_volume_z >= self.pressure_volume_z_threshold
        )
        if not pressure_active:
            return None

        if (
            btc_return <= -self.pressure_threshold
            and h4_return_3 >= 0.0030
            and h4_return_6 <= 0.0575
            and close > h4_ema40
            and close < open_price
            and close_location <= 0.48
            and ema40_distance_atr <= 3.10
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema40_distance_atr)

        if (
            btc_return >= self.pressure_threshold
            and h4_return_3 <= -0.0030
            and h4_return_6 >= -0.0575
            and close < h4_ema40
            and close > open_price
            and close_location >= 0.52
            and ema40_distance_atr >= -3.10
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema40_distance_atr)

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
        "h4_return_3": float(row["h4_return_3"]),
        "h4_return_6": float(row["h4_return_6"]),
        "close_location": close_location,
        "ema40_distance_atr": ema40_distance_atr,
        "btc_close": float(row["btc_close"]),
        "btc_return_5d": float(row["btc_return_5d"]),
        "btc_return_20d": float(row["btc_return_20d"]),
        "btc_return_z126": float(row["btc_return_z126"]),
        "btc_abs_return_percentile252": float(row["btc_abs_return_percentile252"]),
        "btc_volume_z126": float(row["btc_volume_z126"]),
        "planned_time_stop_h4_bars": 6,
    }

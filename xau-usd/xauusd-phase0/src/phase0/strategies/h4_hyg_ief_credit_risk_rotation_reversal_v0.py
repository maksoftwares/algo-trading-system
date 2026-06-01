from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.hyg_ief_credit_risk_rotation_data import HYG_IEF_CREDIT_RISK_ROTATION_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h1_hyg_ief_credit_risk_rotation_followthrough_v0 import _credit_risk_features_for_h1


class H4HygIefCreditRiskRotationReversalV0Strategy(StrategyBase):
    """Research-only H4 XAU reversal candidate using HYG/IEF credit-risk rotation."""

    name = "h4_hyg_ief_credit_risk_rotation_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.55
    stress_threshold = 0.0060
    stress_z_threshold = 0.35
    stress_percentile_threshold = 0.55

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        rotation = data_context.get(HYG_IEF_CREDIT_RISK_ROTATION_FRAME_KEY)
        if not isinstance(rotation, pd.DataFrame):
            raise ConfigError(
                "h4_hyg_ief_credit_risk_rotation_reversal_v0 requires "
                "data_context['hyg_ief_credit_risk_rotation'] with shifted HYG/IEF daily observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))
        h4["h4_return_12"] = np.log(close / close.shift(12))
        h4["h4_return_24"] = np.log(close / close.shift(24))

        rotation_features = _credit_risk_features_for_h1(h4, rotation)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                rotation_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
            key = (f"{iso.year}-W{iso.week:02d}", direction)
            if key in used_week_direction:
                continue
            used_week_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_HYG_IEF_CREDIT_RISK_ROTATION_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_week": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.15 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.15 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported HYG/IEF H4 reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid HYG/IEF H4 reversal trade plan risk.")

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
                "max_holding_bars": 336,
                "planned_time_stop_h4_bars": 7,
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
            row["credit_stress_5d"],
            row["credit_stress_z126"],
            row["credit_stress_abs_percentile252"],
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
        stress = float(row["credit_stress_5d"])
        stress_z = float(row["credit_stress_z126"])
        stress_percentile = float(row["credit_stress_abs_percentile252"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - h4_ema40) / h4_atr
        stress_active = (
            abs(stress) >= self.stress_threshold
            and abs(stress_z) >= self.stress_z_threshold
            and stress_percentile >= self.stress_percentile_threshold
        )
        if not stress_active:
            return None

        if (
            stress >= self.stress_threshold
            and h4_return_12 <= -0.0045
            and h4_return_24 >= -0.0450
            and h4_return_6 <= 0.0010
            and close > open_price
            and close_location >= 0.60
            and ema40_distance_atr >= -2.50
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema40_distance_atr)

        if (
            stress <= -self.stress_threshold
            and h4_return_12 >= 0.0045
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
        "hyg_close": float(row["hyg_close"]),
        "ief_close": float(row["ief_close"]),
        "hyg_return_5d": float(row["hyg_return_5d"]),
        "ief_return_5d": float(row["ief_return_5d"]),
        "credit_stress_5d": float(row["credit_stress_5d"]),
        "credit_stress_z126": float(row["credit_stress_z126"]),
        "credit_stress_abs_percentile252": float(row["credit_stress_abs_percentile252"]),
        "hyg_volume_z126": float(row["hyg_volume_z126"]),
        "ief_volume_z126": float(row["ief_volume_z126"]),
    }

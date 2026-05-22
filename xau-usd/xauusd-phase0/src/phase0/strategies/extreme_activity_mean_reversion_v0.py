from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import (
    StrategyBase,
    context_point_size,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class ExtremeActivityMeanReversionV0Strategy(StrategyBase):
    """Disabled research strategy for the locked extreme activity mean-reversion v0 hypothesis."""

    name = "extreme_activity_mean_reversion_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        high = pd.to_numeric(m5["high"], errors="coerce")
        low = pd.to_numeric(m5["low"], errors="coerce")
        m5["m5_range"] = high - low
        m5["prior_96_high"] = high.shift(1).rolling(96, min_periods=96).max()
        m5["prior_96_low"] = low.shift(1).rolling(96, min_periods=96).min()
        context["M5"] = m5
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        symbol = context_symbol(context)
        point_size = context_point_size(context)
        signals: list[Signal] = []
        last_signal_position = -1000

        for m5_position in range(100, len(m5)):
            if m5_position - last_signal_position < 24:
                continue
            row = m5.iloc[m5_position]
            setup = self._setup_at_position(m5, m5_position)
            if setup is None:
                continue
            last_signal_position = m5_position
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=pd.Timestamp(row["timestamp_utc"]).to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"EXTREME_ACTIVITY_MEAN_REVERSION_V0_{direction}",
                    metadata={
                        **setup,
                        "m5_index": int(m5_position),
                        "point_size": point_size,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m5_atr = float(signal.metadata["m5_atr14"])
        direction = signal.direction.upper()
        if direction == "SHORT":
            stop_loss = float(signal.metadata["spike_high"]) + 0.25 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        elif direction == "LONG":
            stop_loss = float(signal.metadata["spike_low"]) - 0.25 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported extreme activity mean-reversion direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid extreme activity mean-reversion v0 trade plan risk.")
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
            risk_reward=1.5,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry},
        )

    def _setup_at_position(self, m5: pd.DataFrame, m5_position: int) -> dict[str, Any] | None:
        row = m5.iloc[m5_position]
        m5_atr = float(row["atr14"])
        prior_high = float(row["prior_96_high"])
        prior_low = float(row["prior_96_low"])
        m5_range = float(row["m5_range"])
        if not value_available(m5_atr, prior_high, prior_low, m5_range):
            return None
        if m5_atr <= 0 or m5_range < 2.2 * m5_atr:
            return None

        high = float(row["high"])
        low = float(row["low"])
        open_price = float(row["open"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body_ratio = abs(open_price - close) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.25:
            return None

        if high >= prior_high + 0.35 * m5_atr and close <= prior_high - 0.10 * m5_atr:
            if close < open_price and close_position <= 0.40:
                return {
                    "direction": "SHORT",
                    "prior_96_high": prior_high,
                    "prior_96_low": prior_low,
                    "m5_atr14": m5_atr,
                    "m5_range": m5_range,
                    "spike_high": high,
                    "spike_low": low,
                    "estimated_entry_price": close,
                    "rejection_body_ratio": body_ratio,
                    "rejection_close_position": close_position,
                }

        if low <= prior_low - 0.35 * m5_atr and close >= prior_low + 0.10 * m5_atr:
            if close > open_price and close_position >= 0.60:
                return {
                    "direction": "LONG",
                    "prior_96_high": prior_high,
                    "prior_96_low": prior_low,
                    "m5_atr14": m5_atr,
                    "m5_range": m5_range,
                    "spike_high": high,
                    "spike_low": low,
                    "estimated_entry_price": close,
                    "rejection_body_ratio": body_ratio,
                    "rejection_close_position": close_position,
                }

        return None


def _timestamp_values(frame: pd.DataFrame) -> np.ndarray:
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce").astype("int64").to_numpy()

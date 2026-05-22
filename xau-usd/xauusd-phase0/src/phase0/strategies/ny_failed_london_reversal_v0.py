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


class NyFailedLondonReversalV0Strategy(StrategyBase):
    """Disabled research strategy for the locked NY failed-London reversal v0 hypothesis."""

    name = "ny_failed_london_reversal_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        m15 = require_frame(context, "M15")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        if "atr14" not in m15:
            m15["atr14"] = atr(m15["high"], m15["low"], m15["close"], 14)

        bar_starts = _bar_start_times(m5)
        day_key = bar_starts.dt.strftime("%Y-%m-%d")
        start_minutes = bar_starts.dt.hour * 60 + bar_starts.dt.minute
        london_mask = (start_minutes >= 7 * 60) & (start_minutes < 11 * 60)
        london_high_by_day = (
            pd.to_numeric(m5.loc[london_mask, "high"], errors="coerce").groupby(day_key[london_mask]).max()
        )
        london_low_by_day = (
            pd.to_numeric(m5.loc[london_mask, "low"], errors="coerce").groupby(day_key[london_mask]).min()
        )
        m5["ny_failed_london_day"] = day_key
        m5["bar_start_minute_utc"] = start_minutes
        m5["london_high"] = day_key.map(london_high_by_day)
        m5["london_low"] = day_key.map(london_low_by_day)
        m5["london_range_width"] = m5["london_high"] - m5["london_low"]

        context["M5"] = m5
        context["M15"] = m15
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        m15 = context["M15"]
        symbol = context_symbol(context)
        point_size = context_point_size(context)
        m5_time_values = _timestamp_values(m5)
        m15_time_values = _timestamp_values(m15)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for m5_position in range(24, len(m5)):
            row = m5.iloc[m5_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            timestamp_value = int(m5_time_values[m5_position])
            m15_position = _latest_completed_position_from_values(m15_time_values, timestamp_value)
            if m15_position is None:
                continue
            setup = self._setup_at_position(m5, m15, m5_position, m15_position)
            if setup is None:
                continue
            day_direction = (str(setup["session_day"]), str(setup["direction"]))
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
                    reason_code=f"NY_FAILED_LONDON_REVERSAL_V0_{direction}",
                    metadata={
                        **setup,
                        "m5_index": int(m5_position),
                        "m15_index": int(m15_position),
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
            stop_loss = float(signal.metadata["sweep_high"]) + 0.25 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        elif direction == "LONG":
            stop_loss = float(signal.metadata["sweep_low"]) - 0.25 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported NY failed-London reversal direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid NY failed-London reversal v0 trade plan risk.")
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

    def _setup_at_position(
        self,
        m5: pd.DataFrame,
        m15: pd.DataFrame,
        m5_position: int,
        m15_position: int,
    ) -> dict[str, Any] | None:
        row = m5.iloc[m5_position]
        start_minute = int(row["bar_start_minute_utc"])
        if start_minute < 13 * 60 + 30 or start_minute >= 16 * 60 + 30:
            return None

        m5_atr = float(row["atr14"])
        m15_atr = float(m15["atr14"].iat[m15_position])
        london_high = float(row["london_high"])
        london_low = float(row["london_low"])
        london_width = float(row["london_range_width"])
        if not value_available(m5_atr, m15_atr, london_high, london_low, london_width):
            return None
        if m5_atr <= 0 or m15_atr <= 0 or london_width <= 0:
            return None
        if london_width < 1.0 * m15_atr or london_width > 10.0 * m15_atr:
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
        if body_ratio < 0.35:
            return None

        if high >= london_high + 0.35 * m5_atr and close <= london_high - 0.10 * m5_atr:
            if close < open_price and close_position <= 0.45:
                return {
                    "direction": "SHORT",
                    "session_day": str(row["ny_failed_london_day"]),
                    "london_high": london_high,
                    "london_low": london_low,
                    "london_range_width": london_width,
                    "m5_atr14": m5_atr,
                    "m15_atr14": m15_atr,
                    "sweep_high": high,
                    "sweep_low": low,
                    "estimated_entry_price": close,
                    "rejection_body_ratio": body_ratio,
                    "rejection_close_position": close_position,
                }

        if low <= london_low - 0.35 * m5_atr and close >= london_low + 0.10 * m5_atr:
            if close > open_price and close_position >= 0.55:
                return {
                    "direction": "LONG",
                    "session_day": str(row["ny_failed_london_day"]),
                    "london_high": london_high,
                    "london_low": london_low,
                    "london_range_width": london_width,
                    "m5_atr14": m5_atr,
                    "m15_atr14": m15_atr,
                    "sweep_high": high,
                    "sweep_low": low,
                    "estimated_entry_price": close,
                    "rejection_body_ratio": body_ratio,
                    "rejection_close_position": close_position,
                }

        return None


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=5)


def _timestamp_values(frame: pd.DataFrame) -> np.ndarray:
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce").astype("int64").to_numpy()


def _latest_completed_position_from_values(values: np.ndarray, timestamp_value: int) -> int | None:
    position = int(np.searchsorted(values, timestamp_value, side="right")) - 1
    return position if position >= 0 else None

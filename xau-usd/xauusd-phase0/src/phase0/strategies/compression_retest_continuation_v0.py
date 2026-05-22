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


class CompressionRetestContinuationV0Strategy(StrategyBase):
    """Disabled research strategy for the locked compression retest continuation v0 hypothesis."""

    name = "compression_retest_continuation_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        m15 = require_frame(context, "M15")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        m15["compression_high_16"] = (
            pd.to_numeric(m15["high"], errors="coerce").rolling(16, min_periods=16).max()
        )
        m15["compression_low_16"] = (
            pd.to_numeric(m15["low"], errors="coerce").rolling(16, min_periods=16).min()
        )
        m15["compression_width_16"] = m15["compression_high_16"] - m15["compression_low_16"]
        m15["compression_width_threshold_120"] = (
            m15["compression_width_16"].shift(1).rolling(120, min_periods=120).quantile(0.35)
        )
        m15["compression_active"] = m15["compression_width_16"] < m15["compression_width_threshold_120"]
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
        last_signal_position = -1000

        for m5_position in range(300, len(m5)):
            if m5_position - last_signal_position < 24:
                continue
            row = m5.iloc[m5_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            timestamp_value = int(m5_time_values[m5_position])
            m15_position = _latest_completed_position_from_values(m15_time_values, timestamp_value)
            if m15_position is None:
                continue
            setup = self._setup_at_position(m5, m15, m5_position, m15_position)
            if setup is None:
                continue
            last_signal_position = m5_position
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"COMPRESSION_RETEST_CONTINUATION_V0_{direction}",
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
        if direction == "LONG":
            stop_loss = min(float(signal.metadata["compression_low"]), float(signal.metadata["retest_low"]))
            stop_loss -= 0.25 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = max(float(signal.metadata["compression_high"]), float(signal.metadata["retest_high"]))
            stop_loss += 0.25 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported compression retest continuation direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid compression retest continuation v0 trade plan risk.")
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
        if m15_position < 135 or not bool(m15["compression_active"].iat[m15_position]):
            return None
        row = m5.iloc[m5_position]
        m5_atr = float(row["atr14"])
        compression_high = float(m15["compression_high_16"].iat[m15_position])
        compression_low = float(m15["compression_low_16"].iat[m15_position])
        compression_width = float(m15["compression_width_16"].iat[m15_position])
        if not value_available(m5_atr, compression_high, compression_low, compression_width):
            return None
        if m5_atr <= 0 or compression_width <= 0:
            return None

        long_setup = self._direction_setup(
            m5=m5,
            m5_position=m5_position,
            direction="LONG",
            level=compression_high,
            opposite_level=compression_low,
            m5_atr=m5_atr,
        )
        if long_setup is not None:
            return {
                **long_setup,
                "compression_high": compression_high,
                "compression_low": compression_low,
                "compression_width": compression_width,
                "m5_atr14": m5_atr,
                "estimated_entry_price": float(row["close"]),
            }

        short_setup = self._direction_setup(
            m5=m5,
            m5_position=m5_position,
            direction="SHORT",
            level=compression_low,
            opposite_level=compression_high,
            m5_atr=m5_atr,
        )
        if short_setup is not None:
            return {
                **short_setup,
                "compression_high": compression_high,
                "compression_low": compression_low,
                "compression_width": compression_width,
                "m5_atr14": m5_atr,
                "estimated_entry_price": float(row["close"]),
            }

        return None

    def _direction_setup(
        self,
        m5: pd.DataFrame,
        m5_position: int,
        direction: str,
        level: float,
        opposite_level: float,
        m5_atr: float,
    ) -> dict[str, Any] | None:
        del opposite_level
        current = m5.iloc[m5_position]
        open_price = float(current["open"])
        high = float(current["high"])
        low = float(current["low"])
        close = float(current["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.30:
            return None

        if direction == "LONG":
            if not (close > open_price and close >= level + 0.10 * m5_atr and close_position >= 0.60):
                return None
        else:
            if not (close < open_price and close <= level - 0.10 * m5_atr and close_position <= 0.40):
                return None

        breakout_position: int | None = None
        retest_position: int | None = None
        retest_high = float("nan")
        retest_low = float("nan")
        start = max(0, m5_position - 12)
        for position in range(start, m5_position):
            candidate = m5.iloc[position]
            candidate_open = float(candidate["open"])
            candidate_high = float(candidate["high"])
            candidate_low = float(candidate["low"])
            candidate_close = float(candidate["close"])
            if breakout_position is None:
                if direction == "LONG":
                    if candidate_close >= level + 0.20 * m5_atr and candidate_close > candidate_open:
                        breakout_position = position
                else:
                    if candidate_close <= level - 0.20 * m5_atr and candidate_close < candidate_open:
                        breakout_position = position
                continue

            if direction == "LONG":
                retest_happened = candidate_low <= level + 0.15 * m5_atr and candidate_close >= level - 0.10 * m5_atr
            else:
                retest_happened = candidate_high >= level - 0.15 * m5_atr and candidate_close <= level + 0.10 * m5_atr
            if retest_happened:
                retest_position = position
                retest_high = candidate_high
                retest_low = candidate_low

        if breakout_position is None or retest_position is None or retest_position >= m5_position:
            return None

        return {
            "direction": direction,
            "breakout_index": int(breakout_position),
            "retest_index": int(retest_position),
            "retest_high": retest_high,
            "retest_low": retest_low,
            "confirmation_body_ratio": body_ratio,
            "confirmation_close_position": close_position,
        }


def _timestamp_values(frame: pd.DataFrame) -> np.ndarray:
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce").astype("int64").to_numpy()


def _latest_completed_position_from_values(values: np.ndarray, timestamp_value: int) -> int | None:
    position = int(np.searchsorted(values, timestamp_value, side="right")) - 1
    return position if position >= 0 else None

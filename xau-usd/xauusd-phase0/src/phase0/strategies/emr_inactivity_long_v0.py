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


class EmrInactivityLongV0Strategy(StrategyBase):
    """Disabled research strategy for the locked emr_inactivity_long_v0 hypothesis."""

    name = "emr_inactivity_long_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        m15 = require_frame(context, "M15")
        h1 = require_frame(context, "H1")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        if "ema50" not in h1:
            h1["ema50"] = h1["close"].ewm(span=50, adjust=False).mean()
        if "ema50_slope12" not in h1:
            h1["ema50_slope12"] = h1["ema50"] - h1["ema50"].shift(12)

        m5["m5_atr14_inactivity_threshold"] = (
            pd.to_numeric(m5["atr14"], errors="coerce")
            .shift(1)
            .rolling(288, min_periods=288)
            .quantile(0.35)
        )
        m5["m5_inactive"] = m5["atr14"] < m5["m5_atr14_inactivity_threshold"]
        m5["prior_96_low"] = pd.to_numeric(m5["low"], errors="coerce").shift(4).rolling(96, min_periods=96).min()
        m5["prior_3_low"] = pd.to_numeric(m5["low"], errors="coerce").shift(1).rolling(3, min_periods=3).min()
        m5["drop_start_open_3"] = pd.to_numeric(m5["open"], errors="coerce").shift(3)
        m5["drop_move_3"] = m5["drop_start_open_3"] - m5["prior_3_low"]

        m15["range_high_16"] = pd.to_numeric(m15["high"], errors="coerce").rolling(16, min_periods=16).max()
        m15["range_low_16"] = pd.to_numeric(m15["low"], errors="coerce").rolling(16, min_periods=16).min()
        m15["range_width_16"] = m15["range_high_16"] - m15["range_low_16"]
        m15["range_width_threshold_120"] = (
            m15["range_width_16"].shift(1).rolling(120, min_periods=120).quantile(0.35)
        )
        m15["m15_inactive"] = m15["range_width_16"] < m15["range_width_threshold_120"]
        context["M5"] = m5
        context["M15"] = m15
        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        m15 = context["M15"]
        h1 = context["H1"]
        symbol = context_symbol(context)
        point_size = context_point_size(context)
        m5_time_values = _timestamp_values(m5)
        m15_time_values = _timestamp_values(m15)
        h1_time_values = _timestamp_values(h1)
        signals: list[Signal] = []

        for m5_position in range(288, len(m5)):
            row = m5.iloc[m5_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            timestamp_value = int(m5_time_values[m5_position])
            m15_position = _latest_completed_position_from_values(m15_time_values, timestamp_value)
            h1_position = _latest_completed_position_from_values(h1_time_values, timestamp_value)
            if m15_position is None or h1_position is None:
                continue
            setup = self._setup_at_position(m5, m15, h1, m5_position, m15_position, h1_position)
            if setup is None:
                continue
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction="LONG",
                    reason_code="EMR_INACTIVITY_LONG_V0",
                    metadata={
                        **setup,
                        "m5_index": int(m5_position),
                        "m15_index": int(m15_position),
                        "h1_index": int(h1_position),
                        "point_size": point_size,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        sweep_low = float(signal.metadata["sweep_low"])
        m5_atr = float(signal.metadata["m5_atr14"])
        stop_loss = sweep_low - 0.25 * m5_atr
        risk_price = estimated_entry - stop_loss
        if risk_price <= 0:
            raise ConfigError("Invalid EMR Inactivity Long v0 trade plan risk.")
        take_profit = estimated_entry + 1.5 * risk_price
        return TradePlan(
            expert=self.name,
            symbol=signal.symbol,
            direction="LONG",
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
        h1: pd.DataFrame,
        m5_position: int,
        m15_position: int,
        h1_position: int,
    ) -> dict[str, Any] | None:
        if m15_position < 135 or h1_position < 12:
            return None
        row = m5.iloc[m5_position]
        m5_atr = float(row["atr14"])
        if not value_available(m5_atr) or m5_atr <= 0:
            return None
        if not bool(row["m5_inactive"]):
            return None
        if not bool(m15["m15_inactive"].iat[m15_position]):
            return None
        if not self._h1_context_ok(h1, h1_position, m5_atr):
            return None

        sweep_low = float(row["low"])
        prior_96_low = float(row["prior_96_low"])
        prior_3_low = float(row["prior_3_low"])
        drop_start_open = float(row["drop_start_open_3"])
        drop_move = float(row["drop_move_3"])
        if not value_available(sweep_low, prior_96_low, prior_3_low, drop_start_open, drop_move):
            return None
        if prior_3_low > prior_96_low - 0.40 * m5_atr:
            return None
        if drop_move < 1.50 * m5_atr:
            return None

        high = float(row["high"])
        low = float(row["low"])
        open_price = float(row["open"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if low > prior_3_low + 0.10 * m5_atr:
            return None
        if close <= open_price:
            return None
        if close_position < 0.60 or body_ratio < 0.40:
            return None
        if close < prior_96_low + 0.10 * m5_atr:
            return None

        return {
            "sweep_low": sweep_low,
            "prior_96_low": prior_96_low,
            "prior_3_low": prior_3_low,
            "drop_start_open": drop_start_open,
            "drop_move": drop_move,
            "m5_atr14": m5_atr,
            "m15_range_width": float(m15["range_width_16"].iat[m15_position]),
            "h1_close": float(h1["close"].iat[h1_position]),
            "h1_ema50": float(h1["ema50"].iat[h1_position]),
            "h1_ema50_slope12": float(h1["ema50_slope12"].iat[h1_position]),
            "estimated_entry_price": close,
            "rejection_close": close,
            "rejection_body_ratio": body_ratio,
            "rejection_close_position": close_position,
        }

    def _h1_context_ok(self, h1: pd.DataFrame, position: int, m5_atr: float) -> bool:
        close = float(h1["close"].iat[position])
        ema50 = float(h1["ema50"].iat[position])
        slope = float(h1["ema50_slope12"].iat[position])
        return value_available(close, ema50, slope) and close >= ema50 - 4.0 * m5_atr and slope >= -2.0 * m5_atr


def _timestamp_values(frame: pd.DataFrame) -> np.ndarray:
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce").astype("int64").to_numpy()


def _latest_completed_position_from_values(values: np.ndarray, timestamp_value: int) -> int | None:
    position = int(np.searchsorted(values, timestamp_value, side="right")) - 1
    return position if position >= 0 else None

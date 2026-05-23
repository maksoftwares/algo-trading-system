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


class M5ImpulseContinuationV0Strategy(StrategyBase):
    """Disabled research strategy for the locked M5 impulse continuation v0 hypothesis."""

    name = "m5_impulse_continuation_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        h1 = require_frame(context, "H1")

        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        if "ema50" not in h1:
            h1["ema50"] = h1["close"].ewm(span=50, adjust=False).mean()
        if "ema50_slope12" not in h1:
            h1["ema50_slope12"] = h1["ema50"] - h1["ema50"].shift(12)

        bar_starts = _bar_start_times(m5)
        m5["bar_start_minute_utc"] = bar_starts.dt.hour * 60 + bar_starts.dt.minute
        m5["session_day_utc"] = bar_starts.dt.strftime("%Y-%m-%d")
        context["M5"] = m5
        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        h1 = context["H1"]
        symbol = context_symbol(context)
        point_size = context_point_size(context)
        m5_time_values = _timestamp_values(m5)
        h1_time_values = _timestamp_values(h1)
        signals: list[Signal] = []
        last_signal_position_by_direction: dict[str, int] = {}

        for m5_position in range(72, len(m5)):
            row = m5.iloc[m5_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            timestamp_value = int(m5_time_values[m5_position])
            h1_position = _latest_completed_position_from_values(h1_time_values, timestamp_value)
            if h1_position is None:
                continue
            setup = self._setup_at_position(m5, h1, m5_position, h1_position)
            if setup is None:
                continue
            direction = str(setup["direction"])
            last_position = last_signal_position_by_direction.get(direction)
            if last_position is not None and m5_position - last_position < 12:
                continue
            last_signal_position_by_direction[direction] = m5_position
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"M5_IMPULSE_CONTINUATION_V0_{direction}",
                    metadata={
                        **setup,
                        "m5_index": int(m5_position),
                        "h1_index": int(h1_position),
                        "point_size": point_size,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        impulse_low = float(signal.metadata["impulse_low"])
        impulse_high = float(signal.metadata["impulse_high"])
        m5_atr = float(signal.metadata["m5_atr14"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = impulse_low - 0.20 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = impulse_high + 0.20 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported M5 impulse continuation direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid M5 impulse continuation v0 trade plan risk.")
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
        h1: pd.DataFrame,
        m5_position: int,
        h1_position: int,
    ) -> dict[str, Any] | None:
        if h1_position < 12 or m5_position < 2:
            return None

        row = m5.iloc[m5_position]
        prev = m5.iloc[m5_position - 1]
        start_minute = int(row["bar_start_minute_utc"])
        if start_minute < 7 * 60 or start_minute >= 17 * 60:
            return None

        m5_atr = float(row["atr14"])
        if not value_available(m5_atr) or m5_atr <= 0:
            return None

        row_quality = _candle_quality(row)
        prev_quality = _candle_quality(prev)
        if row_quality is None or prev_quality is None:
            return None
        row_body, row_close_position = row_quality
        prev_body, prev_close_position = prev_quality
        if row_body < 0.45 or prev_body < 0.35:
            return None

        open_prev = float(prev["open"])
        close = float(row["close"])
        impulse_high = max(float(prev["high"]), float(row["high"]))
        impulse_low = min(float(prev["low"]), float(row["low"]))
        impulse_range = impulse_high - impulse_low
        net_move = abs(close - open_prev)
        if impulse_range <= 0 or impulse_range > 3.0 * m5_atr or net_move < 0.75 * m5_atr:
            return None

        h1_close = float(h1["close"].iat[h1_position])
        h1_ema50 = float(h1["ema50"].iat[h1_position])
        h1_slope = float(h1["ema50_slope12"].iat[h1_position])
        if not value_available(h1_close, h1_ema50, h1_slope):
            return None

        prev_close = float(prev["close"])
        row_open = float(row["open"])
        if (
            prev_close > open_prev
            and close > row_open
            and close > prev_close
            and row_close_position >= 0.70
            and h1_close >= h1_ema50
            and h1_slope >= 0
        ):
            return self._metadata("LONG", row, prev, m5_atr, impulse_high, impulse_low, net_move, h1_close, h1_ema50, h1_slope)

        if (
            prev_close < open_prev
            and close < row_open
            and close < prev_close
            and row_close_position <= 0.30
            and h1_close <= h1_ema50
            and h1_slope <= 0
        ):
            return self._metadata("SHORT", row, prev, m5_atr, impulse_high, impulse_low, net_move, h1_close, h1_ema50, h1_slope)

        return None

    def _metadata(
        self,
        direction: str,
        row: pd.Series,
        prev: pd.Series,
        m5_atr: float,
        impulse_high: float,
        impulse_low: float,
        net_move: float,
        h1_close: float,
        h1_ema50: float,
        h1_slope: float,
    ) -> dict[str, Any]:
        return {
            "direction": direction,
            "session_day_utc": str(row["session_day_utc"]),
            "m5_atr14": m5_atr,
            "impulse_start_time_utc": str(prev["timestamp_utc"]),
            "impulse_end_time_utc": str(row["timestamp_utc"]),
            "impulse_high": impulse_high,
            "impulse_low": impulse_low,
            "impulse_net_move": net_move,
            "h1_close": h1_close,
            "h1_ema50": h1_ema50,
            "h1_ema50_slope12": h1_slope,
            "estimated_entry_price": float(row["close"]),
        }


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


def _candle_quality(row: pd.Series) -> tuple[float, float] | None:
    high = float(row["high"])
    low = float(row["low"])
    open_price = float(row["open"])
    close = float(row["close"])
    candle_range = high - low
    if candle_range <= 0:
        return None
    body_ratio = abs(close - open_price) / candle_range
    close_position = (close - low) / candle_range
    return body_ratio, close_position

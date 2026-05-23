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


class M15InsideBarBreakoutV0Strategy(StrategyBase):
    """Disabled research strategy for the locked M15 inside-bar breakout v0 hypothesis."""

    name = "m15_inside_bar_breakout_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        m15 = require_frame(context, "M15")
        h1 = require_frame(context, "H1")

        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        if "atr14" not in m15:
            m15["atr14"] = atr(m15["high"], m15["low"], m15["close"], 14)
        if "ema50" not in h1:
            h1["ema50"] = h1["close"].ewm(span=50, adjust=False).mean()
        if "ema50_slope12" not in h1:
            h1["ema50_slope12"] = h1["ema50"] - h1["ema50"].shift(12)

        bar_starts = _bar_start_times(m5)
        m5["bar_start_minute_utc"] = bar_starts.dt.hour * 60 + bar_starts.dt.minute
        m5["session_day_utc"] = bar_starts.dt.strftime("%Y-%m-%d")

        mother_high = pd.to_numeric(m15["high"], errors="coerce").shift(1)
        mother_low = pd.to_numeric(m15["low"], errors="coerce").shift(1)
        mother_range = mother_high - mother_low
        inside_range = pd.to_numeric(m15["high"], errors="coerce") - pd.to_numeric(m15["low"], errors="coerce")
        m15["mother_high"] = mother_high
        m15["mother_low"] = mother_low
        m15["mother_range"] = mother_range
        m15["inside_range"] = inside_range
        m15["is_inside_bar"] = (
            (pd.to_numeric(m15["high"], errors="coerce") <= mother_high)
            & (pd.to_numeric(m15["low"], errors="coerce") >= mother_low)
            & (inside_range <= 0.70 * mother_range)
            & (mother_range >= 0.60 * pd.to_numeric(m15["atr14"], errors="coerce").shift(1))
        )

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
        used_inside_bars: set[tuple[str, str]] = set()

        for m5_position in range(72, len(m5)):
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
            inside_key = (str(setup["inside_bar_time_utc"]), str(setup["direction"]))
            if inside_key in used_inside_bars:
                continue
            used_inside_bars.add(inside_key)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"M15_INSIDE_BAR_BREAKOUT_V0_{direction}",
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
        inside_high = float(signal.metadata["inside_high"])
        inside_low = float(signal.metadata["inside_low"])
        m5_atr = float(signal.metadata["m5_atr14"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = min(inside_low, estimated_entry - m5_atr)
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = max(inside_high, estimated_entry + m5_atr)
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported M15 inside-bar breakout direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid M15 inside-bar breakout v0 trade plan risk.")
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
        h1: pd.DataFrame,
        m5_position: int,
        m15_position: int,
        h1_position: int,
    ) -> dict[str, Any] | None:
        if m15_position < 20 or h1_position < 12:
            return None

        row = m5.iloc[m5_position]
        start_minute = int(row["bar_start_minute_utc"])
        if start_minute < 7 * 60 or start_minute >= 17 * 60:
            return None

        row_time = pd.Timestamp(row["timestamp_utc"])
        inside_position = _latest_recent_inside_position(m15, m15_position, row_time)
        if inside_position is None:
            return None
        inside = m15.iloc[inside_position]
        if not bool(inside["is_inside_bar"]):
            return None
        inside_time = pd.Timestamp(inside["timestamp_utc"])
        minutes_after_inside = (row_time - inside_time).total_seconds() / 60.0
        if minutes_after_inside < 0 or minutes_after_inside > 45:
            return None

        m5_atr = float(row["atr14"])
        mother_high = float(inside["mother_high"])
        mother_low = float(inside["mother_low"])
        mother_range = float(inside["mother_range"])
        inside_high = float(inside["high"])
        inside_low = float(inside["low"])
        inside_range = float(inside["inside_range"])
        if not value_available(m5_atr, mother_high, mother_low, mother_range, inside_high, inside_low, inside_range):
            return None
        if m5_atr <= 0 or mother_range <= 0 or inside_range <= 0:
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0 or candle_range > 2.5 * m5_atr:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.40:
            return None

        h1_close = float(h1["close"].iat[h1_position])
        h1_ema50 = float(h1["ema50"].iat[h1_position])
        h1_slope = float(h1["ema50_slope12"].iat[h1_position])
        if not value_available(h1_close, h1_ema50, h1_slope):
            return None

        if (
            close >= mother_high + 0.10 * m5_atr
            and close > open_price
            and close_position >= 0.65
            and h1_close >= h1_ema50
            and h1_slope >= 0
        ):
            return self._metadata(
                "LONG",
                row,
                inside,
                mother_high,
                mother_low,
                mother_range,
                inside_high,
                inside_low,
                inside_range,
                m5_atr,
                h1_close,
                h1_ema50,
                h1_slope,
                open_price,
                high,
                low,
                close,
                body_ratio,
                close_position,
            )

        if (
            close <= mother_low - 0.10 * m5_atr
            and close < open_price
            and close_position <= 0.35
            and h1_close <= h1_ema50
            and h1_slope <= 0
        ):
            return self._metadata(
                "SHORT",
                row,
                inside,
                mother_high,
                mother_low,
                mother_range,
                inside_high,
                inside_low,
                inside_range,
                m5_atr,
                h1_close,
                h1_ema50,
                h1_slope,
                open_price,
                high,
                low,
                close,
                body_ratio,
                close_position,
            )

        return None

    def _metadata(
        self,
        direction: str,
        row: pd.Series,
        inside: pd.Series,
        mother_high: float,
        mother_low: float,
        mother_range: float,
        inside_high: float,
        inside_low: float,
        inside_range: float,
        m5_atr: float,
        h1_close: float,
        h1_ema50: float,
        h1_slope: float,
        open_price: float,
        high: float,
        low: float,
        close: float,
        body_ratio: float,
        close_position: float,
    ) -> dict[str, Any]:
        return {
            "direction": direction,
            "session_day_utc": str(row["session_day_utc"]),
            "inside_bar_time_utc": str(inside["timestamp_utc"]),
            "inside_m15_index": int(inside.name),
            "mother_high": mother_high,
            "mother_low": mother_low,
            "mother_range": mother_range,
            "inside_high": inside_high,
            "inside_low": inside_low,
            "inside_range": inside_range,
            "m5_atr14": m5_atr,
            "h1_close": h1_close,
            "h1_ema50": h1_ema50,
            "h1_ema50_slope12": h1_slope,
            "breakout_open": open_price,
            "breakout_high": high,
            "breakout_low": low,
            "breakout_close": close,
            "breakout_body_ratio": body_ratio,
            "breakout_close_position": close_position,
            "estimated_entry_price": close,
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


def _latest_recent_inside_position(
    m15: pd.DataFrame,
    latest_completed_position: int,
    row_time: pd.Timestamp,
    max_age_minutes: int = 45,
) -> int | None:
    for position in range(latest_completed_position, max(-1, latest_completed_position - 4), -1):
        if position < 0 or not bool(m15["is_inside_bar"].iat[position]):
            continue
        inside_time = pd.Timestamp(m15["timestamp_utc"].iat[position])
        age_minutes = (row_time - inside_time).total_seconds() / 60.0
        if 0 <= age_minutes <= max_age_minutes:
            return position
    return None

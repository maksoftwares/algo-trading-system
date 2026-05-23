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
)


class LiquiditySweepReversalV0Strategy(StrategyBase):
    """Disabled research strategy for the locked liquidity sweep reversal v0 hypothesis."""

    name = "liquidity_sweep_reversal_v0"
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
        highs = pd.to_numeric(m5["high"], errors="coerce")
        lows = pd.to_numeric(m5["low"], errors="coerce")

        day_levels = pd.DataFrame({"day": day_key, "high": highs, "low": lows}).groupby("day", sort=True).agg(
            day_high=("high", "max"),
            day_low=("low", "min"),
        )
        day_levels["previous_day_high"] = day_levels["day_high"].shift(1)
        day_levels["previous_day_low"] = day_levels["day_low"].shift(1)

        asia_mask = (start_minutes >= 0) & (start_minutes < 6 * 60)
        london_mask = (start_minutes >= 7 * 60) & (start_minutes < 11 * 60)
        asia_high_by_day = highs.loc[asia_mask].groupby(day_key[asia_mask]).max()
        asia_low_by_day = lows.loc[asia_mask].groupby(day_key[asia_mask]).min()
        london_high_by_day = highs.loc[london_mask].groupby(day_key[london_mask]).max()
        london_low_by_day = lows.loc[london_mask].groupby(day_key[london_mask]).min()

        m5["liquidity_sweep_day"] = day_key
        m5["bar_start_minute_utc"] = start_minutes
        m5["previous_day_high"] = day_key.map(day_levels["previous_day_high"])
        m5["previous_day_low"] = day_key.map(day_levels["previous_day_low"])
        m5["asia_high"] = day_key.map(asia_high_by_day)
        m5["asia_low"] = day_key.map(asia_low_by_day)
        m5["london_high"] = day_key.map(london_high_by_day)
        m5["london_low"] = day_key.map(london_low_by_day)

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
        used_day_level: set[tuple[str, str, str]] = set()

        for m5_position in range(300, len(m5)):
            row = m5.iloc[m5_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            timestamp_value = int(m5_time_values[m5_position])
            m15_position = _latest_completed_position_from_values(m15_time_values, timestamp_value)
            if m15_position is None:
                continue
            setup = self._setup_at_position(m5, m15, m5_position, m15_position)
            if setup is None:
                continue
            day_level = (
                str(setup["session_day"]),
                str(setup["direction"]),
                str(setup["level_kind"]),
            )
            if day_level in used_day_level:
                continue
            used_day_level.add(day_level)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"LIQUIDITY_SWEEP_REVERSAL_V0_{direction}",
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
            raise ConfigError(f"Unsupported liquidity sweep reversal direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid liquidity sweep reversal v0 trade plan risk.")
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
        if start_minute < 7 * 60 or start_minute >= 17 * 60:
            return None

        m5_atr = _safe_float(row.get("atr14"))
        m15_atr = _safe_float(m15["atr14"].iat[m15_position])
        if m5_atr is None or m15_atr is None or m5_atr <= 0 or m15_atr <= 0:
            return None

        high = float(row["high"])
        low = float(row["low"])
        open_price = float(row["open"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body = abs(close - open_price)
        body_ratio = body / candle_range
        close_position = (close - low) / candle_range
        upper_wick = high - max(open_price, close)
        lower_wick = min(open_price, close) - low
        if body_ratio < 0.20:
            return None

        short_setup = self._short_setup(row, high, low, open_price, close, m5_atr, body, upper_wick, close_position)
        if short_setup is not None:
            return {
                **short_setup,
                "session_day": str(row["liquidity_sweep_day"]),
                "m5_atr14": m5_atr,
                "m15_atr14": m15_atr,
                "sweep_high": high,
                "sweep_low": low,
                "estimated_entry_price": close,
                "rejection_body_ratio": body_ratio,
                "rejection_close_position": close_position,
            }

        long_setup = self._long_setup(row, high, low, open_price, close, m5_atr, body, lower_wick, close_position)
        if long_setup is not None:
            return {
                **long_setup,
                "session_day": str(row["liquidity_sweep_day"]),
                "m5_atr14": m5_atr,
                "m15_atr14": m15_atr,
                "sweep_high": high,
                "sweep_low": low,
                "estimated_entry_price": close,
                "rejection_body_ratio": body_ratio,
                "rejection_close_position": close_position,
            }

        return None

    def _short_setup(
        self,
        row: pd.Series,
        high: float,
        low: float,
        open_price: float,
        close: float,
        m5_atr: float,
        body: float,
        upper_wick: float,
        close_position: float,
    ) -> dict[str, Any] | None:
        if close >= open_price or close_position > 0.45 or upper_wick < 1.25 * max(body, 0.000001):
            return None
        for level_kind, level in self._high_levels(row):
            if high >= level + 0.20 * m5_atr and close <= level - 0.05 * m5_atr:
                return {
                    "direction": "SHORT",
                    "level_kind": level_kind,
                    "level": level,
                    "sweep_distance_atr": (high - level) / m5_atr,
                    "reclaim_distance_atr": (level - close) / m5_atr,
                }
        return None

    def _long_setup(
        self,
        row: pd.Series,
        high: float,
        low: float,
        open_price: float,
        close: float,
        m5_atr: float,
        body: float,
        lower_wick: float,
        close_position: float,
    ) -> dict[str, Any] | None:
        del high
        if close <= open_price or close_position < 0.55 or lower_wick < 1.25 * max(body, 0.000001):
            return None
        for level_kind, level in self._low_levels(row):
            if low <= level - 0.20 * m5_atr and close >= level + 0.05 * m5_atr:
                return {
                    "direction": "LONG",
                    "level_kind": level_kind,
                    "level": level,
                    "sweep_distance_atr": (level - low) / m5_atr,
                    "reclaim_distance_atr": (close - level) / m5_atr,
                }
        return None

    def _high_levels(self, row: pd.Series) -> list[tuple[str, float]]:
        start_minute = int(row["bar_start_minute_utc"])
        levels: list[tuple[str, float]] = []
        previous_day_high = _safe_float(row.get("previous_day_high"))
        if previous_day_high is not None:
            levels.append(("previous_day_high", previous_day_high))
        asia_high = _safe_float(row.get("asia_high"))
        if asia_high is not None and start_minute >= 7 * 60:
            levels.append(("asia_high", asia_high))
        london_high = _safe_float(row.get("london_high"))
        if london_high is not None and start_minute >= 13 * 60 + 30:
            levels.append(("london_high", london_high))
        return levels

    def _low_levels(self, row: pd.Series) -> list[tuple[str, float]]:
        start_minute = int(row["bar_start_minute_utc"])
        levels: list[tuple[str, float]] = []
        previous_day_low = _safe_float(row.get("previous_day_low"))
        if previous_day_low is not None:
            levels.append(("previous_day_low", previous_day_low))
        asia_low = _safe_float(row.get("asia_low"))
        if asia_low is not None and start_minute >= 7 * 60:
            levels.append(("asia_low", asia_low))
        london_low = _safe_float(row.get("london_low"))
        if london_low is not None and start_minute >= 13 * 60 + 30:
            levels.append(("london_low", london_low))
        return levels


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


def _safe_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(result):
        return None
    return result

from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_point_size, context_symbol, copy_context, require_frame


class DailyPivotReclaimV0Strategy(StrategyBase):
    """Disabled research strategy for the locked daily pivot reclaim v0 hypothesis."""

    name = "daily_pivot_reclaim_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)

        bar_starts = _bar_start_times(m5)
        day_key = bar_starts.dt.strftime("%Y-%m-%d")
        daily = pd.DataFrame(
            {
                "day": day_key,
                "high": pd.to_numeric(m5["high"], errors="coerce"),
                "low": pd.to_numeric(m5["low"], errors="coerce"),
                "close": pd.to_numeric(m5["close"], errors="coerce"),
            }
        )
        day_levels = daily.groupby("day", sort=True).agg(
            day_high=("high", "max"),
            day_low=("low", "min"),
            day_close=("close", "last"),
        )
        day_levels["previous_day_pivot"] = (
            day_levels["day_high"].shift(1) + day_levels["day_low"].shift(1) + day_levels["day_close"].shift(1)
        ) / 3.0

        m5["daily_pivot_day"] = day_key
        m5["bar_start_minute_utc"] = bar_starts.dt.hour * 60 + bar_starts.dt.minute
        m5["previous_day_pivot"] = day_key.map(day_levels["previous_day_pivot"])
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
        used_day_direction: set[tuple[str, str]] = set()

        for m5_position in range(300, len(m5)):
            row = m5.iloc[m5_position]
            setup = self._setup_at_position(row)
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
                    timestamp_utc=pd.Timestamp(row["timestamp_utc"]).to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"DAILY_PIVOT_RECLAIM_V0_{direction}",
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
        if direction == "LONG":
            stop_loss = float(signal.metadata["reclaim_low"]) - 0.25 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["reclaim_high"]) + 0.25 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported daily pivot reclaim direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid daily pivot reclaim v0 trade plan risk.")
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

    def _setup_at_position(self, row: pd.Series) -> dict[str, Any] | None:
        start_minute = int(row["bar_start_minute_utc"])
        if start_minute < 7 * 60 or start_minute >= 17 * 60:
            return None

        pivot = _safe_float(row.get("previous_day_pivot"))
        m5_atr = _safe_float(row.get("atr14"))
        if pivot is None or m5_atr is None or m5_atr <= 0:
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.25:
            return None

        if low <= pivot - 0.25 * m5_atr and close >= pivot + 0.10 * m5_atr:
            if close > open_price and close_position >= 0.60:
                return {
                    "direction": "LONG",
                    "session_day": str(row["daily_pivot_day"]),
                    "level_kind": "previous_day_pivot",
                    "level": pivot,
                    "m5_atr14": m5_atr,
                    "reclaim_high": high,
                    "reclaim_low": low,
                    "estimated_entry_price": close,
                    "confirmation_body_ratio": body_ratio,
                    "confirmation_close_position": close_position,
                }

        if high >= pivot + 0.25 * m5_atr and close <= pivot - 0.10 * m5_atr:
            if close < open_price and close_position <= 0.40:
                return {
                    "direction": "SHORT",
                    "session_day": str(row["daily_pivot_day"]),
                    "level_kind": "previous_day_pivot",
                    "level": pivot,
                    "m5_atr14": m5_atr,
                    "reclaim_high": high,
                    "reclaim_low": low,
                    "estimated_entry_price": close,
                    "confirmation_body_ratio": body_ratio,
                    "confirmation_close_position": close_position,
                }

        return None


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=5)


def _safe_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

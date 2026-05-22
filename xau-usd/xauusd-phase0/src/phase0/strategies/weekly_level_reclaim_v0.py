from __future__ import annotations

from typing import Any

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


class WeeklyLevelReclaimV0Strategy(StrategyBase):
    """Disabled research strategy for the locked weekly level reclaim v0 hypothesis."""

    name = "weekly_level_reclaim_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)

        bar_starts = _bar_start_times(m5)
        iso = bar_starts.dt.isocalendar()
        week_key = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
        weekly = pd.DataFrame(
            {
                "week": week_key,
                "high": pd.to_numeric(m5["high"], errors="coerce"),
                "low": pd.to_numeric(m5["low"], errors="coerce"),
            }
        )
        week_levels = weekly.groupby("week", sort=True).agg(week_high=("high", "max"), week_low=("low", "min"))
        week_levels["previous_week_high"] = week_levels["week_high"].shift(1)
        week_levels["previous_week_low"] = week_levels["week_low"].shift(1)
        m5["level_week"] = week_key
        m5["previous_week_high"] = week_key.map(week_levels["previous_week_high"])
        m5["previous_week_low"] = week_key.map(week_levels["previous_week_low"])
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
        used_week_direction: set[tuple[str, str]] = set()

        for m5_position in range(300, len(m5)):
            row = m5.iloc[m5_position]
            setup = self._setup_at_position(m5, m5_position)
            if setup is None:
                continue
            week_direction = (str(setup["week"]), str(setup["direction"]))
            if week_direction in used_week_direction:
                continue
            used_week_direction.add(week_direction)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=pd.Timestamp(row["timestamp_utc"]).to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"WEEKLY_LEVEL_RECLAIM_V0_{direction}",
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
            stop_loss = float(signal.metadata["sweep_low"]) - 0.25 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["sweep_high"]) + 0.25 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported weekly level reclaim direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid weekly level reclaim v0 trade plan risk.")
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
        previous_high = float(row["previous_week_high"])
        previous_low = float(row["previous_week_low"])
        if not value_available(m5_atr, previous_high, previous_low) or m5_atr <= 0:
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
        if body_ratio < 0.30:
            return None

        if low <= previous_low - 0.35 * m5_atr and close >= previous_low + 0.10 * m5_atr:
            if close > open_price and close_position >= 0.60:
                return {
                    "direction": "LONG",
                    "week": str(row["level_week"]),
                    "level": previous_low,
                    "previous_week_high": previous_high,
                    "previous_week_low": previous_low,
                    "m5_atr14": m5_atr,
                    "sweep_high": high,
                    "sweep_low": low,
                    "estimated_entry_price": close,
                    "reclaim_body_ratio": body_ratio,
                    "reclaim_close_position": close_position,
                }

        if high >= previous_high + 0.35 * m5_atr and close <= previous_high - 0.10 * m5_atr:
            if close < open_price and close_position <= 0.40:
                return {
                    "direction": "SHORT",
                    "week": str(row["level_week"]),
                    "level": previous_high,
                    "previous_week_high": previous_high,
                    "previous_week_low": previous_low,
                    "m5_atr14": m5_atr,
                    "sweep_high": high,
                    "sweep_low": low,
                    "estimated_entry_price": close,
                    "reclaim_body_ratio": body_ratio,
                    "reclaim_close_position": close_position,
                }

        return None


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=5)

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


class SessionVwapReclaimV0Strategy(StrategyBase):
    """Disabled research strategy for the locked session VWAP reclaim v0 hypothesis."""

    name = "session_vwap_reclaim_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)

        bar_starts = _bar_start_times(m5)
        day_key = bar_starts.dt.strftime("%Y-%m-%d")
        start_minutes = bar_starts.dt.hour * 60 + bar_starts.dt.minute
        session_mask = (start_minutes >= 7 * 60) & (start_minutes < 17 * 60)
        typical = (
            pd.to_numeric(m5["high"], errors="coerce")
            + pd.to_numeric(m5["low"], errors="coerce")
            + pd.to_numeric(m5["close"], errors="coerce")
        ) / 3.0
        weights = _volume_weights(m5)
        weighted_price = typical * weights

        m5["vwap_day"] = day_key
        m5["bar_start_minute_utc"] = start_minutes
        m5["session_vwap"] = np.nan
        for day in sorted(day_key[session_mask].dropna().unique()):
            mask = session_mask & (day_key == day)
            cumulative_weight = weights.loc[mask].cumsum()
            cumulative_price = weighted_price.loc[mask].cumsum()
            m5.loc[mask, "session_vwap"] = cumulative_price / cumulative_weight

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

        for m5_position in range(24, len(m5)):
            row = m5.iloc[m5_position]
            setup = self._setup_at_position(m5, m5_position)
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
                    reason_code=f"SESSION_VWAP_RECLAIM_V0_{direction}",
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
            raise ConfigError(f"Unsupported session VWAP reclaim direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid session VWAP reclaim v0 trade plan risk.")
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
        start_minute = int(row["bar_start_minute_utc"])
        if start_minute < 8 * 60 or start_minute >= 17 * 60:
            return None

        m5_atr = float(row["atr14"])
        session_vwap = float(row["session_vwap"])
        if not value_available(m5_atr, session_vwap) or m5_atr <= 0:
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

        if low <= session_vwap - 1.00 * m5_atr and close >= session_vwap + 0.10 * m5_atr:
            if close > open_price and close_position >= 0.60:
                return {
                    "direction": "LONG",
                    "session_day": str(row["vwap_day"]),
                    "session_vwap": session_vwap,
                    "m5_atr14": m5_atr,
                    "sweep_high": high,
                    "sweep_low": low,
                    "estimated_entry_price": close,
                    "reclaim_body_ratio": body_ratio,
                    "reclaim_close_position": close_position,
                }

        if high >= session_vwap + 1.00 * m5_atr and close <= session_vwap - 0.10 * m5_atr:
            if close < open_price and close_position <= 0.40:
                return {
                    "direction": "SHORT",
                    "session_day": str(row["vwap_day"]),
                    "session_vwap": session_vwap,
                    "m5_atr14": m5_atr,
                    "sweep_high": high,
                    "sweep_low": low,
                    "estimated_entry_price": close,
                    "reclaim_body_ratio": body_ratio,
                    "reclaim_close_position": close_position,
                }

        return None


def _volume_weights(frame: pd.DataFrame) -> pd.Series:
    for column in ("tick_volume", "volume", "real_volume"):
        if column in frame:
            values = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
            if values.gt(0).any():
                return values.clip(lower=1.0)
    return pd.Series(1.0, index=frame.index)


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=5)

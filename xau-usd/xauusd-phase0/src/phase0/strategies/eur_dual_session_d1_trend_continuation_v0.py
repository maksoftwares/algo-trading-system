from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import (
    StrategyBase,
    context_point_size,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class EurDualSessionD1TrendContinuationV0Strategy(StrategyBase):
    """Research-only Wave-4 EURUSD dual-funded-session daily-trend continuation.

    Locked hypothesis: docs/hypothesis_eur_dual_session_d1_trend_continuation_v0.md
    Trigger windows: first initiative H1 bar ending 09:00-11:00 Europe/London OR
    09:00-11:00 America/New_York, in the D1 EMA20/EMA50 trend direction.
    timestamp_utc equals the bar END everywhere; stop floor is 375 symbol points.
    """

    name = "eur_dual_session_d1_trend_continuation_v0"
    version = "0.1-research-disabled"

    risk_reward = 2.0
    day_timezone = "America/New_York"
    london_timezone = "Europe/London"
    trigger_end_hours = (9, 10, 11)
    min_body_fraction = 0.35
    stop_atr_multiple = 1.5
    stop_floor_points = 375.0

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["event_local_date"] = h1["timestamp_utc"].dt.tz_convert(self.day_timezone).dt.strftime("%Y-%m-%d")
        h1["london_hour"] = h1["timestamp_utc"].dt.tz_convert(self.london_timezone).dt.hour
        h1["ny_hour"] = h1["timestamp_utc"].dt.tz_convert(self.day_timezone).dt.hour
        context["H1"] = h1

        d1 = require_frame(context, "D1")
        d1_close = pd.to_numeric(d1["close"], errors="coerce")
        d1["d1_ema20"] = ema(d1_close, 20)
        d1["d1_ema50"] = ema(d1_close, 50)
        context["D1"] = d1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        d1 = context["D1"]
        symbol = context_symbol(context)
        d1_times = d1["timestamp_utc"]
        signals: list[Signal] = []

        in_window = h1["london_hour"].isin(self.trigger_end_hours) | h1["ny_hour"].isin(self.trigger_end_hours)

        for local_date, day in h1.groupby("event_local_date", sort=True):
            date_start_utc = pd.Timestamp(str(local_date), tz=self.day_timezone).tz_convert("UTC")
            eligible = d1[d1_times <= date_start_utc]
            if eligible.empty:
                continue
            state_row = eligible.iloc[-1]
            if not value_available(state_row["d1_ema20"], state_row["d1_ema50"]):
                continue
            if float(state_row["d1_ema20"]) > float(state_row["d1_ema50"]):
                trend = "LONG"
            elif float(state_row["d1_ema20"]) < float(state_row["d1_ema50"]):
                trend = "SHORT"
            else:
                continue

            previous_row = None
            for position in range(len(day)):
                row = day.iloc[position]
                if bool(in_window.loc[row.name]) and previous_row is not None:
                    setup = self._initiative_setup(row, previous_row, trend)
                    if setup is not None:
                        timestamp = pd.Timestamp(row["timestamp_utc"])
                        signals.append(
                            Signal(
                                expert=self.name,
                                timestamp_utc=timestamp.to_pydatetime(),
                                symbol=symbol,
                                direction=trend,
                                reason_code=f"EUR_DUAL_SESSION_D1_TREND_CONTINUATION_V0_{trend}",
                                metadata={**setup, "direction": trend, "event_local_date": str(local_date)},
                            )
                        )
                        break
                previous_row = row
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        trigger_atr = float(signal.metadata["h1_atr14"])
        point_size = context_point_size(data_context)
        stop_distance = max(self.stop_atr_multiple * trigger_atr, self.stop_floor_points * point_size)

        if direction == "LONG":
            stop_loss = estimated_entry - stop_distance
            take_profit = estimated_entry + self.risk_reward * stop_distance
        elif direction == "SHORT":
            stop_loss = estimated_entry + stop_distance
            take_profit = estimated_entry - self.risk_reward * stop_distance
        else:
            raise ConfigError(f"Unsupported EUR dual session direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid EUR dual session trade plan risk.")

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
            risk_reward=self.risk_reward,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "stop_distance_price_units": stop_distance},
        )

    def _initiative_setup(self, row: pd.Series, previous_row: pd.Series, trend: str) -> dict[str, Any] | None:
        required = (
            row["open"], row["high"], row["low"], row["close"], row["h1_atr14"],
            previous_row["high"], previous_row["low"],
        )
        if not value_available(*required):
            return None
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        trigger_atr = float(row["h1_atr14"])
        if trigger_atr <= 0:
            return None
        candle_range = high - low
        if candle_range <= 0:
            return None
        body_fraction = abs(close - open_price) / candle_range
        if body_fraction < self.min_body_fraction:
            return None
        if trend == "LONG":
            if not (close > open_price and close > float(previous_row["high"])):
                return None
        else:
            if not (close < open_price and close < float(previous_row["low"])):
                return None
        return {"estimated_entry_price": close, "h1_atr14": trigger_atr, "body_fraction": body_fraction}

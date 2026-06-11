from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class XauNyMorningTrendPullbackV0Strategy(StrategyBase):
    """Research-only Wave-2 NY-morning funded-impulse pullback continuation candidate.

    Locked hypothesis: docs/hypothesis_xau_ny_morning_trend_pullback_v0.md
    All windows are defined on completed H1 bars whose timestamp_utc equals the
    bar END converted to America/New_York local time (DST-correct via IANA rules).
    """

    name = "xau_ny_morning_trend_pullback_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.5
    event_timezone = "America/New_York"
    impulse_open_end_hour = 9
    impulse_close_end_hour = 10
    trigger_end_hours = (11, 12, 13)
    impulse_min_atr = 1.00
    impulse_max_atr = 6.00
    stop_atr_multiple = 1.2
    stop_floor_price_units = 3.75

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        local_end = h1["timestamp_utc"].dt.tz_convert(self.event_timezone)
        h1["event_local_date"] = local_end.dt.strftime("%Y-%m-%d")
        h1["event_local_hour"] = local_end.dt.hour
        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []

        for local_date, day in h1.groupby("event_local_date", sort=True):
            open_rows = day[day["event_local_hour"] == self.impulse_open_end_hour]
            close_rows = day[day["event_local_hour"] == self.impulse_close_end_hour]
            if open_rows.empty or close_rows.empty:
                continue
            impulse_open = open_rows.iloc[0]["open"]
            impulse_bar = close_rows.iloc[0]
            if not value_available(impulse_open, impulse_bar["close"], impulse_bar["h1_atr14"]):
                continue
            impulse_open = float(impulse_open)
            impulse_close = float(impulse_bar["close"])
            impulse_atr = float(impulse_bar["h1_atr14"])
            if impulse_atr <= 0:
                continue
            impulse = impulse_close - impulse_open
            impulse_multiple = abs(impulse) / impulse_atr
            if impulse_multiple < self.impulse_min_atr or impulse_multiple > self.impulse_max_atr:
                continue
            impulse_up = impulse > 0

            triggers = day[day["event_local_hour"].isin(self.trigger_end_hours)].sort_values("timestamp_utc")
            for _, row in triggers.iterrows():
                setup = self._pullback_setup(row, impulse_up, impulse_open)
                if setup is None:
                    continue
                timestamp = pd.Timestamp(row["timestamp_utc"])
                direction = "LONG" if impulse_up else "SHORT"
                signals.append(
                    Signal(
                        expert=self.name,
                        timestamp_utc=timestamp.to_pydatetime(),
                        symbol=symbol,
                        direction=direction,
                        reason_code=f"XAU_NY_MORNING_TREND_PULLBACK_V0_{direction}",
                        metadata={
                            **setup,
                            "direction": direction,
                            "event_local_date": str(local_date),
                            "impulse_price_units": impulse,
                            "impulse_atr_multiple": impulse_multiple,
                            "impulse_open_price": impulse_open,
                        },
                    )
                )
                break  # first qualifying pullback per New_York date wins
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        trigger_atr = float(signal.metadata["h1_atr14"])
        stop_distance = max(self.stop_atr_multiple * trigger_atr, self.stop_floor_price_units)

        if direction == "LONG":
            stop_loss = estimated_entry - stop_distance
            take_profit = estimated_entry + self.risk_reward * stop_distance
        elif direction == "SHORT":
            stop_loss = estimated_entry + stop_distance
            take_profit = estimated_entry - self.risk_reward * stop_distance
        else:
            raise ConfigError(f"Unsupported NY morning pullback direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid NY morning pullback trade plan risk.")

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

    def _pullback_setup(self, row: pd.Series, impulse_up: bool, impulse_open: float) -> dict[str, Any] | None:
        required = (row["open"], row["close"], row["h1_atr14"])
        if not value_available(*required):
            return None
        open_price = float(row["open"])
        close = float(row["close"])
        trigger_atr = float(row["h1_atr14"])
        if trigger_atr <= 0:
            return None

        if impulse_up:
            counter_close = close < open_price
            holds_origin = close > impulse_open
        else:
            counter_close = close > open_price
            holds_origin = close < impulse_open
        if not (counter_close and holds_origin):
            return None

        return {
            "estimated_entry_price": close,
            "h1_atr14": trigger_atr,
            "trigger_local_hour": int(row["event_local_hour"]),
        }

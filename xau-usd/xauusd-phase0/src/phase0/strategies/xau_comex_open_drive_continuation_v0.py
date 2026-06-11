from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class XauComexOpenDriveContinuationV0Strategy(StrategyBase):
    """Research-only Wave-2 COMEX/NYSE open-hour drive continuation candidate.

    Locked hypothesis: docs/hypothesis_xau_comex_open_drive_continuation_v0.md
    The drive bar is the completed H1 bar with America/New_York bar-end 10:00
    (it contains the 09:30 opens); timestamp_utc equals the bar END.
    """

    name = "xau_comex_open_drive_continuation_v0"
    version = "0.1-research-disabled"

    risk_reward = 2.0
    event_timezone = "America/New_York"
    drive_end_hour = 10
    range_min_atr = 1.30
    min_body_fraction = 0.50
    close_location_fraction = 0.30
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
            drive_rows = day[day["event_local_hour"] == self.drive_end_hour]
            if drive_rows.empty:
                continue
            drive_bar = drive_rows.iloc[0]
            setup = self._drive_setup(drive_bar)
            if setup is None:
                continue

            timestamp = pd.Timestamp(drive_bar["timestamp_utc"])
            direction = setup["direction"]
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"XAU_COMEX_OPEN_DRIVE_CONTINUATION_V0_{direction}",
                    metadata={**setup, "event_local_date": str(local_date)},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        drive_atr = float(signal.metadata["h1_atr14"])
        stop_distance = max(self.stop_atr_multiple * drive_atr, self.stop_floor_price_units)

        if direction == "LONG":
            stop_loss = estimated_entry - stop_distance
            take_profit = estimated_entry + self.risk_reward * stop_distance
        elif direction == "SHORT":
            stop_loss = estimated_entry + stop_distance
            take_profit = estimated_entry - self.risk_reward * stop_distance
        else:
            raise ConfigError(f"Unsupported open drive direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid open drive trade plan risk.")

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

    def _drive_setup(self, row: pd.Series) -> dict[str, Any] | None:
        required = (row["open"], row["high"], row["low"], row["close"], row["h1_atr14"])
        if not value_available(*required):
            return None
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        drive_atr = float(row["h1_atr14"])
        if drive_atr <= 0:
            return None

        candle_range = high - low
        if candle_range <= 0 or candle_range < self.range_min_atr * drive_atr:
            return None
        body_fraction = abs(close - open_price) / candle_range
        if body_fraction < self.min_body_fraction:
            return None
        close_location = (close - low) / candle_range

        if close > open_price and close_location >= 1.0 - self.close_location_fraction:
            direction = "LONG"
        elif close < open_price and close_location <= self.close_location_fraction:
            direction = "SHORT"
        else:
            return None

        return {
            "direction": direction,
            "estimated_entry_price": close,
            "h1_atr14": drive_atr,
            "drive_range_atr_multiple": candle_range / drive_atr,
            "body_fraction": body_fraction,
            "close_location": close_location,
        }

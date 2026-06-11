from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class XauLbmaAmFixFlowV0Strategy(StrategyBase):
    """Research-only Lane B LBMA AM auction post-fix imbalance continuation candidate.

    Locked hypothesis: docs/hypothesis_xau_lbma_am_fix_flow_v0.md
    All windows are defined on completed H1 bars whose timestamp_utc equals the
    bar END converted to Europe/London local time (DST-correct via IANA rules).
    The fix bar is the H1 bar with London bar-end 11:00 (contains the 10:30 auction).
    """

    name = "xau_lbma_am_fix_flow_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.5
    event_timezone = "Europe/London"
    prefix_end_hours = (7, 8, 9, 10)
    fix_end_hour = 11
    range_min_atr = 0.50
    range_max_atr = 3.50
    break_min_atr = 0.15
    close_location_fraction = 0.40
    min_body_fraction = 0.35
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
            prefix = day[day["event_local_hour"].isin(self.prefix_end_hours)]
            if len(prefix) < len(self.prefix_end_hours):
                continue
            prefix_high = float(pd.to_numeric(prefix["high"], errors="coerce").max())
            prefix_low = float(pd.to_numeric(prefix["low"], errors="coerce").min())
            sanity_row = prefix[prefix["event_local_hour"] == self.prefix_end_hours[-1]]
            if sanity_row.empty:
                continue
            sanity_atr = sanity_row.iloc[0]["h1_atr14"]
            if not value_available(prefix_high, prefix_low, sanity_atr):
                continue
            sanity_atr = float(sanity_atr)
            if sanity_atr <= 0:
                continue
            range_width = prefix_high - prefix_low
            if range_width < self.range_min_atr * sanity_atr or range_width > self.range_max_atr * sanity_atr:
                continue

            fix_rows = day[day["event_local_hour"] == self.fix_end_hour]
            if fix_rows.empty:
                continue
            fix_bar = fix_rows.iloc[0]
            setup = self._fix_setup(fix_bar, prefix_high, prefix_low)
            if setup is None:
                continue

            timestamp = pd.Timestamp(fix_bar["timestamp_utc"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=setup["direction"],
                    reason_code=f"XAU_LBMA_AM_FIX_FLOW_V0_{setup['direction']}",
                    metadata={
                        **setup,
                        "event_local_date": str(local_date),
                        "prefix_high": prefix_high,
                        "prefix_low": prefix_low,
                        "prefix_range_width": range_width,
                        "range_sanity_atr": sanity_atr,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        fix_atr = float(signal.metadata["h1_atr14"])
        stop_distance = max(self.stop_atr_multiple * fix_atr, self.stop_floor_price_units)

        if direction == "LONG":
            stop_loss = estimated_entry - stop_distance
            take_profit = estimated_entry + self.risk_reward * stop_distance
        elif direction == "SHORT":
            stop_loss = estimated_entry + stop_distance
            take_profit = estimated_entry - self.risk_reward * stop_distance
        else:
            raise ConfigError(f"Unsupported LBMA AM fix flow direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid LBMA AM fix flow trade plan risk.")

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

    def _fix_setup(self, row: pd.Series, prefix_high: float, prefix_low: float) -> dict[str, Any] | None:
        required = (row["open"], row["high"], row["low"], row["close"], row["h1_atr14"])
        if not value_available(*required):
            return None
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        fix_atr = float(row["h1_atr14"])
        if fix_atr <= 0:
            return None

        candle_range = high - low
        if candle_range <= 0:
            return None
        body_fraction = abs(close - open_price) / candle_range
        if body_fraction < self.min_body_fraction:
            return None
        close_location = (close - low) / candle_range
        break_margin = self.break_min_atr * fix_atr

        if (
            close >= prefix_high + break_margin
            and close > open_price
            and close_location >= 1.0 - self.close_location_fraction
        ):
            direction = "LONG"
        elif (
            close <= prefix_low - break_margin
            and close < open_price
            and close_location <= self.close_location_fraction
        ):
            direction = "SHORT"
        else:
            return None

        return {
            "direction": direction,
            "estimated_entry_price": close,
            "h1_atr14": fix_atr,
            "body_fraction": body_fraction,
            "close_location": close_location,
        }

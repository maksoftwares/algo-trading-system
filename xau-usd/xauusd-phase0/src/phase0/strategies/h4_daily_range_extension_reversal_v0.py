from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    latest_completed_position,
    require_frame,
    value_available,
)


class H4DailyRangeExtensionReversalV0Strategy(StrategyBase):
    """Disabled research strategy for the locked H4 daily range-extension reversal v0 hypothesis."""

    name = "h4_daily_range_extension_reversal_v0"
    version = "0.1-research-disabled"

    decision_hours_utc = {8, 12, 16, 20}
    min_day_extension_prior_range = 0.85
    min_h4_range_atr = 0.60
    close_back_fraction = 0.35
    min_body_ratio = 0.22
    stop_buffer_atr = 0.25
    risk_reward = 1.25
    max_holding_h4_bars = 6

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        h4_open = pd.to_numeric(h4["open"], errors="coerce")
        h4_high = pd.to_numeric(h4["high"], errors="coerce")
        h4_low = pd.to_numeric(h4["low"], errors="coerce")
        h4_close = pd.to_numeric(h4["close"], errors="coerce")

        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(h4_high, h4_low, h4_close, 14)
        if "h4_range" not in h4:
            h4["h4_range"] = h4_high - h4_low
        h4_range = pd.to_numeric(h4["h4_range"], errors="coerce").replace(0.0, pd.NA)
        if "h4_close_position" not in h4:
            h4["h4_close_position"] = (h4_close - h4_low) / h4_range
        if "h4_body_ratio" not in h4:
            h4["h4_body_ratio"] = (h4_close - h4_open).abs() / h4_range

        day_key = _h4_day_key(h4)
        if "h4_utc_day" not in h4:
            h4["h4_utc_day"] = day_key
        if "day_open_so_far" not in h4:
            h4["day_open_so_far"] = h4_open.groupby(day_key, sort=False).transform("first")
        if "day_high_so_far" not in h4:
            h4["day_high_so_far"] = h4_high.groupby(day_key, sort=False).cummax()
        if "day_low_so_far" not in h4:
            h4["day_low_so_far"] = h4_low.groupby(day_key, sort=False).cummin()

        d1_high = pd.to_numeric(d1["high"], errors="coerce")
        d1_low = pd.to_numeric(d1["low"], errors="coerce")
        if "d1_range" not in d1:
            d1["d1_range"] = d1_high - d1_low
        if "prior_d1_range_median20" not in d1:
            d1["prior_d1_range_median20"] = (
                pd.to_numeric(d1["d1_range"], errors="coerce")
                .shift(1)
                .rolling(20, min_periods=20)
                .median()
            )

        context["H4"] = h4
        context["D1"] = d1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        d1 = context["D1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_days: set[str] = set()

        for h4_position in range(40, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            if _utc_hour(timestamp) not in self.decision_hours_utc:
                continue
            d1_state = self._d1_state_at_timestamp(d1, timestamp)
            if d1_state is None:
                continue
            setup = self._setup_at_row(row, d1_state)
            if setup is None:
                continue

            signal_day = str(row["h4_utc_day"])
            if signal_day in used_days:
                continue
            used_days.add(signal_day)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_DAILY_RANGE_EXTENSION_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(h4_position), "signal_day": signal_day},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["day_low_so_far"]) - self.stop_buffer_atr * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["day_high_so_far"]) + self.stop_buffer_atr * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H4 daily range-extension reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4 daily range-extension reversal v0 trade plan risk.")

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
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "planned_time_stop_h4_bars": self.max_holding_h4_bars,
                "max_holding_bars": self.max_holding_h4_bars * 48,
            },
        )

    def _d1_state_at_timestamp(self, d1: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, float] | None:
        d1_position = latest_completed_position(d1, timestamp)
        if d1_position is None or d1_position < 21:
            return None

        row = d1.iloc[d1_position]
        prior_range = row["prior_d1_range_median20"]
        if not value_available(prior_range):
            return None
        prior_range_value = float(prior_range)
        if prior_range_value <= 0:
            return None
        return {"prior_d1_range_median20": prior_range_value, "d1_index": int(d1_position)}

    def _setup_at_row(self, row: pd.Series, d1_state: dict[str, float]) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_range"],
            row["h4_close_position"],
            row["h4_body_ratio"],
            row["day_open_so_far"],
            row["day_high_so_far"],
            row["day_low_so_far"],
            d1_state["prior_d1_range_median20"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_range = float(row["h4_range"])
        close_position = float(row["h4_close_position"])
        body_ratio = float(row["h4_body_ratio"])
        day_open = float(row["day_open_so_far"])
        day_high = float(row["day_high_so_far"])
        day_low = float(row["day_low_so_far"])
        prior_range = float(d1_state["prior_d1_range_median20"])

        if h4_atr <= 0 or h4_range <= 0 or prior_range <= 0:
            return None
        if h4_range < self.min_h4_range_atr * h4_atr or body_ratio < self.min_body_ratio:
            return None

        upside_extension = (day_high - day_open) / prior_range
        downside_extension = (day_open - day_low) / prior_range
        touches_day_high = high >= day_high - 0.10 * h4_atr
        touches_day_low = low <= day_low + 0.10 * h4_atr

        if (
            upside_extension >= self.min_day_extension_prior_range
            and touches_day_high
            and close < open_price
            and close_position <= self.close_back_fraction
        ):
            return {
                **d1_state,
                "direction": "SHORT",
                "extension_direction": "UP",
                "h4_atr14": h4_atr,
                "h4_range": h4_range,
                "h4_close_position": close_position,
                "h4_body_ratio": body_ratio,
                "day_open_so_far": day_open,
                "day_high_so_far": day_high,
                "day_low_so_far": day_low,
                "day_extension_prior_range": upside_extension,
                "estimated_entry_price": close,
            }

        if (
            downside_extension >= self.min_day_extension_prior_range
            and touches_day_low
            and close > open_price
            and close_position >= 1.0 - self.close_back_fraction
        ):
            return {
                **d1_state,
                "direction": "LONG",
                "extension_direction": "DOWN",
                "h4_atr14": h4_atr,
                "h4_range": h4_range,
                "h4_close_position": close_position,
                "h4_body_ratio": body_ratio,
                "day_open_so_far": day_open,
                "day_high_so_far": day_high,
                "day_low_so_far": day_low,
                "day_extension_prior_range": downside_extension,
                "estimated_entry_price": close,
            }

        return None


def _h4_day_key(h4: pd.DataFrame) -> pd.Series:
    source = h4["bar_start_utc"] if "bar_start_utc" in h4 else h4["timestamp_utc"]
    return pd.to_datetime(source, utc=True, errors="coerce").dt.strftime("%Y-%m-%d")


def _utc_hour(timestamp: pd.Timestamp) -> int:
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return int(timestamp.hour)

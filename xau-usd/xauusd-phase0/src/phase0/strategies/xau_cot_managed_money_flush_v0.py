from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.cot_gold_data import COT_FRAME_KEY
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class XauCotManagedMoneyFlushV0Strategy(StrategyBase):
    """Research-only Wave-3 COT managed-money positioning-extreme candidate.

    Locked hypothesis: docs/hypothesis_xau_cot_managed_money_flush_v0.md
    Weekly net managed-money z-score (trailing 156 reports, min 52, 4-day
    availability lag) sets a LONG bias at z <= -1.25 and a SHORT bias at
    z >= +1.25; entry is the first initiative H1 bar with America/New_York
    bar-end 10:00-12:00 in the bias direction. timestamp_utc equals bar END.
    """

    name = "xau_cot_managed_money_flush_v0"
    version = "0.1-research-disabled"

    risk_reward = 2.0
    event_timezone = "America/New_York"
    trigger_end_hours = (10, 11, 12)
    min_body_fraction = 0.35
    z_window_reports = 156
    z_min_reports = 52
    z_entry_threshold = 1.25
    availability_lag_days = 4
    stop_atr_multiple = 1.5
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
        cot = data_context.get(COT_FRAME_KEY)
        if not isinstance(cot, pd.DataFrame) or cot.empty:
            return []
        cot = cot.copy()
        cot["report_date"] = pd.to_datetime(cot["report_date"], utc=True, errors="coerce")
        cot = cot.dropna(subset=["report_date"]).sort_values("report_date").reset_index(drop=True)
        net = (
            pd.to_numeric(cot["managed_money_long_all"], errors="coerce")
            - pd.to_numeric(cot["managed_money_short_all"], errors="coerce")
        )
        rolling_mean = net.rolling(self.z_window_reports, min_periods=self.z_min_reports).mean()
        rolling_std = net.rolling(self.z_window_reports, min_periods=self.z_min_reports).std()
        z_scores = (net - rolling_mean) / rolling_std
        available_from = cot["report_date"] + pd.Timedelta(days=self.availability_lag_days)

        symbol = context_symbol(context)
        signals: list[Signal] = []

        for local_date, day in h1.groupby("event_local_date", sort=True):
            triggers = day[day["event_local_hour"].isin(self.trigger_end_hours)]
            if triggers.empty:
                continue
            date_start_utc = pd.Timestamp(str(local_date), tz=self.event_timezone).tz_convert("UTC")

            eligible = z_scores[available_from <= date_start_utc]
            if eligible.empty:
                continue
            z_value = eligible.iloc[-1]
            if not value_available(z_value):
                continue
            z_value = float(z_value)
            if z_value <= -self.z_entry_threshold:
                bias = "LONG"
            elif z_value >= self.z_entry_threshold:
                bias = "SHORT"
            else:
                continue

            previous_row = None
            for position in range(len(day)):
                row = day.iloc[position]
                if int(row["event_local_hour"]) in self.trigger_end_hours and previous_row is not None:
                    setup = self._initiative_setup(row, previous_row, bias)
                    if setup is not None:
                        timestamp = pd.Timestamp(row["timestamp_utc"])
                        signals.append(
                            Signal(
                                expert=self.name,
                                timestamp_utc=timestamp.to_pydatetime(),
                                symbol=symbol,
                                direction=bias,
                                reason_code=f"XAU_COT_MANAGED_MONEY_FLUSH_V0_{bias}",
                                metadata={
                                    **setup,
                                    "direction": bias,
                                    "event_local_date": str(local_date),
                                    "cot_net_z_score": z_value,
                                },
                            )
                        )
                        break
                previous_row = row
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
            raise ConfigError(f"Unsupported COT flush direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid COT flush trade plan risk.")

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

    def _initiative_setup(self, row: pd.Series, previous_row: pd.Series, bias: str) -> dict[str, Any] | None:
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
        if bias == "LONG":
            if not (close > open_price and close > float(previous_row["high"])):
                return None
        else:
            if not (close < open_price and close < float(previous_row["low"])):
                return None
        return {
            "estimated_entry_price": close,
            "h1_atr14": trigger_atr,
            "body_fraction": body_fraction,
            "trigger_local_hour": int(row["event_local_hour"]),
        }

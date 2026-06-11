from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.macro_real_yield_data import MACRO_FRAME_KEY
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class XauRealYieldRegimeD1TrendV0Strategy(StrategyBase):
    """Research-only Wave-3 real-yield-confirmed daily-trend NY-window continuation.

    Locked hypothesis: docs/hypothesis_xau_real_yield_regime_d1_trend_v0.md
    Trade the D1 EMA20/EMA50 trend only when the 20-observation real-yield change
    (FRED DFII10, macro_proxy frame) confirms it; entry is the first initiative H1
    bar with America/New_York bar-end 10:00-12:00. timestamp_utc equals bar END.
    """

    name = "xau_real_yield_regime_d1_trend_v0"
    version = "0.1-research-disabled"

    risk_reward = 2.0
    event_timezone = "America/New_York"
    trigger_end_hours = (10, 11, 12)
    min_body_fraction = 0.35
    yield_change_observations = 20
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
        macro = data_context.get(MACRO_FRAME_KEY)
        if not isinstance(macro, pd.DataFrame) or macro.empty:
            return []
        macro = macro.copy()
        macro["timestamp_utc"] = pd.to_datetime(macro["timestamp_utc"], utc=True, errors="coerce")
        macro = macro.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc").reset_index(drop=True)
        macro_yield = pd.to_numeric(macro["real_yield_10y"], errors="coerce")

        symbol = context_symbol(context)
        d1_times = d1["timestamp_utc"]
        signals: list[Signal] = []

        for local_date, day in h1.groupby("event_local_date", sort=True):
            triggers = day[day["event_local_hour"].isin(self.trigger_end_hours)]
            if triggers.empty:
                continue
            date_start_utc = pd.Timestamp(str(local_date), tz=self.event_timezone).tz_convert("UTC")

            eligible_d1 = d1[d1_times <= date_start_utc]
            if eligible_d1.empty:
                continue
            state_row = eligible_d1.iloc[-1]
            if not value_available(state_row["d1_ema20"], state_row["d1_ema50"]):
                continue
            if float(state_row["d1_ema20"]) > float(state_row["d1_ema50"]):
                trend = "LONG"
            elif float(state_row["d1_ema20"]) < float(state_row["d1_ema50"]):
                trend = "SHORT"
            else:
                continue

            eligible_macro = macro[macro["timestamp_utc"] <= date_start_utc]
            if len(eligible_macro) <= self.yield_change_observations:
                continue
            latest_yield = macro_yield.iloc[eligible_macro.index[-1]]
            past_yield = macro_yield.iloc[eligible_macro.index[-1 - self.yield_change_observations]]
            if not value_available(latest_yield, past_yield):
                continue
            yield_change = float(latest_yield) - float(past_yield)
            if yield_change < 0:
                regime = "LONG"
            elif yield_change > 0:
                regime = "SHORT"
            else:
                continue
            if regime != trend:
                continue

            previous_row = None
            for position in range(len(day)):
                row = day.iloc[position]
                if int(row["event_local_hour"]) in self.trigger_end_hours and previous_row is not None:
                    setup = self._initiative_setup(row, previous_row, trend)
                    if setup is not None:
                        timestamp = pd.Timestamp(row["timestamp_utc"])
                        signals.append(
                            Signal(
                                expert=self.name,
                                timestamp_utc=timestamp.to_pydatetime(),
                                symbol=symbol,
                                direction=trend,
                                reason_code=f"XAU_REAL_YIELD_REGIME_D1_TREND_V0_{trend}",
                                metadata={
                                    **setup,
                                    "direction": trend,
                                    "event_local_date": str(local_date),
                                    "real_yield_change_20obs": yield_change,
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
            raise ConfigError(f"Unsupported real-yield regime direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid real-yield regime trade plan risk.")

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
        return {
            "estimated_entry_price": close,
            "h1_atr14": trigger_atr,
            "body_fraction": body_fraction,
            "trigger_local_hour": int(row["event_local_hour"]),
        }

from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema, slope
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    latest_completed_position,
    require_frame,
    value_available,
)


class D1MomentumH4PullbackV0Strategy(StrategyBase):
    """Disabled research strategy for the locked D1 momentum / H4 pullback v0 hypothesis."""

    name = "d1_momentum_h4_pullback_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        if "atr14" not in h4:
            h4["atr14"] = atr(h4["high"], h4["low"], h4["close"], 14)
        if "ema20" not in h4:
            h4["ema20"] = ema(h4["close"], 20)

        if "atr14" not in d1:
            d1["atr14"] = atr(d1["high"], d1["low"], d1["close"], 14)
        if "ema20" not in d1:
            d1["ema20"] = ema(d1["close"], 20)
        if "ema50" not in d1:
            d1["ema50"] = ema(d1["close"], 50)
        if "ema20_slope5" not in d1:
            d1["ema20_slope5"] = slope(d1["ema20"], 5)
        if "momentum5" not in d1:
            d1["momentum5"] = pd.to_numeric(d1["close"], errors="coerce") - pd.to_numeric(
                d1["close"], errors="coerce"
            ).shift(5)

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
        used_iso_weeks: set[str] = set()

        for h4_position in range(60, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            state = self._d1_state_at_timestamp(d1, timestamp)
            if state is None:
                continue

            setup = self._setup_at_position(h4, h4_position, state)
            if setup is None:
                continue

            week_key = _iso_week_key(timestamp)
            if week_key in used_iso_weeks:
                continue
            used_iso_weeks.add(week_key)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"D1_MOMENTUM_H4_PULLBACK_V0_{direction}",
                    metadata={
                        **setup,
                        "h4_index": int(h4_position),
                        "iso_week": week_key,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = float(signal.metadata["pullback_low"]) - 0.25 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 2.0 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["pullback_high"]) + 0.25 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 2.0 * risk_price
        else:
            raise ConfigError(f"Unsupported D1 momentum H4 pullback direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid D1 momentum H4 pullback v0 trade plan risk.")

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
            risk_reward=2.0,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry},
        )

    def _d1_state_at_timestamp(self, d1: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, Any] | None:
        d1_position = latest_completed_position(d1, timestamp)
        if d1_position is None or d1_position < 55:
            return None

        row = d1.iloc[d1_position]
        close_raw = row["close"]
        atr_raw = row["atr14"]
        ema20_raw = row["ema20"]
        ema50_raw = row["ema50"]
        slope_raw = row["ema20_slope5"]
        momentum_raw = row["momentum5"]
        if not value_available(close_raw, atr_raw, ema20_raw, ema50_raw, slope_raw, momentum_raw):
            return None

        close = float(close_raw)
        d1_atr = float(atr_raw)
        ema20_value = float(ema20_raw)
        ema50_value = float(ema50_raw)
        ema20_slope = float(slope_raw)
        momentum5 = float(momentum_raw)
        if d1_atr <= 0:
            return None

        if close > ema20_value > ema50_value and ema20_slope > 0 and momentum5 >= 0.25 * d1_atr:
            return {
                "direction": "LONG",
                "d1_index": int(d1_position),
                "d1_close": close,
                "d1_atr14": d1_atr,
                "d1_ema20": ema20_value,
                "d1_ema50": ema50_value,
                "d1_ema20_slope5": ema20_slope,
                "d1_momentum5": momentum5,
            }

        if close < ema20_value < ema50_value and ema20_slope < 0 and momentum5 <= -0.25 * d1_atr:
            return {
                "direction": "SHORT",
                "d1_index": int(d1_position),
                "d1_close": close,
                "d1_atr14": d1_atr,
                "d1_ema20": ema20_value,
                "d1_ema50": ema50_value,
                "d1_ema20_slope5": ema20_slope,
                "d1_momentum5": momentum5,
            }

        return None

    def _setup_at_position(
        self,
        h4: pd.DataFrame,
        h4_position: int,
        d1_state: dict[str, Any],
    ) -> dict[str, Any] | None:
        row = h4.iloc[h4_position]
        prev = h4.iloc[h4_position - 1]
        h4_atr_raw = row["atr14"]
        ema20_raw = row["ema20"]
        if not value_available(h4_atr_raw, ema20_raw):
            return None

        h4_atr = float(h4_atr_raw)
        ema20_value = float(ema20_raw)
        if h4_atr <= 0:
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        prev_close = float(prev["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None

        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.20:
            return None

        direction = str(d1_state["direction"])
        if direction == "LONG":
            pulled_to_ema = low <= ema20_value + 0.35 * h4_atr
            reclaimed_above_ema = close >= ema20_value - 0.05 * h4_atr
            if pulled_to_ema and reclaimed_above_ema and close > open_price and close > prev_close:
                return {
                    **d1_state,
                    "direction": "LONG",
                    "h4_atr14": h4_atr,
                    "h4_ema20": ema20_value,
                    "pullback_high": high,
                    "pullback_low": low,
                    "estimated_entry_price": close,
                    "pullback_body_ratio": body_ratio,
                    "pullback_close_position": close_position,
                }

        if direction == "SHORT":
            pulled_to_ema = high >= ema20_value - 0.35 * h4_atr
            reclaimed_below_ema = close <= ema20_value + 0.05 * h4_atr
            if pulled_to_ema and reclaimed_below_ema and close < open_price and close < prev_close:
                return {
                    **d1_state,
                    "direction": "SHORT",
                    "h4_atr14": h4_atr,
                    "h4_ema20": ema20_value,
                    "pullback_high": high,
                    "pullback_low": low,
                    "estimated_entry_price": close,
                    "pullback_body_ratio": body_ratio,
                    "pullback_close_position": close_position,
                }

        return None


def _iso_week_key(timestamp: pd.Timestamp) -> str:
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    iso = timestamp.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"

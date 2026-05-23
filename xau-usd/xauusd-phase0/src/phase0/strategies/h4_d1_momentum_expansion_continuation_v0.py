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


class H4D1MomentumExpansionContinuationV0Strategy(StrategyBase):
    """Disabled research strategy for the locked H4/D1 momentum expansion continuation v0 hypothesis."""

    name = "h4_d1_momentum_expansion_continuation_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        if "atr14" not in h4:
            h4["atr14"] = atr(h4["high"], h4["low"], h4["close"], 14)
        if "range" not in h4:
            h4["range"] = pd.to_numeric(h4["high"], errors="coerce") - pd.to_numeric(
                h4["low"], errors="coerce"
            )
        if "body" not in h4:
            h4["body"] = (
                pd.to_numeric(h4["close"], errors="coerce")
                - pd.to_numeric(h4["open"], errors="coerce")
            ).abs()
        if "close_position" not in h4:
            h4_range = pd.to_numeric(h4["range"], errors="coerce").replace(0.0, pd.NA)
            h4["close_position"] = (
                pd.to_numeric(h4["close"], errors="coerce") - pd.to_numeric(h4["low"], errors="coerce")
            ) / h4_range
        if "momentum3" not in h4:
            h4["momentum3"] = pd.to_numeric(h4["close"], errors="coerce") - pd.to_numeric(
                h4["close"], errors="coerce"
            ).shift(3)

        if "atr14" not in d1:
            d1["atr14"] = atr(d1["high"], d1["low"], d1["close"], 14)
        if "momentum5" not in d1:
            d1["momentum5"] = pd.to_numeric(d1["close"], errors="coerce") - pd.to_numeric(
                d1["close"], errors="coerce"
            ).shift(5)
        if "up_closes5" not in d1 or "down_closes5" not in d1:
            close_delta = pd.to_numeric(d1["close"], errors="coerce").diff()
            d1["up_closes5"] = (close_delta > 0).rolling(5, min_periods=5).sum()
            d1["down_closes5"] = (close_delta < 0).rolling(5, min_periods=5).sum()

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

        for h4_position in range(30, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            d1_state = self._d1_state_at_timestamp(d1, timestamp)
            if d1_state is None:
                continue

            setup = self._setup_at_position(h4, h4_position, d1_state)
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
                    reason_code=f"H4_D1_MOMENTUM_EXPANSION_CONTINUATION_V0_{direction}",
                    metadata={**setup, "h4_index": int(h4_position), "iso_week": week_key},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = float(signal.metadata["expansion_low"]) - 0.25 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["expansion_high"]) + 0.25 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported H4/D1 momentum expansion direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4/D1 momentum expansion continuation v0 trade plan risk.")

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

    def _d1_state_at_timestamp(self, d1: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, Any] | None:
        d1_position = latest_completed_position(d1, timestamp)
        if d1_position is None or d1_position < 20:
            return None

        row = d1.iloc[d1_position]
        required = (row["atr14"], row["momentum5"], row["up_closes5"], row["down_closes5"])
        if not value_available(*required):
            return None

        d1_atr = float(row["atr14"])
        momentum5 = float(row["momentum5"])
        up_closes5 = float(row["up_closes5"])
        down_closes5 = float(row["down_closes5"])
        if d1_atr <= 0:
            return None

        if momentum5 >= 0.75 * d1_atr and up_closes5 >= 3:
            return {
                "direction": "LONG",
                "d1_index": int(d1_position),
                "d1_atr14": d1_atr,
                "d1_momentum5": momentum5,
                "d1_up_closes5": up_closes5,
                "d1_down_closes5": down_closes5,
            }

        if momentum5 <= -0.75 * d1_atr and down_closes5 >= 3:
            return {
                "direction": "SHORT",
                "d1_index": int(d1_position),
                "d1_atr14": d1_atr,
                "d1_momentum5": momentum5,
                "d1_up_closes5": up_closes5,
                "d1_down_closes5": down_closes5,
            }

        return None

    def _setup_at_position(
        self,
        h4: pd.DataFrame,
        h4_position: int,
        d1_state: dict[str, Any],
    ) -> dict[str, Any] | None:
        row = h4.iloc[h4_position]
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["range"],
            row["body"],
            row["close_position"],
            row["momentum3"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["atr14"])
        candle_range = float(row["range"])
        body = float(row["body"])
        close_position = float(row["close_position"])
        h4_momentum3 = float(row["momentum3"])
        if h4_atr <= 0 or candle_range <= 0:
            return None

        body_ratio = body / candle_range
        if candle_range < 1.10 * h4_atr or body_ratio < 0.50:
            return None

        direction = str(d1_state["direction"])
        if direction == "LONG":
            if close > open_price and close_position >= 0.70 and h4_momentum3 >= 0.25 * h4_atr:
                return {
                    **d1_state,
                    "direction": "LONG",
                    "h4_atr14": h4_atr,
                    "h4_momentum3": h4_momentum3,
                    "expansion_high": high,
                    "expansion_low": low,
                    "estimated_entry_price": close,
                    "expansion_range": candle_range,
                    "expansion_body_ratio": body_ratio,
                    "expansion_close_position": close_position,
                }

        if direction == "SHORT":
            if close < open_price and close_position <= 0.30 and h4_momentum3 <= -0.25 * h4_atr:
                return {
                    **d1_state,
                    "direction": "SHORT",
                    "h4_atr14": h4_atr,
                    "h4_momentum3": h4_momentum3,
                    "expansion_high": high,
                    "expansion_low": low,
                    "estimated_entry_price": close,
                    "expansion_range": candle_range,
                    "expansion_body_ratio": body_ratio,
                    "expansion_close_position": close_position,
                }

        return None


def _iso_week_key(timestamp: pd.Timestamp) -> str:
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    iso = timestamp.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"

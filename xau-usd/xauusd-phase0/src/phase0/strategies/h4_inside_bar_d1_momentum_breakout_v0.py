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


class H4InsideBarD1MomentumBreakoutV0Strategy(StrategyBase):
    """Disabled research strategy for the locked H4 inside-bar D1 momentum breakout v0 hypothesis."""

    name = "h4_inside_bar_d1_momentum_breakout_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        if "atr14" not in h4:
            h4["atr14"] = atr(h4["high"], h4["low"], h4["close"], 14)
        mother_high = pd.to_numeric(h4["high"], errors="coerce").shift(1)
        mother_low = pd.to_numeric(h4["low"], errors="coerce").shift(1)
        mother_range = mother_high - mother_low
        inside_range = pd.to_numeric(h4["high"], errors="coerce") - pd.to_numeric(h4["low"], errors="coerce")
        h4["mother_high"] = mother_high
        h4["mother_low"] = mother_low
        h4["mother_range"] = mother_range
        h4["inside_range"] = inside_range
        h4["is_inside_bar"] = (
            (pd.to_numeric(h4["high"], errors="coerce") <= mother_high)
            & (pd.to_numeric(h4["low"], errors="coerce") >= mother_low)
            & (inside_range <= 0.70 * mother_range)
            & (mother_range >= 0.60 * pd.to_numeric(h4["atr14"], errors="coerce").shift(1))
        )

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
        used_inside_bars: set[tuple[int, str]] = set()

        for h4_position in range(30, len(h4)):
            row = h4.iloc[h4_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            d1_state = self._d1_state_at_timestamp(d1, timestamp)
            if d1_state is None:
                continue

            setup = self._setup_at_position(h4, h4_position, d1_state)
            if setup is None:
                continue

            inside_key = (int(setup["inside_h4_index"]), str(setup["direction"]))
            if inside_key in used_inside_bars:
                continue
            used_inside_bars.add(inside_key)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_INSIDE_BAR_D1_MOMENTUM_BREAKOUT_V0_{direction}",
                    metadata={**setup, "h4_index": int(h4_position)},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = min(float(signal.metadata["inside_low"]), estimated_entry - 0.75 * h4_atr)
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = max(float(signal.metadata["inside_high"]), estimated_entry + 0.75 * h4_atr)
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported H4 inside-bar breakout direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4 inside-bar D1 momentum breakout v0 trade plan risk.")

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

        if momentum5 >= 0.50 * d1_atr and up_closes5 >= 3:
            return {
                "direction": "LONG",
                "d1_index": int(d1_position),
                "d1_atr14": d1_atr,
                "d1_momentum5": momentum5,
                "d1_up_closes5": up_closes5,
                "d1_down_closes5": down_closes5,
            }

        if momentum5 <= -0.50 * d1_atr and down_closes5 >= 3:
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
        inside_position = _latest_recent_inside_position(h4, h4_position)
        if inside_position is None:
            return None

        inside = h4.iloc[inside_position]
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            inside["mother_high"],
            inside["mother_low"],
            inside["mother_range"],
            inside["inside_range"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["atr14"])
        mother_high = float(inside["mother_high"])
        mother_low = float(inside["mother_low"])
        mother_range = float(inside["mother_range"])
        inside_high = float(inside["high"])
        inside_low = float(inside["low"])
        inside_range = float(inside["inside_range"])
        if h4_atr <= 0 or mother_range <= 0 or inside_range <= 0:
            return None

        candle_range = high - low
        if candle_range <= 0 or candle_range > 3.0 * h4_atr:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.35:
            return None

        direction = str(d1_state["direction"])
        if (
            direction == "LONG"
            and close >= mother_high + 0.05 * h4_atr
            and close > open_price
            and close_position >= 0.65
        ):
            return self._metadata(
                "LONG",
                d1_state,
                h4_atr,
                int(inside_position),
                mother_high,
                mother_low,
                mother_range,
                inside_high,
                inside_low,
                inside_range,
                close,
                body_ratio,
                close_position,
            )

        if (
            direction == "SHORT"
            and close <= mother_low - 0.05 * h4_atr
            and close < open_price
            and close_position <= 0.35
        ):
            return self._metadata(
                "SHORT",
                d1_state,
                h4_atr,
                int(inside_position),
                mother_high,
                mother_low,
                mother_range,
                inside_high,
                inside_low,
                inside_range,
                close,
                body_ratio,
                close_position,
            )

        return None

    def _metadata(
        self,
        direction: str,
        d1_state: dict[str, Any],
        h4_atr: float,
        inside_position: int,
        mother_high: float,
        mother_low: float,
        mother_range: float,
        inside_high: float,
        inside_low: float,
        inside_range: float,
        close: float,
        body_ratio: float,
        close_position: float,
    ) -> dict[str, Any]:
        return {
            **d1_state,
            "direction": direction,
            "h4_atr14": h4_atr,
            "inside_h4_index": inside_position,
            "mother_high": mother_high,
            "mother_low": mother_low,
            "mother_range": mother_range,
            "inside_high": inside_high,
            "inside_low": inside_low,
            "inside_range": inside_range,
            "estimated_entry_price": close,
            "breakout_body_ratio": body_ratio,
            "breakout_close_position": close_position,
        }


def _latest_recent_inside_position(
    h4: pd.DataFrame,
    latest_completed_position: int,
    max_age_bars: int = 3,
) -> int | None:
    for position in range(latest_completed_position - 1, max(-1, latest_completed_position - max_age_bars - 1), -1):
        if position < 0 or not bool(h4["is_inside_bar"].iat[position]):
            continue
        return position
    return None

from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import TradePlan
from phase0.strategies.base import value_available
from phase0.strategies.h4_daily_range_extension_reversal_v0 import H4DailyRangeExtensionReversalV0Strategy


class H4DailyRangeExtensionContinuationV0Strategy(H4DailyRangeExtensionReversalV0Strategy):
    """Disabled research strategy for H4 daily range-extension continuation v0."""

    name = "h4_daily_range_extension_continuation_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.40
    close_continue_fraction = 0.65
    max_holding_h4_bars = 5

    def build_trade_plan(self, signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["signal_low"]) - self.stop_buffer_atr * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["signal_high"]) + self.stop_buffer_atr * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H4 daily range-extension continuation direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4 daily range-extension continuation v0 trade plan risk.")

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
            and close > open_price
            and close_position >= self.close_continue_fraction
        ):
            return self._metadata(d1_state, "LONG", "UP", row, upside_extension, close)

        if (
            downside_extension >= self.min_day_extension_prior_range
            and touches_day_low
            and close < open_price
            and close_position <= 1.0 - self.close_continue_fraction
        ):
            return self._metadata(d1_state, "SHORT", "DOWN", row, downside_extension, close)

        return None

    def _metadata(
        self,
        d1_state: dict[str, float],
        direction: str,
        extension_direction: str,
        row: pd.Series,
        extension: float,
        estimated_entry: float,
    ) -> dict[str, Any]:
        return {
            **d1_state,
            "direction": direction,
            "extension_direction": extension_direction,
            "h4_atr14": float(row["h4_atr14"]),
            "h4_range": float(row["h4_range"]),
            "h4_close_position": float(row["h4_close_position"]),
            "h4_body_ratio": float(row["h4_body_ratio"]),
            "day_open_so_far": float(row["day_open_so_far"]),
            "day_high_so_far": float(row["day_high_so_far"]),
            "day_low_so_far": float(row["day_low_so_far"]),
            "day_extension_prior_range": extension,
            "signal_high": float(row["high"]),
            "signal_low": float(row["low"]),
            "estimated_entry_price": estimated_entry,
        }

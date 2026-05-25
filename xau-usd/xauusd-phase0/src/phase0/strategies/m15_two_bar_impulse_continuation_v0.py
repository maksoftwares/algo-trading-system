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
    require_frame,
    value_available,
)


class M15TwoBarImpulseContinuationV0Strategy(StrategyBase):
    """Research-only M15 two-bar impulse continuation candidate."""

    name = "m15_two_bar_impulse_continuation_v0"
    version = "0.1-research-disabled"

    impulse_threshold_atr = 1.55
    min_body_ratio = 0.38
    min_prior_body_ratio = 0.25
    max_final_range_atr = 3.40
    risk_reward = 1.20

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m15 = require_frame(context, "M15")

        if "atr14" not in m15:
            m15["atr14"] = atr(m15["high"], m15["low"], m15["close"], 14)

        open_price = pd.to_numeric(m15["open"], errors="coerce")
        high = pd.to_numeric(m15["high"], errors="coerce")
        low = pd.to_numeric(m15["low"], errors="coerce")
        close = pd.to_numeric(m15["close"], errors="coerce")
        atr14 = pd.to_numeric(m15["atr14"], errors="coerce")
        bar_range = high - low

        m15["m15_bar_range"] = bar_range
        m15["m15_body_ratio"] = (close - open_price).abs() / bar_range.replace(0.0, pd.NA)
        m15["m15_close_position"] = (close - low) / bar_range.replace(0.0, pd.NA)
        m15["m15_impulse_move"] = close - close.shift(2)
        m15["m15_impulse_move_atr"] = m15["m15_impulse_move"] / atr14.replace(0.0, pd.NA)
        m15["m15_final_range_atr"] = bar_range / atr14.replace(0.0, pd.NA)
        m15["m15_prior_body_ratio"] = m15["m15_body_ratio"].shift(1)
        m15["m15_prior_open"] = open_price.shift(1)
        m15["m15_prior_close"] = close.shift(1)
        m15["m15_two_bar_high"] = high.rolling(2).max()
        m15["m15_two_bar_low"] = low.rolling(2).min()

        context["M15"] = m15
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m15 = context["M15"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(30, len(m15)):
            row = m15.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            day_direction = (timestamp.strftime("%Y-%m-%d"), str(setup["direction"]))
            if day_direction in used_day_direction:
                continue
            used_day_direction.add(day_direction)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"M15_TWO_BAR_IMPULSE_CONTINUATION_V0_{direction}",
                    metadata={**setup, "m15_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m15_atr = float(signal.metadata["atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["two_bar_low"]) - 0.25 * m15_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["two_bar_high"]) + 0.25 * m15_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported M15 impulse-continuation direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid M15 two-bar impulse-continuation trade plan risk.")

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
                "max_holding_bars": 48,
                "planned_time_stop_m15_bars": 16,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["m15_impulse_move_atr"],
            row["m15_body_ratio"],
            row["m15_prior_body_ratio"],
            row["m15_close_position"],
            row["m15_final_range_atr"],
            row["m15_prior_open"],
            row["m15_prior_close"],
            row["m15_two_bar_high"],
            row["m15_two_bar_low"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        atr14 = float(row["atr14"])
        impulse_atr = float(row["m15_impulse_move_atr"])
        body_ratio = float(row["m15_body_ratio"])
        prior_body_ratio = float(row["m15_prior_body_ratio"])
        close_position = float(row["m15_close_position"])
        final_range_atr = float(row["m15_final_range_atr"])
        prior_open = float(row["m15_prior_open"])
        prior_close = float(row["m15_prior_close"])
        two_bar_high = float(row["m15_two_bar_high"])
        two_bar_low = float(row["m15_two_bar_low"])

        if atr14 <= 0:
            return None
        if body_ratio < self.min_body_ratio or prior_body_ratio < self.min_prior_body_ratio:
            return None
        if final_range_atr <= 0 or final_range_atr > self.max_final_range_atr:
            return None

        if (
            impulse_atr >= self.impulse_threshold_atr
            and prior_close > prior_open
            and close > open_price
            and close_position >= 0.62
        ):
            return _setup_metadata(row, "LONG", close, two_bar_high, two_bar_low)

        if (
            impulse_atr <= -self.impulse_threshold_atr
            and prior_close < prior_open
            and close < open_price
            and close_position <= 0.38
        ):
            return _setup_metadata(row, "SHORT", close, two_bar_high, two_bar_low)

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    two_bar_high: float,
    two_bar_low: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "m15_open": float(row["open"]),
        "m15_high": float(row["high"]),
        "m15_low": float(row["low"]),
        "m15_close": float(row["close"]),
        "atr14": float(row["atr14"]),
        "impulse_move_atr": float(row["m15_impulse_move_atr"]),
        "body_ratio": float(row["m15_body_ratio"]),
        "prior_body_ratio": float(row["m15_prior_body_ratio"]),
        "close_position": float(row["m15_close_position"]),
        "final_range_atr": float(row["m15_final_range_atr"]),
        "two_bar_high": two_bar_high,
        "two_bar_low": two_bar_low,
    }

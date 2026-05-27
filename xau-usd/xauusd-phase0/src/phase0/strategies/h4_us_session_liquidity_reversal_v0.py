from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H4UsSessionLiquidityReversalV0Strategy(StrategyBase):
    """Disabled research strategy for the locked H4 US-session liquidity reversal v0 hypothesis."""

    name = "h4_us_session_liquidity_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.35
    min_range_atr = 1.35
    close_back_fraction = 0.35
    stop_buffer_atr = 0.15
    lookback_h4_bars = 20
    us_session_end_hours_utc = {16, 20}
    max_holding_h4_bars = 12

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")

        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_range" not in h4:
            h4["h4_range"] = high - low
        if "h4_close_position" not in h4:
            h4_range = pd.to_numeric(h4["h4_range"], errors="coerce").replace(0.0, pd.NA)
            h4["h4_close_position"] = (close - low) / h4_range
        if "h4_upper_wick_ratio" not in h4 or "h4_lower_wick_ratio" not in h4:
            h4_range = pd.to_numeric(h4["h4_range"], errors="coerce").replace(0.0, pd.NA)
            open_price = pd.to_numeric(h4["open"], errors="coerce")
            h4["h4_upper_wick_ratio"] = (high - pd.concat([open_price, close], axis=1).max(axis=1)) / h4_range
            h4["h4_lower_wick_ratio"] = (pd.concat([open_price, close], axis=1).min(axis=1) - low) / h4_range
        if "prior_h4_high_20" not in h4:
            h4["prior_h4_high_20"] = high.shift(1).rolling(self.lookback_h4_bars, min_periods=self.lookback_h4_bars).max()
        if "prior_h4_low_20" not in h4:
            h4["prior_h4_low_20"] = low.shift(1).rolling(self.lookback_h4_bars, min_periods=self.lookback_h4_bars).min()

        context["H4"] = h4
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_days: set[str] = set()

        for position in range(self.lookback_h4_bars + 14, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            signal_day = timestamp.strftime("%Y-%m-%d")
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
                    reason_code=f"H4_US_SESSION_LIQUIDITY_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_day": signal_day},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["liquidity_low"]) - self.stop_buffer_atr * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["liquidity_high"]) + self.stop_buffer_atr * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H4 US-session liquidity reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4 US-session liquidity reversal v0 trade plan risk.")

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
                "max_holding_bars": self.max_holding_h4_bars * 48,
                "planned_time_stop_h4_bars": self.max_holding_h4_bars,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        timestamp = pd.Timestamp(row["timestamp_utc"])
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        if timestamp.hour not in self.us_session_end_hours_utc:
            return None

        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_range"],
            row["h4_close_position"],
            row["h4_upper_wick_ratio"],
            row["h4_lower_wick_ratio"],
            row["prior_h4_high_20"],
            row["prior_h4_low_20"],
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
        upper_wick_ratio = float(row["h4_upper_wick_ratio"])
        lower_wick_ratio = float(row["h4_lower_wick_ratio"])
        prior_high = float(row["prior_h4_high_20"])
        prior_low = float(row["prior_h4_low_20"])
        if h4_atr <= 0 or h4_range <= 0:
            return None
        if h4_range < self.min_range_atr * h4_atr:
            return None

        upside_sweep = high > prior_high + 0.05 * h4_atr
        downside_sweep = low < prior_low - 0.05 * h4_atr
        range_atr = h4_range / h4_atr

        if (
            upside_sweep
            and close < open_price
            and close_position <= self.close_back_fraction
            and upper_wick_ratio >= self.close_back_fraction
        ):
            return {
                "direction": "SHORT",
                "session_end_hour_utc": int(timestamp.hour),
                "h4_atr14": h4_atr,
                "h4_range": h4_range,
                "range_atr": range_atr,
                "close_position": close_position,
                "upper_wick_ratio": upper_wick_ratio,
                "lower_wick_ratio": lower_wick_ratio,
                "prior_h4_high_20": prior_high,
                "prior_h4_low_20": prior_low,
                "liquidity_high": high,
                "liquidity_low": low,
                "estimated_entry_price": close,
                "sweep_direction": "UP",
            }

        if (
            downside_sweep
            and close > open_price
            and close_position >= 1.0 - self.close_back_fraction
            and lower_wick_ratio >= self.close_back_fraction
        ):
            return {
                "direction": "LONG",
                "session_end_hour_utc": int(timestamp.hour),
                "h4_atr14": h4_atr,
                "h4_range": h4_range,
                "range_atr": range_atr,
                "close_position": close_position,
                "upper_wick_ratio": upper_wick_ratio,
                "lower_wick_ratio": lower_wick_ratio,
                "prior_h4_high_20": prior_high,
                "prior_h4_low_20": prior_low,
                "liquidity_high": high,
                "liquidity_low": low,
                "estimated_entry_price": close,
                "sweep_direction": "DOWN",
            }

        return None

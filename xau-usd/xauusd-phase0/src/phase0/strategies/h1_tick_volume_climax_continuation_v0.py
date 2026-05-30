from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H1TickVolumeClimaxContinuationV0Strategy(StrategyBase):
    """Research-only H1 tick-volume participation continuation candidate."""

    name = "h1_tick_volume_climax_continuation_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.45

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")

        close = pd.to_numeric(h1["close"], errors="coerce")
        open_price = pd.to_numeric(h1["open"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        if "atr14" not in h1:
            h1["atr14"] = atr(high, low, close, 14)
        h1["ema21"] = ema(close, 21)
        h1["ema50"] = ema(close, 50)

        tick_count = _tick_count_series(h1)
        prior_mean = tick_count.shift(1).rolling(240, min_periods=80).mean()
        prior_std = tick_count.shift(1).rolling(240, min_periods=80).std()
        prior_median = tick_count.shift(1).rolling(240, min_periods=80).median()
        bar_range = high - low
        atr14 = pd.to_numeric(h1["atr14"], errors="coerce")

        h1["h1_tick_count"] = tick_count
        h1["tick_count_z"] = (tick_count - prior_mean) / prior_std.replace(0.0, pd.NA)
        h1["tick_count_ratio"] = tick_count / prior_median.replace(0.0, pd.NA)
        h1["h1_range_atr"] = bar_range / atr14.replace(0.0, pd.NA)
        h1["h1_body_ratio"] = (close - open_price).abs() / bar_range.replace(0.0, pd.NA)
        h1["h1_close_position"] = (close - low) / bar_range.replace(0.0, pd.NA)
        h1["h1_move_atr"] = (close - open_price) / atr14.replace(0.0, pd.NA)
        h1["h1_return_6"] = np.log(close / close.shift(6))
        h1["h1_return_24"] = np.log(close / close.shift(24))

        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(260, len(h1)):
            row = h1.iloc[position]
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
                    reason_code=f"H1_TICK_VOLUME_CLIMAX_CONTINUATION_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["h1_low"]) - 0.20 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["h1_high"]) + 0.20 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H1 tick-volume continuation direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 tick-volume climax continuation trade plan risk.")

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
                "max_holding_bars": 144,
                "planned_time_stop_h1_bars": 12,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        timestamp = pd.Timestamp(row["timestamp_utc"])
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        if timestamp.weekday() >= 5:
            return None

        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["ema21"],
            row["ema50"],
            row["h1_tick_count"],
            row["tick_count_z"],
            row["tick_count_ratio"],
            row["h1_range_atr"],
            row["h1_body_ratio"],
            row["h1_close_position"],
            row["h1_move_atr"],
            row["h1_return_6"],
            row["h1_return_24"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        atr14 = float(row["atr14"])
        ema21_value = float(row["ema21"])
        ema50_value = float(row["ema50"])
        tick_count_z = float(row["tick_count_z"])
        tick_count_ratio = float(row["tick_count_ratio"])
        h1_range_atr = float(row["h1_range_atr"])
        h1_body_ratio = float(row["h1_body_ratio"])
        h1_close_position = float(row["h1_close_position"])
        h1_move_atr = float(row["h1_move_atr"])
        h1_return_6 = float(row["h1_return_6"])
        h1_return_24 = float(row["h1_return_24"])

        if atr14 <= 0:
            return None
        if tick_count_z < 1.10 or tick_count_ratio < 1.18:
            return None
        if not (0.80 <= h1_range_atr <= 3.80):
            return None
        if h1_body_ratio < 0.45:
            return None
        if abs(h1_return_24) > 0.030:
            return None

        if (
            close > open_price
            and h1_move_atr >= 0.45
            and h1_return_6 >= 0.0010
            and h1_close_position >= 0.72
            and close >= ema21_value
            and ema21_value >= ema50_value * 0.998
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            close < open_price
            and h1_move_atr <= -0.45
            and h1_return_6 <= -0.0010
            and h1_close_position <= 0.28
            and close <= ema21_value
            and ema21_value <= ema50_value * 1.002
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _tick_count_series(h1: pd.DataFrame) -> pd.Series:
    if "tick_count" in h1:
        return pd.to_numeric(h1["tick_count"], errors="coerce")
    if "volume_sum" in h1:
        return pd.to_numeric(h1["volume_sum"], errors="coerce")
    raise ConfigError("h1_tick_volume_climax_continuation_v0 requires H1 tick_count or volume_sum.")


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_open": float(row["open"]),
        "h1_high": float(row["high"]),
        "h1_low": float(row["low"]),
        "h1_close": float(row["close"]),
        "atr14": float(row["atr14"]),
        "ema21": float(row["ema21"]),
        "ema50": float(row["ema50"]),
        "h1_tick_count": float(row["h1_tick_count"]),
        "tick_count_z": float(row["tick_count_z"]),
        "tick_count_ratio": float(row["tick_count_ratio"]),
        "h1_range_atr": float(row["h1_range_atr"]),
        "h1_body_ratio": float(row["h1_body_ratio"]),
        "h1_close_position": float(row["h1_close_position"]),
        "h1_move_atr": float(row["h1_move_atr"]),
        "h1_return_6": float(row["h1_return_6"]),
        "h1_return_24": float(row["h1_return_24"]),
    }

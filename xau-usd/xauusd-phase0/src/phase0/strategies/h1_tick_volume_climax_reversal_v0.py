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


class H1TickVolumeClimaxReversalV0Strategy(StrategyBase):
    """Research-only H1 tick-volume climax reversal candidate."""

    name = "h1_tick_volume_climax_reversal_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")

        if "atr14" not in h1:
            h1["atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)

        tick_count = _tick_count_series(h1)
        prior_mean = tick_count.shift(1).rolling(240, min_periods=80).mean()
        prior_std = tick_count.shift(1).rolling(240, min_periods=80).std()
        prior_median = tick_count.shift(1).rolling(240, min_periods=80).median()
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        open_price = pd.to_numeric(h1["open"], errors="coerce")
        close = pd.to_numeric(h1["close"], errors="coerce")
        bar_range = high - low

        h1["h1_tick_count"] = tick_count
        h1["tick_count_z"] = (tick_count - prior_mean) / prior_std.replace(0.0, pd.NA)
        h1["tick_count_ratio"] = tick_count / prior_median.replace(0.0, pd.NA)
        h1["h1_range_atr"] = bar_range / pd.to_numeric(h1["atr14"], errors="coerce").replace(
            0.0,
            pd.NA,
        )
        h1["h1_body_ratio"] = (close - open_price).abs() / bar_range.replace(0.0, pd.NA)
        h1["h1_close_position"] = (close - low) / bar_range.replace(0.0, pd.NA)

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
                    reason_code=f"H1_TICK_VOLUME_CLIMAX_REVERSAL_V0_{direction}",
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
            stop_loss = float(signal.metadata["h1_low"]) - 0.30 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.50 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["h1_high"]) + 0.30 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.50 * risk_price
        else:
            raise ConfigError(f"Unsupported H1 tick-volume climax direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 tick-volume climax trade plan risk.")

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
            risk_reward=1.50,
            reason_code=signal.reason_code,
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 288,
                "planned_time_stop_h1_bars": 24,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["h1_tick_count"],
            row["tick_count_z"],
            row["tick_count_ratio"],
            row["h1_range_atr"],
            row["h1_body_ratio"],
            row["h1_close_position"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        atr14 = float(row["atr14"])
        tick_count_z = float(row["tick_count_z"])
        tick_count_ratio = float(row["tick_count_ratio"])
        h1_range_atr = float(row["h1_range_atr"])
        h1_body_ratio = float(row["h1_body_ratio"])
        h1_close_position = float(row["h1_close_position"])
        if atr14 <= 0:
            return None
        if tick_count_z < 1.15 or tick_count_ratio < 1.20:
            return None
        if not (0.85 <= h1_range_atr <= 4.20):
            return None
        if h1_body_ratio < 0.25:
            return None

        h1_move_atr = (close - open_price) / atr14
        if h1_move_atr <= -0.45 and 0.22 <= h1_close_position <= 0.68:
            return _setup_metadata(row, "LONG", close)
        if h1_move_atr >= 0.45 and 0.32 <= h1_close_position <= 0.78:
            return _setup_metadata(row, "SHORT", close)
        return None


def _tick_count_series(h1: pd.DataFrame) -> pd.Series:
    if "tick_count" in h1:
        return pd.to_numeric(h1["tick_count"], errors="coerce")
    if "volume_sum" in h1:
        return pd.to_numeric(h1["volume_sum"], errors="coerce")
    raise ConfigError("h1_tick_volume_climax_reversal_v0 requires H1 tick_count or volume_sum.")


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_open": float(row["open"]),
        "h1_high": float(row["high"]),
        "h1_low": float(row["low"]),
        "h1_close": float(row["close"]),
        "atr14": float(row["atr14"]),
        "h1_tick_count": float(row["h1_tick_count"]),
        "tick_count_z": float(row["tick_count_z"]),
        "tick_count_ratio": float(row["tick_count_ratio"]),
        "h1_range_atr": float(row["h1_range_atr"]),
        "h1_body_ratio": float(row["h1_body_ratio"]),
        "h1_close_position": float(row["h1_close_position"]),
    }

from __future__ import annotations

from typing import Any

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


class H1SmoothTrendExhaustionReversalV0Strategy(StrategyBase):
    """Research-only H1 smooth-trend exhaustion reversal candidate."""

    name = "h1_smooth_trend_exhaustion_reversal_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")

        if "atr14" not in h1:
            h1["atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)
        if "ema50" not in h1:
            h1["ema50"] = ema(h1["close"], 50)

        close = pd.to_numeric(h1["close"], errors="coerce")
        open_price = pd.to_numeric(h1["open"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        atr14 = pd.to_numeric(h1["atr14"], errors="coerce")

        range_price = high - low
        body = (close - open_price).abs()
        one_hour_moves = close.diff().abs()
        rolling_path = one_hour_moves.rolling(24, min_periods=24).sum()
        net_move = close - close.shift(24)

        h1["trend_move_24h_atr"] = net_move / atr14.replace(0.0, pd.NA)
        h1["trend_efficiency_24h"] = net_move.abs() / rolling_path.replace(0.0, pd.NA)
        h1["ema50_stretch_atr"] = (close - pd.to_numeric(h1["ema50"], errors="coerce")) / atr14.replace(
            0.0,
            pd.NA,
        )
        h1["signal_range_atr"] = range_price / atr14.replace(0.0, pd.NA)
        h1["signal_body_ratio"] = body / range_price.replace(0.0, pd.NA)
        h1["signal_close_position"] = (close - low) / range_price.replace(0.0, pd.NA)

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

        for position in range(80, len(h1)):
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
                    reason_code=f"H1_SMOOTH_TREND_EXHAUSTION_REVERSAL_V0_{direction}",
                    metadata={**setup, "h1_index": int(position)},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["signal_low"]) - 0.35 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.40 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["signal_high"]) + 0.35 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.40 * risk_price
        else:
            raise ConfigError(f"Unsupported H1 smooth trend exhaustion direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 smooth trend exhaustion trade plan risk.")

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
            risk_reward=1.40,
            reason_code=signal.reason_code,
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 576,
                "planned_time_stop_h1_bars": 48,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["ema50"],
            row["trend_move_24h_atr"],
            row["trend_efficiency_24h"],
            row["ema50_stretch_atr"],
            row["signal_range_atr"],
            row["signal_body_ratio"],
            row["signal_close_position"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        atr14 = float(row["atr14"])
        if atr14 <= 0:
            return None

        trend_move_24h_atr = float(row["trend_move_24h_atr"])
        trend_efficiency_24h = float(row["trend_efficiency_24h"])
        ema50_stretch_atr = float(row["ema50_stretch_atr"])
        signal_range_atr = float(row["signal_range_atr"])
        signal_body_ratio = float(row["signal_body_ratio"])
        signal_close_position = float(row["signal_close_position"])

        if not (0.35 <= signal_range_atr <= 2.60):
            return None
        if trend_efficiency_24h < 0.58 or signal_body_ratio < 0.25:
            return None

        if (
            trend_move_24h_atr <= -2.20
            and ema50_stretch_atr <= -1.00
            and close > open_price
            and signal_close_position >= 0.62
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            trend_move_24h_atr >= 2.20
            and ema50_stretch_atr >= 1.00
            and close < open_price
            and signal_close_position <= 0.38
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "signal_open": float(row["open"]),
        "signal_high": float(row["high"]),
        "signal_low": float(row["low"]),
        "signal_close": float(row["close"]),
        "atr14": float(row["atr14"]),
        "ema50": float(row["ema50"]),
        "trend_move_24h_atr": float(row["trend_move_24h_atr"]),
        "trend_efficiency_24h": float(row["trend_efficiency_24h"]),
        "ema50_stretch_atr": float(row["ema50_stretch_atr"]),
        "signal_range_atr": float(row["signal_range_atr"]),
        "signal_body_ratio": float(row["signal_body_ratio"]),
        "signal_close_position": float(row["signal_close_position"]),
    }

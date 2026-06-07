from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H1VolatilityExpansionPullbackContinuationV0Strategy(StrategyBase):
    """Research-only H1 volatility expansion pullback continuation candidate."""

    name = "h1_volatility_expansion_pullback_continuation_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        close = pd.to_numeric(h1["close"], errors="coerce")
        open_price = pd.to_numeric(h1["open"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")

        h1["atr14"] = atr(high, low, close, 14)
        h1["ema21"] = ema(close, 21)
        h1["ema50"] = ema(close, 50)
        atr14 = pd.to_numeric(h1["atr14"], errors="coerce")

        h1["atr14_percentile240"] = _rolling_last_percentile(atr14, 240).shift(1)
        h1["trend_move_24h_atr"] = (close - close.shift(24)) / atr14.replace(0.0, pd.NA)
        h1["pullback_move_3h_atr"] = (close - close.shift(3)) / atr14.replace(0.0, pd.NA)
        bar_range = high - low
        h1["signal_range_atr"] = bar_range / atr14.replace(0.0, pd.NA)
        h1["signal_body_ratio"] = (close - open_price).abs() / bar_range.replace(0.0, pd.NA)
        h1["signal_close_position"] = (close - low) / bar_range.replace(0.0, pd.NA)
        h1["pullback_low_6"] = low.rolling(6, min_periods=6).min()
        h1["pullback_high_6"] = high.rolling(6, min_periods=6).max()
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

        for position in range(280, len(h1)):
            row = h1.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            direction = str(setup["direction"])
            key = (timestamp.strftime("%Y-%m-%d"), direction)
            if key in used_day_direction:
                continue
            used_day_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_VOL_EXP_PULLBACK_CONTINUATION_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["pullback_low_6"]) - 0.25 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["pullback_high_6"]) + 0.25 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H1 volatility expansion pullback direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 volatility expansion pullback trade plan risk.")

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
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry, "planned_time_stop_h1_bars": 18},
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["ema21"],
            row["ema50"],
            row["atr14_percentile240"],
            row["trend_move_24h_atr"],
            row["pullback_move_3h_atr"],
            row["signal_range_atr"],
            row["signal_body_ratio"],
            row["signal_close_position"],
            row["pullback_low_6"],
            row["pullback_high_6"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        atr14 = float(row["atr14"])
        ema21 = float(row["ema21"])
        ema50 = float(row["ema50"])
        atr_percentile = float(row["atr14_percentile240"])
        trend_move = float(row["trend_move_24h_atr"])
        pullback_move = float(row["pullback_move_3h_atr"])
        range_atr = float(row["signal_range_atr"])
        body_ratio = float(row["signal_body_ratio"])
        close_position = float(row["signal_close_position"])
        if atr14 <= 0:
            return None
        if atr_percentile < 0.70:
            return None
        if not (0.35 <= range_atr <= 2.80) or body_ratio < 0.30:
            return None

        if (
            trend_move >= 2.10
            and -1.25 <= pullback_move <= -0.25
            and close > ema21 > ema50
            and close > open_price
            and close_position >= 0.62
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            trend_move <= -2.10
            and 0.25 <= pullback_move <= 1.25
            and close < ema21 < ema50
            and close < open_price
            and close_position <= 0.38
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _rolling_last_percentile(series: pd.Series, window: int) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")

    def percentile(window_values: np.ndarray) -> float:
        valid = window_values[np.isfinite(window_values)]
        if len(valid) == 0:
            return np.nan
        current = valid[-1]
        return float((valid <= current).sum() / len(valid))

    return values.rolling(window, min_periods=max(60, window // 2)).apply(percentile, raw=True)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "signal_open": float(row["open"]),
        "signal_high": float(row["high"]),
        "signal_low": float(row["low"]),
        "signal_close": float(row["close"]),
        "atr14": float(row["atr14"]),
        "ema21": float(row["ema21"]),
        "ema50": float(row["ema50"]),
        "atr14_percentile240": float(row["atr14_percentile240"]),
        "trend_move_24h_atr": float(row["trend_move_24h_atr"]),
        "pullback_move_3h_atr": float(row["pullback_move_3h_atr"]),
        "signal_range_atr": float(row["signal_range_atr"]),
        "signal_body_ratio": float(row["signal_body_ratio"]),
        "signal_close_position": float(row["signal_close_position"]),
        "pullback_low_6": float(row["pullback_low_6"]),
        "pullback_high_6": float(row["pullback_high_6"]),
    }

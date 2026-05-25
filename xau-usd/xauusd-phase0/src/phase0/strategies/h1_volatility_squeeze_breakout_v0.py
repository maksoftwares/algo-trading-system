from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema, slope
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H1VolatilitySqueezeBreakoutV0Strategy(StrategyBase):
    """Research-only H1 volatility compression breakout candidate."""

    name = "h1_volatility_squeeze_breakout_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.60

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        close = pd.to_numeric(h1["close"], errors="coerce")
        open_price = pd.to_numeric(h1["open"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")

        if "atr14" not in h1:
            h1["atr14"] = atr(high, low, close, 14)
        if "ema50" not in h1:
            h1["ema50"] = ema(close, 50)
        if "ema50_slope12" not in h1:
            h1["ema50_slope12"] = slope(h1["ema50"], 12)

        atr14 = pd.to_numeric(h1["atr14"], errors="coerce")
        rolling_mean = close.rolling(20, min_periods=20).mean()
        rolling_std = close.rolling(20, min_periods=20).std()
        h1["bb_mid20"] = rolling_mean
        h1["bb_upper20"] = rolling_mean + 2.0 * rolling_std
        h1["bb_lower20"] = rolling_mean - 2.0 * rolling_std
        h1["bb_width_atr"] = (4.0 * rolling_std) / atr14.replace(0.0, pd.NA)
        h1["bb_width_percentile240"] = _rolling_last_percentile(h1["bb_width_atr"], 240).shift(1)

        candle_range = high - low
        body = (close - open_price).abs()
        h1["signal_range_atr"] = candle_range / atr14.replace(0.0, pd.NA)
        h1["signal_body_ratio"] = body / candle_range.replace(0.0, pd.NA)
        h1["signal_close_position"] = (close - low) / candle_range.replace(0.0, pd.NA)

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
                    reason_code=f"H1_VOLATILITY_SQUEEZE_BREAKOUT_V0_{direction}",
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
            stop_loss = float(signal.metadata["signal_low"]) - 0.25 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["signal_high"]) + 0.25 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H1 volatility squeeze direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 volatility squeeze breakout trade plan risk.")

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
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["ema50"],
            row["bb_upper20"],
            row["bb_lower20"],
            row["bb_width_atr"],
            row["bb_width_percentile240"],
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
        ema50 = float(row["ema50"])
        upper_band = float(row["bb_upper20"])
        lower_band = float(row["bb_lower20"])
        width_percentile = float(row["bb_width_percentile240"])
        signal_range_atr = float(row["signal_range_atr"])
        signal_body_ratio = float(row["signal_body_ratio"])
        signal_close_position = float(row["signal_close_position"])
        if atr14 <= 0:
            return None
        if width_percentile > 0.25:
            return None
        if not (0.55 <= signal_range_atr <= 3.20):
            return None
        if signal_body_ratio < 0.45:
            return None

        if (
            close > upper_band
            and close > open_price
            and signal_close_position >= 0.70
            and close > ema50
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            close < lower_band
            and close < open_price
            and signal_close_position <= 0.30
            and close < ema50
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

    return values.rolling(window, min_periods=max(30, window // 2)).apply(percentile, raw=True)


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
        "ema50_slope12": float(row["ema50_slope12"]) if pd.notna(row["ema50_slope12"]) else 0.0,
        "bb_mid20": float(row["bb_mid20"]),
        "bb_upper20": float(row["bb_upper20"]),
        "bb_lower20": float(row["bb_lower20"]),
        "bb_width_atr": float(row["bb_width_atr"]),
        "bb_width_percentile240": float(row["bb_width_percentile240"]),
        "signal_range_atr": float(row["signal_range_atr"]),
        "signal_body_ratio": float(row["signal_body_ratio"]),
        "signal_close_position": float(row["signal_close_position"]),
    }

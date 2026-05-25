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


class H1ReturnAutocorrelationStateV0Strategy(StrategyBase):
    """Research-only H1 return-state continuation candidate."""

    name = "h1_return_autocorrelation_state_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")

        if "atr14" not in h1:
            h1["atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)
        if "ema24" not in h1:
            h1["ema24"] = ema(h1["close"], 24)

        close = pd.to_numeric(h1["close"], errors="coerce")
        open_price = pd.to_numeric(h1["open"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        atr14 = pd.to_numeric(h1["atr14"], errors="coerce")
        returns = np.log(close / close.shift(1))
        one_hour_moves = close.diff().abs()
        rolling_path_24h = one_hour_moves.rolling(24, min_periods=24).sum()
        net_move_24h = close - close.shift(24)
        range_price = high - low

        h1["h1_log_return"] = returns
        h1["return_autocorr_72h"] = returns.rolling(72, min_periods=48).corr(returns.shift(1))
        h1["realized_vol_24h"] = returns.rolling(24, min_periods=24).std() * np.sqrt(24)
        h1["realized_vol_120h"] = returns.rolling(120, min_periods=72).std() * np.sqrt(24)
        h1["realized_vol_ratio"] = h1["realized_vol_24h"] / h1["realized_vol_120h"].replace(
            0.0,
            pd.NA,
        )
        h1["momentum_6h_atr"] = (close - close.shift(6)) / atr14.replace(0.0, pd.NA)
        h1["momentum_24h_atr"] = net_move_24h / atr14.replace(0.0, pd.NA)
        h1["directional_efficiency_24h"] = net_move_24h.abs() / rolling_path_24h.replace(
            0.0,
            pd.NA,
        )
        h1["candle_body_ratio"] = (close - open_price).abs() / range_price.replace(0.0, pd.NA)
        h1["candle_close_position"] = (close - low) / range_price.replace(0.0, pd.NA)
        h1["model_state_score"] = _model_state_score(
            h1["return_autocorr_72h"],
            h1["directional_efficiency_24h"],
            h1["realized_vol_ratio"],
        )

        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_week_direction: set[tuple[str, str]] = set()

        for position in range(140, len(h1)):
            row = h1.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            iso = timestamp.isocalendar()
            week_direction = (f"{iso.year}-W{iso.week:02d}", str(setup["direction"]))
            if week_direction in used_week_direction:
                continue
            used_week_direction.add(week_direction)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_RETURN_AUTOCORRELATION_STATE_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "iso_week": week_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.20 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.70 * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.20 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.70 * risk_price
        else:
            raise ConfigError(f"Unsupported H1 return-state direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 return-state trade plan risk.")

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
            risk_reward=1.70,
            reason_code=signal.reason_code,
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 432,
                "planned_time_stop_h1_bars": 36,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["close"],
            row["atr14"],
            row["ema24"],
            row["return_autocorr_72h"],
            row["realized_vol_ratio"],
            row["momentum_6h_atr"],
            row["momentum_24h_atr"],
            row["directional_efficiency_24h"],
            row["candle_body_ratio"],
            row["candle_close_position"],
            row["model_state_score"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        atr14 = float(row["atr14"])
        ema24 = float(row["ema24"])
        return_autocorr = float(row["return_autocorr_72h"])
        realized_vol_ratio = float(row["realized_vol_ratio"])
        momentum_6h_atr = float(row["momentum_6h_atr"])
        momentum_24h_atr = float(row["momentum_24h_atr"])
        directional_efficiency = float(row["directional_efficiency_24h"])
        candle_body_ratio = float(row["candle_body_ratio"])
        candle_close_position = float(row["candle_close_position"])
        model_state_score = float(row["model_state_score"])
        if atr14 <= 0:
            return None
        if not (0.55 <= realized_vol_ratio <= 1.95):
            return None
        if candle_body_ratio < 0.20 or directional_efficiency < 0.24 or return_autocorr < 0.02:
            return None
        if model_state_score < 0.75:
            return None

        if (
            momentum_6h_atr >= 0.45
            and momentum_24h_atr >= 0.80
            and close > ema24
            and close > open_price
            and candle_close_position >= 0.55
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            momentum_6h_atr <= -0.45
            and momentum_24h_atr <= -0.80
            and close < ema24
            and close < open_price
            and candle_close_position <= 0.45
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _model_state_score(
    return_autocorr: pd.Series,
    directional_efficiency: pd.Series,
    realized_vol_ratio: pd.Series,
) -> pd.Series:
    vol_stability = 1.0 - (pd.to_numeric(realized_vol_ratio, errors="coerce") - 1.0).abs()
    return (
        6.0 * pd.to_numeric(return_autocorr, errors="coerce")
        + 1.8 * (pd.to_numeric(directional_efficiency, errors="coerce") - 0.24)
        + 0.35 * vol_stability
    )


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "signal_open": float(row["open"]),
        "signal_close": float(row["close"]),
        "atr14": float(row["atr14"]),
        "ema24": float(row["ema24"]),
        "return_autocorr_72h": float(row["return_autocorr_72h"]),
        "realized_vol_ratio": float(row["realized_vol_ratio"]),
        "momentum_6h_atr": float(row["momentum_6h_atr"]),
        "momentum_24h_atr": float(row["momentum_24h_atr"]),
        "directional_efficiency_24h": float(row["directional_efficiency_24h"]),
        "candle_body_ratio": float(row["candle_body_ratio"]),
        "candle_close_position": float(row["candle_close_position"]),
        "model_state_score": float(row["model_state_score"]),
    }

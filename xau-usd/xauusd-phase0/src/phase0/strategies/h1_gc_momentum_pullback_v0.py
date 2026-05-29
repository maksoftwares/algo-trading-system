from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gc_futures_volume_data import GC_FUTURES_VOLUME_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H1GcMomentumPullbackV0Strategy(StrategyBase):
    """Research-only H1 GC futures momentum with XAU pullback-continuation candidate."""

    name = "h1_gc_momentum_pullback_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50
    gc_return_5d_threshold = 0.0060
    gc_return_20d_threshold = 0.0120
    decision_hours_utc = {7, 11, 15, 19}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        gc_daily = data_context.get(GC_FUTURES_VOLUME_FRAME_KEY)
        if not isinstance(gc_daily, pd.DataFrame):
            raise ConfigError(
                "h1_gc_momentum_pullback_v0 requires data_context['gc_futures_volume'] "
                "with shifted GC continuous futures daily observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        if "h1_atr14" not in h1:
            h1["h1_atr14"] = atr(high, low, close, 14)
        if "h1_ema21" not in h1:
            h1["h1_ema21"] = ema(close, 21)
        if "h1_ema50" not in h1:
            h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_24"] = np.log(close / close.shift(24))

        gc_features = _gc_features_for_h1(h1, gc_daily)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                gc_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
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
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(160, len(h1)):
            row = h1.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            signal_day = timestamp.strftime("%Y-%m-%d")
            day_direction = (signal_day, str(setup["direction"]))
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
                    reason_code=f"H1_GC_MOMENTUM_PULLBACK_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": signal_day},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["h1_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.15 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.15 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported GC momentum pullback direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid GC momentum pullback trade plan risk.")

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
        if timestamp.hour not in self.decision_hours_utc:
            return None

        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h1_atr14"],
            row["h1_ema21"],
            row["h1_ema50"],
            row["h1_return_24"],
            row["gc_return_5d"],
            row["gc_return_20d"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        ema21 = float(row["h1_ema21"])
        ema50 = float(row["h1_ema50"])
        h1_return_24 = float(row["h1_return_24"])
        gc_return_5d = float(row["gc_return_5d"])
        gc_return_20d = float(row["gc_return_20d"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        near_ema21 = low <= ema21 + 0.35 * h1_atr and high >= ema21 - 0.35 * h1_atr

        if (
            gc_return_5d >= self.gc_return_5d_threshold
            and gc_return_20d >= self.gc_return_20d_threshold
            and close >= ema50
            and ema21 >= ema50
            and h1_return_24 >= -0.0010
            and near_ema21
            and close > open_price
            and close_location >= 0.55
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            gc_return_5d <= -self.gc_return_5d_threshold
            and gc_return_20d <= -self.gc_return_20d_threshold
            and close <= ema50
            and ema21 <= ema50
            and h1_return_24 <= 0.0010
            and near_ema21
            and close < open_price
            and close_location <= 0.45
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _gc_features_for_h1(h1: pd.DataFrame, gc_daily: pd.DataFrame) -> pd.DataFrame:
    gc = gc_daily[["timestamp_utc", "close"]].copy()
    gc["timestamp_utc"] = pd.to_datetime(gc["timestamp_utc"], utc=True, errors="coerce")
    gc["gc_close"] = pd.to_numeric(gc["close"], errors="coerce")
    gc = gc.drop(columns=["close"]).dropna().sort_values("timestamp_utc")
    gc = gc.drop_duplicates("timestamp_utc").reset_index(drop=True)
    gc["gc_return_5d"] = np.log(gc["gc_close"] / gc["gc_close"].shift(5))
    gc["gc_return_20d"] = np.log(gc["gc_close"] / gc["gc_close"].shift(20))
    gc["gc_ema20"] = ema(gc["gc_close"], 20)
    gc["gc_ema50"] = ema(gc["gc_close"], 50)
    feature_columns = ["gc_close", "gc_return_5d", "gc_return_20d", "gc_ema20", "gc_ema50"]
    gc[feature_columns] = gc[feature_columns].shift(1)

    h1_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h1)),
        }
    )
    merged = pd.merge_asof(
        h1_times.sort_values("timestamp_utc"),
        gc[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema21": float(row["h1_ema21"]),
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_24": float(row["h1_return_24"]),
        "gc_close": float(row["gc_close"]),
        "gc_return_5d": float(row["gc_return_5d"]),
        "gc_return_20d": float(row["gc_return_20d"]),
        "gc_ema20": float(row["gc_ema20"]),
        "gc_ema50": float(row["gc_ema50"]),
        "close_location": close_location,
    }

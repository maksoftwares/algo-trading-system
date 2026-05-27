from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gc_futures_volume_data import GC_FUTURES_VOLUME_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H4GoldFuturesVolumeClimaxV0Strategy(StrategyBase):
    """Research-only GC futures daily-volume climax candidate."""

    name = "h4_gold_futures_volume_climax_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.55
    volume_percentile_threshold = 0.82
    volume_z_threshold = 1.00
    prior_day_return_threshold = 0.004
    decision_hours_utc = {8, 12, 16}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")
        gc_volume = data_context.get(GC_FUTURES_VOLUME_FRAME_KEY)
        if not isinstance(gc_volume, pd.DataFrame):
            raise ConfigError(
                "h4_gold_futures_volume_climax_v0 requires data_context['gc_futures_volume'] "
                "with GC continuous futures daily volume observations."
            )

        h4_close = pd.to_numeric(h4["close"], errors="coerce")
        h4_high = pd.to_numeric(h4["high"], errors="coerce")
        h4_low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(h4_high, h4_low, h4_close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(h4_close, 40)

        d1_features = _d1_features_for_h4(h4, d1)
        futures_features = _gc_volume_features_for_h4(h4, gc_volume)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                d1_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
                futures_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
        )
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

        for position in range(260, len(h4)):
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
                    reason_code=f"H4_GOLD_FUTURES_VOLUME_CLIMAX_V0_{direction}",
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
            stop_loss = estimated_entry - 1.20 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.20 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported GC futures volume climax direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid GC futures volume climax v0 trade plan risk.")

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
                "max_holding_bars": 384,
                "planned_time_stop_h4_bars": 8,
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
            row["h4_atr14"],
            row["h4_ema40"],
            row["prior_d1_return"],
            row["prior_d1_range_atr"],
            row["gc_volume"],
            row["gc_volume_percentile252"],
            row["gc_volume_z126"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        prior_d1_return = float(row["prior_d1_return"])
        prior_d1_range_atr = float(row["prior_d1_range_atr"])
        volume_percentile = float(row["gc_volume_percentile252"])
        volume_z = float(row["gc_volume_z126"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        volume_climax = (
            volume_percentile >= self.volume_percentile_threshold
            and volume_z >= self.volume_z_threshold
            and prior_d1_range_atr >= 1.10
        )

        if (
            volume_climax
            and prior_d1_return <= -self.prior_day_return_threshold
            and close > open_price
            and close_location >= 0.58
            and close <= h4_ema40 + 0.75 * h4_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            volume_climax
            and prior_d1_return >= self.prior_day_return_threshold
            and close < open_price
            and close_location <= 0.42
            and close >= h4_ema40 - 0.75 * h4_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _gc_volume_features_for_h4(h4: pd.DataFrame, gc_volume: pd.DataFrame) -> pd.DataFrame:
    frame = gc_volume[["timestamp_utc", "volume", "close"]].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    frame["volume"] = pd.to_numeric(frame["volume"], errors="coerce")
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "volume", "close"]).sort_values("timestamp_utc")
    frame = frame.drop_duplicates("timestamp_utc").reset_index(drop=True)
    frame["gc_volume_percentile252"] = _rolling_percentile(frame["volume"], 252)
    frame["gc_volume_z126"] = _rolling_zscore(np.log(frame["volume"].replace(0.0, np.nan)), 126)
    frame["gc_return_1d"] = np.log(frame["close"] / frame["close"].shift(1))
    feature_columns = ["volume", "gc_volume_percentile252", "gc_volume_z126", "gc_return_1d"]
    frame[feature_columns] = frame[feature_columns].shift(1)
    frame = frame.rename(columns={"volume": "gc_volume"})

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        frame[["timestamp_utc", "gc_volume", "gc_volume_percentile252", "gc_volume_z126", "gc_return_1d"]].sort_values(
            "timestamp_utc"
        ),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _d1_features_for_h4(h4: pd.DataFrame, d1: pd.DataFrame) -> pd.DataFrame:
    frame = d1[["timestamp_utc", "open", "high", "low", "close"]].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("open", "high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna().sort_values("timestamp_utc").drop_duplicates("timestamp_utc").reset_index(drop=True)
    frame["d1_atr14"] = atr(frame["high"], frame["low"], frame["close"], 14)
    frame["prior_d1_return"] = np.log(frame["close"] / frame["open"])
    frame["prior_d1_range_atr"] = (frame["high"] - frame["low"]) / frame["d1_atr14"].replace(0.0, np.nan)
    feature_columns = ["prior_d1_return", "prior_d1_range_atr"]
    frame[feature_columns] = frame[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _rolling_percentile(series: pd.Series, window: int) -> pd.Series:
    minimum = max(60, window // 2)

    def percentile(values: np.ndarray) -> float:
        valid = values[np.isfinite(values)]
        if len(valid) == 0:
            return np.nan
        return float(np.sum(valid <= valid[-1]) / len(valid))

    return pd.to_numeric(series, errors="coerce").rolling(window, min_periods=minimum).apply(percentile, raw=True)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    minimum = max(40, window // 2)
    mean = values.rolling(window, min_periods=minimum).mean()
    std = values.rolling(window, min_periods=minimum).std()
    return (values - mean) / std.replace(0.0, np.nan)


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "prior_d1_return": float(row["prior_d1_return"]),
        "prior_d1_range_atr": float(row["prior_d1_range_atr"]),
        "gc_volume": float(row["gc_volume"]),
        "gc_volume_percentile252": float(row["gc_volume_percentile252"]),
        "gc_volume_z126": float(row["gc_volume_z126"]),
        "gc_return_1d": float(row["gc_return_1d"]) if value_available(row["gc_return_1d"]) else float("nan"),
        "close_location": close_location,
    }

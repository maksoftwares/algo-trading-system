from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.tlt_shy_duration_rotation_data import TLT_SHY_DURATION_ROTATION_FRAME_KEY


class H1TltShyDurationRotationFollowthroughV0Strategy(StrategyBase):
    """Research-only H1 XAU follow-through candidate using TLT/SHY duration rotation."""

    name = "h1_tlt_shy_duration_rotation_followthrough_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50
    pressure_threshold = 0.0060
    pressure_z_threshold = 0.35
    pressure_percentile_threshold = 0.55
    decision_hours_utc = {7, 9, 11, 13, 15, 17, 19, 21}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        pressure = data_context.get(TLT_SHY_DURATION_ROTATION_FRAME_KEY)
        if not isinstance(pressure, pd.DataFrame):
            raise ConfigError(
                "h1_tlt_shy_duration_rotation_followthrough_v0 requires "
                "data_context['tlt_shy_duration_rotation'] with shifted TLT/SHY daily observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["h1_ema21"] = ema(close, 21)
        h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_6"] = np.log(close / close.shift(6))
        h1["h1_return_12"] = np.log(close / close.shift(12))
        h1["h1_return_24"] = np.log(close / close.shift(24))

        pressure_features = _duration_features_for_h1(h1, pressure)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                pressure_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(180, len(h1)):
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
                    reason_code=f"H1_TLT_SHY_DURATION_ROTATION_FOLLOWTHROUGH_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["h1_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.05 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.05 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported TLT/SHY duration-rotation direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid TLT/SHY duration-rotation trade plan risk.")

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
                "max_holding_bars": 120,
                "planned_time_stop_h1_bars": 10,
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
            row["h1_return_6"],
            row["h1_return_12"],
            row["h1_return_24"],
            row["duration_pressure_5d"],
            row["duration_pressure_z126"],
            row["duration_pressure_abs_percentile252"],
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
        h1_return_6 = float(row["h1_return_6"])
        h1_return_12 = float(row["h1_return_12"])
        h1_return_24 = float(row["h1_return_24"])
        pressure = float(row["duration_pressure_5d"])
        pressure_z = float(row["duration_pressure_z126"])
        pressure_percentile = float(row["duration_pressure_abs_percentile252"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        pressure_active = (
            abs(pressure) >= self.pressure_threshold
            and abs(pressure_z) >= self.pressure_z_threshold
            and pressure_percentile >= self.pressure_percentile_threshold
        )
        if not pressure_active:
            return None

        if (
            pressure >= self.pressure_threshold
            and close > ema50
            and ema21 >= ema50
            and h1_return_12 >= 0.0015
            and h1_return_6 >= -0.0005
            and h1_return_24 <= 0.0250
            and close > open_price
            and close_location >= 0.60
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            pressure <= -self.pressure_threshold
            and close < ema50
            and ema21 <= ema50
            and h1_return_12 <= -0.0015
            and h1_return_6 <= 0.0005
            and h1_return_24 >= -0.0250
            and close < open_price
            and close_location <= 0.40
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _duration_features_for_h1(h1: pd.DataFrame, pressure: pd.DataFrame) -> pd.DataFrame:
    frame = pressure[["timestamp_utc", "tlt_close", "tlt_volume", "shy_close", "shy_volume"]].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("tlt_close", "tlt_volume", "shy_close", "shy_volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "tlt_close", "shy_close"]).sort_values("timestamp_utc")
    frame = frame.drop_duplicates("timestamp_utc").reset_index(drop=True)
    frame["tlt_return_5d"] = np.log(frame["tlt_close"] / frame["tlt_close"].shift(5))
    frame["shy_return_5d"] = np.log(frame["shy_close"] / frame["shy_close"].shift(5))
    frame["duration_pressure_5d"] = frame["tlt_return_5d"] - frame["shy_return_5d"]
    frame["duration_pressure_z126"] = _rolling_zscore(frame["duration_pressure_5d"], 126)
    frame["duration_pressure_abs_percentile252"] = _rolling_percentile(
        frame["duration_pressure_5d"].abs(),
        252,
    )
    frame["tlt_volume_z126"] = _rolling_zscore(np.log(frame["tlt_volume"].replace(0.0, np.nan)), 126)
    frame["shy_volume_z126"] = _rolling_zscore(np.log(frame["shy_volume"].replace(0.0, np.nan)), 126)
    feature_columns = [
        "tlt_close",
        "tlt_volume",
        "shy_close",
        "shy_volume",
        "tlt_return_5d",
        "shy_return_5d",
        "duration_pressure_5d",
        "duration_pressure_z126",
        "duration_pressure_abs_percentile252",
        "tlt_volume_z126",
        "shy_volume_z126",
    ]
    frame[feature_columns] = frame[feature_columns].shift(1)

    h1_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h1)),
        }
    )
    merged = pd.merge_asof(
        h1_times.sort_values("timestamp_utc"),
        frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _rolling_percentile(series: pd.Series, window: int) -> pd.Series:
    minimum = max(60, window // 2)

    def percentile(values: np.ndarray) -> float:
        current = values[-1]
        return float(np.sum(values <= current) / len(values))

    return series.rolling(window, min_periods=minimum).apply(percentile, raw=True)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    minimum = max(40, window // 2)
    mean = series.rolling(window, min_periods=minimum).mean()
    std = series.rolling(window, min_periods=minimum).std()
    return (series - mean) / std.replace(0.0, np.nan)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float, close_location: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema21": float(row["h1_ema21"]),
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_6": float(row["h1_return_6"]),
        "h1_return_12": float(row["h1_return_12"]),
        "h1_return_24": float(row["h1_return_24"]),
        "close_location": close_location,
        "tlt_close": float(row["tlt_close"]),
        "shy_close": float(row["shy_close"]),
        "tlt_return_5d": float(row["tlt_return_5d"]),
        "shy_return_5d": float(row["shy_return_5d"]),
        "duration_pressure_5d": float(row["duration_pressure_5d"]),
        "duration_pressure_z126": float(row["duration_pressure_z126"]),
        "duration_pressure_abs_percentile252": float(
            row["duration_pressure_abs_percentile252"]
        ),
        "tlt_volume_z126": float(row["tlt_volume_z126"]),
        "shy_volume_z126": float(row["shy_volume_z126"]),
    }

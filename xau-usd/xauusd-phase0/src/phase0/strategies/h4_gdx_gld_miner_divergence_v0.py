from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gdx_gld_relative_data import GDX_GLD_RELATIVE_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H4GdxGldMinerDivergenceV0Strategy(StrategyBase):
    """Research-only H4 gold-miner divergence reversal candidate."""

    name = "h4_gdx_gld_miner_divergence_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50
    relative_return_threshold = 0.012
    relative_z_threshold = 0.85
    relative_percentile_threshold = 0.65
    h4_return_threshold = 0.0030
    decision_hours_utc = {12, 16, 20}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        relative_flow = data_context.get(GDX_GLD_RELATIVE_FRAME_KEY)
        if not isinstance(relative_flow, pd.DataFrame):
            raise ConfigError(
                "h4_gdx_gld_miner_divergence_v0 requires "
                "data_context['gdx_gld_relative_flow'] with GLD/GDX daily observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_12"] = np.log(close / close.shift(12))

        relative_features = _relative_features_for_h4(h4, relative_flow)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                relative_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(260, len(h4)):
            row = h4.iloc[position]
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
                    reason_code=f"H4_GDX_GLD_MINER_DIVERGENCE_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.10 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.10 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported miner divergence direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid miner divergence trade plan risk.")

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
                "max_holding_bars": 288,
                "planned_time_stop_h4_bars": 6,
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
            row["h4_return_12"],
            row["gld_return_1d"],
            row["gdx_return_1d"],
            row["miner_relative_return_1d"],
            row["miner_relative_z126"],
            row["miner_abs_relative_percentile252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_12 = float(row["h4_return_12"])
        relative_return = float(row["miner_relative_return_1d"])
        relative_z = float(row["miner_relative_z126"])
        abs_relative_percentile = float(row["miner_abs_relative_percentile252"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        divergence_active = (
            abs(relative_return) >= self.relative_return_threshold
            and abs(relative_z) >= self.relative_z_threshold
            and abs_relative_percentile >= self.relative_percentile_threshold
        )

        if (
            divergence_active
            and relative_return >= self.relative_return_threshold
            and h4_return_12 <= -self.h4_return_threshold
            and close > open_price
            and close_location >= 0.58
            and close <= h4_ema40 + 0.50 * h4_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            divergence_active
            and relative_return <= -self.relative_return_threshold
            and h4_return_12 >= self.h4_return_threshold
            and close < open_price
            and close_location <= 0.42
            and close >= h4_ema40 - 0.50 * h4_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _relative_features_for_h4(h4: pd.DataFrame, relative_flow: pd.DataFrame) -> pd.DataFrame:
    frame = relative_flow[
        ["timestamp_utc", "gld_close", "gld_volume", "gdx_close", "gdx_volume"]
    ].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("gld_close", "gld_volume", "gdx_close", "gdx_volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "gld_close", "gdx_close"]).sort_values("timestamp_utc")
    frame = frame.drop_duplicates("timestamp_utc").reset_index(drop=True)
    frame["gld_return_1d"] = np.log(frame["gld_close"] / frame["gld_close"].shift(1))
    frame["gdx_return_1d"] = np.log(frame["gdx_close"] / frame["gdx_close"].shift(1))
    frame["miner_relative_return_1d"] = frame["gdx_return_1d"] - frame["gld_return_1d"]
    frame["miner_relative_z126"] = _rolling_zscore(frame["miner_relative_return_1d"], 126)
    frame["miner_abs_relative_percentile252"] = _rolling_percentile(
        frame["miner_relative_return_1d"].abs(),
        252,
    )
    frame["gdx_volume_z126"] = _rolling_zscore(np.log(frame["gdx_volume"].replace(0.0, np.nan)), 126)
    feature_columns = [
        "gld_close",
        "gld_volume",
        "gdx_close",
        "gdx_volume",
        "gld_return_1d",
        "gdx_return_1d",
        "miner_relative_return_1d",
        "miner_relative_z126",
        "miner_abs_relative_percentile252",
        "gdx_volume_z126",
    ]
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
        current = values[-1]
        return float(np.sum(values <= current) / len(values))

    return series.rolling(window, min_periods=minimum).apply(percentile, raw=True)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    minimum = max(40, window // 2)
    mean = series.rolling(window, min_periods=minimum).mean()
    std = series.rolling(window, min_periods=minimum).std()
    return (series - mean) / std.replace(0.0, np.nan)


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
        "h4_return_12": float(row["h4_return_12"]),
        "close_location": close_location,
        "gld_close": float(row["gld_close"]),
        "gdx_close": float(row["gdx_close"]),
        "gld_return_1d": float(row["gld_return_1d"]),
        "gdx_return_1d": float(row["gdx_return_1d"]),
        "miner_relative_return_1d": float(row["miner_relative_return_1d"]),
        "miner_relative_z126": float(row["miner_relative_z126"]),
        "miner_abs_relative_percentile252": float(row["miner_abs_relative_percentile252"]),
        "gdx_volume_z126": float(row["gdx_volume_z126"]),
    }

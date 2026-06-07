from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.btc_risk_pressure_data import BTC_RISK_PRESSURE_FRAME_KEY
from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H4BtcVolumeClimaxGoldReversalV0Strategy(StrategyBase):
    """Research-only H4 XAU reversal candidate gated by shifted BTC volume climax."""

    name = "h4_btc_volume_climax_gold_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.55

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        btc = data_context.get(BTC_RISK_PRESSURE_FRAME_KEY)
        if not isinstance(btc, pd.DataFrame):
            raise ConfigError(f"{self.name} requires data_context['btc_risk_pressure'].")

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema50"] = ema(close, 50)
        h4["h4_return_3"] = np.log(close / close.shift(3))
        h4["h4_return_6"] = np.log(close / close.shift(6))

        btc_features = _btc_volume_climax_features_for_h4(h4, btc)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                btc_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
        used_week_direction: set[tuple[str, str]] = set()

        for position in range(180, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            iso = timestamp.isocalendar()
            direction = str(setup["direction"])
            key = (f"{iso.year}-W{iso.week:02d}", direction)
            if key in used_week_direction:
                continue
            used_week_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_BTC_VOLUME_CLIMAX_GOLD_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_week": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.45 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.45 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported BTC volume-climax direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid BTC volume-climax trade plan risk.")

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
            metadata={**signal.metadata, "max_holding_bars": 288, "planned_time_stop_h4_bars": 7},
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema50"],
            row["h4_return_3"],
            row["h4_return_6"],
            row["btc_return_1d"],
            row["btc_return_3d"],
            row["btc_volume_z126"],
            row["btc_volume_percentile252"],
            row["btc_volume_ratio_5_40"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema50 = float(row["h4_ema50"])
        h4_return_3 = float(row["h4_return_3"])
        h4_return_6 = float(row["h4_return_6"])
        btc_return_1d = float(row["btc_return_1d"])
        btc_return_3d = float(row["btc_return_3d"])
        btc_volume_z = float(row["btc_volume_z126"])
        btc_volume_percentile = float(row["btc_volume_percentile252"])
        btc_volume_ratio = float(row["btc_volume_ratio_5_40"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema50_distance_atr = (close - h4_ema50) / h4_atr
        btc_volume_climax = (
            btc_volume_z >= 0.95
            and btc_volume_percentile >= 0.78
            and btc_volume_ratio >= 1.12
        )
        if not btc_volume_climax:
            return None

        if (
            btc_return_3d <= -0.030
            and btc_return_1d <= 0.012
            and h4_return_6 <= -0.0050
            and h4_return_3 >= -0.0120
            and close > open_price
            and close_location >= 0.58
            and ema50_distance_atr >= -2.50
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema50_distance_atr)

        if (
            btc_return_3d >= 0.030
            and btc_return_1d >= -0.012
            and h4_return_6 >= 0.0050
            and h4_return_3 <= 0.0120
            and close < open_price
            and close_location <= 0.42
            and ema50_distance_atr <= 2.50
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema50_distance_atr)

        return None


def _btc_volume_climax_features_for_h4(h4: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    frame = btc[["timestamp_utc", "btc_close", "btc_volume"]].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("btc_close", "btc_volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "btc_close"]).sort_values("timestamp_utc")
    frame = frame.drop_duplicates("timestamp_utc").reset_index(drop=True)
    frame["btc_return_1d"] = np.log(frame["btc_close"] / frame["btc_close"].shift(1))
    frame["btc_return_3d"] = np.log(frame["btc_close"] / frame["btc_close"].shift(3))
    frame["btc_return_10d"] = np.log(frame["btc_close"] / frame["btc_close"].shift(10))
    log_volume = np.log(frame["btc_volume"].replace(0.0, np.nan))
    frame["btc_volume_z126"] = _rolling_zscore(log_volume, 126)
    frame["btc_volume_percentile252"] = _rolling_percentile(log_volume, 252)
    frame["btc_volume_ratio_5_40"] = (
        frame["btc_volume"].rolling(5, min_periods=4).mean()
        / frame["btc_volume"].rolling(40, min_periods=24).mean().replace(0.0, np.nan)
    )
    feature_columns = [
        "btc_close",
        "btc_volume",
        "btc_return_1d",
        "btc_return_3d",
        "btc_return_10d",
        "btc_volume_z126",
        "btc_volume_percentile252",
        "btc_volume_ratio_5_40",
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
    ema50_distance_atr: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema50": float(row["h4_ema50"]),
        "h4_return_3": float(row["h4_return_3"]),
        "h4_return_6": float(row["h4_return_6"]),
        "close_location": close_location,
        "ema50_distance_atr": ema50_distance_atr,
        "btc_close": float(row["btc_close"]),
        "btc_return_1d": float(row["btc_return_1d"]),
        "btc_return_3d": float(row["btc_return_3d"]),
        "btc_return_10d": float(row["btc_return_10d"]),
        "btc_volume_z126": float(row["btc_volume_z126"]),
        "btc_volume_percentile252": float(row["btc_volume_percentile252"]),
        "btc_volume_ratio_5_40": float(row["btc_volume_ratio_5_40"]),
        "planned_time_stop_h4_bars": 7,
    }

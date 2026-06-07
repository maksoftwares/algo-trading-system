from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.btc_risk_pressure_data import BTC_RISK_PRESSURE_FRAME_KEY
from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h4_btc_volatility_regime_gold_breakout_v0 import _rolling_percentile


class H4BtcWhipsawGoldReversalV0Strategy(StrategyBase):
    """Research-only H4 XAU rejection during shifted BTC whipsaw regimes."""

    name = "h4_btc_whipsaw_gold_reversal_v0"
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
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_3"] = np.log(close / close.shift(3))
        h4["h4_return_6"] = np.log(close / close.shift(6))
        h4["h4_return_12"] = np.log(close / close.shift(12))

        btc_features = _btc_whipsaw_features_for_h4(h4, btc)
        h4 = pd.concat(
            [h4.reset_index(drop=True), btc_features.drop(columns=["timestamp_utc"]).reset_index(drop=True)],
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
        used_three_day_direction: set[tuple[str, str]] = set()

        for position in range(180, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue
            timestamp = pd.Timestamp(row["timestamp_utc"])
            direction = str(setup["direction"])
            bucket = timestamp.floor("D") - pd.Timedelta(days=timestamp.dayofyear % 3)
            key = (bucket.strftime("%Y-%m-%d"), direction)
            if key in used_three_day_direction:
                continue
            used_three_day_direction.add(key)
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"{self.name.upper()}_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_three_day_bucket": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])
        if direction == "LONG":
            stop_loss = estimated_entry - 1.40 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.40 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported BTC whipsaw reversal direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid BTC whipsaw reversal trade plan risk.")
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
            metadata={**signal.metadata, "max_holding_bars": 288, "planned_time_stop_h4_bars": 8},
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_3"],
            row["h4_return_6"],
            row["h4_return_12"],
            row["btc_return_20d"],
            row["btc_path_efficiency_20d"],
            row["btc_vol_ratio_10_40"],
            row["btc_vol_percentile252"],
            row["btc_abs_return_percentile252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_3 = float(row["h4_return_3"])
        h4_return_6 = float(row["h4_return_6"])
        h4_return_12 = float(row["h4_return_12"])
        btc_return_20d = float(row["btc_return_20d"])
        btc_efficiency = float(row["btc_path_efficiency_20d"])
        btc_vol_ratio = float(row["btc_vol_ratio_10_40"])
        btc_vol_percentile = float(row["btc_vol_percentile252"])
        btc_abs_percentile = float(row["btc_abs_return_percentile252"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - h4_ema40) / h4_atr
        btc_whipsaw = (
            btc_efficiency <= 0.42
            and btc_vol_ratio >= 1.04
            and btc_vol_percentile >= 0.55
            and btc_abs_percentile >= 0.45
            and abs(btc_return_20d) <= 0.22
        )
        if not btc_whipsaw:
            return None

        if (
            h4_return_6 <= -0.0030
            and h4_return_12 >= -0.0600
            and h4_return_3 >= -0.0140
            and close > open_price
            and close_location >= 0.56
            and ema40_distance_atr >= -3.10
        ):
            return _metadata(row, "LONG", close, close_location, ema40_distance_atr)

        if (
            h4_return_6 >= 0.0030
            and h4_return_12 <= 0.0600
            and h4_return_3 <= 0.0140
            and close < open_price
            and close_location <= 0.44
            and ema40_distance_atr <= 3.10
        ):
            return _metadata(row, "SHORT", close, close_location, ema40_distance_atr)

        return None


def _btc_whipsaw_features_for_h4(h4: pd.DataFrame, btc: pd.DataFrame) -> pd.DataFrame:
    frame = btc[["timestamp_utc", "btc_close", "btc_volume"]].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    frame["btc_close"] = pd.to_numeric(frame["btc_close"], errors="coerce")
    frame["btc_volume"] = pd.to_numeric(frame["btc_volume"], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "btc_close"]).sort_values("timestamp_utc")
    frame = frame.drop_duplicates("timestamp_utc").reset_index(drop=True)
    frame["btc_return_1d"] = np.log(frame["btc_close"] / frame["btc_close"].shift(1))
    frame["btc_return_20d"] = np.log(frame["btc_close"] / frame["btc_close"].shift(20))
    path_length = frame["btc_return_1d"].abs().rolling(20, min_periods=16).sum()
    frame["btc_path_efficiency_20d"] = frame["btc_return_20d"].abs() / path_length.replace(0.0, np.nan)
    frame["btc_realized_vol_10d"] = frame["btc_return_1d"].rolling(10, min_periods=8).std()
    frame["btc_realized_vol_40d"] = frame["btc_return_1d"].rolling(40, min_periods=24).std()
    frame["btc_vol_ratio_10_40"] = frame["btc_realized_vol_10d"] / frame["btc_realized_vol_40d"].replace(0.0, np.nan)
    frame["btc_vol_percentile252"] = _rolling_percentile(frame["btc_realized_vol_10d"], 252)
    frame["btc_abs_return_percentile252"] = _rolling_percentile(frame["btc_return_1d"].abs(), 252)
    feature_columns = [
        "btc_close",
        "btc_return_1d",
        "btc_return_20d",
        "btc_path_efficiency_20d",
        "btc_realized_vol_10d",
        "btc_realized_vol_40d",
        "btc_vol_ratio_10_40",
        "btc_vol_percentile252",
        "btc_abs_return_percentile252",
    ]
    frame[feature_columns] = frame[feature_columns].shift(1)
    h4_times = pd.DataFrame(
        {"timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"), "_row_order": range(len(h4))}
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema40_distance_atr: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": float(estimated_entry),
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_3": float(row["h4_return_3"]),
        "h4_return_6": float(row["h4_return_6"]),
        "h4_return_12": float(row["h4_return_12"]),
        "close_location": float(close_location),
        "ema40_distance_atr": float(ema40_distance_atr),
        "btc_close": float(row["btc_close"]),
        "btc_return_1d": float(row["btc_return_1d"]),
        "btc_return_20d": float(row["btc_return_20d"]),
        "btc_path_efficiency_20d": float(row["btc_path_efficiency_20d"]),
        "btc_realized_vol_10d": float(row["btc_realized_vol_10d"]),
        "btc_realized_vol_40d": float(row["btc_realized_vol_40d"]),
        "btc_vol_ratio_10_40": float(row["btc_vol_ratio_10_40"]),
        "btc_vol_percentile252": float(row["btc_vol_percentile252"]),
        "btc_abs_return_percentile252": float(row["btc_abs_return_percentile252"]),
        "planned_time_stop_h4_bars": 8,
    }

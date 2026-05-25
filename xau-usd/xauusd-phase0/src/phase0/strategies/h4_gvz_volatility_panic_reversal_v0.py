from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gvz_volatility_data import GVZ_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H4GvzVolatilityPanicReversalV0Strategy(StrategyBase):
    """Research-only H4 gold implied-volatility panic reversal candidate."""

    name = "h4_gvz_volatility_panic_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.60

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        gvz = data_context.get(GVZ_FRAME_KEY)
        if not isinstance(gvz, pd.DataFrame):
            raise ConfigError(
                "h4_gvz_volatility_panic_reversal_v0 requires "
                "data_context['gvz_volatility'] with FRED GVZCLS observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_12"] = np.log(close / close.shift(12))

        gvz_features = _gvz_features_for_h4(h4, gvz)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                gvz_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(80, len(h4)):
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
                    reason_code=f"H4_GVZ_VOLATILITY_PANIC_REVERSAL_V0_{direction}",
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
            stop_loss = estimated_entry - 1.25 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.25 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported GVZ volatility panic direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid GVZ volatility panic trade plan risk.")

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
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_12"],
            row["gvz_close"],
            row["gvz_return_5d"],
            row["gvz_percentile252"],
            row["gvz_return_5d_z126"],
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
        gvz_return_5d = float(row["gvz_return_5d"])
        gvz_percentile = float(row["gvz_percentile252"])
        gvz_return_z = float(row["gvz_return_5d_z126"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        gvz_panic = gvz_percentile >= 0.70 and (gvz_return_5d >= 0.06 or gvz_return_z >= 0.65)

        if (
            gvz_panic
            and h4_return_12 <= -0.004
            and close > open_price
            and close_location >= 0.55
            and close <= h4_ema40 + 0.35 * h4_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            gvz_panic
            and h4_return_12 >= 0.004
            and close < open_price
            and close_location <= 0.45
            and close >= h4_ema40 - 0.35 * h4_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _gvz_features_for_h4(h4: pd.DataFrame, gvz: pd.DataFrame) -> pd.DataFrame:
    gvz_frame = gvz[["timestamp_utc", "gvz_close"]].copy()
    gvz_frame["timestamp_utc"] = pd.to_datetime(
        gvz_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    gvz_frame["gvz_close"] = pd.to_numeric(gvz_frame["gvz_close"], errors="coerce")
    gvz_frame = gvz_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    gvz_frame["gvz_return_5d"] = np.log(gvz_frame["gvz_close"] / gvz_frame["gvz_close"].shift(5))
    gvz_frame["gvz_percentile252"] = _rolling_percentile(gvz_frame["gvz_close"], 252)
    gvz_frame["gvz_return_5d_z126"] = _rolling_zscore(gvz_frame["gvz_return_5d"], 126)

    feature_columns = [
        "gvz_close",
        "gvz_return_5d",
        "gvz_percentile252",
        "gvz_return_5d_z126",
    ]
    gvz_frame[feature_columns] = gvz_frame[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        gvz_frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _rolling_percentile(series: pd.Series, window: int) -> pd.Series:
    minimum = max(40, window // 2)

    def percentile(values: np.ndarray) -> float:
        current = values[-1]
        return float(np.sum(values <= current) / len(values))

    return series.rolling(window, min_periods=minimum).apply(percentile, raw=True)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    minimum = max(30, window // 2)
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
        "gvz_close": float(row["gvz_close"]),
        "gvz_return_5d": float(row["gvz_return_5d"]),
        "gvz_percentile252": float(row["gvz_percentile252"]),
        "gvz_return_5d_z126": float(row["gvz_return_5d_z126"]),
    }

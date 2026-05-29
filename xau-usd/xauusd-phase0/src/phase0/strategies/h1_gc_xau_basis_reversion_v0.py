from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gc_futures_volume_data import GC_FUTURES_VOLUME_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H1GcXauBasisReversionV0Strategy(StrategyBase):
    """Research-only H1 GC futures versus XAU spot basis reversion candidate."""

    name = "h1_gc_xau_basis_reversion_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50
    divergence_threshold = 0.0020
    basis_z_threshold = 0.35
    decision_hours_utc = {7, 11, 15, 19}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        d1 = require_frame(context, "D1")
        gc_daily = data_context.get(GC_FUTURES_VOLUME_FRAME_KEY)
        if not isinstance(gc_daily, pd.DataFrame):
            raise ConfigError(
                "h1_gc_xau_basis_reversion_v0 requires data_context['gc_futures_volume'] "
                "with shifted GC continuous futures daily observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        if "h1_atr14" not in h1:
            h1["h1_atr14"] = atr(high, low, close, 14)
        if "h1_ema40" not in h1:
            h1["h1_ema40"] = ema(close, 40)

        basis_features = _basis_features_for_h1(h1, d1, gc_daily)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                basis_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
                    reason_code=f"H1_GC_XAU_BASIS_REVERSION_V0_{direction}",
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
            stop_loss = estimated_entry - 1.10 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.10 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported GC/XAU basis reversion direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid GC/XAU basis reversion trade plan risk.")

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
                "max_holding_bars": 216,
                "planned_time_stop_h1_bars": 18,
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
            row["h1_ema40"],
            row["gc_return_1d"],
            row["xau_return_1d"],
            row["gc_minus_xau_return_1d"],
            row["gc_xau_basis_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema40 = float(row["h1_ema40"])
        divergence = float(row["gc_minus_xau_return_1d"])
        basis_z = float(row["gc_xau_basis_z252"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range

        if (
            divergence >= self.divergence_threshold
            and basis_z >= self.basis_z_threshold
            and close > open_price
            and close_location >= 0.56
            and close >= h1_ema40 - 0.80 * h1_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            divergence <= -self.divergence_threshold
            and basis_z <= -self.basis_z_threshold
            and close < open_price
            and close_location <= 0.44
            and close <= h1_ema40 + 0.80 * h1_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _basis_features_for_h1(h1: pd.DataFrame, d1: pd.DataFrame, gc_daily: pd.DataFrame) -> pd.DataFrame:
    xau = d1[["timestamp_utc", "close"]].copy()
    xau["timestamp_utc"] = pd.to_datetime(xau["timestamp_utc"], utc=True, errors="coerce")
    xau["xau_d1_close"] = pd.to_numeric(xau["close"], errors="coerce")
    xau = xau.drop(columns=["close"]).dropna().sort_values("timestamp_utc")
    xau = xau.drop_duplicates("timestamp_utc").reset_index(drop=True)

    gc = gc_daily[["timestamp_utc", "close"]].copy()
    gc["timestamp_utc"] = pd.to_datetime(gc["timestamp_utc"], utc=True, errors="coerce")
    gc["gc_close"] = pd.to_numeric(gc["close"], errors="coerce")
    gc = gc.drop(columns=["close"]).dropna().sort_values("timestamp_utc")
    gc = gc.drop_duplicates("timestamp_utc").reset_index(drop=True)

    daily = pd.merge_asof(
        xau.sort_values("timestamp_utc"),
        gc.sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="nearest",
        tolerance=pd.Timedelta(days=3),
    ).dropna(subset=["xau_d1_close", "gc_close"])
    daily["xau_return_1d"] = np.log(daily["xau_d1_close"] / daily["xau_d1_close"].shift(1))
    daily["gc_return_1d"] = np.log(daily["gc_close"] / daily["gc_close"].shift(1))
    daily["gc_minus_xau_return_1d"] = daily["gc_return_1d"] - daily["xau_return_1d"]
    daily["gc_xau_basis"] = np.log(daily["gc_close"] / daily["xau_d1_close"])
    daily["gc_xau_basis_z252"] = _rolling_zscore(daily["gc_xau_basis"], 252)
    feature_columns = [
        "xau_d1_close",
        "gc_close",
        "xau_return_1d",
        "gc_return_1d",
        "gc_minus_xau_return_1d",
        "gc_xau_basis",
        "gc_xau_basis_z252",
    ]
    daily[feature_columns] = daily[feature_columns].shift(1)

    h1_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h1)),
        }
    )
    merged = pd.merge_asof(
        h1_times.sort_values("timestamp_utc"),
        daily[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


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
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema40": float(row["h1_ema40"]),
        "xau_d1_close": float(row["xau_d1_close"]),
        "gc_close": float(row["gc_close"]),
        "xau_return_1d": float(row["xau_return_1d"]),
        "gc_return_1d": float(row["gc_return_1d"]),
        "gc_minus_xau_return_1d": float(row["gc_minus_xau_return_1d"]),
        "gc_xau_basis": float(row["gc_xau_basis"]),
        "gc_xau_basis_z252": float(row["gc_xau_basis_z252"]),
        "close_location": close_location,
    }

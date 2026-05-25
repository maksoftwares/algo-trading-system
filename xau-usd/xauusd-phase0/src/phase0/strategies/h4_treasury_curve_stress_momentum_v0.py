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
from phase0.treasury_curve_data import TREASURY_CURVE_FRAME_KEY


class H4TreasuryCurveStressMomentumV0Strategy(StrategyBase):
    """Research-only H4 nominal Treasury curve stress momentum candidate."""

    name = "h4_treasury_curve_stress_momentum_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.65

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        treasury = data_context.get(TREASURY_CURVE_FRAME_KEY)
        if not isinstance(treasury, pd.DataFrame):
            raise ConfigError(
                "h4_treasury_curve_stress_momentum_v0 requires "
                "data_context['treasury_curve'] with FRED DGS2/DGS10/T10Y2Y observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))

        treasury_features = _treasury_features_for_h4(h4, treasury)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                treasury_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(100, len(h4)):
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
                    reason_code=f"H4_TREASURY_CURVE_STRESS_MOMENTUM_V0_{direction}",
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
            stop_loss = estimated_entry - 1.20 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.20 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported Treasury curve direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid Treasury curve trade plan risk.")

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
                "max_holding_bars": 432,
                "planned_time_stop_h4_bars": 9,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_6"],
            row["dgs2"],
            row["dgs10"],
            row["treasury_10y2y"],
            row["dgs2_change_20d"],
            row["dgs10_change_20d"],
            row["treasury_10y2y_change_20d"],
            row["dgs2_change_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        dgs2_change = float(row["dgs2_change_20d"])
        dgs10_change = float(row["dgs10_change_20d"])
        curve_change = float(row["treasury_10y2y_change_20d"])
        dgs2_change_z = float(row["dgs2_change_z252"])
        if h4_atr <= 0:
            return None

        easing_steepening = (
            dgs2_change <= -0.18
            and dgs10_change <= -0.12
            and (curve_change >= 0.05 or dgs2_change_z <= -0.65)
        )
        tightening_flattening = (
            dgs2_change >= 0.18
            and dgs10_change >= 0.12
            and (curve_change <= -0.05 or dgs2_change_z >= 0.65)
        )

        if easing_steepening and close > h4_ema40 and close > open_price and h4_return_6 > 0.0:
            return _setup_metadata(row, "LONG", close)

        if (
            tightening_flattening
            and close < h4_ema40
            and close < open_price
            and h4_return_6 < 0.0
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _treasury_features_for_h4(h4: pd.DataFrame, treasury: pd.DataFrame) -> pd.DataFrame:
    treasury_frame = treasury[["timestamp_utc", "dgs2", "dgs10", "treasury_10y2y"]].copy()
    treasury_frame["timestamp_utc"] = pd.to_datetime(
        treasury_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    for column in ("dgs2", "dgs10", "treasury_10y2y"):
        treasury_frame[column] = pd.to_numeric(treasury_frame[column], errors="coerce")
    treasury_frame = treasury_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    treasury_frame["dgs2_change_20d"] = treasury_frame["dgs2"] - treasury_frame["dgs2"].shift(20)
    treasury_frame["dgs10_change_20d"] = (
        treasury_frame["dgs10"] - treasury_frame["dgs10"].shift(20)
    )
    treasury_frame["treasury_10y2y_change_20d"] = (
        treasury_frame["treasury_10y2y"] - treasury_frame["treasury_10y2y"].shift(20)
    )
    treasury_frame["dgs2_change_z252"] = _rolling_zscore(
        treasury_frame["dgs2_change_20d"],
        252,
    )

    feature_columns = [
        "dgs2",
        "dgs10",
        "treasury_10y2y",
        "dgs2_change_20d",
        "dgs10_change_20d",
        "treasury_10y2y_change_20d",
        "dgs2_change_z252",
    ]
    treasury_frame[feature_columns] = treasury_frame[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        treasury_frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    minimum = max(40, window // 2)
    mean = series.rolling(window, min_periods=minimum).mean()
    std = series.rolling(window, min_periods=minimum).std()
    return (series - mean) / std.replace(0.0, np.nan)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_6": float(row["h4_return_6"]),
        "dgs2": float(row["dgs2"]),
        "dgs10": float(row["dgs10"]),
        "treasury_10y2y": float(row["treasury_10y2y"]),
        "dgs2_change_20d": float(row["dgs2_change_20d"]),
        "dgs10_change_20d": float(row["dgs10_change_20d"]),
        "treasury_10y2y_change_20d": float(row["treasury_10y2y_change_20d"]),
        "dgs2_change_z252": float(row["dgs2_change_z252"]),
    }

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.credit_spread_data import CREDIT_SPREAD_FRAME_KEY
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H4CreditSpreadStressMomentumV0Strategy(StrategyBase):
    """Research-only H4 corporate credit spread stress momentum candidate."""

    name = "h4_credit_spread_stress_momentum_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.65

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        credit = data_context.get(CREDIT_SPREAD_FRAME_KEY)
        if not isinstance(credit, pd.DataFrame):
            raise ConfigError(
                "h4_credit_spread_stress_momentum_v0 requires "
                "data_context['credit_spread'] with FRED BAA10Y/AAA10Y observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))

        credit_features = _credit_features_for_h4(h4, credit)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                credit_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
                    reason_code=f"H4_CREDIT_SPREAD_STRESS_MOMENTUM_V0_{direction}",
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
            raise ConfigError(f"Unsupported credit spread direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid credit spread trade plan risk.")

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
            row["baa10y"],
            row["aaa10y"],
            row["credit_quality_spread"],
            row["baa10y_change_20d"],
            row["aaa10y_change_20d"],
            row["credit_quality_spread_change_20d"],
            row["baa10y_change_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        baa_change = float(row["baa10y_change_20d"])
        quality_change = float(row["credit_quality_spread_change_20d"])
        baa_change_z = float(row["baa10y_change_z252"])
        if h4_atr <= 0:
            return None

        credit_stress = (
            baa_change >= 0.14 and quality_change >= 0.04
        ) or baa_change_z >= 0.65
        credit_relief = (
            baa_change <= -0.14 and quality_change <= -0.04
        ) or baa_change_z <= -0.65

        if credit_stress and close > h4_ema40 and close > open_price and h4_return_6 > 0.0:
            return _setup_metadata(row, "LONG", close)

        if credit_relief and close < h4_ema40 and close < open_price and h4_return_6 < 0.0:
            return _setup_metadata(row, "SHORT", close)

        return None


def _credit_features_for_h4(h4: pd.DataFrame, credit: pd.DataFrame) -> pd.DataFrame:
    credit_frame = credit[["timestamp_utc", "baa10y", "aaa10y"]].copy()
    credit_frame["timestamp_utc"] = pd.to_datetime(
        credit_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    for column in ("baa10y", "aaa10y"):
        credit_frame[column] = pd.to_numeric(credit_frame[column], errors="coerce")
    credit_frame = credit_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    credit_frame["credit_quality_spread"] = credit_frame["baa10y"] - credit_frame["aaa10y"]
    credit_frame["baa10y_change_20d"] = (
        credit_frame["baa10y"] - credit_frame["baa10y"].shift(20)
    )
    credit_frame["aaa10y_change_20d"] = (
        credit_frame["aaa10y"] - credit_frame["aaa10y"].shift(20)
    )
    credit_frame["credit_quality_spread_change_20d"] = (
        credit_frame["credit_quality_spread"]
        - credit_frame["credit_quality_spread"].shift(20)
    )
    credit_frame["baa10y_change_z252"] = _rolling_zscore(
        credit_frame["baa10y_change_20d"],
        252,
    )

    feature_columns = [
        "baa10y",
        "aaa10y",
        "credit_quality_spread",
        "baa10y_change_20d",
        "aaa10y_change_20d",
        "credit_quality_spread_change_20d",
        "baa10y_change_z252",
    ]
    credit_frame[feature_columns] = credit_frame[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        credit_frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
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
        "baa10y": float(row["baa10y"]),
        "aaa10y": float(row["aaa10y"]),
        "credit_quality_spread": float(row["credit_quality_spread"]),
        "baa10y_change_20d": float(row["baa10y_change_20d"]),
        "aaa10y_change_20d": float(row["aaa10y_change_20d"]),
        "credit_quality_spread_change_20d": float(
            row["credit_quality_spread_change_20d"]
        ),
        "baa10y_change_z252": float(row["baa10y_change_z252"]),
    }

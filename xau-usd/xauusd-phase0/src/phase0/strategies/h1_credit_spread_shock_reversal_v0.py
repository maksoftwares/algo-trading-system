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


class H1CreditSpreadShockReversalV0Strategy(StrategyBase):
    """Research-only H1 corporate credit-spread shock reversal candidate."""

    name = "h1_credit_spread_shock_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.45
    decision_hours_utc = frozenset({7, 9, 11, 13, 15, 17, 19, 21})

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        credit = data_context.get(CREDIT_SPREAD_FRAME_KEY)
        if not isinstance(credit, pd.DataFrame):
            raise ConfigError(
                "h1_credit_spread_shock_reversal_v0 requires "
                "data_context['credit_spread'] with FRED BAA10Y/AAA10Y observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        if "h1_atr14" not in h1:
            h1["h1_atr14"] = atr(high, low, close, 14)
        if "h1_ema50" not in h1:
            h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_8"] = np.log(close / close.shift(8))
        h1["h1_return_24"] = np.log(close / close.shift(24))

        credit_features = _credit_features_for_h1(h1, credit)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                credit_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(100, len(h1)):
            row = h1.iloc[position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            if timestamp.hour not in self.decision_hours_utc:
                continue

            setup = self._setup_at_row(row)
            if setup is None:
                continue

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
                    reason_code=f"H1_CREDIT_SPREAD_SHOCK_REVERSAL_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["h1_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.00 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.00 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported credit shock reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid credit shock reversal trade plan risk.")

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
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h1_atr14"],
            row["h1_ema50"],
            row["h1_return_8"],
            row["h1_return_24"],
            row["baa10y"],
            row["aaa10y"],
            row["credit_quality_spread"],
            row["baa10y_change_10d"],
            row["credit_quality_spread_change_10d"],
            row["baa10y_change_z252"],
            row["credit_quality_spread_change_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema50 = float(row["h1_ema50"])
        h1_return_8 = float(row["h1_return_8"])
        h1_return_24 = float(row["h1_return_24"])
        baa_change = float(row["baa10y_change_10d"])
        quality_change = float(row["credit_quality_spread_change_10d"])
        baa_change_z = float(row["baa10y_change_z252"])
        quality_change_z = float(row["credit_quality_spread_change_z252"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        credit_stress_shock = (
            baa_change >= 0.12 and quality_change >= 0.03
        ) or baa_change_z >= 0.75 or quality_change_z >= 0.75
        credit_relief_shock = (
            baa_change <= -0.12 and quality_change <= -0.03
        ) or baa_change_z <= -0.75 or quality_change_z <= -0.75

        if (
            credit_stress_shock
            and h1_return_24 <= -0.004
            and h1_return_8 >= -0.002
            and close > open_price
            and close_location >= 0.60
            and close <= h1_ema50 * 1.015
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            credit_relief_shock
            and h1_return_24 >= 0.004
            and h1_return_8 <= 0.002
            and close < open_price
            and close_location <= 0.40
            and close >= h1_ema50 * 0.985
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _credit_features_for_h1(h1: pd.DataFrame, credit: pd.DataFrame) -> pd.DataFrame:
    credit_frame = credit[["timestamp_utc", "baa10y", "aaa10y"]].copy()
    credit_frame["timestamp_utc"] = pd.to_datetime(
        credit_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    credit_frame["baa10y"] = pd.to_numeric(credit_frame["baa10y"], errors="coerce")
    credit_frame["aaa10y"] = pd.to_numeric(credit_frame["aaa10y"], errors="coerce")
    credit_frame = credit_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    credit_frame["credit_quality_spread"] = credit_frame["baa10y"] - credit_frame["aaa10y"]
    credit_frame["baa10y_change_10d"] = (
        credit_frame["baa10y"] - credit_frame["baa10y"].shift(10)
    )
    credit_frame["aaa10y_change_10d"] = (
        credit_frame["aaa10y"] - credit_frame["aaa10y"].shift(10)
    )
    credit_frame["credit_quality_spread_change_10d"] = (
        credit_frame["credit_quality_spread"]
        - credit_frame["credit_quality_spread"].shift(10)
    )
    credit_frame["baa10y_change_z252"] = _rolling_zscore(
        credit_frame["baa10y_change_10d"],
        252,
    )
    credit_frame["credit_quality_spread_change_z252"] = _rolling_zscore(
        credit_frame["credit_quality_spread_change_10d"],
        252,
    )

    feature_columns = [
        "baa10y",
        "aaa10y",
        "credit_quality_spread",
        "baa10y_change_10d",
        "aaa10y_change_10d",
        "credit_quality_spread_change_10d",
        "baa10y_change_z252",
        "credit_quality_spread_change_z252",
    ]
    credit_frame[feature_columns] = credit_frame[feature_columns].shift(1)

    h1_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h1)),
        }
    )
    merged = pd.merge_asof(
        h1_times.sort_values("timestamp_utc"),
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
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_8": float(row["h1_return_8"]),
        "h1_return_24": float(row["h1_return_24"]),
        "close_location": close_location,
        "baa10y": float(row["baa10y"]),
        "aaa10y": float(row["aaa10y"]),
        "credit_quality_spread": float(row["credit_quality_spread"]),
        "baa10y_change_10d": float(row["baa10y_change_10d"]),
        "aaa10y_change_10d": float(row["aaa10y_change_10d"]),
        "credit_quality_spread_change_10d": float(
            row["credit_quality_spread_change_10d"]
        ),
        "baa10y_change_z252": float(row["baa10y_change_z252"]),
        "credit_quality_spread_change_z252": float(
            row["credit_quality_spread_change_z252"]
        ),
    }

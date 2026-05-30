from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.inflation_expectations_data import INFLATION_EXPECTATIONS_FRAME_KEY
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H1BreakevenInflationShockReversalV0Strategy(StrategyBase):
    """Research-only H1 breakeven-inflation shock reversal candidate."""

    name = "h1_breakeven_inflation_shock_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.45
    decision_hours_utc = frozenset({7, 9, 11, 13, 15, 17, 19, 21})

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        inflation = data_context.get(INFLATION_EXPECTATIONS_FRAME_KEY)
        if not isinstance(inflation, pd.DataFrame):
            raise ConfigError(
                "h1_breakeven_inflation_shock_reversal_v0 requires "
                "data_context['inflation_expectations'] with FRED T5YIE/T10YIE observations."
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

        inflation_features = _inflation_features_for_h1(h1, inflation)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                inflation_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
                    reason_code=f"H1_BREAKEVEN_INFLATION_SHOCK_REVERSAL_V0_{direction}",
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
            raise ConfigError(f"Unsupported breakeven shock reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid breakeven shock reversal trade plan risk.")

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
            row["breakeven_5y"],
            row["breakeven_10y"],
            row["breakeven_5y_change_10d"],
            row["breakeven_10y_change_10d"],
            row["breakeven_5y_change_z252"],
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
        breakeven_5y_change = float(row["breakeven_5y_change_10d"])
        breakeven_10y_change = float(row["breakeven_10y_change_10d"])
        breakeven_5y_change_z = float(row["breakeven_5y_change_z252"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        inflation_shock = (
            breakeven_5y_change >= 0.08 and breakeven_10y_change >= 0.05
        ) or breakeven_5y_change_z >= 0.75
        disinflation_shock = (
            breakeven_5y_change <= -0.08 and breakeven_10y_change <= -0.05
        ) or breakeven_5y_change_z <= -0.75

        if (
            inflation_shock
            and h1_return_24 <= -0.004
            and h1_return_8 >= -0.002
            and close > open_price
            and close_location >= 0.60
            and close <= h1_ema50 * 1.015
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            disinflation_shock
            and h1_return_24 >= 0.004
            and h1_return_8 <= 0.002
            and close < open_price
            and close_location <= 0.40
            and close >= h1_ema50 * 0.985
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _inflation_features_for_h1(h1: pd.DataFrame, inflation: pd.DataFrame) -> pd.DataFrame:
    inflation_frame = inflation[["timestamp_utc", "breakeven_5y", "breakeven_10y"]].copy()
    inflation_frame["timestamp_utc"] = pd.to_datetime(
        inflation_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    inflation_frame["breakeven_5y"] = pd.to_numeric(
        inflation_frame["breakeven_5y"],
        errors="coerce",
    )
    inflation_frame["breakeven_10y"] = pd.to_numeric(
        inflation_frame["breakeven_10y"],
        errors="coerce",
    )
    inflation_frame = inflation_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    inflation_frame["breakeven_5y_change_10d"] = (
        inflation_frame["breakeven_5y"] - inflation_frame["breakeven_5y"].shift(10)
    )
    inflation_frame["breakeven_10y_change_10d"] = (
        inflation_frame["breakeven_10y"] - inflation_frame["breakeven_10y"].shift(10)
    )
    inflation_frame["breakeven_5y_change_z252"] = _rolling_zscore(
        inflation_frame["breakeven_5y_change_10d"],
        252,
    )
    inflation_frame["breakeven_5y_10y_spread"] = (
        inflation_frame["breakeven_5y"] - inflation_frame["breakeven_10y"]
    )

    feature_columns = [
        "breakeven_5y",
        "breakeven_10y",
        "breakeven_5y_change_10d",
        "breakeven_10y_change_10d",
        "breakeven_5y_change_z252",
        "breakeven_5y_10y_spread",
    ]
    inflation_frame[feature_columns] = inflation_frame[feature_columns].shift(1)

    h1_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h1)),
        }
    )
    merged = pd.merge_asof(
        h1_times.sort_values("timestamp_utc"),
        inflation_frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
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
        "breakeven_5y": float(row["breakeven_5y"]),
        "breakeven_10y": float(row["breakeven_10y"]),
        "breakeven_5y_change_10d": float(row["breakeven_5y_change_10d"]),
        "breakeven_10y_change_10d": float(row["breakeven_10y_change_10d"]),
        "breakeven_5y_change_z252": float(row["breakeven_5y_change_z252"]),
        "breakeven_5y_10y_spread": float(row["breakeven_5y_10y_spread"]),
    }

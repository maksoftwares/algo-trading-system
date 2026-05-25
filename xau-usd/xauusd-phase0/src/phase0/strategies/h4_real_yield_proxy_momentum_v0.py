from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.macro_real_yield_data import MACRO_FRAME_KEY
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H4RealYieldProxyMomentumV0Strategy(StrategyBase):
    """Research-only H4 real-yield and dollar macro momentum candidate."""

    name = "h4_real_yield_proxy_momentum_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.80

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        macro = data_context.get(MACRO_FRAME_KEY)
        if not isinstance(macro, pd.DataFrame):
            raise ConfigError(
                "h4_real_yield_proxy_momentum_v0 requires data_context['macro_proxy'] "
                "with FRED DFII10 and DTWEXBGS observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))

        macro_features = _macro_features_for_h4(h4, macro)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                macro_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(160, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            iso = timestamp.isocalendar()
            week_direction = (f"{iso.year}-W{iso.week:02d}", str(setup["direction"]))
            if week_direction in used_week_direction:
                continue
            used_week_direction.add(week_direction)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_REAL_YIELD_PROXY_MOMENTUM_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_week": week_direction[0]},
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
            raise ConfigError(f"Unsupported real-yield proxy direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid real-yield proxy trade plan risk.")

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
                "max_holding_bars": 576,
                "planned_time_stop_h4_bars": 12,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_6"],
            row["real_yield_change_20d"],
            row["dollar_return_20d"],
            row["real_yield_change_z252"],
            row["dollar_return_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        real_yield_change_20d = float(row["real_yield_change_20d"])
        dollar_return_20d = float(row["dollar_return_20d"])
        real_yield_z = float(row["real_yield_change_z252"])
        dollar_z = float(row["dollar_return_z252"])
        if h4_atr <= 0:
            return None

        if (
            real_yield_change_20d <= -0.20
            and dollar_return_20d <= -0.0075
            and (real_yield_z <= -0.50 or dollar_z <= -0.50)
            and close > h4_ema40
            and close > open_price
            and h4_return_6 > 0.0
        ):
            return _setup_metadata(row, "LONG", close)

        if (
            real_yield_change_20d >= 0.20
            and dollar_return_20d >= 0.0075
            and (real_yield_z >= 0.50 or dollar_z >= 0.50)
            and close < h4_ema40
            and close < open_price
            and h4_return_6 < 0.0
        ):
            return _setup_metadata(row, "SHORT", close)

        return None


def _macro_features_for_h4(h4: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    macro_frame = macro[["timestamp_utc", "real_yield_10y", "dollar_index_broad"]].copy()
    macro_frame["timestamp_utc"] = pd.to_datetime(
        macro_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    macro_frame["real_yield_10y"] = pd.to_numeric(macro_frame["real_yield_10y"], errors="coerce")
    macro_frame["dollar_index_broad"] = pd.to_numeric(
        macro_frame["dollar_index_broad"],
        errors="coerce",
    )
    macro_frame = macro_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    macro_frame["real_yield_change_20d"] = (
        macro_frame["real_yield_10y"] - macro_frame["real_yield_10y"].shift(20)
    )
    macro_frame["dollar_return_20d"] = np.log(
        macro_frame["dollar_index_broad"] / macro_frame["dollar_index_broad"].shift(20)
    )
    macro_frame["real_yield_change_z252"] = _rolling_zscore(
        macro_frame["real_yield_change_20d"],
        252,
    )
    macro_frame["dollar_return_z252"] = _rolling_zscore(macro_frame["dollar_return_20d"], 252)
    feature_columns = [
        "real_yield_10y",
        "dollar_index_broad",
        "real_yield_change_20d",
        "dollar_return_20d",
        "real_yield_change_z252",
        "dollar_return_z252",
    ]
    macro_frame[feature_columns] = macro_frame[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        macro_frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
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
        "real_yield_10y": float(row["real_yield_10y"]),
        "dollar_index_broad": float(row["dollar_index_broad"]),
        "real_yield_change_20d": float(row["real_yield_change_20d"]),
        "dollar_return_20d": float(row["dollar_return_20d"]),
        "real_yield_change_z252": float(row["real_yield_change_z252"]),
        "dollar_return_z252": float(row["dollar_return_z252"]),
    }

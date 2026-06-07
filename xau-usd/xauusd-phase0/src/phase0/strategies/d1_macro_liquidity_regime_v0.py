from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.macro_liquidity_data import MACRO_LIQUIDITY_FRAME_KEY
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class D1MacroLiquidityRegimeV0Strategy(StrategyBase):
    """Research-only D1 macro-liquidity regime with H4 confirmation."""

    name = "d1_macro_liquidity_regime_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.70

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")
        macro = data_context.get(MACRO_LIQUIDITY_FRAME_KEY)
        if not isinstance(macro, pd.DataFrame):
            raise ConfigError(
                "d1_macro_liquidity_regime_v0 requires data_context['macro_liquidity'] "
                "with FRED WALCL and DTWEXBGS observations."
            )

        h4_close = pd.to_numeric(h4["close"], errors="coerce")
        h4_high = pd.to_numeric(h4["high"], errors="coerce")
        h4_low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(h4_high, h4_low, h4_close, 14)
        h4["h4_ema40"] = ema(h4_close, 40)
        h4["h4_return_3"] = np.log(h4_close / h4_close.shift(3))
        h4["h4_return_12"] = np.log(h4_close / h4_close.shift(12))

        d1_close = pd.to_numeric(d1["close"], errors="coerce")
        d1_high = pd.to_numeric(d1["high"], errors="coerce")
        d1_low = pd.to_numeric(d1["low"], errors="coerce")
        d1["d1_atr14"] = atr(d1_high, d1_low, d1_close, 14)
        d1["d1_ema20"] = ema(d1_close, 20)
        d1["d1_return_5"] = np.log(d1_close / d1_close.shift(5))
        d1["d1_return_20"] = np.log(d1_close / d1_close.shift(20))

        macro_features = _macro_liquidity_features_for_h4(h4, macro)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                macro_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
        )
        d1_features = _d1_features_for_h4(h4, d1)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                d1_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
        )
        context["H4"] = h4
        context["D1"] = d1
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
            week_direction = (f"{iso.year}-W{iso.week:02d}", direction)
            if week_direction in used_week_direction:
                continue
            used_week_direction.add(week_direction)
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"D1_MACRO_LIQUIDITY_REGIME_V0_{direction}",
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
            stop_loss = estimated_entry - 1.45 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.45 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported macro-liquidity regime direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid macro-liquidity regime trade plan risk.")
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
            metadata={**signal.metadata, "max_holding_bars": 576, "planned_time_stop_h4_bars": 12},
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
            row["h4_return_12"],
            row["d1_atr14_shifted"],
            row["d1_return_5_shifted"],
            row["d1_return_20_shifted"],
            row["fed_assets_return_13w"],
            row["fed_assets_return_z156w"],
            row["dollar_return_20d"],
            row["dollar_return_z252"],
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
        h4_return_12 = float(row["h4_return_12"])
        d1_atr = float(row["d1_atr14_shifted"])
        d1_return_5 = float(row["d1_return_5_shifted"])
        d1_return_20 = float(row["d1_return_20_shifted"])
        fed_return = float(row["fed_assets_return_13w"])
        fed_z = float(row["fed_assets_return_z156w"])
        dollar_return = float(row["dollar_return_20d"])
        dollar_z = float(row["dollar_return_z252"])
        if h4_atr <= 0 or d1_atr <= 0:
            return None
        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - h4_ema40) / h4_atr

        liquidity_bullish = fed_return >= 0.012 and fed_z >= 0.35 and dollar_return <= -0.0040 and dollar_z <= -0.25
        liquidity_bearish = fed_return <= -0.012 and fed_z <= -0.35 and dollar_return >= 0.0040 and dollar_z >= 0.25

        if (
            liquidity_bullish
            and d1_return_20 >= -0.025
            and d1_return_5 <= 0.018
            and h4_return_12 <= 0.020
            and h4_return_3 >= -0.004
            and close > open_price
            and close_location >= 0.58
            and ema40_distance_atr >= -2.75
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema40_distance_atr)

        if (
            liquidity_bearish
            and d1_return_20 <= 0.025
            and d1_return_5 >= -0.018
            and h4_return_12 >= -0.020
            and h4_return_3 <= 0.004
            and close < open_price
            and close_location <= 0.42
            and ema40_distance_atr <= 2.75
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema40_distance_atr)

        return None


def _macro_liquidity_features_for_h4(h4: pd.DataFrame, macro: pd.DataFrame) -> pd.DataFrame:
    frame = macro[["timestamp_utc", "fed_total_assets", "dollar_index_broad"]].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    frame["fed_total_assets"] = pd.to_numeric(frame["fed_total_assets"], errors="coerce")
    frame["dollar_index_broad"] = pd.to_numeric(frame["dollar_index_broad"], errors="coerce")
    frame = frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    frame["fed_assets_return_13w"] = np.log(frame["fed_total_assets"] / frame["fed_total_assets"].shift(65))
    frame["fed_assets_return_z156w"] = _rolling_zscore(frame["fed_assets_return_13w"], 780)
    frame["dollar_return_20d"] = np.log(frame["dollar_index_broad"] / frame["dollar_index_broad"].shift(20))
    frame["dollar_return_z252"] = _rolling_zscore(frame["dollar_return_20d"], 252)
    feature_columns = [
        "fed_total_assets",
        "dollar_index_broad",
        "fed_assets_return_13w",
        "fed_assets_return_z156w",
        "dollar_return_20d",
        "dollar_return_z252",
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


def _d1_features_for_h4(h4: pd.DataFrame, d1: pd.DataFrame) -> pd.DataFrame:
    columns = ["timestamp_utc", "d1_atr14", "d1_ema20", "d1_return_5", "d1_return_20"]
    frame = d1[columns].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in columns[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    shifted = [column for column in columns[1:]]
    frame[shifted] = frame[shifted].shift(1)
    frame = frame.rename(columns={column: f"{column}_shifted" for column in shifted})
    h4_times = pd.DataFrame(
        {"timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"), "_row_order": range(len(h4))}
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        frame.sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    minimum = max(40, window // 2)
    mean = series.rolling(window, min_periods=minimum).mean()
    std = series.rolling(window, min_periods=minimum).std()
    return (series - mean) / std.replace(0.0, np.nan)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float, close_location: float, ema40_distance_atr: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_3": float(row["h4_return_3"]),
        "h4_return_12": float(row["h4_return_12"]),
        "d1_atr14": float(row["d1_atr14_shifted"]),
        "d1_return_5": float(row["d1_return_5_shifted"]),
        "d1_return_20": float(row["d1_return_20_shifted"]),
        "close_location": close_location,
        "ema40_distance_atr": ema40_distance_atr,
        "fed_total_assets": float(row["fed_total_assets"]),
        "dollar_index_broad": float(row["dollar_index_broad"]),
        "fed_assets_return_13w": float(row["fed_assets_return_13w"]),
        "fed_assets_return_z156w": float(row["fed_assets_return_z156w"]),
        "dollar_return_20d": float(row["dollar_return_20d"]),
        "dollar_return_z252": float(row["dollar_return_z252"]),
    }

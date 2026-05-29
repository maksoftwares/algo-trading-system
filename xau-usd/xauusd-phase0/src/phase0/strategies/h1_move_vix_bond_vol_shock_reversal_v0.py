from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.move_bond_vol_data import MOVE_BOND_VOL_FRAME_KEY
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.vix_risk_data import VIX_FRAME_KEY


class H1MoveVixBondVolShockReversalV0Strategy(StrategyBase):
    """Research-only H1 XAU reversal candidate using MOVE/VIX rates-volatility stress."""

    name = "h1_move_vix_bond_vol_shock_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        move = data_context.get(MOVE_BOND_VOL_FRAME_KEY)
        vix = data_context.get(VIX_FRAME_KEY)
        if not isinstance(move, pd.DataFrame):
            raise ConfigError(
                "h1_move_vix_bond_vol_shock_reversal_v0 requires "
                "data_context['move_bond_vol'] with shifted MOVE observations."
            )
        if not isinstance(vix, pd.DataFrame):
            raise ConfigError(
                "h1_move_vix_bond_vol_shock_reversal_v0 requires "
                "data_context['vix_risk'] with shifted VIXCLS observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["h1_ema40"] = ema(close, 40)
        h1["h1_return_6"] = np.log(close / close.shift(6))
        h1["h1_return_24"] = np.log(close / close.shift(24))

        shock_features = _move_vix_features_for_h1(h1, move, vix)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                shock_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            direction = str(setup["direction"])
            key = (timestamp.strftime("%Y-%m-%d"), direction)
            if key in used_day_direction:
                continue
            used_day_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_MOVE_VIX_BOND_VOL_SHOCK_REVERSAL_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": key[0]},
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
            raise ConfigError(f"Unsupported MOVE/VIX bond-vol shock direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid MOVE/VIX bond-vol shock trade plan risk.")

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
            row["h1_ema40"],
            row["h1_return_6"],
            row["h1_return_24"],
            row["move_close"],
            row["vix_close"],
            row["move_return_5d"],
            row["vix_return_5d"],
            row["move_vix_ratio_z252"],
            row["move_vix_ratio_change_5d"],
            row["move_vix_ratio_change_z126"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema40 = float(row["h1_ema40"])
        h1_return_6 = float(row["h1_return_6"])
        h1_return_24 = float(row["h1_return_24"])
        move_return_5d = float(row["move_return_5d"])
        vix_return_5d = float(row["vix_return_5d"])
        ratio_z = float(row["move_vix_ratio_z252"])
        ratio_change = float(row["move_vix_ratio_change_5d"])
        ratio_change_z = float(row["move_vix_ratio_change_z126"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        bond_vol_shock = (
            move_return_5d >= 0.060
            and move_return_5d > vix_return_5d + 0.015
            and ratio_z >= 0.35
            and (ratio_change >= 0.035 or ratio_change_z >= 0.40)
        )
        if not bond_vol_shock:
            return None

        if (
            h1_return_6 <= -0.0025
            and h1_return_24 >= -0.0300
            and close > open_price
            and close_location >= 0.60
            and close <= h1_ema40 + 0.70 * h1_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            h1_return_6 >= 0.0025
            and h1_return_24 <= 0.0300
            and close < open_price
            and close_location <= 0.40
            and close >= h1_ema40 - 0.70 * h1_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


def _move_vix_features_for_h1(h1: pd.DataFrame, move: pd.DataFrame, vix: pd.DataFrame) -> pd.DataFrame:
    move_frame = _vol_frame(move, "move")
    vix_frame = _vol_frame(vix, "vix")
    vol = pd.merge_asof(
        move_frame.sort_values("timestamp_utc"),
        vix_frame.sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="nearest",
        tolerance=pd.Timedelta(days=3),
    ).dropna(subset=["move_close", "vix_close"])
    vol["move_return_5d"] = np.log(vol["move_close"] / vol["move_close"].shift(5))
    vol["vix_return_5d"] = np.log(vol["vix_close"] / vol["vix_close"].shift(5))
    vol["move_vix_ratio"] = np.log(vol["move_close"] / vol["vix_close"])
    vol["move_vix_ratio_z252"] = _rolling_zscore(vol["move_vix_ratio"], 252)
    vol["move_vix_ratio_change_5d"] = vol["move_vix_ratio"] - vol["move_vix_ratio"].shift(5)
    vol["move_vix_ratio_change_z126"] = _rolling_zscore(vol["move_vix_ratio_change_5d"], 126)

    feature_columns = [
        "move_close",
        "vix_close",
        "move_return_5d",
        "vix_return_5d",
        "move_vix_ratio",
        "move_vix_ratio_z252",
        "move_vix_ratio_change_5d",
        "move_vix_ratio_change_z126",
    ]
    vol[feature_columns] = vol[feature_columns].shift(1)

    h1_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h1)),
        }
    )
    merged = pd.merge_asof(
        h1_times.sort_values("timestamp_utc"),
        vol[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _vol_frame(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    source = frame[["timestamp_utc", f"{prefix}_close"]].copy()
    source["timestamp_utc"] = pd.to_datetime(source["timestamp_utc"], utc=True, errors="coerce")
    source[f"{prefix}_close"] = pd.to_numeric(source[f"{prefix}_close"], errors="coerce")
    return source.dropna().sort_values("timestamp_utc").reset_index(drop=True)


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
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema40": float(row["h1_ema40"]),
        "h1_return_6": float(row["h1_return_6"]),
        "h1_return_24": float(row["h1_return_24"]),
        "close_location": close_location,
        "move_close": float(row["move_close"]),
        "vix_close": float(row["vix_close"]),
        "move_return_5d": float(row["move_return_5d"]),
        "vix_return_5d": float(row["vix_return_5d"]),
        "move_vix_ratio": float(row["move_vix_ratio"]),
        "move_vix_ratio_z252": float(row["move_vix_ratio_z252"]),
        "move_vix_ratio_change_5d": float(row["move_vix_ratio_change_5d"]),
        "move_vix_ratio_change_z126": float(row["move_vix_ratio_change_z126"]),
    }

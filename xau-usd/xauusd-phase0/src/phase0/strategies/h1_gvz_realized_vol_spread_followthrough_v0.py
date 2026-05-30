from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gvz_volatility_data import GVZ_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h1_gvz_realized_vol_spread_reversal_v0 import (
    _gvz_realized_features_for_h1,
)


class H1GvzRealizedVolSpreadFollowthroughV0Strategy(StrategyBase):
    """Research-only H1 GVZ versus realized-volatility spread follow-through candidate."""

    name = "h1_gvz_realized_vol_spread_followthrough_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.50
    decision_hours_utc = frozenset({6, 8, 10, 12, 14, 16, 18, 20})

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        gvz = data_context.get(GVZ_FRAME_KEY)
        if not isinstance(gvz, pd.DataFrame):
            raise ConfigError(
                "h1_gvz_realized_vol_spread_followthrough_v0 requires "
                "data_context['gvz_volatility'] with FRED GVZCLS observations."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["h1_ema40"] = ema(close, 40)
        h1["h1_log_return"] = np.log(close / close.shift(1))
        h1["h1_return_8"] = np.log(close / close.shift(8))
        h1["h1_return_24"] = np.log(close / close.shift(24))
        h1["h1_realized_vol_72h"] = h1["h1_log_return"].rolling(72, min_periods=36).std()
        h1["h1_realized_vol_ann_pct"] = h1["h1_realized_vol_72h"] * np.sqrt(24 * 252) * 100.0

        gvz_features = _gvz_realized_features_for_h1(h1, gvz)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                gvz_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(120, len(h1)):
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
                    reason_code=f"H1_GVZ_REALIZED_VOL_SPREAD_FOLLOWTHROUGH_V0_{direction}",
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
            stop_loss = estimated_entry - 1.05 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.05 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported GVZ-realized follow-through direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid GVZ-realized spread follow-through trade plan risk.")

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
            row["h1_return_8"],
            row["h1_return_24"],
            row["h1_realized_vol_ann_pct"],
            row["gvz_close"],
            row["gvz_return_5d"],
            row["gvz_percentile252"],
            row["gvz_realized_spread"],
            row["gvz_realized_spread_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema40 = float(row["h1_ema40"])
        h1_return_8 = float(row["h1_return_8"])
        h1_return_24 = float(row["h1_return_24"])
        gvz_return_5d = float(row["gvz_return_5d"])
        gvz_percentile = float(row["gvz_percentile252"])
        spread = float(row["gvz_realized_spread"])
        spread_z = float(row["gvz_realized_spread_z252"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        volatility_premium = (
            gvz_percentile >= 0.65
            and gvz_return_5d >= 0.03
            and (spread >= 4.0 or spread_z >= 0.45)
        )
        if not volatility_premium:
            return None

        if (
            h1_return_24 >= 0.004
            and h1_return_8 >= -0.001
            and close > open_price
            and close_location >= 0.58
            and close >= h1_ema40 - 0.75 * h1_atr
        ):
            return _setup_metadata(row, "LONG", close, close_location)

        if (
            h1_return_24 <= -0.004
            and h1_return_8 <= 0.001
            and close < open_price
            and close_location <= 0.42
            and close <= h1_ema40 + 0.75 * h1_atr
        ):
            return _setup_metadata(row, "SHORT", close, close_location)

        return None


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
        "h1_return_8": float(row["h1_return_8"]),
        "h1_return_24": float(row["h1_return_24"]),
        "h1_realized_vol_ann_pct": float(row["h1_realized_vol_ann_pct"]),
        "close_location": close_location,
        "gvz_close": float(row["gvz_close"]),
        "gvz_return_5d": float(row["gvz_return_5d"]),
        "gvz_percentile252": float(row["gvz_percentile252"]),
        "gvz_realized_spread": float(row["gvz_realized_spread"]),
        "gvz_realized_spread_z252": float(row["gvz_realized_spread_z252"]),
    }

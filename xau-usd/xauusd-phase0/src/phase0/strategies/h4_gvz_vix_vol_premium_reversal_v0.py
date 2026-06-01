from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gvz_volatility_data import GVZ_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h1_gvz_vix_vol_premium_reversal_v0 import _gvz_vix_features_for_h1
from phase0.vix_risk_data import VIX_FRAME_KEY


class H4GvzVixVolPremiumReversalV0Strategy(StrategyBase):
    """Research-only H4 gold-volatility-premium reversal candidate."""

    name = "h4_gvz_vix_vol_premium_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.55

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        gvz = data_context.get(GVZ_FRAME_KEY)
        vix = data_context.get(VIX_FRAME_KEY)
        if not isinstance(gvz, pd.DataFrame):
            raise ConfigError(
                "h4_gvz_vix_vol_premium_reversal_v0 requires "
                "data_context['gvz_volatility'] with FRED GVZCLS observations."
            )
        if not isinstance(vix, pd.DataFrame):
            raise ConfigError(
                "h4_gvz_vix_vol_premium_reversal_v0 requires "
                "data_context['vix_risk'] with FRED VIXCLS observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))
        h4["h4_return_12"] = np.log(close / close.shift(12))

        premium_features = _gvz_vix_features_for_h1(h4, gvz, vix)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                premium_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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

        for position in range(120, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            iso = timestamp.isocalendar()
            direction = str(setup["direction"])
            key = (f"{iso.year}-W{iso.week:02d}", direction)
            if key in used_week_direction:
                continue
            used_week_direction.add(key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_GVZ_VIX_VOL_PREMIUM_REVERSAL_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_week": key[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 1.15 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.15 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported GVZ/VIX H4 vol-premium reversal direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid GVZ/VIX H4 vol-premium reversal trade plan risk.")

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
                "max_holding_bars": 336,
                "planned_time_stop_h4_bars": 7,
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
            row["h4_return_6"],
            row["h4_return_12"],
            row["gvz_close"],
            row["vix_close"],
            row["gvz_return_5d"],
            row["vix_return_5d"],
            row["gvz_vix_ratio_z252"],
            row["gvz_vix_ratio_change_5d"],
            row["gvz_vix_ratio_change_z126"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        h4_return_12 = float(row["h4_return_12"])
        gvz_return_5d = float(row["gvz_return_5d"])
        vix_return_5d = float(row["vix_return_5d"])
        ratio_z = float(row["gvz_vix_ratio_z252"])
        ratio_change = float(row["gvz_vix_ratio_change_5d"])
        ratio_change_z = float(row["gvz_vix_ratio_change_z126"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - h4_ema40) / h4_atr
        gold_vol_premium = (
            ratio_z >= 0.45
            and gvz_return_5d > vix_return_5d
            and (ratio_change >= 0.030 or ratio_change_z >= 0.45)
        )
        if not gold_vol_premium:
            return None

        if (
            h4_return_6 <= -0.0045
            and h4_return_12 >= -0.0500
            and close > open_price
            and close_location >= 0.60
            and ema40_distance_atr <= 0.80
        ):
            return _setup_metadata(row, "LONG", close, close_location, ema40_distance_atr)

        if (
            h4_return_6 >= 0.0045
            and h4_return_12 <= 0.0500
            and close < open_price
            and close_location <= 0.40
            and ema40_distance_atr >= -0.80
        ):
            return _setup_metadata(row, "SHORT", close, close_location, ema40_distance_atr)

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema40_distance_atr: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_6": float(row["h4_return_6"]),
        "h4_return_12": float(row["h4_return_12"]),
        "close_location": close_location,
        "ema40_distance_atr": ema40_distance_atr,
        "gvz_close": float(row["gvz_close"]),
        "vix_close": float(row["vix_close"]),
        "gvz_return_5d": float(row["gvz_return_5d"]),
        "vix_return_5d": float(row["vix_return_5d"]),
        "gvz_vix_ratio": float(row["gvz_vix_ratio"]),
        "gvz_vix_ratio_z252": float(row["gvz_vix_ratio_z252"]),
        "gvz_vix_ratio_change_5d": float(row["gvz_vix_ratio_change_5d"]),
        "gvz_vix_ratio_change_z126": float(row["gvz_vix_ratio_change_z126"]),
    }

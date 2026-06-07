from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.btc_risk_pressure_data import BTC_RISK_PRESSURE_FRAME_KEY
from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gvz_volatility_data import GVZ_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h1_gvz_vix_vol_premium_reversal_v0 import _gvz_vix_features_for_h1
from phase0.strategies.h4_btc_volatility_regime_gold_breakout_v0 import _btc_volatility_features_for_h4
from phase0.vix_risk_data import VIX_FRAME_KEY


class H1BtcGvzDualVolReversalV0Strategy(StrategyBase):
    """Research-only H1 XAU rejection during BTC and gold-volatility stress."""

    name = "h1_btc_gvz_dual_vol_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.45
    decision_hours_utc = {7, 10, 13, 16, 19}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        btc = data_context.get(BTC_RISK_PRESSURE_FRAME_KEY)
        gvz = data_context.get(GVZ_FRAME_KEY)
        vix = data_context.get(VIX_FRAME_KEY)
        if not isinstance(btc, pd.DataFrame):
            raise ConfigError(f"{self.name} requires data_context['btc_risk_pressure'].")
        if not isinstance(gvz, pd.DataFrame):
            raise ConfigError(f"{self.name} requires data_context['gvz_volatility'].")
        if not isinstance(vix, pd.DataFrame):
            raise ConfigError(f"{self.name} requires data_context['vix_risk'].")

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["h1_ema40"] = ema(close, 40)
        h1["h1_return_6"] = np.log(close / close.shift(6))
        h1["h1_return_12"] = np.log(close / close.shift(12))

        btc_features = _btc_volatility_features_for_h4(h1, btc)
        gvz_features = _gvz_vix_features_for_h1(h1, gvz, vix)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                btc_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
                    reason_code=f"{self.name.upper()}_{direction}",
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
            stop_loss = estimated_entry - 1.35 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.35 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H1 BTC/GVZ dual-vol reversal direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid H1 BTC/GVZ dual-vol reversal trade plan risk.")
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
            metadata={**signal.metadata, "max_holding_bars": 144, "planned_time_stop_h1_bars": 18},
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
            row["h1_return_6"],
            row["h1_return_12"],
            row["btc_vol_ratio_10_40"],
            row["btc_vol_percentile252"],
            row["btc_abs_return_percentile252"],
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
        h1_atr = float(row["h1_atr14"])
        h1_ema40 = float(row["h1_ema40"])
        h1_return_6 = float(row["h1_return_6"])
        h1_return_12 = float(row["h1_return_12"])
        btc_vol_ratio = float(row["btc_vol_ratio_10_40"])
        btc_vol_percentile = float(row["btc_vol_percentile252"])
        btc_abs_percentile = float(row["btc_abs_return_percentile252"])
        gvz_return_5d = float(row["gvz_return_5d"])
        vix_return_5d = float(row["vix_return_5d"])
        ratio_z = float(row["gvz_vix_ratio_z252"])
        ratio_change = float(row["gvz_vix_ratio_change_5d"])
        ratio_change_z = float(row["gvz_vix_ratio_change_z126"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - h1_ema40) / h1_atr
        btc_vol_stress = (
            btc_vol_ratio >= 1.04
            and btc_vol_percentile >= 0.52
            and btc_abs_percentile >= 0.42
        )
        gold_vol_premium = (
            ratio_z >= 0.30
            and gvz_return_5d > vix_return_5d
            and (ratio_change >= 0.018 or ratio_change_z >= 0.30)
        )
        if not (btc_vol_stress and gold_vol_premium):
            return None

        if (
            h1_return_6 <= -0.0020
            and h1_return_12 >= -0.0400
            and close > open_price
            and close_location >= 0.56
            and ema40_distance_atr <= 1.20
        ):
            return _metadata(row, "LONG", close, close_location, ema40_distance_atr)

        if (
            h1_return_6 >= 0.0020
            and h1_return_12 <= 0.0400
            and close < open_price
            and close_location <= 0.44
            and ema40_distance_atr >= -1.20
        ):
            return _metadata(row, "SHORT", close, close_location, ema40_distance_atr)

        return None


def _metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    close_location: float,
    ema40_distance_atr: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": float(estimated_entry),
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema40": float(row["h1_ema40"]),
        "h1_return_6": float(row["h1_return_6"]),
        "h1_return_12": float(row["h1_return_12"]),
        "close_location": float(close_location),
        "ema40_distance_atr": float(ema40_distance_atr),
        "btc_close": float(row["btc_close"]),
        "btc_return_1d": float(row["btc_return_1d"]),
        "btc_vol_ratio_10_40": float(row["btc_vol_ratio_10_40"]),
        "btc_vol_percentile252": float(row["btc_vol_percentile252"]),
        "btc_abs_return_percentile252": float(row["btc_abs_return_percentile252"]),
        "gvz_close": float(row["gvz_close"]),
        "vix_close": float(row["vix_close"]),
        "gvz_return_5d": float(row["gvz_return_5d"]),
        "vix_return_5d": float(row["vix_return_5d"]),
        "gvz_vix_ratio": float(row["gvz_vix_ratio"]),
        "gvz_vix_ratio_z252": float(row["gvz_vix_ratio_z252"]),
        "gvz_vix_ratio_change_5d": float(row["gvz_vix_ratio_change_5d"]),
        "gvz_vix_ratio_change_z126": float(row["gvz_vix_ratio_change_z126"]),
        "planned_time_stop_h1_bars": 18,
    }

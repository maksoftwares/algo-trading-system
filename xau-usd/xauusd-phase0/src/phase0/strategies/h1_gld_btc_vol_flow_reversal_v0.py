from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.btc_risk_pressure_data import BTC_RISK_PRESSURE_FRAME_KEY
from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.gld_etf_flow_data import GLD_ETF_FLOW_FRAME_KEY
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h4_btc_volatility_regime_gold_breakout_v0 import _btc_volatility_features_for_h4
from phase0.strategies.h4_gld_etf_flow_reversal_v0 import _gld_flow_features_for_h4


class H1GldBtcVolFlowReversalV0Strategy(StrategyBase):
    """Research-only H1 reversal during GLD flow stress and BTC volatility expansion."""

    name = "h1_gld_btc_vol_flow_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.45
    decision_hours_utc = {8, 12, 16, 20}

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        gld_flow = data_context.get(GLD_ETF_FLOW_FRAME_KEY)
        btc = data_context.get(BTC_RISK_PRESSURE_FRAME_KEY)
        if not isinstance(gld_flow, pd.DataFrame):
            raise ConfigError(f"{self.name} requires data_context['gld_etf_flow'].")
        if not isinstance(btc, pd.DataFrame):
            raise ConfigError(f"{self.name} requires data_context['btc_risk_pressure'].")

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        h1["h1_ema50"] = ema(close, 50)
        h1["h1_return_6"] = np.log(close / close.shift(6))
        h1["h1_return_12"] = np.log(close / close.shift(12))
        h1["h1_return_24"] = np.log(close / close.shift(24))

        gld_features = _gld_flow_features_for_h4(h1, gld_flow)
        btc_features = _btc_volatility_features_for_h4(h1, btc)
        h1 = pd.concat(
            [
                h1.reset_index(drop=True),
                gld_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
                btc_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
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
        for position in range(220, len(h1)):
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
                    reason_code=f"H1_GLD_BTC_VOL_FLOW_REVERSAL_V0_{direction}",
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
            raise ConfigError(f"Unsupported H1 GLD/BTC flow reversal direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid H1 GLD/BTC flow reversal trade plan risk.")
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
            metadata={**signal.metadata, "max_holding_bars": 100, "planned_time_stop_h1_bars": 10},
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
            row["h1_ema50"],
            row["h1_return_6"],
            row["h1_return_12"],
            row["h1_return_24"],
            row["gld_return_1d"],
            row["gld_volume_percentile252"],
            row["gld_volume_z126"],
            row["gld_dollar_volume_z126"],
            row["btc_vol_ratio_10_40"],
            row["btc_vol_percentile252"],
            row["btc_abs_return_percentile252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h1_atr = float(row["h1_atr14"])
        h1_ema50 = float(row["h1_ema50"])
        h1_return_6 = float(row["h1_return_6"])
        h1_return_12 = float(row["h1_return_12"])
        h1_return_24 = float(row["h1_return_24"])
        gld_return_1d = float(row["gld_return_1d"])
        volume_percentile = float(row["gld_volume_percentile252"])
        volume_z = float(row["gld_volume_z126"])
        dollar_volume_z = float(row["gld_dollar_volume_z126"])
        btc_vol_ratio = float(row["btc_vol_ratio_10_40"])
        btc_vol_percentile = float(row["btc_vol_percentile252"])
        btc_abs_return_percentile = float(row["btc_abs_return_percentile252"])
        if h1_atr <= 0:
            return None

        candle_range = max(high - low, h1_atr * 0.05)
        close_location = (close - low) / candle_range
        flow_stress = volume_percentile >= 0.80 and max(volume_z, dollar_volume_z) >= 0.85 and abs(gld_return_1d) >= 0.0030
        btc_vol_regime = btc_vol_ratio >= 1.08 and btc_vol_percentile >= 0.60 and btc_abs_return_percentile >= 0.48
        if not (flow_stress and btc_vol_regime):
            return None

        if (
            gld_return_1d <= -0.0030
            and h1_return_12 <= -0.0012
            and h1_return_6 >= h1_return_12
            and h1_return_24 >= -0.0180
            and close > open_price
            and close_location >= 0.58
            and close <= h1_ema50 + 1.00 * h1_atr
        ):
            return _metadata(row, "LONG", close, close_location)

        if (
            gld_return_1d >= 0.0030
            and h1_return_12 >= 0.0012
            and h1_return_6 <= h1_return_12
            and h1_return_24 <= 0.0180
            and close < open_price
            and close_location <= 0.42
            and close >= h1_ema50 - 1.00 * h1_atr
        ):
            return _metadata(row, "SHORT", close, close_location)

        return None


def _metadata(row: pd.Series, direction: str, estimated_entry: float, close_location: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": float(estimated_entry),
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema50": float(row["h1_ema50"]),
        "h1_return_6": float(row["h1_return_6"]),
        "h1_return_12": float(row["h1_return_12"]),
        "h1_return_24": float(row["h1_return_24"]),
        "close_location": float(close_location),
        "gld_close": float(row["gld_close"]),
        "gld_return_1d": float(row["gld_return_1d"]),
        "gld_volume_percentile252": float(row["gld_volume_percentile252"]),
        "gld_volume_z126": float(row["gld_volume_z126"]),
        "gld_dollar_volume_z126": float(row["gld_dollar_volume_z126"]),
        "btc_vol_ratio_10_40": float(row["btc_vol_ratio_10_40"]),
        "btc_vol_percentile252": float(row["btc_vol_percentile252"]),
        "btc_abs_return_percentile252": float(row["btc_abs_return_percentile252"]),
        "planned_time_stop_h1_bars": 10,
    }

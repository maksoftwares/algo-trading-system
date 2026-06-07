from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.btc_risk_pressure_data import BTC_RISK_PRESSURE_FRAME_KEY
from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available
from phase0.strategies.h4_btc_volatility_regime_gold_breakout_v0 import _btc_volatility_features_for_h4


class H4BtcVolatilityRegimeGoldReversalV0Strategy(StrategyBase):
    """Research-only H4 XAU exhaustion reversal during shifted high BTC volatility."""

    name = "h4_btc_volatility_regime_gold_reversal_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.55

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        btc = data_context.get(BTC_RISK_PRESSURE_FRAME_KEY)
        if not isinstance(btc, pd.DataFrame):
            raise ConfigError(f"{self.name} requires data_context['btc_risk_pressure'].")

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(high, low, close, 14)
        h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_3"] = np.log(close / close.shift(3))
        h4["h4_return_6"] = np.log(close / close.shift(6))

        btc_features = _btc_volatility_features_for_h4(h4, btc)
        h4 = pd.concat(
            [h4.reset_index(drop=True), btc_features.drop(columns=["timestamp_utc"]).reset_index(drop=True)],
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

        for position in range(180, len(h4)):
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
                    reason_code=f"{self.name.upper()}_{direction}",
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
            stop_loss = estimated_entry - 1.45 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.45 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported BTC volatility-regime reversal direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid BTC volatility-regime reversal trade plan risk.")
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
            metadata={**signal.metadata, "max_holding_bars": 288, "planned_time_stop_h4_bars": 8},
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
            row["h4_return_6"],
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
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_3 = float(row["h4_return_3"])
        h4_return_6 = float(row["h4_return_6"])
        btc_vol_ratio = float(row["btc_vol_ratio_10_40"])
        btc_vol_percentile = float(row["btc_vol_percentile252"])
        btc_abs_percentile = float(row["btc_abs_return_percentile252"])
        if h4_atr <= 0:
            return None

        candle_range = max(high - low, h4_atr * 0.05)
        close_location = (close - low) / candle_range
        ema40_distance_atr = (close - h4_ema40) / h4_atr
        high_btc_vol = (
            btc_vol_ratio >= 1.12
            and btc_vol_percentile >= 0.62
            and btc_abs_percentile >= 0.48
        )
        if not high_btc_vol:
            return None

        if (
            h4_return_6 <= -0.0040
            and h4_return_3 >= -0.0120
            and close > open_price
            and close_location >= 0.58
            and ema40_distance_atr >= -2.75
        ):
            return _metadata(row, "LONG", close, close_location, ema40_distance_atr)

        if (
            h4_return_6 >= 0.0040
            and h4_return_3 <= 0.0120
            and close < open_price
            and close_location <= 0.42
            and ema40_distance_atr <= 2.75
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
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_3": float(row["h4_return_3"]),
        "h4_return_6": float(row["h4_return_6"]),
        "close_location": float(close_location),
        "ema40_distance_atr": float(ema40_distance_atr),
        "btc_close": float(row["btc_close"]),
        "btc_return_1d": float(row["btc_return_1d"]),
        "btc_vol_ratio_10_40": float(row["btc_vol_ratio_10_40"]),
        "btc_vol_percentile252": float(row["btc_vol_percentile252"]),
        "btc_abs_return_percentile252": float(row["btc_abs_return_percentile252"]),
        "planned_time_stop_h4_bars": 8,
    }

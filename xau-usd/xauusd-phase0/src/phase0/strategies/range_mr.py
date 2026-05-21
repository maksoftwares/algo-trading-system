from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.candles import bearish_pin_bar, bullish_pin_bar
from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import adx, atr
from phase0.strategies.base import (
    StrategyBase,
    context_point_size,
    context_symbol,
    copy_context,
    latest_completed_position,
    require_frame,
    value_available,
)


class RangeMeanReversionStrategy(StrategyBase):
    name = "range_mr"
    version = "1.0"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        m15 = require_frame(context, "M15")
        m5 = require_frame(context, "M5")
        point_size = context_point_size(context)

        if "adx14" not in h1:
            h1["adx14"] = adx(h1["high"], h1["low"], h1["close"], 14)
        if "atr14" not in m15:
            m15["atr14"] = atr(m15["high"], m15["low"], m15["close"], 14)
        if "bullish_pin_bar" not in m5:
            m5["bullish_pin_bar"] = bullish_pin_bar(m5, point_size)
        if "bearish_pin_bar" not in m5:
            m5["bearish_pin_bar"] = bearish_pin_bar(m5, point_size)

        context["H1"] = h1
        context["M15"] = m15
        context["M5"] = m5
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        m15 = context["M15"]
        m5 = context["M5"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        h1_time_ns = h1["timestamp_utc"].astype("int64").to_numpy()
        m15_time_ns = m15["timestamp_utc"].astype("int64").to_numpy()
        m5_time_ns = m5["timestamp_utc"].astype("int64").to_numpy()
        h1_range_ok = self._h1_range_ok(h1)
        m15_state = self._m15_range_state_arrays(m15)
        m5_low = m5["low"].to_numpy()
        m5_high = m5["high"].to_numpy()
        m5_bullish_pin = m5["bullish_pin_bar"].to_numpy()
        m5_bearish_pin = m5["bearish_pin_bar"].to_numpy()

        for m5_position, timestamp_ns in enumerate(m5_time_ns):
            h1_position = int(np.searchsorted(h1_time_ns, timestamp_ns, side="right")) - 1
            m15_position = int(np.searchsorted(m15_time_ns, timestamp_ns, side="right")) - 1
            if (
                h1_position < 0
                or m15_position < 0
                or h1_position >= len(h1_range_ok)
                or m15_position >= len(m15_state["valid"])
                or not h1_range_ok[h1_position]
                or not m15_state["valid"][m15_position]
            ):
                continue

            atr14_m15 = float(m15_state["atr14"][m15_position])
            lower_boundary = float(m15_state["lower_boundary"][m15_position])
            upper_boundary = float(m15_state["upper_boundary"][m15_position])
            lower_trigger = lower_boundary + 0.2 * atr14_m15
            upper_trigger = upper_boundary - 0.2 * atr14_m15
            base_metadata = {
                "upper_boundary": upper_boundary,
                "lower_boundary": lower_boundary,
                "range_width": float(upper_boundary - lower_boundary),
                "upper_touches": int(m15_state["upper_touches"][m15_position]),
                "lower_touches": int(m15_state["lower_touches"][m15_position]),
                "atr14_m15": atr14_m15,
                "h1_index": int(h1_position),
                "m15_index": int(m15_position),
                "m15_time_utc": m15["timestamp_utc"].iat[m15_position],
                "m5_index": int(m5_position),
                "m5_time_utc": m5["timestamp_utc"].iat[m5_position],
            }

            if float(m5_low[m5_position]) <= lower_trigger and bool(m5_bullish_pin[m5_position]):
                timestamp = pd.Timestamp(m5["timestamp_utc"].iat[m5_position])
                signals.append(
                    Signal(
                        expert=self.name,
                        timestamp_utc=timestamp.to_pydatetime(),
                        symbol=symbol,
                        direction="LONG",
                        reason_code="RANGE_MR_LONG",
                        metadata=base_metadata,
                    )
                )

            if float(m5_high[m5_position]) >= upper_trigger and bool(m5_bearish_pin[m5_position]):
                timestamp = pd.Timestamp(m5["timestamp_utc"].iat[m5_position])
                signals.append(
                    Signal(
                        expert=self.name,
                        timestamp_utc=timestamp.to_pydatetime(),
                        symbol=symbol,
                        direction="SHORT",
                        reason_code="RANGE_MR_SHORT",
                        metadata=base_metadata,
                    )
                )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        upper_boundary = float(signal.metadata["upper_boundary"])
        lower_boundary = float(signal.metadata["lower_boundary"])
        atr14_m15 = float(signal.metadata["atr14_m15"])

        if signal.direction == "LONG":
            entry_price = lower_boundary
            stop_loss = lower_boundary - 0.3 * atr14_m15
            take_profit = upper_boundary
            risk_price = entry_price - stop_loss
            reward_price = take_profit - entry_price
            if take_profit <= entry_price or risk_price <= 0:
                raise ConfigError("Invalid Range MR long trade plan risk/reward.")
        else:
            entry_price = upper_boundary
            stop_loss = upper_boundary + 0.3 * atr14_m15
            take_profit = lower_boundary
            risk_price = stop_loss - entry_price
            reward_price = entry_price - take_profit
            if take_profit >= entry_price or risk_price <= 0:
                raise ConfigError("Invalid Range MR short trade plan risk/reward.")

        risk_reward = reward_price / risk_price
        if risk_reward < 1.0:
            raise ConfigError("Range MR reward/risk must be at least 1.0.")

        return TradePlan(
            expert=self.name,
            symbol=signal.symbol,
            direction=signal.direction,
            signal_time_utc=signal.timestamp_utc,
            entry_type="LIMIT",
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            invalidation_level=stop_loss,
            risk_reward=risk_reward,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "expires_after_bars": 6},
        )

    def _h1_range_ok(self, h1: pd.DataFrame) -> np.ndarray:
        adx14 = pd.to_numeric(h1["adx14"], errors="coerce")
        return (adx14.rolling(20, min_periods=20).max() < 20).fillna(False).to_numpy()

    def _m15_range_state_arrays(self, m15: pd.DataFrame) -> dict[str, np.ndarray]:
        highs = pd.to_numeric(m15["high"], errors="coerce")
        lows = pd.to_numeric(m15["low"], errors="coerce")
        atr14 = pd.to_numeric(m15["atr14"], errors="coerce").to_numpy()
        high_values = highs.to_numpy()
        low_values = lows.to_numpy()
        upper_boundary = highs.rolling(50, min_periods=50).max().to_numpy()
        lower_boundary = lows.rolling(50, min_periods=50).min().to_numpy()
        valid = np.zeros(len(m15), dtype=bool)
        upper_touches = np.zeros(len(m15), dtype=int)
        lower_touches = np.zeros(len(m15), dtype=int)

        for position in range(49, len(m15)):
            latest_atr = float(atr14[position])
            upper = float(upper_boundary[position])
            lower = float(lower_boundary[position])
            if not value_available(latest_atr, upper, lower) or latest_atr <= 0:
                continue
            if upper - lower < 2.0 * latest_atr:
                continue

            high_window = high_values[position - 49 : position + 1]
            low_window = low_values[position - 49 : position + 1]
            upper_touch_count = int(np.count_nonzero(high_window >= upper - 0.2 * latest_atr))
            lower_touch_count = int(np.count_nonzero(low_window <= lower + 0.2 * latest_atr))
            if upper_touch_count < 3 or lower_touch_count < 3:
                continue
            valid[position] = True
            upper_touches[position] = upper_touch_count
            lower_touches[position] = lower_touch_count

        return {
            "valid": valid,
            "upper_boundary": upper_boundary,
            "lower_boundary": lower_boundary,
            "upper_touches": upper_touches,
            "lower_touches": lower_touches,
            "atr14": atr14,
        }

    def _range_state(
        self,
        h1: pd.DataFrame,
        m15: pd.DataFrame,
        timestamp: pd.Timestamp,
    ) -> dict[str, Any] | None:
        h1_position = latest_completed_position(h1, timestamp)
        m15_position = latest_completed_position(m15, timestamp)
        if h1_position is None or m15_position is None or h1_position < 19 or m15_position < 49:
            return None

        h1_window = h1.iloc[h1_position - 19 : h1_position + 1]
        if h1_window["adx14"].isna().any() or not (h1_window["adx14"] < 20).all():
            return None

        m15_window = m15.iloc[m15_position - 49 : m15_position + 1]
        latest_atr = float(m15.iloc[m15_position]["atr14"])
        if not value_available(latest_atr) or latest_atr <= 0:
            return None

        upper_boundary = float(m15_window["high"].max())
        lower_boundary = float(m15_window["low"].min())
        range_width = upper_boundary - lower_boundary
        if range_width < 2.0 * latest_atr:
            return None

        upper_touches = int((m15_window["high"] >= upper_boundary - 0.2 * latest_atr).sum())
        lower_touches = int((m15_window["low"] <= lower_boundary + 0.2 * latest_atr).sum())
        if upper_touches < 3 or lower_touches < 3:
            return None

        return {
            "upper_boundary": upper_boundary,
            "lower_boundary": lower_boundary,
            "range_width": range_width,
            "upper_touches": upper_touches,
            "lower_touches": lower_touches,
            "atr14_m15": latest_atr,
            "h1_index": int(h1_position),
            "m15_index": int(m15_position),
            "m15_time_utc": m15.iloc[m15_position]["timestamp_utc"],
        }

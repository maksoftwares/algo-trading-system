from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.candles import bearish_engulfing, bearish_pin_bar, bullish_engulfing, bullish_pin_bar
from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema, slope
from phase0.strategies.base import (
    StrategyBase,
    context_point_size,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class TrendPullbackStrategy(StrategyBase):
    name = "trend_pullback"
    version = "1.0"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        m15 = require_frame(context, "M15")
        m5 = require_frame(context, "M5")
        point_size = context_point_size(context)

        if "ema50" not in h1:
            h1["ema50"] = ema(h1["close"], 50)
        if "ema200" not in h1:
            h1["ema200"] = ema(h1["close"], 200)
        if "ema50_slope20" not in h1:
            h1["ema50_slope20"] = slope(h1["ema50"], 20)
        if "atr14" not in h1:
            h1["atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)

        if "ema21" not in m15:
            m15["ema21"] = ema(m15["close"], 21)
        if "atr14" not in m15:
            m15["atr14"] = atr(m15["high"], m15["low"], m15["close"], 14)

        if "bullish_engulfing" not in m5:
            m5["bullish_engulfing"] = bullish_engulfing(m5)
        if "bearish_engulfing" not in m5:
            m5["bearish_engulfing"] = bearish_engulfing(m5)
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
        h1_ema50 = h1["ema50"].to_numpy()
        h1_ema200 = h1["ema200"].to_numpy()
        h1_slope = h1["ema50_slope20"].to_numpy()
        h1_atr = h1["atr14"].to_numpy()
        m15_close = m15["close"].to_numpy()
        m15_ema21 = m15["ema21"].to_numpy()
        m15_atr = m15["atr14"].to_numpy()
        m5_close = m5["close"].to_numpy()
        m5_bullish = (m5["bullish_engulfing"] | m5["bullish_pin_bar"]).to_numpy()
        m5_bearish = (m5["bearish_engulfing"] | m5["bearish_pin_bar"]).to_numpy()

        for position, timestamp_ns in enumerate(m5_time_ns):
            h1_position = int(np.searchsorted(h1_time_ns, timestamp_ns, side="right")) - 1
            m15_position = int(np.searchsorted(m15_time_ns, timestamp_ns, side="right")) - 1
            if h1_position < 0 or m15_position < 0:
                continue
            if not value_available(
                h1_ema50[h1_position],
                h1_ema200[h1_position],
                h1_slope[h1_position],
                h1_atr[h1_position],
                m15_ema21[m15_position],
                m15_atr[m15_position],
            ):
                continue

            pullback_distance = abs(float(m15_close[m15_position]) - float(m15_ema21[m15_position]))
            if pullback_distance > 0.5 * float(h1_atr[h1_position]):
                continue

            timestamp = pd.Timestamp(m5["timestamp_utc"].iat[position])
            metadata = {
                "m5_index": int(position),
                "m15_index": int(m15_position),
                "h1_timestamp_utc": h1["timestamp_utc"].iat[h1_position],
                "m15_timestamp_utc": m15["timestamp_utc"].iat[m15_position],
                "m5_close": float(m5_close[position]),
                "m15_atr14": float(m15_atr[m15_position]),
            }

            if (
                float(h1_ema50[h1_position]) > float(h1_ema200[h1_position])
                and float(h1_slope[h1_position]) > 0
                and bool(m5_bullish[position])
            ):
                signals.append(
                    Signal(
                        expert=self.name,
                        timestamp_utc=timestamp.to_pydatetime(),
                        symbol=symbol,
                        direction="LONG",
                        reason_code="TREND_PULLBACK_LONG",
                        metadata=metadata,
                    )
                )

            if (
                float(h1_ema50[h1_position]) < float(h1_ema200[h1_position])
                and float(h1_slope[h1_position]) < 0
                and bool(m5_bearish[position])
            ):
                signals.append(
                    Signal(
                        expert=self.name,
                        timestamp_utc=timestamp.to_pydatetime(),
                        symbol=symbol,
                        direction="SHORT",
                        reason_code="TREND_PULLBACK_SHORT",
                        metadata=metadata,
                    )
                )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        m5 = data_context.get("M5")
        if not isinstance(m5, pd.DataFrame):
            raise ConfigError("Trend Pullback requires M5 bars for trade planning.")
        m5_position = int(signal.metadata["m5_index"])
        m15_atr = float(signal.metadata["m15_atr14"])
        estimated_entry = float(signal.metadata["m5_close"])
        window = m5.iloc[max(0, m5_position - 9) : m5_position + 1]
        if len(window) < 10:
            raise ConfigError("Trend Pullback requires 10 completed M5 bars for pullback high/low.")

        if signal.direction == "LONG":
            stop_loss = float(window["low"].min()) - 0.1 * m15_atr
            risk_price = estimated_entry - stop_loss
            if risk_price <= 0 or stop_loss >= estimated_entry:
                raise ConfigError("Invalid Trend Pullback long trade plan risk.")
            take_profit = estimated_entry + 1.5 * risk_price
        else:
            stop_loss = float(window["high"].max()) + 0.1 * m15_atr
            risk_price = stop_loss - estimated_entry
            if risk_price <= 0 or stop_loss <= estimated_entry:
                raise ConfigError("Invalid Trend Pullback short trade plan risk.")
            take_profit = estimated_entry - 1.5 * risk_price

        return TradePlan(
            expert=self.name,
            symbol=signal.symbol,
            direction=signal.direction,
            signal_time_utc=signal.timestamp_utc,
            entry_type="MARKET",
            entry_price=None,
            stop_loss=stop_loss,
            take_profit=take_profit,
            invalidation_level=stop_loss,
            risk_reward=1.5,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry},
        )

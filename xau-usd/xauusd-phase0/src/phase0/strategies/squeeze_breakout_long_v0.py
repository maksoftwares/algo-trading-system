from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import (
    StrategyBase,
    context_point_size,
    context_symbol,
    copy_context,
    latest_completed_position,
    require_frame,
    value_available,
)


class SqueezeBreakoutLongV0Strategy(StrategyBase):
    """Disabled research strategy for the locked squeeze_breakout_long_v0 hypothesis."""

    name = "squeeze_breakout_long_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        m15 = require_frame(context, "M15")
        h1 = require_frame(context, "H1")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        if "ema50" not in h1:
            h1["ema50"] = h1["close"].ewm(span=50, adjust=False).mean()
        if "ema50_slope12" not in h1:
            h1["ema50_slope12"] = h1["ema50"] - h1["ema50"].shift(12)
        context["M5"] = m5
        context["M15"] = m15
        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        m15 = context["M15"]
        h1 = context["H1"]
        symbol = context_symbol(context)
        point_size = context_point_size(context)
        signals: list[Signal] = []

        for m5_position in range(288, len(m5)):
            row = m5.iloc[m5_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            m15_position = latest_completed_position(m15, timestamp)
            h1_position = latest_completed_position(h1, timestamp)
            if m15_position is None or h1_position is None:
                continue
            setup = self._setup_at_position(m5, m15, h1, m5_position, m15_position, h1_position)
            if setup is None:
                continue
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction="LONG",
                    reason_code="SQUEEZE_BREAKOUT_LONG_V0",
                    metadata={
                        **setup,
                        "m5_index": int(m5_position),
                        "m15_index": int(m15_position),
                        "h1_index": int(h1_position),
                        "point_size": point_size,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        compression_low = float(signal.metadata["compression_low"])
        m5_atr = float(signal.metadata["m5_atr14"])
        stop_loss = min(compression_low, estimated_entry - m5_atr)
        risk_price = estimated_entry - stop_loss
        if risk_price <= 0:
            raise ConfigError("Invalid Squeeze Breakout Long v0 trade plan risk.")
        take_profit = estimated_entry + 1.5 * risk_price
        return TradePlan(
            expert=self.name,
            symbol=signal.symbol,
            direction="LONG",
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

    def _setup_at_position(
        self,
        m5: pd.DataFrame,
        m15: pd.DataFrame,
        h1: pd.DataFrame,
        m5_position: int,
        m15_position: int,
        h1_position: int,
    ) -> dict[str, Any] | None:
        if m15_position < 135 or h1_position < 12:
            return None
        row = m5.iloc[m5_position]
        m5_atr = float(row["atr14"])
        if not value_available(m5_atr) or m5_atr <= 0:
            return None
        if not self._m5_atr_compressed(m5, m5_position):
            return None
        if not self._h1_context_ok(h1, h1_position):
            return None

        compression = m15.iloc[m15_position - 15 : m15_position + 1]
        compression_high = float(compression["high"].max())
        compression_low = float(compression["low"].min())
        compression_width = compression_high - compression_low
        if compression_width <= 0:
            return None
        if not self._m15_range_compressed(m15, m15_position, compression_width):
            return None

        high = float(row["high"])
        low = float(row["low"])
        open_price = float(row["open"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if close <= compression_high + 0.20 * m5_atr:
            return None
        if close_position < 0.65 or body_ratio < 0.45:
            return None

        return {
            "compression_high": compression_high,
            "compression_low": compression_low,
            "compression_width": compression_width,
            "m5_atr14": m5_atr,
            "h1_close": float(h1["close"].iat[h1_position]),
            "h1_ema50": float(h1["ema50"].iat[h1_position]),
            "h1_ema50_slope12": float(h1["ema50_slope12"].iat[h1_position]),
            "estimated_entry_price": close,
            "breakout_close": close,
            "breakout_body_ratio": body_ratio,
            "breakout_close_position": close_position,
        }

    def _m5_atr_compressed(self, m5: pd.DataFrame, position: int) -> bool:
        prior = pd.to_numeric(m5["atr14"].iloc[position - 288 : position], errors="coerce").dropna()
        if len(prior) < 288:
            return False
        current = float(m5["atr14"].iat[position])
        return current < float(prior.quantile(0.40))

    def _m15_range_compressed(self, m15: pd.DataFrame, position: int, current_width: float) -> bool:
        widths: list[float] = []
        for end_position in range(position - 120, position):
            if end_position < 15:
                continue
            window = m15.iloc[end_position - 15 : end_position + 1]
            width = float(window["high"].max()) - float(window["low"].min())
            if width > 0:
                widths.append(width)
        if len(widths) < 120:
            return False
        threshold = float(pd.Series(widths).quantile(0.35))
        return current_width < threshold

    def _h1_context_ok(self, h1: pd.DataFrame, position: int) -> bool:
        close = float(h1["close"].iat[position])
        ema50 = float(h1["ema50"].iat[position])
        slope = float(h1["ema50_slope12"].iat[position])
        return value_available(close, ema50, slope) and close > ema50 and slope >= 0

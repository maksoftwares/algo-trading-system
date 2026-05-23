from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class W1D1MomentumContinuationV0Strategy(StrategyBase):
    """Disabled research strategy for the locked W1/D1 momentum continuation v0 hypothesis."""

    name = "w1_d1_momentum_continuation_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        d1 = require_frame(context, "D1")

        if "atr14" not in d1:
            d1["atr14"] = atr(d1["high"], d1["low"], d1["close"], 14)
        if "momentum5" not in d1:
            d1["momentum5"] = pd.to_numeric(d1["close"], errors="coerce") - pd.to_numeric(
                d1["close"], errors="coerce"
            ).shift(5)
        if "momentum20" not in d1:
            d1["momentum20"] = pd.to_numeric(d1["close"], errors="coerce") - pd.to_numeric(
                d1["close"], errors="coerce"
            ).shift(20)
        if "range" not in d1:
            d1["range"] = pd.to_numeric(d1["high"], errors="coerce") - pd.to_numeric(
                d1["low"], errors="coerce"
            )
        if "body" not in d1:
            d1["body"] = (
                pd.to_numeric(d1["close"], errors="coerce")
                - pd.to_numeric(d1["open"], errors="coerce")
            ).abs()
        if "close_position" not in d1:
            d1_range = pd.to_numeric(d1["range"], errors="coerce").replace(0.0, pd.NA)
            d1["close_position"] = (
                pd.to_numeric(d1["close"], errors="coerce") - pd.to_numeric(d1["low"], errors="coerce")
            ) / d1_range

        context["D1"] = d1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        d1 = context["D1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_iso_weeks: set[str] = set()

        for d1_position in range(25, len(d1)):
            row = d1.iloc[d1_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            setup = self._setup_at_position(d1, d1_position)
            if setup is None:
                continue
            week_key = _iso_week_key(timestamp)
            if week_key in used_iso_weeks:
                continue
            used_iso_weeks.add(week_key)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"W1_D1_MOMENTUM_CONTINUATION_V0_{direction}",
                    metadata={**setup, "d1_index": int(d1_position), "iso_week": week_key},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        d1_atr = float(signal.metadata["d1_atr14"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = float(signal.metadata["signal_low"]) - 0.20 * d1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["signal_high"]) + 0.20 * d1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported W1/D1 momentum continuation direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid W1/D1 momentum continuation v0 trade plan risk.")

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
            risk_reward=1.5,
            reason_code=signal.reason_code,
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry},
        )

    def _setup_at_position(self, d1: pd.DataFrame, d1_position: int) -> dict[str, Any] | None:
        row = d1.iloc[d1_position]
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["momentum5"],
            row["momentum20"],
            row["range"],
            row["body"],
            row["close_position"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        d1_atr = float(row["atr14"])
        momentum5 = float(row["momentum5"])
        momentum20 = float(row["momentum20"])
        d1_range = float(row["range"])
        body = float(row["body"])
        close_position = float(row["close_position"])
        if d1_atr <= 0 or d1_range <= 0:
            return None

        body_ratio = body / d1_range
        if d1_range < 0.75 * d1_atr or body_ratio < 0.35:
            return None

        if (
            momentum20 >= 1.25 * d1_atr
            and momentum5 >= 0.25 * d1_atr
            and close > open_price
            and close_position >= 0.65
        ):
            return {
                "direction": "LONG",
                "d1_atr14": d1_atr,
                "d1_momentum5": momentum5,
                "d1_momentum20": momentum20,
                "signal_high": high,
                "signal_low": low,
                "estimated_entry_price": close,
                "signal_body_ratio": body_ratio,
                "signal_close_position": close_position,
            }

        if (
            momentum20 <= -1.25 * d1_atr
            and momentum5 <= -0.25 * d1_atr
            and close < open_price
            and close_position <= 0.35
        ):
            return {
                "direction": "SHORT",
                "d1_atr14": d1_atr,
                "d1_momentum5": momentum5,
                "d1_momentum20": momentum20,
                "signal_high": high,
                "signal_low": low,
                "estimated_entry_price": close,
                "signal_body_ratio": body_ratio,
                "signal_close_position": close_position,
            }

        return None


def _iso_week_key(timestamp: pd.Timestamp) -> str:
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    iso = timestamp.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"

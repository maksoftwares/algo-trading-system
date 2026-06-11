from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class XauNyM5MomentumIgnitionV0Strategy(StrategyBase):
    """Research-only Wave-6 M5 participation-burst (momentum ignition) candidate.

    Locked hypothesis: docs/hypothesis_xau_ny_m5_momentum_ignition_v0.md
    Three consecutive directional M5 bars with range expansion inside the
    09:35-12:00 America/New_York bar-end window; wide ATR-floored stop.
    No price level and no retest sequence (independent of breakout_retest).
    """

    name = "xau_ny_m5_momentum_ignition_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.5
    event_timezone = "America/New_York"
    window_start_minutes = 9 * 60 + 35
    window_end_minutes = 12 * 60
    bar_range_min_atr = 1.2
    net_move_min_atr = 2.0
    stop_atr_multiple = 8.0
    stop_floor_price_units = 3.75

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        close = pd.to_numeric(m5["close"], errors="coerce")
        high = pd.to_numeric(m5["high"], errors="coerce")
        low = pd.to_numeric(m5["low"], errors="coerce")
        m5["m5_atr20"] = atr(high, low, close, 20)
        local_end = m5["timestamp_utc"].dt.tz_convert(self.event_timezone)
        m5["event_local_date"] = local_end.dt.strftime("%Y-%m-%d")
        m5["event_local_minutes"] = local_end.dt.hour * 60 + local_end.dt.minute
        context["M5"] = m5
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_dates: set[str] = set()

        opens = pd.to_numeric(m5["open"], errors="coerce").to_numpy()
        highs = pd.to_numeric(m5["high"], errors="coerce").to_numpy()
        lows = pd.to_numeric(m5["low"], errors="coerce").to_numpy()
        closes = pd.to_numeric(m5["close"], errors="coerce").to_numpy()
        atrs = pd.to_numeric(m5["m5_atr20"], errors="coerce").to_numpy()
        minutes = m5["event_local_minutes"].to_numpy()
        dates = m5["event_local_date"].to_numpy()

        for i in range(22, len(m5)):
            if not (self.window_start_minutes <= minutes[i] <= self.window_end_minutes):
                continue
            day = dates[i]
            if day in used_dates:
                continue
            window = slice(i - 2, i + 1)
            if not value_available(*opens[window], *closes[window], *atrs[window], highs[i], lows[i]):
                continue
            third_atr = float(atrs[i])
            if third_atr <= 0:
                continue
            directions = [closes[j] - opens[j] for j in range(i - 2, i + 1)]
            if all(d > 0 for d in directions):
                direction = "LONG"
            elif all(d < 0 for d in directions):
                direction = "SHORT"
            else:
                continue
            ranges_ok = all(
                (highs[j] - lows[j]) >= self.bar_range_min_atr * float(atrs[j])
                for j in range(i - 2, i + 1)
                if atrs[j] > 0
            ) and all(atrs[j] > 0 for j in range(i - 2, i + 1))
            if not ranges_ok:
                continue
            net_move = closes[i] - opens[i - 2]
            if abs(net_move) < self.net_move_min_atr * third_atr:
                continue
            if (direction == "LONG") != (net_move > 0):
                continue

            used_dates.add(day)
            timestamp = pd.Timestamp(m5.iloc[i]["timestamp_utc"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"XAU_NY_M5_MOMENTUM_IGNITION_V0_{direction}",
                    metadata={
                        "direction": direction,
                        "estimated_entry_price": float(closes[i]),
                        "m5_atr20": third_atr,
                        "net_move_atr_multiple": float(abs(net_move) / third_atr),
                        "event_local_date": str(day),
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m5_atr = float(signal.metadata["m5_atr20"])
        stop_distance = max(self.stop_atr_multiple * m5_atr, self.stop_floor_price_units)

        if direction == "LONG":
            stop_loss = estimated_entry - stop_distance
            take_profit = estimated_entry + self.risk_reward * stop_distance
        elif direction == "SHORT":
            stop_loss = estimated_entry + stop_distance
            take_profit = estimated_entry - self.risk_reward * stop_distance
        else:
            raise ConfigError(f"Unsupported M5 ignition direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid M5 ignition trade plan risk.")

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
            metadata={**signal.metadata, "stop_distance_price_units": stop_distance},
        )

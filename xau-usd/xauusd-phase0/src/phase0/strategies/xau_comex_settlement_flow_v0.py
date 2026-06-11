from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class XauComexSettlementFlowV0Strategy(StrategyBase):
    """Research-only Lane B COMEX settlement position-squaring fade candidate.

    Locked hypothesis: docs/hypothesis_xau_comex_settlement_flow_v0.md
    All windows are defined on completed H1 bars whose timestamp_utc equals the
    bar END converted to America/New_York local time (DST-correct via IANA rules).
    The settlement bar is the H1 bar with New_York bar-end 14:00 (contains the
    13:30 ET settlement boundary). The fade direction is opposite the
    pre-settlement impulse measured from the open of the bar ending 10:00.
    """

    name = "xau_comex_settlement_flow_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.2
    event_timezone = "America/New_York"
    impulse_open_end_hour = 10
    settlement_end_hour = 14
    impulse_min_atr = 1.50
    impulse_max_atr = 5.00
    stop_atr_multiple = 1.2
    stop_floor_price_units = 3.75

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        h1["h1_atr14"] = atr(high, low, close, 14)
        local_end = h1["timestamp_utc"].dt.tz_convert(self.event_timezone)
        h1["event_local_date"] = local_end.dt.strftime("%Y-%m-%d")
        h1["event_local_hour"] = local_end.dt.hour
        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []

        for local_date, day in h1.groupby("event_local_date", sort=True):
            open_rows = day[day["event_local_hour"] == self.impulse_open_end_hour]
            settlement_rows = day[day["event_local_hour"] == self.settlement_end_hour]
            if open_rows.empty or settlement_rows.empty:
                continue
            open_bar = open_rows.iloc[0]
            settlement_bar = settlement_rows.iloc[0]
            required = (
                open_bar["open"],
                settlement_bar["close"],
                settlement_bar["h1_atr14"],
            )
            if not value_available(*required):
                continue
            impulse_open = float(open_bar["open"])
            settlement_close = float(settlement_bar["close"])
            settlement_atr = float(settlement_bar["h1_atr14"])
            if settlement_atr <= 0:
                continue

            impulse = settlement_close - impulse_open
            impulse_atr_multiple = abs(impulse) / settlement_atr
            if impulse_atr_multiple < self.impulse_min_atr or impulse_atr_multiple > self.impulse_max_atr:
                continue

            direction = "SHORT" if impulse > 0 else "LONG"
            timestamp = pd.Timestamp(settlement_bar["timestamp_utc"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"XAU_COMEX_SETTLEMENT_FLOW_V0_{direction}",
                    metadata={
                        "direction": direction,
                        "estimated_entry_price": settlement_close,
                        "h1_atr14": settlement_atr,
                        "impulse_price_units": impulse,
                        "impulse_atr_multiple": impulse_atr_multiple,
                        "impulse_open_price": impulse_open,
                        "event_local_date": str(local_date),
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        settlement_atr = float(signal.metadata["h1_atr14"])
        stop_distance = max(self.stop_atr_multiple * settlement_atr, self.stop_floor_price_units)

        if direction == "LONG":
            stop_loss = estimated_entry - stop_distance
            take_profit = estimated_entry + self.risk_reward * stop_distance
        elif direction == "SHORT":
            stop_loss = estimated_entry + stop_distance
            take_profit = estimated_entry - self.risk_reward * stop_distance
        else:
            raise ConfigError(f"Unsupported COMEX settlement flow direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid COMEX settlement flow trade plan risk.")

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

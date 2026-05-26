from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.macro_event_calendar import MACRO_EVENT_FRAME_KEY
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H1MacroEventAftershockV0Strategy(StrategyBase):
    """Research-only H1 macro-event aftershock continuation candidate."""

    name = "h1_macro_event_aftershock_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.35
    min_event_move_atr = 0.08
    min_event_range_atr = 0.30

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")
        events = data_context.get(MACRO_EVENT_FRAME_KEY)
        if not isinstance(events, pd.DataFrame):
            raise ConfigError(
                "h1_macro_event_aftershock_v0 requires "
                "data_context['macro_event_calendar'] with standardized US macro event slots."
            )

        close = pd.to_numeric(h1["close"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        if "h1_atr14" not in h1:
            h1["h1_atr14"] = atr(high, low, close, 14)
        if "h1_ema24" not in h1:
            h1["h1_ema24"] = ema(close, 24)
        h1["h1_return_6"] = np.log(close / close.shift(6))

        context["H1"] = h1
        context[MACRO_EVENT_FRAME_KEY] = _prepare_events(events)
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        events = context[MACRO_EVENT_FRAME_KEY]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_events: set[str] = set()

        h1_times = pd.DatetimeIndex(pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce"))
        if h1_times.isna().any():
            raise ConfigError("H1 macro-event aftershock received invalid H1 timestamps.")

        for _, event in events.iterrows():
            setup = self._setup_for_event(h1, h1_times, event)
            if setup is None:
                continue
            event_id = str(setup["event_id"])
            if event_id in used_events:
                continue
            used_events.add(event_id)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=pd.Timestamp(setup["signal_timestamp_utc"]).to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_MACRO_EVENT_AFTERSHOCK_V0_{direction}",
                    metadata=setup,
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["h1_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 0.95 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 0.95 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported macro-event aftershock direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid macro-event aftershock trade plan risk.")

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
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 144,
                "planned_time_stop_h1_bars": 12,
            },
        )

    def _setup_for_event(
        self,
        h1: pd.DataFrame,
        h1_times: pd.DatetimeIndex,
        event: pd.Series,
    ) -> dict[str, Any] | None:
        event_timestamp = pd.Timestamp(event["timestamp_utc"])
        if event_timestamp.tzinfo is None:
            event_timestamp = event_timestamp.tz_localize("UTC")
        else:
            event_timestamp = event_timestamp.tz_convert("UTC")

        confirm_start = event_timestamp + pd.Timedelta(minutes=75)
        confirm_deadline = event_timestamp + pd.Timedelta(hours=4)
        confirm_pos = int(h1_times.searchsorted(confirm_start, side="left"))
        if confirm_pos >= len(h1_times) or h1_times[confirm_pos] > confirm_deadline:
            return None

        pre_pos = int(h1_times.searchsorted(event_timestamp, side="left")) - 1
        if pre_pos < 24 or confirm_pos <= pre_pos:
            return None

        row = h1.iloc[confirm_pos]
        pre_row = h1.iloc[pre_pos]
        required = (
            row["close"],
            row["h1_atr14"],
            row["h1_ema24"],
            row["h1_return_6"],
            pre_row["close"],
        )
        if not value_available(*required):
            return None

        close = float(row["close"])
        pre_close = float(pre_row["close"])
        h1_atr = float(row["h1_atr14"])
        if h1_atr <= 0:
            return None

        event_slice = h1.iloc[pre_pos + 1 : confirm_pos + 1]
        event_range = float(event_slice["high"].max() - event_slice["low"].min())
        event_move_atr = (close - pre_close) / h1_atr
        event_range_atr = event_range / h1_atr
        if abs(event_move_atr) < self.min_event_move_atr:
            return None
        if event_range_atr < self.min_event_range_atr:
            return None

        direction = "LONG" if event_move_atr > 0 else "SHORT"
        return _setup_metadata(
            event=event,
            row=row,
            direction=direction,
            estimated_entry=close,
            event_move_atr=event_move_atr,
            event_range_atr=event_range_atr,
            h1_index=confirm_pos,
        )


def _prepare_events(events: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp_utc", "event_type", "source_rule"}
    missing = required.difference(events.columns)
    if missing:
        raise ConfigError(
            "Macro-event calendar missing required column(s): "
            + ", ".join(sorted(missing))
        )
    prepared = events.copy()
    prepared["timestamp_utc"] = pd.to_datetime(prepared["timestamp_utc"], utc=True, errors="coerce")
    prepared = prepared.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc")
    return prepared.reset_index(drop=True)


def _setup_metadata(
    event: pd.Series,
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    event_move_atr: float,
    event_range_atr: float,
    h1_index: int,
) -> dict[str, Any]:
    event_timestamp = pd.Timestamp(event["timestamp_utc"])
    return {
        "direction": direction,
        "signal_timestamp_utc": pd.Timestamp(row["timestamp_utc"]).isoformat(),
        "estimated_entry_price": estimated_entry,
        "h1_atr14": float(row["h1_atr14"]),
        "h1_ema24": float(row["h1_ema24"]),
        "h1_return_6": float(row["h1_return_6"]),
        "event_timestamp_utc": event_timestamp.isoformat(),
        "event_type": str(event["event_type"]),
        "event_source_rule": str(event["source_rule"]),
        "event_move_atr": float(event_move_atr),
        "event_range_atr": float(event_range_atr),
        "h1_index": int(h1_index),
        "event_id": f"{event_timestamp.isoformat()}_{event['event_type']}",
    }

from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class WeeklyOpenReversionV0Strategy(StrategyBase):
    """Disabled research strategy for the locked weekly open reversion v0 hypothesis."""

    name = "weekly_open_reversion_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m15 = require_frame(context, "M15")
        if "atr14" not in m15:
            m15["atr14"] = atr(m15["high"], m15["low"], m15["close"], 14)

        bar_starts = _bar_start_times(m15)
        iso = bar_starts.dt.isocalendar()
        week_key = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
        m15["week_key"] = week_key
        m15["week_open"] = week_key.map(
            pd.DataFrame(
                {
                    "week": week_key,
                    "open": pd.to_numeric(m15["open"], errors="coerce"),
                }
            )
            .groupby("week", sort=True)["open"]
            .first()
        )
        m15["week_bar_index"] = m15.groupby("week_key", sort=False).cumcount()
        m15["bar_start_minute_utc"] = bar_starts.dt.hour * 60 + bar_starts.dt.minute
        context["M15"] = m15
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m15 = context["M15"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_week_direction: set[tuple[str, str]] = set()

        for m15_position in range(96, len(m15)):
            row = m15.iloc[m15_position]
            setup = self._setup_at_position(m15, m15_position)
            if setup is None:
                continue

            week_direction = (str(setup["week_key"]), str(setup["direction"]))
            if week_direction in used_week_direction:
                continue

            used_week_direction.add(week_direction)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=pd.Timestamp(row["timestamp_utc"]).to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"WEEKLY_OPEN_REVERSION_V0_{direction}",
                    metadata={**setup, "m15_index": int(m15_position)},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m15_atr = float(signal.metadata["m15_atr14"])
        weekly_open = float(signal.metadata["week_open"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = float(signal.metadata["reversal_low"]) - 0.35 * m15_atr
            risk_price = estimated_entry - stop_loss
            reward_price = weekly_open - estimated_entry
            take_profit = weekly_open
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["reversal_high"]) + 0.35 * m15_atr
            risk_price = stop_loss - estimated_entry
            reward_price = estimated_entry - weekly_open
            take_profit = weekly_open
        else:
            raise ConfigError(f"Unsupported weekly open reversion direction {signal.direction!r}.")

        if risk_price <= 0 or reward_price <= 0:
            raise ConfigError("Invalid weekly open reversion v0 trade plan risk/reward.")

        risk_reward = reward_price / risk_price
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
            risk_reward=risk_reward,
            reason_code=signal.reason_code,
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "risk_reward": risk_reward,
            },
        )

    def _setup_at_position(self, m15: pd.DataFrame, m15_position: int) -> dict[str, Any] | None:
        row = m15.iloc[m15_position]
        m15_atr_raw = row["atr14"]
        week_open_raw = row["week_open"]
        if not value_available(m15_atr_raw, week_open_raw):
            return None

        m15_atr = float(m15_atr_raw)
        week_open = float(week_open_raw)
        if m15_atr <= 0:
            return None

        # Avoid Monday discovery and thin late-week rollover windows.
        week_bar_index = int(row["week_bar_index"])
        start_minute = int(row["bar_start_minute_utc"])
        if week_bar_index < 96 or week_bar_index > 430:
            return None
        if start_minute < 7 * 60 or start_minute >= 20 * 60:
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None

        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        lower_wick_ratio = (min(open_price, close) - low) / candle_range
        upper_wick_ratio = (high - max(open_price, close)) / candle_range
        if body_ratio < 0.25:
            return None

        displacement = close - week_open
        if displacement <= -2.25 * m15_atr:
            reward_price = week_open - close
            stop_loss = low - 0.35 * m15_atr
            risk_price = close - stop_loss
            if (
                close > open_price
                and close_position >= 0.65
                and lower_wick_ratio >= 0.20
                and risk_price > 0
                and reward_price / risk_price >= 1.15
            ):
                return {
                    "direction": "LONG",
                    "week_key": str(row["week_key"]),
                    "week_open": week_open,
                    "m15_atr14": m15_atr,
                    "reversal_high": high,
                    "reversal_low": low,
                    "estimated_entry_price": close,
                    "weekly_open_displacement_atr": displacement / m15_atr,
                    "reversal_body_ratio": body_ratio,
                    "reversal_close_position": close_position,
                    "reversal_lower_wick_ratio": lower_wick_ratio,
                    "reversal_upper_wick_ratio": upper_wick_ratio,
                }

        if displacement >= 2.25 * m15_atr:
            reward_price = close - week_open
            stop_loss = high + 0.35 * m15_atr
            risk_price = stop_loss - close
            if (
                close < open_price
                and close_position <= 0.35
                and upper_wick_ratio >= 0.20
                and risk_price > 0
                and reward_price / risk_price >= 1.15
            ):
                return {
                    "direction": "SHORT",
                    "week_key": str(row["week_key"]),
                    "week_open": week_open,
                    "m15_atr14": m15_atr,
                    "reversal_high": high,
                    "reversal_low": low,
                    "estimated_entry_price": close,
                    "weekly_open_displacement_atr": displacement / m15_atr,
                    "reversal_body_ratio": body_ratio,
                    "reversal_close_position": close_position,
                    "reversal_lower_wick_ratio": lower_wick_ratio,
                    "reversal_upper_wick_ratio": upper_wick_ratio,
                }

        return None


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=15)

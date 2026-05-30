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


class WeekendGapReversionV0Strategy(StrategyBase):
    """Research-only weekend gap-fill reversion candidate."""

    name = "weekend_gap_reversion_v0"
    version = "0.1-research-disabled"

    min_gap_atr = 0.35
    min_reward_risk = 1.15

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m15 = require_frame(context, "M15")
        if "atr14" not in m15:
            m15["atr14"] = atr(m15["high"], m15["low"], m15["close"], 14)

        starts = _bar_start_times(m15)
        m15["bar_start_utc"] = starts
        m15["prev_bar_start_utc"] = starts.shift(1)
        m15["prev_close"] = pd.to_numeric(m15["close"], errors="coerce").shift(1)
        m15["market_break_hours"] = (starts - starts.shift(1)).dt.total_seconds() / 3600.0
        iso = starts.dt.isocalendar()
        m15["gap_week_key"] = iso["year"].astype(str) + "-W" + iso["week"].astype(str).str.zfill(2)
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

        for position in range(96, len(m15)):
            row = m15.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            week_direction = (str(setup["gap_week_key"]), str(setup["direction"]))
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
                    reason_code=f"WEEKEND_GAP_REVERSION_V0_{direction}",
                    metadata={**setup, "m15_index": int(position)},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m15_atr = float(signal.metadata["m15_atr14"])
        pre_gap_close = float(signal.metadata["pre_gap_close"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = float(signal.metadata["gap_bar_low"]) - 0.35 * m15_atr
            risk_price = estimated_entry - stop_loss
            reward_price = pre_gap_close - estimated_entry
            take_profit = pre_gap_close
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["gap_bar_high"]) + 0.35 * m15_atr
            risk_price = stop_loss - estimated_entry
            reward_price = estimated_entry - pre_gap_close
            take_profit = pre_gap_close
        else:
            raise ConfigError(f"Unsupported weekend gap reversion direction {signal.direction!r}.")

        if risk_price <= 0 or reward_price <= 0:
            raise ConfigError("Invalid weekend gap reversion v0 trade plan risk/reward.")

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
                "max_holding_bars": 96,
                "planned_time_stop_m5_bars": 96,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["atr14"],
            row["prev_close"],
            row["market_break_hours"],
        )
        if not value_available(*required):
            return None

        break_hours = float(row["market_break_hours"])
        if break_hours < 24.0 or break_hours > 96.0:
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        m15_atr = float(row["atr14"])
        pre_gap_close = float(row["prev_close"])
        if m15_atr <= 0:
            return None

        candle_range = high - low
        if candle_range <= 0:
            return None

        gap = open_price - pre_gap_close
        gap_atr = gap / m15_atr
        if abs(gap_atr) < self.min_gap_atr:
            return None

        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.15:
            return None

        if gap_atr <= -self.min_gap_atr:
            reward_price = pre_gap_close - close
            stop_loss = low - 0.35 * m15_atr
            risk_price = close - stop_loss
            if (
                close < pre_gap_close - 0.05 * m15_atr
                and close > open_price
                and close_position >= 0.60
                and risk_price > 0
                and reward_price / risk_price >= self.min_reward_risk
            ):
                return _setup_metadata(row, "LONG", close, pre_gap_close, gap_atr, body_ratio, close_position)

        if gap_atr >= self.min_gap_atr:
            reward_price = close - pre_gap_close
            stop_loss = high + 0.35 * m15_atr
            risk_price = stop_loss - close
            if (
                close > pre_gap_close + 0.05 * m15_atr
                and close < open_price
                and close_position <= 0.40
                and risk_price > 0
                and reward_price / risk_price >= self.min_reward_risk
            ):
                return _setup_metadata(row, "SHORT", close, pre_gap_close, gap_atr, body_ratio, close_position)

        return None


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    pre_gap_close: float,
    gap_atr: float,
    body_ratio: float,
    close_position: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "gap_week_key": str(row["gap_week_key"]),
        "estimated_entry_price": estimated_entry,
        "pre_gap_close": pre_gap_close,
        "m15_atr14": float(row["atr14"]),
        "gap_bar_high": float(row["high"]),
        "gap_bar_low": float(row["low"]),
        "gap_open": float(row["open"]),
        "gap_atr": gap_atr,
        "market_break_hours": float(row["market_break_hours"]),
        "reversal_body_ratio": body_ratio,
        "reversal_close_position": close_position,
    }


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=15)

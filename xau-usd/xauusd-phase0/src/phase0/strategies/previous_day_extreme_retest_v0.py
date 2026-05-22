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
    require_frame,
    value_available,
)


class PreviousDayExtremeRetestV0Strategy(StrategyBase):
    """Disabled research strategy for the locked previous-day extreme retest v0 hypothesis."""

    name = "previous_day_extreme_retest_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)

        bar_starts = _bar_start_times(m5)
        day_key = bar_starts.dt.strftime("%Y-%m-%d")
        daily = pd.DataFrame(
            {
                "day": day_key,
                "high": pd.to_numeric(m5["high"], errors="coerce"),
                "low": pd.to_numeric(m5["low"], errors="coerce"),
            }
        )
        day_levels = daily.groupby("day", sort=True).agg(day_high=("high", "max"), day_low=("low", "min"))
        day_levels["previous_day_high"] = day_levels["day_high"].shift(1)
        day_levels["previous_day_low"] = day_levels["day_low"].shift(1)
        m5["level_day"] = day_key
        m5["previous_day_high"] = day_key.map(day_levels["previous_day_high"])
        m5["previous_day_low"] = day_key.map(day_levels["previous_day_low"])
        context["M5"] = m5
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        symbol = context_symbol(context)
        point_size = context_point_size(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for m5_position in range(300, len(m5)):
            row = m5.iloc[m5_position]
            setup = self._setup_at_position(m5, m5_position)
            if setup is None:
                continue
            day_direction = (str(setup["session_day"]), str(setup["direction"]))
            if day_direction in used_day_direction:
                continue
            used_day_direction.add(day_direction)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=pd.Timestamp(row["timestamp_utc"]).to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"PREVIOUS_DAY_EXTREME_RETEST_V0_{direction}",
                    metadata={
                        **setup,
                        "m5_index": int(m5_position),
                        "point_size": point_size,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m5_atr = float(signal.metadata["m5_atr14"])
        direction = signal.direction.upper()
        if direction == "LONG":
            stop_loss = min(float(signal.metadata["level"]), float(signal.metadata["retest_low"])) - 0.25 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = max(float(signal.metadata["level"]), float(signal.metadata["retest_high"])) + 0.25 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported previous-day extreme retest direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid previous-day extreme retest v0 trade plan risk.")
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

    def _setup_at_position(self, m5: pd.DataFrame, m5_position: int) -> dict[str, Any] | None:
        row = m5.iloc[m5_position]
        m5_atr = float(row["atr14"])
        previous_high = float(row["previous_day_high"])
        previous_low = float(row["previous_day_low"])
        if not value_available(m5_atr, previous_high, previous_low) or m5_atr <= 0:
            return None

        long_setup = self._direction_setup(m5, m5_position, "LONG", previous_high, m5_atr)
        if long_setup is not None:
            return {
                **long_setup,
                "session_day": str(row["level_day"]),
                "previous_day_high": previous_high,
                "previous_day_low": previous_low,
                "m5_atr14": m5_atr,
                "estimated_entry_price": float(row["close"]),
            }

        short_setup = self._direction_setup(m5, m5_position, "SHORT", previous_low, m5_atr)
        if short_setup is not None:
            return {
                **short_setup,
                "session_day": str(row["level_day"]),
                "previous_day_high": previous_high,
                "previous_day_low": previous_low,
                "m5_atr14": m5_atr,
                "estimated_entry_price": float(row["close"]),
            }

        return None

    def _direction_setup(
        self,
        m5: pd.DataFrame,
        m5_position: int,
        direction: str,
        level: float,
        m5_atr: float,
    ) -> dict[str, Any] | None:
        current = m5.iloc[m5_position]
        open_price = float(current["open"])
        high = float(current["high"])
        low = float(current["low"])
        close = float(current["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.30:
            return None

        if direction == "LONG":
            if not (close > open_price and close >= level + 0.10 * m5_atr and close_position >= 0.60):
                return None
        else:
            if not (close < open_price and close <= level - 0.10 * m5_atr and close_position <= 0.40):
                return None

        breakout_position: int | None = None
        retest_position: int | None = None
        retest_high = float("nan")
        retest_low = float("nan")
        start = max(0, m5_position - 18)
        for position in range(start, m5_position):
            candidate = m5.iloc[position]
            candidate_open = float(candidate["open"])
            candidate_high = float(candidate["high"])
            candidate_low = float(candidate["low"])
            candidate_close = float(candidate["close"])
            if breakout_position is None:
                if direction == "LONG":
                    if candidate_close >= level + 0.25 * m5_atr and candidate_close > candidate_open:
                        breakout_position = position
                else:
                    if candidate_close <= level - 0.25 * m5_atr and candidate_close < candidate_open:
                        breakout_position = position
                continue

            if direction == "LONG":
                retest_happened = candidate_low <= level + 0.15 * m5_atr and candidate_close >= level - 0.10 * m5_atr
            else:
                retest_happened = candidate_high >= level - 0.15 * m5_atr and candidate_close <= level + 0.10 * m5_atr
            if retest_happened:
                retest_position = position
                retest_high = candidate_high
                retest_low = candidate_low

        if breakout_position is None or retest_position is None or retest_position >= m5_position:
            return None

        return {
            "direction": direction,
            "level": level,
            "breakout_index": int(breakout_position),
            "retest_index": int(retest_position),
            "retest_high": retest_high,
            "retest_low": retest_low,
            "confirmation_body_ratio": body_ratio,
            "confirmation_close_position": close_position,
        }


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=5)

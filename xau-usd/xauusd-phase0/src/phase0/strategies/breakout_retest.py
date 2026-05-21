from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.levels import (
    add_latest_confirmed_swings,
    add_previous_completed_daily_levels,
    add_previous_completed_weekly_levels,
    drop_duplicate_levels,
)
from phase0.strategies.base import (
    StrategyBase,
    context_point_size,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class BreakoutRetestStrategy(StrategyBase):
    name = "breakout_retest"
    version = "1.0"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)
        if "previous_daily_high" not in m5 or "previous_daily_low" not in m5:
            m5 = add_previous_completed_daily_levels(m5)
        if "previous_weekly_high" not in m5 or "previous_weekly_low" not in m5:
            m5 = add_previous_completed_weekly_levels(m5)
        if "latest_swing_high" not in m5 or "latest_swing_low" not in m5:
            m5 = add_latest_confirmed_swings(m5, left=4, right=4)
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
        arrays = self._bar_arrays(m5)

        for confirmation_position in range(2, len(m5)):
            retest_position = confirmation_position - 1
            candidates: list[dict[str, Any]] = []
            if float(arrays["close"][confirmation_position]) > float(arrays["open"][confirmation_position]):
                candidates.extend(
                    self._long_candidates(arrays, retest_position, point_size)
                )
            if float(arrays["close"][confirmation_position]) < float(arrays["open"][confirmation_position]):
                candidates.extend(
                    self._short_candidates(arrays, retest_position, point_size)
                )
            if not candidates:
                continue

            candidates.sort(key=lambda item: (item["stop_distance"], item["level_time_utc"]))
            selected = candidates[0]
            confirmation_time = m5["timestamp_utc"].iat[confirmation_position]
            retest_time = m5["timestamp_utc"].iat[retest_position]
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=confirmation_time.to_pydatetime(),
                    symbol=symbol,
                    direction=selected["direction"],
                    reason_code=selected["reason_code"],
                    metadata={
                        **selected,
                        "confirmation_index": int(confirmation_position),
                        "confirmation_time_utc": confirmation_time,
                        "retest_index": int(retest_position),
                        "retest_time_utc": retest_time,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        entry_price = float(signal.metadata["entry_price"])
        stop_loss = float(signal.metadata["stop_loss"])
        if signal.direction == "LONG":
            risk_price = entry_price - stop_loss
            if risk_price <= 0:
                raise ConfigError("Invalid Breakout-Retest long trade plan risk.")
            take_profit = entry_price + 1.5 * risk_price
        else:
            risk_price = stop_loss - entry_price
            if risk_price <= 0:
                raise ConfigError("Invalid Breakout-Retest short trade plan risk.")
            take_profit = entry_price - 1.5 * risk_price

        return TradePlan(
            expert=self.name,
            symbol=signal.symbol,
            direction=signal.direction,
            signal_time_utc=signal.timestamp_utc,
            entry_type="STOP",
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            invalidation_level=stop_loss,
            risk_reward=1.5,
            reason_code=signal.reason_code,
            metadata=signal.metadata,
        )

    def _long_candidates(
        self,
        arrays: dict[str, Any],
        retest_position: int,
        point_size: float,
    ) -> list[dict[str, Any]]:
        retest_atr = float(arrays["atr14"][retest_position])
        if not value_available(retest_atr):
            return []
        retest_low = float(arrays["low"][retest_position])
        retest_high = float(arrays["high"][retest_position])
        retest_close = float(arrays["close"][retest_position])

        candidates: list[dict[str, Any]] = []
        for break_position in range(max(0, retest_position - 20), retest_position):
            break_atr = float(arrays["atr14"][break_position])
            if not value_available(break_atr):
                continue
            for level in self._candidate_levels_from_arrays(arrays, break_position, "LONG", point_size):
                price = float(level["level_price"])
                if float(arrays["close"][break_position]) < price + 0.3 * break_atr:
                    continue
                if not (retest_low <= price + 5.0 * point_size):
                    continue
                if retest_close < price:
                    continue
                entry_price = retest_high + point_size
                stop_loss = retest_low - 0.1 * retest_atr
                risk_price = entry_price - stop_loss
                if risk_price <= 0:
                    continue
                candidates.append(
                    {
                        "direction": "LONG",
                        "reason_code": "BREAKOUT_RETEST_LONG",
                        "level_price": price,
                        "level_kind": level["level_kind"],
                        "level_time_utc": level["level_time_utc"],
                        "break_index": int(break_position),
                        "break_time_utc": arrays["timestamp"][break_position],
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "stop_distance": risk_price,
                        "expires_after_bars": 5,
                    }
                )
        return candidates

    def _short_candidates(
        self,
        arrays: dict[str, Any],
        retest_position: int,
        point_size: float,
    ) -> list[dict[str, Any]]:
        retest_atr = float(arrays["atr14"][retest_position])
        if not value_available(retest_atr):
            return []
        retest_low = float(arrays["low"][retest_position])
        retest_high = float(arrays["high"][retest_position])
        retest_close = float(arrays["close"][retest_position])

        candidates: list[dict[str, Any]] = []
        for break_position in range(max(0, retest_position - 20), retest_position):
            break_atr = float(arrays["atr14"][break_position])
            if not value_available(break_atr):
                continue
            for level in self._candidate_levels_from_arrays(arrays, break_position, "SHORT", point_size):
                price = float(level["level_price"])
                if float(arrays["close"][break_position]) > price - 0.3 * break_atr:
                    continue
                if not (retest_high >= price - 5.0 * point_size):
                    continue
                if retest_close > price:
                    continue
                entry_price = retest_low - point_size
                stop_loss = retest_high + 0.1 * retest_atr
                risk_price = stop_loss - entry_price
                if risk_price <= 0:
                    continue
                candidates.append(
                    {
                        "direction": "SHORT",
                        "reason_code": "BREAKOUT_RETEST_SHORT",
                        "level_price": price,
                        "level_kind": level["level_kind"],
                        "level_time_utc": level["level_time_utc"],
                        "break_index": int(break_position),
                        "break_time_utc": arrays["timestamp"][break_position],
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "stop_distance": risk_price,
                        "expires_after_bars": 5,
                    }
                )
        return candidates

    def _bar_arrays(self, m5: pd.DataFrame) -> dict[str, Any]:
        return {
            "timestamp": m5["timestamp_utc"].to_numpy(),
            "open": m5["open"].to_numpy(),
            "high": m5["high"].to_numpy(),
            "low": m5["low"].to_numpy(),
            "close": m5["close"].to_numpy(),
            "atr14": m5["atr14"].to_numpy(),
            "previous_daily_high": m5["previous_daily_high"].to_numpy(),
            "previous_daily_low": m5["previous_daily_low"].to_numpy(),
            "previous_weekly_high": m5["previous_weekly_high"].to_numpy(),
            "previous_weekly_low": m5["previous_weekly_low"].to_numpy(),
            "latest_swing_high": m5["latest_swing_high"].to_numpy(),
            "latest_swing_low": m5["latest_swing_low"].to_numpy(),
            "latest_swing_high_time_utc": m5["latest_swing_high_time_utc"].to_numpy(),
            "latest_swing_low_time_utc": m5["latest_swing_low_time_utc"].to_numpy(),
        }

    def _candidate_levels_from_arrays(
        self,
        arrays: dict[str, Any],
        position: int,
        direction: str,
        point_size: float,
    ) -> list[dict[str, Any]]:
        timestamp = arrays["timestamp"][position]
        if direction == "LONG":
            raw = (
                ("previous_daily_high", arrays["previous_daily_high"][position], timestamp),
                ("previous_weekly_high", arrays["previous_weekly_high"][position], timestamp),
                (
                    "latest_swing_high",
                    arrays["latest_swing_high"][position],
                    arrays["latest_swing_high_time_utc"][position],
                ),
            )
        else:
            raw = (
                ("previous_daily_low", arrays["previous_daily_low"][position], timestamp),
                ("previous_weekly_low", arrays["previous_weekly_low"][position], timestamp),
                (
                    "latest_swing_low",
                    arrays["latest_swing_low"][position],
                    arrays["latest_swing_low_time_utc"][position],
                ),
            )

        levels = [
            {"level_kind": kind, "level_price": float(price), "level_time_utc": level_time}
            for kind, price, level_time in raw
            if pd.notna(price) and pd.notna(level_time)
        ]
        if not levels:
            return []

        tolerance_price = 10.0 * point_size
        kept: list[dict[str, Any]] = []
        kept_prices: list[float] = []
        for level in sorted(
            levels,
            key=lambda item: pd.Timestamp(item["level_time_utc"]),
            reverse=True,
        ):
            price = float(level["level_price"])
            if all(abs(price - kept_price) > tolerance_price for kept_price in kept_prices):
                kept.append(level)
                kept_prices.append(price)
        return sorted(kept, key=lambda item: pd.Timestamp(item["level_time_utc"]))

    def _candidate_levels(
        self,
        row: pd.Series,
        direction: str,
        point_size: float,
    ) -> list[dict[str, Any]]:
        if direction == "LONG":
            raw = [
                ("previous_daily_high", row.get("previous_daily_high"), row["timestamp_utc"]),
                ("previous_weekly_high", row.get("previous_weekly_high"), row["timestamp_utc"]),
                ("latest_swing_high", row.get("latest_swing_high"), row.get("latest_swing_high_time_utc")),
            ]
        else:
            raw = [
                ("previous_daily_low", row.get("previous_daily_low"), row["timestamp_utc"]),
                ("previous_weekly_low", row.get("previous_weekly_low"), row["timestamp_utc"]),
                ("latest_swing_low", row.get("latest_swing_low"), row.get("latest_swing_low_time_utc")),
            ]

        levels = pd.DataFrame(
            [
                {"level_kind": kind, "level_price": price, "level_time_utc": timestamp}
                for kind, price, timestamp in raw
                if pd.notna(price) and pd.notna(timestamp)
            ]
        )
        if levels.empty:
            return []
        return drop_duplicate_levels(levels, point_size=point_size, tolerance_points=10).to_dict("records")

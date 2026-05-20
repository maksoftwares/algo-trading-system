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

        for confirmation_position in range(2, len(m5)):
            confirmation = m5.iloc[confirmation_position]
            retest_position = confirmation_position - 1
            retest = m5.iloc[retest_position]
            candidates: list[dict[str, Any]] = []
            if float(confirmation["close"]) > float(confirmation["open"]):
                candidates.extend(
                    self._long_candidates(m5, retest_position, confirmation_position, point_size)
                )
            if float(confirmation["close"]) < float(confirmation["open"]):
                candidates.extend(
                    self._short_candidates(m5, retest_position, confirmation_position, point_size)
                )
            if not candidates:
                continue

            candidates.sort(key=lambda item: (item["stop_distance"], item["level_time_utc"]))
            selected = candidates[0]
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=confirmation["timestamp_utc"].to_pydatetime(),
                    symbol=symbol,
                    direction=selected["direction"],
                    reason_code=selected["reason_code"],
                    metadata={
                        **selected,
                        "confirmation_index": int(confirmation_position),
                        "confirmation_time_utc": confirmation["timestamp_utc"],
                        "retest_index": int(retest_position),
                        "retest_time_utc": retest["timestamp_utc"],
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
        m5: pd.DataFrame,
        retest_position: int,
        confirmation_position: int,
        point_size: float,
    ) -> list[dict[str, Any]]:
        retest = m5.iloc[retest_position]
        retest_atr = float(retest["atr14"])
        if not value_available(retest_atr):
            return []

        candidates: list[dict[str, Any]] = []
        for break_position in range(max(0, retest_position - 20), retest_position):
            break_row = m5.iloc[break_position]
            if not value_available(break_row["atr14"]):
                continue
            for level in self._candidate_levels(break_row, "LONG", point_size):
                price = float(level["level_price"])
                if float(break_row["close"]) < price + 0.3 * float(break_row["atr14"]):
                    continue
                if not (float(retest["low"]) <= price + 5.0 * point_size):
                    continue
                if float(retest["close"]) < price:
                    continue
                entry_price = float(retest["high"]) + point_size
                stop_loss = float(retest["low"]) - 0.1 * retest_atr
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
                        "break_time_utc": break_row["timestamp_utc"],
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "stop_distance": risk_price,
                        "expires_after_bars": 5,
                    }
                )
        return candidates

    def _short_candidates(
        self,
        m5: pd.DataFrame,
        retest_position: int,
        confirmation_position: int,
        point_size: float,
    ) -> list[dict[str, Any]]:
        del confirmation_position
        retest = m5.iloc[retest_position]
        retest_atr = float(retest["atr14"])
        if not value_available(retest_atr):
            return []

        candidates: list[dict[str, Any]] = []
        for break_position in range(max(0, retest_position - 20), retest_position):
            break_row = m5.iloc[break_position]
            if not value_available(break_row["atr14"]):
                continue
            for level in self._candidate_levels(break_row, "SHORT", point_size):
                price = float(level["level_price"])
                if float(break_row["close"]) > price - 0.3 * float(break_row["atr14"]):
                    continue
                if not (float(retest["high"]) >= price - 5.0 * point_size):
                    continue
                if float(retest["close"]) > price:
                    continue
                entry_price = float(retest["low"]) - point_size
                stop_loss = float(retest["high"]) + 0.1 * retest_atr
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
                        "break_time_utc": break_row["timestamp_utc"],
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "stop_distance": risk_price,
                        "expires_after_bars": 5,
                    }
                )
        return candidates

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

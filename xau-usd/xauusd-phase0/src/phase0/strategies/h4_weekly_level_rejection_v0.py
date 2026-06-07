from __future__ import annotations

from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H4WeeklyLevelRejectionV0Strategy(StrategyBase):
    """Research-only H4 rejection of previous completed weekly extremes."""

    name = "h4_weekly_level_rejection_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.65

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        h4_close = pd.to_numeric(h4["close"], errors="coerce")
        h4_high = pd.to_numeric(h4["high"], errors="coerce")
        h4_low = pd.to_numeric(h4["low"], errors="coerce")
        h4["h4_atr14"] = atr(h4_high, h4_low, h4_close, 14)

        weekly = _completed_week_levels(d1)
        h4_times = pd.DataFrame(
            {
                "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
                "_row_order": range(len(h4)),
            }
        )
        merged = pd.merge_asof(
            h4_times.sort_values("timestamp_utc"),
            weekly.sort_values("timestamp_utc"),
            on="timestamp_utc",
            direction="backward",
        ).sort_values("_row_order")

        weekly_columns = [
            "previous_week_key",
            "previous_week_high",
            "previous_week_low",
            "previous_week_close",
            "previous_week_range",
        ]
        h4 = pd.concat([h4.reset_index(drop=True), merged[weekly_columns].reset_index(drop=True)], axis=1)
        context["H4"] = h4
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_week_direction: set[tuple[str, str]] = set()

        for position in range(80, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            week_key = _iso_week_key(timestamp)
            direction = str(setup["direction"])
            used_key = (week_key, direction)
            if used_key in used_week_direction:
                continue
            used_week_direction.add(used_key)

            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H4_WEEKLY_LEVEL_REJECTION_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_week": week_key},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = float(signal.metadata["rejection_low"]) - 0.35 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["rejection_high"]) + 0.35 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H4 weekly level rejection direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4 weekly level rejection trade plan risk.")

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
            metadata={**signal.metadata, "estimated_entry_price": estimated_entry},
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            row["h4_atr14"],
            row["previous_week_high"],
            row["previous_week_low"],
            row["previous_week_range"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        previous_week_high = float(row["previous_week_high"])
        previous_week_low = float(row["previous_week_low"])
        previous_week_range = float(row["previous_week_range"])
        if h4_atr <= 0 or previous_week_range < 1.50 * h4_atr:
            return None

        candle_range = high - low
        if candle_range <= 0 or candle_range < 0.55 * h4_atr:
            return None
        body_ratio = abs(close - open_price) / candle_range
        close_location = (close - low) / candle_range
        if body_ratio < 0.20:
            return None

        if (
            high >= previous_week_high + 0.10 * h4_atr
            and close <= previous_week_high - 0.05 * h4_atr
            and close < open_price
            and close_location <= 0.45
        ):
            return _setup_metadata(
                row, "SHORT", "previous_week_high", previous_week_high, h4_atr, high, low, close, body_ratio, close_location
            )

        if (
            low <= previous_week_low - 0.10 * h4_atr
            and close >= previous_week_low + 0.05 * h4_atr
            and close > open_price
            and close_location >= 0.55
        ):
            return _setup_metadata(
                row, "LONG", "previous_week_low", previous_week_low, h4_atr, high, low, close, body_ratio, close_location
            )

        return None


def _completed_week_levels(d1: pd.DataFrame) -> pd.DataFrame:
    frame = d1[["timestamp_utc", "high", "low", "close"]].copy()
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce")
    for column in ("high", "low", "close"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["timestamp_utc", "high", "low", "close"]).sort_values("timestamp_utc")

    iso = frame["timestamp_utc"].dt.isocalendar()
    frame["week_key"] = iso.year.astype(str) + "-W" + iso.week.astype(str).str.zfill(2)
    weekly = frame.groupby("week_key", sort=True).agg(
        timestamp_utc=("timestamp_utc", "max"),
        week_high=("high", "max"),
        week_low=("low", "min"),
        week_close=("close", "last"),
    )
    weekly["week_range"] = weekly["week_high"] - weekly["week_low"]
    weekly["previous_week_key"] = weekly.index.to_series().shift(1)
    weekly["previous_week_high"] = weekly["week_high"].shift(1)
    weekly["previous_week_low"] = weekly["week_low"].shift(1)
    weekly["previous_week_close"] = weekly["week_close"].shift(1)
    weekly["previous_week_range"] = weekly["week_range"].shift(1)
    return weekly.reset_index(drop=True)[
        [
            "timestamp_utc",
            "previous_week_key",
            "previous_week_high",
            "previous_week_low",
            "previous_week_close",
            "previous_week_range",
        ]
    ]


def _setup_metadata(
    row: pd.Series,
    direction: str,
    level_kind: str,
    level: float,
    h4_atr: float,
    high: float,
    low: float,
    close: float,
    body_ratio: float,
    close_location: float,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "level_kind": level_kind,
        "level": level,
        "previous_week_key": str(row["previous_week_key"]),
        "previous_week_range": float(row["previous_week_range"]),
        "h4_atr14": h4_atr,
        "rejection_high": high,
        "rejection_low": low,
        "estimated_entry_price": close,
        "confirmation_body_ratio": body_ratio,
        "confirmation_close_position": close_location,
    }


def _iso_week_key(timestamp: pd.Timestamp) -> str:
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    iso = timestamp.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"

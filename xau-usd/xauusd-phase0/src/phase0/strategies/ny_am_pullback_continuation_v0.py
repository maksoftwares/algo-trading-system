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


class NyAmPullbackContinuationV0Strategy(StrategyBase):
    """Disabled research strategy for the locked NY AM pullback continuation v0 hypothesis."""

    name = "ny_am_pullback_continuation_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)

        local_starts = _bar_start_times(m5).dt.tz_convert("America/New_York")
        day_key = local_starts.dt.strftime("%Y-%m-%d")
        local_minutes = local_starts.dt.hour * 60 + local_starts.dt.minute
        opening_mask = (local_minutes >= 9 * 60 + 30) & (local_minutes < 10 * 60)
        opening = pd.DataFrame(
            {
                "day": day_key[opening_mask],
                "open": pd.to_numeric(m5.loc[opening_mask, "open"], errors="coerce"),
                "high": pd.to_numeric(m5.loc[opening_mask, "high"], errors="coerce"),
                "low": pd.to_numeric(m5.loc[opening_mask, "low"], errors="coerce"),
                "close": pd.to_numeric(m5.loc[opening_mask, "close"], errors="coerce"),
            }
        )
        drive = opening.groupby("day", sort=True).agg(
            drive_open=("open", "first"),
            drive_high=("high", "max"),
            drive_low=("low", "min"),
            drive_close=("close", "last"),
        )
        m5["ny_am_day"] = day_key
        m5["ny_local_start_minute"] = local_minutes
        m5["opening_drive_open"] = day_key.map(drive["drive_open"])
        m5["opening_drive_high"] = day_key.map(drive["drive_high"])
        m5["opening_drive_low"] = day_key.map(drive["drive_low"])
        m5["opening_drive_close"] = day_key.map(drive["drive_close"])
        m5["opening_drive_mid"] = (m5["opening_drive_high"] + m5["opening_drive_low"]) / 2.0

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
        used_days: set[str] = set()

        for m5_position in range(24, len(m5)):
            row = m5.iloc[m5_position]
            setup = self._setup_at_position(m5, m5_position)
            if setup is None:
                continue
            session_day = str(setup["session_day"])
            if session_day in used_days:
                continue
            used_days.add(session_day)
            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=pd.Timestamp(row["timestamp_utc"]).to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"NY_AM_PULLBACK_CONTINUATION_V0_{direction}",
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
            stop_loss = float(signal.metadata["pullback_low"]) - 0.25 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = float(signal.metadata["pullback_high"]) + 0.25 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported NY AM pullback continuation direction {signal.direction!r}.")
        if risk_price <= 0:
            raise ConfigError("Invalid NY AM pullback continuation v0 trade plan risk.")
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
        local_minute = int(row["ny_local_start_minute"])
        if local_minute < 10 * 60 or local_minute >= 12 * 60:
            return None

        m5_atr = float(row["atr14"])
        drive_open = float(row["opening_drive_open"])
        drive_high = float(row["opening_drive_high"])
        drive_low = float(row["opening_drive_low"])
        drive_close = float(row["opening_drive_close"])
        drive_mid = float(row["opening_drive_mid"])
        if not value_available(m5_atr, drive_open, drive_high, drive_low, drive_close, drive_mid):
            return None
        if m5_atr <= 0 or drive_high <= drive_low:
            return None

        drive_move = drive_close - drive_open
        if drive_move >= 0.80 * m5_atr:
            return self._direction_setup(m5, m5_position, "LONG", row, m5_atr, drive_open, drive_high, drive_low, drive_close, drive_mid)
        if drive_move <= -0.80 * m5_atr:
            return self._direction_setup(m5, m5_position, "SHORT", row, m5_atr, drive_open, drive_high, drive_low, drive_close, drive_mid)
        return None

    def _direction_setup(
        self,
        m5: pd.DataFrame,
        m5_position: int,
        direction: str,
        row: pd.Series,
        m5_atr: float,
        drive_open: float,
        drive_high: float,
        drive_low: float,
        drive_close: float,
        drive_mid: float,
    ) -> dict[str, Any] | None:
        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        candle_range = high - low
        if candle_range <= 0:
            return None
        body_ratio = abs(open_price - close) / candle_range
        close_position = (close - low) / candle_range
        if body_ratio < 0.30:
            return None

        pullback_position: int | None = None
        pullback_high = float("nan")
        pullback_low = float("nan")
        for position in range(max(0, m5_position - 8), m5_position):
            candidate = m5.iloc[position]
            candidate_high = float(candidate["high"])
            candidate_low = float(candidate["low"])
            candidate_close = float(candidate["close"])
            if direction == "LONG":
                if (
                    candidate_low <= drive_mid + 0.15 * m5_atr
                    and candidate_low >= drive_mid - 0.25 * m5_atr
                    and candidate_close >= drive_mid - 0.25 * m5_atr
                ):
                    pullback_position = position
                    pullback_high = candidate_high
                    pullback_low = candidate_low
            else:
                if (
                    candidate_high >= drive_mid - 0.15 * m5_atr
                    and candidate_high <= drive_mid + 0.25 * m5_atr
                    and candidate_close <= drive_mid + 0.25 * m5_atr
                ):
                    pullback_position = position
                    pullback_high = candidate_high
                    pullback_low = candidate_low

        if pullback_position is None:
            return None

        if direction == "LONG":
            if not (close > open_price and close >= drive_mid + 0.20 * m5_atr and close_position >= 0.60):
                return None
        else:
            if not (close < open_price and close <= drive_mid - 0.20 * m5_atr and close_position <= 0.40):
                return None

        return {
            "direction": direction,
            "session_day": str(row["ny_am_day"]),
            "opening_drive_open": drive_open,
            "opening_drive_high": drive_high,
            "opening_drive_low": drive_low,
            "opening_drive_close": drive_close,
            "opening_drive_mid": drive_mid,
            "m5_atr14": m5_atr,
            "pullback_index": int(pullback_position),
            "pullback_high": pullback_high,
            "pullback_low": pullback_low,
            "estimated_entry_price": close,
            "confirmation_body_ratio": body_ratio,
            "confirmation_close_position": close_position,
        }


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=5)

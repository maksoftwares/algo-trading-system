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


class OpeningDriveFailedContinuationV0Strategy(StrategyBase):
    """Disabled research strategy for the locked opening-drive failed-continuation v0 hypothesis."""

    name = "opening_drive_failed_continuation_v0"
    version = "0.1-research-disabled"

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], 14)

        bar_starts = _bar_start_times(m5)
        m5["bar_start_minute_utc"] = bar_starts.dt.hour * 60 + bar_starts.dt.minute
        m5["session_day_utc"] = bar_starts.dt.strftime("%Y-%m-%d")

        drive_mask = (
            (m5["bar_start_minute_utc"] >= 13 * 60 + 30)
            & (m5["bar_start_minute_utc"] < 14 * 60)
        )
        drive = m5.loc[drive_mask].copy()
        if drive.empty:
            m5["opening_drive_open"] = pd.NA
            m5["opening_drive_close"] = pd.NA
            m5["opening_drive_high"] = pd.NA
            m5["opening_drive_low"] = pd.NA
            m5["opening_drive_range"] = pd.NA
        else:
            grouped = drive.groupby("session_day_utc", sort=False)
            drive_open = grouped["open"].first()
            drive_close = grouped["close"].last()
            drive_high = grouped["high"].max()
            drive_low = grouped["low"].min()
            m5["opening_drive_open"] = m5["session_day_utc"].map(drive_open)
            m5["opening_drive_close"] = m5["session_day_utc"].map(drive_close)
            m5["opening_drive_high"] = m5["session_day_utc"].map(drive_high)
            m5["opening_drive_low"] = m5["session_day_utc"].map(drive_low)
            m5["opening_drive_range"] = m5["opening_drive_high"] - m5["opening_drive_low"]

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
        used_session_days: set[str] = set()

        for position in range(1, len(m5)):
            setup = self._setup_at_position(m5, position)
            if setup is None:
                continue
            session_day = str(setup["session_day_utc"])
            if session_day in used_session_days:
                continue
            used_session_days.add(session_day)
            direction = str(setup["direction"])
            timestamp = pd.Timestamp(m5["timestamp_utc"].iat[position])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"OPENING_DRIVE_FAILED_CONTINUATION_V0_{direction}",
                    metadata={
                        **setup,
                        "m5_index": int(position),
                        "point_size": point_size,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m5_atr = float(signal.metadata["m5_atr14"])
        drive_high = float(signal.metadata["opening_drive_high"])
        drive_low = float(signal.metadata["opening_drive_low"])
        failure_high = float(signal.metadata["failure_high"])
        failure_low = float(signal.metadata["failure_low"])
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = min(failure_low, drive_low) - 0.25 * m5_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.5 * risk_price
        elif direction == "SHORT":
            stop_loss = max(failure_high, drive_high) + 0.25 * m5_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.5 * risk_price
        else:
            raise ConfigError(f"Unsupported opening-drive failed-continuation direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid opening-drive failed-continuation v0 trade plan risk.")
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

    def _setup_at_position(self, m5: pd.DataFrame, position: int) -> dict[str, Any] | None:
        row = m5.iloc[position]
        start_minute = int(row["bar_start_minute_utc"])
        if start_minute < 14 * 60 or start_minute >= 16 * 60:
            return None

        m5_atr = float(row["atr14"])
        drive_open = float(row["opening_drive_open"])
        drive_close = float(row["opening_drive_close"])
        drive_high = float(row["opening_drive_high"])
        drive_low = float(row["opening_drive_low"])
        drive_range = float(row["opening_drive_range"])
        if not value_available(m5_atr, drive_open, drive_close, drive_high, drive_low, drive_range):
            return None
        if m5_atr <= 0 or drive_range <= 0:
            return None
        if drive_range < 1.0 * m5_atr or drive_range > 8.0 * m5_atr:
            return None

        drive_body = abs(drive_close - drive_open)
        drive_body_ratio = drive_body / drive_range
        if drive_body_ratio < 0.35:
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
        if body_ratio < 0.35:
            return None

        if (
            drive_close > drive_open
            and high >= drive_high + 0.10 * m5_atr
            and close <= drive_high - 0.05 * m5_atr
            and close < open_price
            and close_position <= 0.45
        ):
            return self._metadata(
                "SHORT",
                row,
                m5_atr,
                drive_open,
                drive_close,
                drive_high,
                drive_low,
                drive_range,
                drive_body_ratio,
                open_price,
                high,
                low,
                close,
                body_ratio,
                close_position,
            )

        if (
            drive_close < drive_open
            and low <= drive_low - 0.10 * m5_atr
            and close >= drive_low + 0.05 * m5_atr
            and close > open_price
            and close_position >= 0.55
        ):
            return self._metadata(
                "LONG",
                row,
                m5_atr,
                drive_open,
                drive_close,
                drive_high,
                drive_low,
                drive_range,
                drive_body_ratio,
                open_price,
                high,
                low,
                close,
                body_ratio,
                close_position,
            )

        return None

    def _metadata(
        self,
        direction: str,
        row: pd.Series,
        m5_atr: float,
        drive_open: float,
        drive_close: float,
        drive_high: float,
        drive_low: float,
        drive_range: float,
        drive_body_ratio: float,
        open_price: float,
        high: float,
        low: float,
        close: float,
        body_ratio: float,
        close_position: float,
    ) -> dict[str, Any]:
        return {
            "direction": direction,
            "session_day_utc": str(row["session_day_utc"]),
            "opening_drive_window_utc": "13:30-14:00",
            "failure_window_utc": "14:00-16:00",
            "opening_drive_open": drive_open,
            "opening_drive_close": drive_close,
            "opening_drive_high": drive_high,
            "opening_drive_low": drive_low,
            "opening_drive_range": drive_range,
            "opening_drive_body_ratio": drive_body_ratio,
            "m5_atr14": m5_atr,
            "failure_open": open_price,
            "failure_high": high,
            "failure_low": low,
            "failure_close": close,
            "failure_body_ratio": body_ratio,
            "failure_close_position": close_position,
            "estimated_entry_price": close,
        }


def _bar_start_times(frame: pd.DataFrame) -> pd.Series:
    if "bar_start_utc" in frame:
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce")
        if not starts.isna().all():
            return starts
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce") - pd.Timedelta(minutes=5)

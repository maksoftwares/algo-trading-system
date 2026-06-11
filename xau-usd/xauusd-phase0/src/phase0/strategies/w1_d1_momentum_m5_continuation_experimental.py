from __future__ import annotations

from typing import Any

import numpy as np
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


class W1D1MomentumM5ContinuationExperimentalStrategy(StrategyBase):
    """Research mirror for W1D1MomentumM5ContinuationExperimental.mq5."""

    name = "w1_d1_momentum_m5_continuation_experimental"
    version = "0.2-active-experimental-mirror"

    d1_ema_fast_period = 20
    d1_ema_slow_period = 50
    w1_momentum_weeks = 4
    m5_ema_period = 20
    m5_atr_period = 14
    min_body_fraction = 0.35
    enable_impulse_trigger = False
    impulse_body_fraction = 0.45
    impulse_atr_multiple = 0.45
    stop_atr_multiple = 4.0
    stop_floor_points = 250
    risk_reward = 1.5
    max_signals_per_day = 12
    cooldown_minutes = 10

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        m5 = require_frame(context, "M5")
        d1 = require_frame(context, "D1")

        if "atr14" not in m5:
            m5["atr14"] = atr(m5["high"], m5["low"], m5["close"], self.m5_atr_period)
        if "ema20" not in m5:
            m5["ema20"] = pd.to_numeric(m5["close"], errors="coerce").ewm(
                span=self.m5_ema_period, adjust=False
            ).mean()
        if "range" not in m5:
            m5["range"] = pd.to_numeric(m5["high"], errors="coerce") - pd.to_numeric(
                m5["low"], errors="coerce"
            )
        if "body_fraction" not in m5:
            m5_range = pd.to_numeric(m5["range"], errors="coerce").replace(0.0, pd.NA)
            m5["body_fraction"] = (
                pd.to_numeric(m5["close"], errors="coerce")
                - pd.to_numeric(m5["open"], errors="coerce")
            ).abs() / m5_range

        if "ema20" not in d1:
            d1["ema20"] = pd.to_numeric(d1["close"], errors="coerce").ewm(
                span=self.d1_ema_fast_period, adjust=False
            ).mean()
        if "ema50" not in d1:
            d1["ema50"] = pd.to_numeric(d1["close"], errors="coerce").ewm(
                span=self.d1_ema_slow_period, adjust=False
            ).mean()

        context["M5"] = m5
        context["D1"] = d1
        context["_W1"] = _weekly_closes_from_d1(d1)
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        m5 = context["M5"]
        d1 = context["D1"]
        w1 = context["_W1"]
        symbol = context_symbol(context)
        point_size = context_point_size(context)

        m5_values = _timestamp_values(m5)
        d1_values = _timestamp_values(d1)
        w1_values = _timestamp_values(w1)
        signals: list[Signal] = []
        signals_by_day: dict[str, int] = {}
        last_signal_time: pd.Timestamp | None = None

        for m5_position in range(max(72, self.m5_ema_period + self.m5_atr_period), len(m5)):
            row = m5.iloc[m5_position]
            timestamp = pd.Timestamp(row["timestamp_utc"])
            timestamp_value = int(m5_values[m5_position])

            day_key = _day_key(timestamp)
            if signals_by_day.get(day_key, 0) >= self.max_signals_per_day:
                continue
            if (
                last_signal_time is not None
                and timestamp - last_signal_time < pd.Timedelta(minutes=self.cooldown_minutes)
            ):
                continue

            d1_position = _latest_completed_position_from_values(d1_values, timestamp_value)
            w1_position = _latest_completed_position_from_values(w1_values, timestamp_value)
            if d1_position is None or w1_position is None:
                continue
            bias = self._higher_timeframe_bias(d1, w1, d1_position, w1_position)
            if bias is None:
                continue
            setup = self._setup_at_position(m5, m5_position, bias)
            if setup is None:
                continue

            direction = str(setup["direction"])
            signals_by_day[day_key] = signals_by_day.get(day_key, 0) + 1
            last_signal_time = timestamp
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"W1D1_M5_CONTINUATION_EXPERIMENTAL_{direction}",
                    metadata={
                        **setup,
                        "m5_index": int(m5_position),
                        "d1_index": int(d1_position),
                        "w1_index": int(w1_position),
                        "point_size": point_size,
                        "signal_day_utc": day_key,
                    },
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        m5_atr = float(signal.metadata["m5_atr14"])
        point_size = float(signal.metadata["point_size"])
        stop_distance = max(self.stop_atr_multiple * m5_atr, self.stop_floor_points * point_size)
        direction = signal.direction.upper()

        if direction == "LONG":
            stop_loss = estimated_entry - stop_distance
            take_profit = estimated_entry + self.risk_reward * stop_distance
        elif direction == "SHORT":
            stop_loss = estimated_entry + stop_distance
            take_profit = estimated_entry - self.risk_reward * stop_distance
        else:
            raise ConfigError(f"Unsupported W1/D1 M5 continuation direction {signal.direction!r}.")

        if stop_distance <= 0:
            raise ConfigError("Invalid W1/D1 M5 continuation trade plan risk.")

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
                "stop_distance_price": stop_distance,
            },
        )

    def _higher_timeframe_bias(
        self,
        d1: pd.DataFrame,
        w1: pd.DataFrame,
        d1_position: int,
        w1_position: int,
    ) -> dict[str, Any] | None:
        if d1_position < self.d1_ema_slow_period or w1_position < self.w1_momentum_weeks:
            return None

        d1_fast = float(d1["ema20"].iat[d1_position])
        d1_slow = float(d1["ema50"].iat[d1_position])
        w1_close_1 = float(w1["close"].iat[w1_position])
        w1_close_n = float(w1["close"].iat[w1_position - self.w1_momentum_weeks])
        if not value_available(d1_fast, d1_slow, w1_close_1, w1_close_n):
            return None

        w1_momentum = w1_close_1 - w1_close_n
        if d1_fast > d1_slow and w1_momentum >= 0:
            return {
                "direction": "LONG",
                "bias_reason": "bull",
                "d1_ema20": d1_fast,
                "d1_ema50": d1_slow,
                "w1_momentum": w1_momentum,
            }
        if d1_fast < d1_slow and w1_momentum <= 0:
            return {
                "direction": "SHORT",
                "bias_reason": "bear",
                "d1_ema20": d1_fast,
                "d1_ema50": d1_slow,
                "w1_momentum": w1_momentum,
            }
        return None

    def _setup_at_position(
        self,
        m5: pd.DataFrame,
        m5_position: int,
        bias: dict[str, Any],
    ) -> dict[str, Any] | None:
        if m5_position < 1:
            return None
        row = m5.iloc[m5_position]
        prev = m5.iloc[m5_position - 1]
        required = (
            row["open"],
            row["high"],
            row["low"],
            row["close"],
            prev["close"],
            row["ema20"],
            row["atr14"],
            row["body_fraction"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        high = float(row["high"])
        low = float(row["low"])
        close = float(row["close"])
        prev_close = float(prev["close"])
        m5_ema = float(row["ema20"])
        m5_atr = float(row["atr14"])
        body_fraction = float(row["body_fraction"])
        if m5_atr <= 0 or body_fraction < self.min_body_fraction:
            return None

        direction = str(bias["direction"])
        trigger_type = ""
        m5_range = high - low
        close_position = (close - low) / m5_range if m5_range > 0 else 0.5
        net_move = abs(close - prev_close)
        if direction == "LONG":
            pullback = low <= m5_ema and close > m5_ema and close > open_price
            impulse = (
                close > m5_ema
                and close > prev_close
                and close > open_price
                and body_fraction >= self.impulse_body_fraction
                and close_position >= 0.65
                and net_move >= self.impulse_atr_multiple * m5_atr
            )
            if pullback:
                trigger_type = "pullback"
            elif self.enable_impulse_trigger and impulse:
                trigger_type = "impulse"
            else:
                return None
        elif direction == "SHORT":
            pullback = high >= m5_ema and close < m5_ema and close < open_price
            impulse = (
                close < m5_ema
                and close < prev_close
                and close < open_price
                and body_fraction >= self.impulse_body_fraction
                and close_position <= 0.35
                and net_move >= self.impulse_atr_multiple * m5_atr
            )
            if pullback:
                trigger_type = "pullback"
            elif self.enable_impulse_trigger and impulse:
                trigger_type = "impulse"
            else:
                return None
        else:
            return None

        return {
            **bias,
            "trigger_type": trigger_type,
            "m5_atr14": m5_atr,
            "m5_ema20": m5_ema,
            "m5_open": open_price,
            "m5_high": high,
            "m5_low": low,
            "m5_close": close,
            "m5_prev_close": prev_close,
            "m5_body_fraction": body_fraction,
            "m5_close_position": close_position,
            "m5_net_move": net_move,
            "estimated_entry_price": close,
        }


def _weekly_closes_from_d1(d1: pd.DataFrame) -> pd.DataFrame:
    prepared = d1.copy()
    prepared["timestamp_utc"] = pd.to_datetime(prepared["timestamp_utc"], utc=True, errors="coerce")
    prepared = prepared.dropna(subset=["timestamp_utc"]).sort_values("timestamp_utc")
    weekly = (
        prepared.set_index("timestamp_utc")[["close"]]
        .resample("W-FRI")
        .last()
        .dropna()
        .reset_index()
    )
    return weekly


def _timestamp_values(frame: pd.DataFrame) -> np.ndarray:
    return pd.to_datetime(frame["timestamp_utc"], utc=True, errors="coerce").astype("int64").to_numpy()


def _latest_completed_position_from_values(values: np.ndarray, timestamp_value: int) -> int | None:
    position = int(np.searchsorted(values, timestamp_value, side="right")) - 1
    return position if position >= 0 else None


def _day_key(timestamp: pd.Timestamp) -> str:
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp.strftime("%Y-%m-%d")

from __future__ import annotations

from typing import Any

import numpy as np
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


class H1CalendarDriftStateV0Strategy(StrategyBase):
    """Research-only learned H1 hour-of-week drift candidate."""

    name = "h1_calendar_drift_state_v0"
    version = "0.1-research-disabled"

    horizon_bars = 6
    training_window = 8760
    min_bucket_observations = 8
    score_threshold = 1.20
    mean_threshold_atr = 0.08

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")

        if "atr14" not in h1:
            h1["atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)

        close = pd.to_numeric(h1["close"], errors="coerce")
        atr14 = pd.to_numeric(h1["atr14"], errors="coerce")
        h1["calendar_hour_bucket"] = _hour_of_week_bucket(h1)
        h1["calendar_forward_return_6h_atr"] = (
            close.shift(-self.horizon_bars) - close
        ) / atr14.replace(0.0, pd.NA)
        mean, score, observations = _walk_forward_bucket_scores(
            h1,
            bucket_column="calendar_hour_bucket",
            label_column="calendar_forward_return_6h_atr",
            horizon_bars=self.horizon_bars,
            training_window=self.training_window,
            min_bucket_observations=self.min_bucket_observations,
        )
        h1["calendar_drift_mean_atr"] = mean
        h1["calendar_drift_score"] = score
        h1["calendar_bucket_observations"] = observations

        context["H1"] = h1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h1 = context["H1"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(self.horizon_bars + 1, len(h1)):
            row = h1.iloc[position]
            setup = self._setup_at_row(row)
            if setup is None:
                continue

            timestamp = pd.Timestamp(row["timestamp_utc"])
            day_direction = (timestamp.strftime("%Y-%m-%d"), str(setup["direction"]))
            if day_direction in used_day_direction:
                continue
            used_day_direction.add(day_direction)

            direction = str(setup["direction"])
            signals.append(
                Signal(
                    expert=self.name,
                    timestamp_utc=timestamp.to_pydatetime(),
                    symbol=symbol,
                    direction=direction,
                    reason_code=f"H1_CALENDAR_DRIFT_STATE_V0_{direction}",
                    metadata={**setup, "h1_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h1_atr = float(signal.metadata["atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 0.95 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.35 * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 0.95 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.35 * risk_price
        else:
            raise ConfigError(f"Unsupported H1 calendar-drift direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 calendar-drift trade plan risk.")

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
            risk_reward=1.35,
            reason_code=signal.reason_code,
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 144,
                "planned_time_stop_h1_bars": 6,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["close"],
            row["atr14"],
            row["calendar_hour_bucket"],
            row["calendar_drift_mean_atr"],
            row["calendar_drift_score"],
            row["calendar_bucket_observations"],
        )
        if not value_available(*required):
            return None

        close = float(row["close"])
        atr14 = float(row["atr14"])
        bucket = int(row["calendar_hour_bucket"])
        mean_atr = float(row["calendar_drift_mean_atr"])
        score = float(row["calendar_drift_score"])
        observations = int(row["calendar_bucket_observations"])
        if atr14 <= 0 or observations < self.min_bucket_observations:
            return None

        if score >= self.score_threshold and mean_atr >= self.mean_threshold_atr:
            return _setup_metadata(row, "LONG", close, bucket, mean_atr, score, observations)
        if score <= -self.score_threshold and mean_atr <= -self.mean_threshold_atr:
            return _setup_metadata(row, "SHORT", close, bucket, mean_atr, score, observations)
        return None


def _hour_of_week_bucket(h1: pd.DataFrame) -> pd.Series:
    timestamps = pd.to_datetime(h1["timestamp_utc"], utc=True, errors="coerce")
    buckets = timestamps.dt.dayofweek * 24 + timestamps.dt.hour
    return buckets.astype("Int64")


def _walk_forward_bucket_scores(
    frame: pd.DataFrame,
    bucket_column: str,
    label_column: str,
    horizon_bars: int,
    training_window: int,
    min_bucket_observations: int,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    buckets = pd.to_numeric(frame[bucket_column], errors="coerce").fillna(-1).to_numpy(dtype=int)
    labels = pd.to_numeric(frame[label_column], errors="coerce").clip(-3.0, 3.0).to_numpy(dtype=float)
    means = np.full(len(frame), np.nan, dtype=float)
    scores = np.full(len(frame), np.nan, dtype=float)
    observations = np.zeros(len(frame), dtype=int)

    positions_by_bucket = {
        bucket: np.flatnonzero(buckets == bucket) for bucket in sorted(set(buckets)) if bucket >= 0
    }
    for position in range(horizon_bars + 1, len(frame)):
        bucket = int(buckets[position])
        if bucket < 0:
            continue
        bucket_positions = positions_by_bucket.get(bucket)
        if bucket_positions is None or len(bucket_positions) == 0:
            continue

        train_end = position - horizon_bars
        train_start = max(0, train_end - training_window)
        left = int(np.searchsorted(bucket_positions, train_start, side="left"))
        right = int(np.searchsorted(bucket_positions, train_end, side="left"))
        train_positions = bucket_positions[left:right]
        if len(train_positions) == 0:
            continue

        sample = labels[train_positions]
        sample = sample[np.isfinite(sample)]
        sample_count = int(len(sample))
        if sample_count < min_bucket_observations:
            continue

        sample_mean = float(sample.mean())
        sample_std = float(sample.std(ddof=1)) if sample_count > 1 else 0.0
        std_error = max(sample_std, 0.15) / np.sqrt(sample_count)
        means[position] = sample_mean
        scores[position] = sample_mean / std_error
        observations[position] = sample_count

    return (
        pd.Series(means, index=frame.index),
        pd.Series(scores, index=frame.index),
        pd.Series(observations, index=frame.index),
    )


def _setup_metadata(
    row: pd.Series,
    direction: str,
    estimated_entry: float,
    bucket: int,
    mean_atr: float,
    score: float,
    observations: int,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "atr14": float(row["atr14"]),
        "calendar_hour_bucket": bucket,
        "calendar_drift_mean_atr": mean_atr,
        "calendar_drift_score": score,
        "calendar_bucket_observations": observations,
    }

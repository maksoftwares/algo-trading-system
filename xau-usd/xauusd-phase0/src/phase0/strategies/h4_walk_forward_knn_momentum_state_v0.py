from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr
from phase0.strategies.base import StrategyBase, context_symbol, copy_context, require_frame, value_available


class H4WalkForwardKnnMomentumStateV0Strategy(StrategyBase):
    """Research-only H4 walk-forward nearest-neighbor momentum-state candidate."""

    name = "h4_walk_forward_knn_momentum_state_v0"
    version = "0.1-research-disabled"

    horizon_h4_bars = 3
    training_window_h4_bars = 1800
    neighbor_count = 60
    min_training_examples = 120
    min_abs_mean_forward_atr = 0.18
    min_abs_score = 1.15
    risk_reward = 1.30

    feature_columns = (
        "h4_return_1_atr",
        "h4_return_3_atr",
        "h4_return_6_atr",
        "h4_range_atr",
        "h4_body_ratio",
        "h4_close_position",
        "d1_momentum5_atr",
        "d1_momentum20_atr",
        "d1_range_atr",
        "d1_close_position",
    )

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        d1 = require_frame(context, "D1")

        h4 = _h4_features(h4, self.horizon_h4_bars)
        d1 = _d1_features(d1)
        h4 = _merge_d1_state(h4, d1)
        context["H4"] = h4
        context["D1"] = d1
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        symbol = context_symbol(context)
        feature_matrix = (
            h4.loc[:, self.feature_columns]
            .apply(pd.to_numeric, errors="coerce")
            .to_numpy(dtype=float, na_value=np.nan)
        )
        labels = pd.to_numeric(h4["forward_return_3h4_atr"], errors="coerce").to_numpy(dtype=float)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        first_position = max(
            self.training_window_h4_bars // 2,
            self.horizon_h4_bars + self.min_training_examples,
        )
        for position in range(first_position, len(h4)):
            row = h4.iloc[position]
            setup = self._setup_at_position(h4, feature_matrix, labels, position)
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
                    reason_code=f"H4_WALK_FORWARD_KNN_MOMENTUM_STATE_V0_{direction}",
                    metadata={**setup, "h4_index": int(position), "signal_day": day_direction[0]},
                )
            )
        return signals

    def build_trade_plan(self, signal: Signal, data_context: dict[str, Any]) -> TradePlan:
        del data_context
        direction = signal.direction.upper()
        estimated_entry = float(signal.metadata["estimated_entry_price"])
        h4_atr = float(signal.metadata["h4_atr14"])

        if direction == "LONG":
            stop_loss = estimated_entry - 0.95 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 0.95 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported H4 KNN state direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H4 walk-forward KNN momentum-state trade plan risk.")

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
                "max_holding_bars": 144,
                "planned_time_stop_h4_bars": self.horizon_h4_bars,
            },
        )

    def _setup_at_position(
        self,
        h4: pd.DataFrame,
        feature_matrix: np.ndarray,
        labels: np.ndarray,
        position: int,
    ) -> dict[str, Any] | None:
        row = h4.iloc[position]
        required = (row["close"], row["atr14"], *[row[column] for column in self.feature_columns])
        if not value_available(*required):
            return None

        h4_atr = float(row["atr14"])
        if h4_atr <= 0:
            return None

        train_end = position - self.horizon_h4_bars
        if train_end <= 0:
            return None
        train_start = max(0, train_end - self.training_window_h4_bars)
        train_features = feature_matrix[train_start:train_end]
        train_labels = labels[train_start:train_end]
        valid = np.isfinite(train_labels) & np.isfinite(train_features).all(axis=1)
        if int(valid.sum()) < self.min_training_examples:
            return None

        current = feature_matrix[position]
        if not np.isfinite(current).all():
            return None

        valid_features = train_features[valid]
        valid_labels = train_labels[valid]
        distances = np.square(valid_features - current).sum(axis=1)
        neighbor_count = min(self.neighbor_count, len(distances))
        neighbor_positions = np.argpartition(distances, neighbor_count - 1)[:neighbor_count]
        neighbor_labels = valid_labels[neighbor_positions]
        mean_forward_atr = float(neighbor_labels.mean())
        std_forward_atr = float(neighbor_labels.std(ddof=1)) if neighbor_count > 1 else 0.0
        score = mean_forward_atr / (max(std_forward_atr, 0.20) / np.sqrt(neighbor_count))

        if mean_forward_atr >= self.min_abs_mean_forward_atr and score >= self.min_abs_score:
            return _setup_metadata(row, "LONG", mean_forward_atr, score, neighbor_count)
        if mean_forward_atr <= -self.min_abs_mean_forward_atr and score <= -self.min_abs_score:
            return _setup_metadata(row, "SHORT", mean_forward_atr, score, neighbor_count)
        return None


def _h4_features(h4: pd.DataFrame, horizon: int) -> pd.DataFrame:
    prepared = h4.copy()
    close = pd.to_numeric(prepared["close"], errors="coerce")
    open_price = pd.to_numeric(prepared["open"], errors="coerce")
    high = pd.to_numeric(prepared["high"], errors="coerce")
    low = pd.to_numeric(prepared["low"], errors="coerce")
    if "atr14" not in prepared:
        prepared["atr14"] = atr(high, low, close, 14)
    atr14 = pd.to_numeric(prepared["atr14"], errors="coerce")
    candle_range = high - low
    prepared["h4_return_1_atr"] = close.diff(1) / atr14.replace(0.0, pd.NA)
    prepared["h4_return_3_atr"] = close.diff(3) / atr14.replace(0.0, pd.NA)
    prepared["h4_return_6_atr"] = close.diff(6) / atr14.replace(0.0, pd.NA)
    prepared["h4_range_atr"] = candle_range / atr14.replace(0.0, pd.NA)
    prepared["h4_body_ratio"] = (close - open_price).abs() / candle_range.replace(0.0, pd.NA)
    prepared["h4_close_position"] = (close - low) / candle_range.replace(0.0, pd.NA)
    prepared["forward_return_3h4_atr"] = (close.shift(-horizon) - close) / atr14.replace(0.0, pd.NA)
    return prepared


def _d1_features(d1: pd.DataFrame) -> pd.DataFrame:
    prepared = d1.copy()
    close = pd.to_numeric(prepared["close"], errors="coerce")
    high = pd.to_numeric(prepared["high"], errors="coerce")
    low = pd.to_numeric(prepared["low"], errors="coerce")
    if "atr14" not in prepared:
        prepared["atr14"] = atr(high, low, close, 14)
    atr14 = pd.to_numeric(prepared["atr14"], errors="coerce")
    candle_range = high - low
    prepared["d1_momentum5_atr"] = close.diff(5) / atr14.replace(0.0, pd.NA)
    prepared["d1_momentum20_atr"] = close.diff(20) / atr14.replace(0.0, pd.NA)
    prepared["d1_range_atr"] = candle_range / atr14.replace(0.0, pd.NA)
    prepared["d1_close_position"] = (close - low) / candle_range.replace(0.0, pd.NA)
    return prepared[
        [
            "timestamp_utc",
            "d1_momentum5_atr",
            "d1_momentum20_atr",
            "d1_range_atr",
            "d1_close_position",
        ]
    ]


def _merge_d1_state(h4: pd.DataFrame, d1: pd.DataFrame) -> pd.DataFrame:
    h4_sorted = h4.sort_values("timestamp_utc").reset_index(drop=True)
    d1_sorted = d1.sort_values("timestamp_utc").reset_index(drop=True)
    return pd.merge_asof(
        h4_sorted,
        d1_sorted,
        on="timestamp_utc",
        direction="backward",
    )


def _setup_metadata(
    row: pd.Series,
    direction: str,
    mean_forward_atr: float,
    score: float,
    neighbor_count: int,
) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": float(row["close"]),
        "h4_atr14": float(row["atr14"]),
        "mean_forward_atr": mean_forward_atr,
        "knn_score": score,
        "neighbor_count": neighbor_count,
        "h4_return_1_atr": float(row["h4_return_1_atr"]),
        "h4_return_3_atr": float(row["h4_return_3_atr"]),
        "h4_return_6_atr": float(row["h4_return_6_atr"]),
        "d1_momentum5_atr": float(row["d1_momentum5_atr"]),
        "d1_momentum20_atr": float(row["d1_momentum20_atr"]),
    }

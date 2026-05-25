from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H1WalkForwardLinearStateV0Strategy(StrategyBase):
    """Research-only auditable walk-forward learned H1 state candidate."""

    name = "h1_walk_forward_linear_state_v0"
    version = "0.1-research-disabled"

    horizon_bars = 12
    training_window = 960
    min_training_rows = 360
    update_every_bars = 12
    ridge_lambda = 0.25
    score_threshold = 0.42

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h1 = require_frame(context, "H1")

        if "atr14" not in h1:
            h1["atr14"] = atr(h1["high"], h1["low"], h1["close"], 14)
        if "ema24" not in h1:
            h1["ema24"] = ema(h1["close"], 24)

        close = pd.to_numeric(h1["close"], errors="coerce")
        open_price = pd.to_numeric(h1["open"], errors="coerce")
        high = pd.to_numeric(h1["high"], errors="coerce")
        low = pd.to_numeric(h1["low"], errors="coerce")
        atr14 = pd.to_numeric(h1["atr14"], errors="coerce")
        returns = np.log(close / close.shift(1))
        one_hour_moves = close.diff().abs()
        path_24h = one_hour_moves.rolling(24, min_periods=24).sum()
        net_24h = close - close.shift(24)
        realized_vol_24h = returns.rolling(24, min_periods=24).std() * np.sqrt(24)
        realized_vol_120h = returns.rolling(120, min_periods=72).std() * np.sqrt(24)
        tick_count = _tick_count_series(h1)
        tick_mean = tick_count.shift(1).rolling(240, min_periods=80).mean()
        tick_std = tick_count.shift(1).rolling(240, min_periods=80).std()

        h1["wf_momentum_6h_atr"] = (close - close.shift(6)) / atr14.replace(0.0, pd.NA)
        h1["wf_momentum_24h_atr"] = net_24h / atr14.replace(0.0, pd.NA)
        h1["wf_close_ema24_atr"] = (close - pd.to_numeric(h1["ema24"], errors="coerce")) / atr14.replace(
            0.0,
            pd.NA,
        )
        h1["wf_range_atr"] = (high - low) / atr14.replace(0.0, pd.NA)
        h1["wf_body_ratio"] = (close - open_price).abs() / (high - low).replace(0.0, pd.NA)
        h1["wf_directional_efficiency_24h"] = net_24h.abs() / path_24h.replace(0.0, pd.NA)
        h1["wf_realized_vol_ratio"] = realized_vol_24h / realized_vol_120h.replace(0.0, pd.NA)
        tick_count_z = (tick_count - tick_mean) / tick_std.replace(0.0, pd.NA)
        h1["wf_tick_count_z"] = tick_count_z.replace([np.inf, -np.inf], pd.NA).fillna(0.0)
        h1["wf_forward_return_12h_atr"] = (close.shift(-self.horizon_bars) - close) / atr14.replace(
            0.0,
            pd.NA,
        )
        h1["wf_model_score"] = _walk_forward_scores(
            h1,
            feature_columns=_feature_columns(),
            label_column="wf_forward_return_12h_atr",
            horizon_bars=self.horizon_bars,
            training_window=self.training_window,
            min_training_rows=self.min_training_rows,
            update_every_bars=self.update_every_bars,
            ridge_lambda=self.ridge_lambda,
        )

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

        for position in range(self.training_window + self.horizon_bars, len(h1)):
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
                    reason_code=f"H1_WALK_FORWARD_LINEAR_STATE_V0_{direction}",
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
            stop_loss = estimated_entry - 1.15 * h1_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + 1.55 * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.15 * h1_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - 1.55 * risk_price
        else:
            raise ConfigError(f"Unsupported H1 walk-forward state direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid H1 walk-forward state trade plan risk.")

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
            risk_reward=1.55,
            reason_code=signal.reason_code,
            metadata={
                **signal.metadata,
                "estimated_entry_price": estimated_entry,
                "max_holding_bars": 288,
                "planned_time_stop_h1_bars": 24,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["close"],
            row["atr14"],
            row["wf_model_score"],
            row["wf_realized_vol_ratio"],
            row["wf_range_atr"],
        )
        if not value_available(*required):
            return None

        close = float(row["close"])
        atr14 = float(row["atr14"])
        score = float(row["wf_model_score"])
        realized_vol_ratio = float(row["wf_realized_vol_ratio"])
        range_atr = float(row["wf_range_atr"])
        if atr14 <= 0:
            return None
        if not (0.35 <= realized_vol_ratio <= 2.75):
            return None
        if range_atr > 4.50:
            return None

        if score >= self.score_threshold:
            return _setup_metadata(row, "LONG", close)
        if score <= -self.score_threshold:
            return _setup_metadata(row, "SHORT", close)
        return None


def _feature_columns() -> list[str]:
    return [
        "wf_momentum_6h_atr",
        "wf_momentum_24h_atr",
        "wf_close_ema24_atr",
        "wf_range_atr",
        "wf_body_ratio",
        "wf_directional_efficiency_24h",
        "wf_realized_vol_ratio",
        "wf_tick_count_z",
    ]


def _walk_forward_scores(
    frame: pd.DataFrame,
    feature_columns: list[str],
    label_column: str,
    horizon_bars: int,
    training_window: int,
    min_training_rows: int,
    update_every_bars: int,
    ridge_lambda: float,
) -> pd.Series:
    features = frame[feature_columns].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    labels = pd.to_numeric(frame[label_column], errors="coerce").clip(-2.5, 2.5).to_numpy(dtype=float)
    scores = np.full(len(frame), np.nan, dtype=float)
    identity = np.eye(features.shape[1] + 1)
    identity[0, 0] = 0.0

    start_position = min_training_rows + horizon_bars
    for position in range(start_position, len(frame), update_every_bars):
        train_end = position - horizon_bars
        train_start = max(0, train_end - training_window)
        train_features = features[train_start:train_end]
        train_labels = labels[train_start:train_end]
        valid = np.isfinite(train_labels) & np.isfinite(train_features).all(axis=1)
        if int(valid.sum()) < min_training_rows:
            continue

        x_train = train_features[valid]
        y_train = train_labels[valid]
        mean = x_train.mean(axis=0)
        std = x_train.std(axis=0)
        std[std == 0.0] = 1.0
        x_scaled = (x_train - mean) / std
        x_design = np.column_stack([np.ones(len(x_scaled)), x_scaled])
        try:
            weights = np.linalg.solve(
                x_design.T @ x_design + ridge_lambda * identity,
                x_design.T @ y_train,
            )
        except np.linalg.LinAlgError:
            continue

        score_end = min(len(frame), position + update_every_bars)
        current = features[position:score_end]
        current_valid = np.isfinite(current).all(axis=1)
        if not current_valid.any():
            continue
        current_scaled = (current[current_valid] - mean) / std
        current_design = np.column_stack([np.ones(len(current_scaled)), current_scaled])
        local_scores = np.full(score_end - position, np.nan, dtype=float)
        local_scores[current_valid] = current_design @ weights
        scores[position:score_end] = local_scores
    return pd.Series(scores, index=frame.index)


def _tick_count_series(h1: pd.DataFrame) -> pd.Series:
    if "tick_count" in h1:
        return pd.to_numeric(h1["tick_count"], errors="coerce")
    if "volume_sum" in h1:
        return pd.to_numeric(h1["volume_sum"], errors="coerce")
    return pd.Series(0.0, index=h1.index)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "atr14": float(row["atr14"]),
        "model_score": float(row["wf_model_score"]),
        "momentum_6h_atr": float(row["wf_momentum_6h_atr"]),
        "momentum_24h_atr": float(row["wf_momentum_24h_atr"]),
        "close_ema24_atr": float(row["wf_close_ema24_atr"]),
        "range_atr": float(row["wf_range_atr"]),
        "body_ratio": float(row["wf_body_ratio"]),
        "directional_efficiency_24h": float(row["wf_directional_efficiency_24h"]),
        "realized_vol_ratio": float(row["wf_realized_vol_ratio"]),
        "tick_count_z": float(row["wf_tick_count_z"]),
    }

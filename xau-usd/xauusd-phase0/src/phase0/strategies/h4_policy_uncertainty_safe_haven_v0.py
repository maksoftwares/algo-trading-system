from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan
from phase0.indicators import atr, ema
from phase0.policy_uncertainty_data import POLICY_UNCERTAINTY_FRAME_KEY
from phase0.strategies.base import (
    StrategyBase,
    context_symbol,
    copy_context,
    require_frame,
    value_available,
)


class H4PolicyUncertaintySafeHavenV0Strategy(StrategyBase):
    """Research-only H4 policy uncertainty safe-haven candidate."""

    name = "h4_policy_uncertainty_safe_haven_v0"
    version = "0.1-research-disabled"

    risk_reward = 1.65

    def prepare_features(self, data_context: dict[str, Any]) -> dict[str, Any]:
        context = copy_context(data_context)
        h4 = require_frame(context, "H4")
        policy = data_context.get(POLICY_UNCERTAINTY_FRAME_KEY)
        if not isinstance(policy, pd.DataFrame):
            raise ConfigError(
                "h4_policy_uncertainty_safe_haven_v0 requires "
                "data_context['policy_uncertainty'] with FRED USEPUINDXD observations."
            )

        close = pd.to_numeric(h4["close"], errors="coerce")
        high = pd.to_numeric(h4["high"], errors="coerce")
        low = pd.to_numeric(h4["low"], errors="coerce")
        if "h4_atr14" not in h4:
            h4["h4_atr14"] = atr(high, low, close, 14)
        if "h4_ema40" not in h4:
            h4["h4_ema40"] = ema(close, 40)
        h4["h4_return_6"] = np.log(close / close.shift(6))

        policy_features = _policy_features_for_h4(h4, policy)
        h4 = pd.concat(
            [
                h4.reset_index(drop=True),
                policy_features.drop(columns=["timestamp_utc"]).reset_index(drop=True),
            ],
            axis=1,
        )
        context["H4"] = h4
        return context

    def generate_signals(self, data_context: dict[str, Any]) -> list[Signal]:
        if data_context.get("open_position_exists", False):
            return []

        context = self.prepare_features(data_context)
        h4 = context["H4"]
        symbol = context_symbol(context)
        signals: list[Signal] = []
        used_day_direction: set[tuple[str, str]] = set()

        for position in range(100, len(h4)):
            row = h4.iloc[position]
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
                    reason_code=f"H4_POLICY_UNCERTAINTY_SAFE_HAVEN_V0_{direction}",
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
            stop_loss = estimated_entry - 1.20 * h4_atr
            risk_price = estimated_entry - stop_loss
            take_profit = estimated_entry + self.risk_reward * risk_price
        elif direction == "SHORT":
            stop_loss = estimated_entry + 1.20 * h4_atr
            risk_price = stop_loss - estimated_entry
            take_profit = estimated_entry - self.risk_reward * risk_price
        else:
            raise ConfigError(f"Unsupported policy uncertainty direction {signal.direction!r}.")

        if risk_price <= 0:
            raise ConfigError("Invalid policy uncertainty trade plan risk.")

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
                "max_holding_bars": 432,
                "planned_time_stop_h4_bars": 9,
            },
        )

    def _setup_at_row(self, row: pd.Series) -> dict[str, Any] | None:
        required = (
            row["open"],
            row["close"],
            row["h4_atr14"],
            row["h4_ema40"],
            row["h4_return_6"],
            row["policy_uncertainty"],
            row["policy_uncertainty_5d_mean"],
            row["policy_uncertainty_ratio_5d_120d"],
            row["policy_uncertainty_change_z252"],
        )
        if not value_available(*required):
            return None

        open_price = float(row["open"])
        close = float(row["close"])
        h4_atr = float(row["h4_atr14"])
        h4_ema40 = float(row["h4_ema40"])
        h4_return_6 = float(row["h4_return_6"])
        policy_ratio = float(row["policy_uncertainty_ratio_5d_120d"])
        policy_change_z = float(row["policy_uncertainty_change_z252"])
        if h4_atr <= 0:
            return None

        safe_haven_state = policy_ratio >= 1.35 or policy_change_z >= 0.75
        calm_unwind_state = policy_ratio <= 0.75 and policy_change_z <= -0.50

        if safe_haven_state and close > h4_ema40 and close > open_price and h4_return_6 > 0.0:
            return _setup_metadata(row, "LONG", close)

        if calm_unwind_state and close < h4_ema40 and close < open_price and h4_return_6 < 0.0:
            return _setup_metadata(row, "SHORT", close)

        return None


def _policy_features_for_h4(h4: pd.DataFrame, policy: pd.DataFrame) -> pd.DataFrame:
    policy_frame = policy[["timestamp_utc", "policy_uncertainty"]].copy()
    policy_frame["timestamp_utc"] = pd.to_datetime(
        policy_frame["timestamp_utc"],
        utc=True,
        errors="coerce",
    )
    policy_frame["policy_uncertainty"] = pd.to_numeric(
        policy_frame["policy_uncertainty"],
        errors="coerce",
    )
    policy_frame = policy_frame.dropna().sort_values("timestamp_utc").reset_index(drop=True)
    policy_frame["policy_uncertainty_5d_mean"] = (
        policy_frame["policy_uncertainty"].rolling(5, min_periods=3).mean()
    )
    policy_frame["policy_uncertainty_120d_median"] = (
        policy_frame["policy_uncertainty"].rolling(120, min_periods=60).median()
    )
    policy_frame["policy_uncertainty_ratio_5d_120d"] = (
        policy_frame["policy_uncertainty_5d_mean"]
        / policy_frame["policy_uncertainty_120d_median"].replace(0.0, np.nan)
    )
    policy_frame["policy_uncertainty_change_20d"] = (
        policy_frame["policy_uncertainty"] - policy_frame["policy_uncertainty"].shift(20)
    )
    policy_frame["policy_uncertainty_change_z252"] = _rolling_zscore(
        policy_frame["policy_uncertainty_change_20d"],
        252,
    )

    feature_columns = [
        "policy_uncertainty",
        "policy_uncertainty_5d_mean",
        "policy_uncertainty_120d_median",
        "policy_uncertainty_ratio_5d_120d",
        "policy_uncertainty_change_20d",
        "policy_uncertainty_change_z252",
    ]
    policy_frame[feature_columns] = policy_frame[feature_columns].shift(1)

    h4_times = pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(h4["timestamp_utc"], utc=True, errors="coerce"),
            "_row_order": range(len(h4)),
        }
    )
    merged = pd.merge_asof(
        h4_times.sort_values("timestamp_utc"),
        policy_frame[["timestamp_utc", *feature_columns]].sort_values("timestamp_utc"),
        on="timestamp_utc",
        direction="backward",
    )
    return merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)


def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
    minimum = max(40, window // 2)
    mean = series.rolling(window, min_periods=minimum).mean()
    std = series.rolling(window, min_periods=minimum).std()
    return (series - mean) / std.replace(0.0, np.nan)


def _setup_metadata(row: pd.Series, direction: str, estimated_entry: float) -> dict[str, Any]:
    return {
        "direction": direction,
        "estimated_entry_price": estimated_entry,
        "h4_atr14": float(row["h4_atr14"]),
        "h4_ema40": float(row["h4_ema40"]),
        "h4_return_6": float(row["h4_return_6"]),
        "policy_uncertainty": float(row["policy_uncertainty"]),
        "policy_uncertainty_5d_mean": float(row["policy_uncertainty_5d_mean"]),
        "policy_uncertainty_120d_median": float(row["policy_uncertainty_120d_median"]),
        "policy_uncertainty_ratio_5d_120d": float(
            row["policy_uncertainty_ratio_5d_120d"]
        ),
        "policy_uncertainty_change_20d": float(row["policy_uncertainty_change_20d"]),
        "policy_uncertainty_change_z252": float(row["policy_uncertainty_change_z252"]),
    }

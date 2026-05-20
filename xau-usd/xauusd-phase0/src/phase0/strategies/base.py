from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from phase0.config import ConfigError
from phase0.data_contracts import Signal, TradePlan


class StrategyBase(ABC):
    """Base interface for mechanical Phase 0 research strategies."""

    name: str
    version: str

    @abstractmethod
    def prepare_features(self, data_context: Any) -> Any:
        """Return data_context with required indicators/features."""

    @abstractmethod
    def generate_signals(self, data_context: Any) -> list[Signal]:
        """Return signals without executing trades or looking ahead."""

    @abstractmethod
    def build_trade_plan(self, signal: Signal, data_context: Any) -> TradePlan:
        """Return a trade plan for the supplied signal."""


def copy_context(data_context: dict[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, value in data_context.items():
        copied[key] = value.copy() if isinstance(value, pd.DataFrame) else value
    return copied


def require_frame(data_context: dict[str, Any], timeframe: str) -> pd.DataFrame:
    if timeframe not in data_context:
        raise ConfigError(f"Strategy context is missing required timeframe {timeframe}.")
    frame = data_context[timeframe]
    if not isinstance(frame, pd.DataFrame):
        raise ConfigError(f"Strategy context {timeframe} must be a pandas DataFrame.")
    if "timestamp_utc" not in frame.columns:
        raise ConfigError(f"Strategy context {timeframe} is missing timestamp_utc.")
    return ensure_utc_sorted(frame)


def ensure_utc_sorted(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    prepared["timestamp_utc"] = pd.to_datetime(prepared["timestamp_utc"], utc=True, errors="coerce")
    if prepared["timestamp_utc"].isna().any():
        raise ConfigError("Strategy input contains invalid timestamp_utc values.")
    return prepared.sort_values("timestamp_utc").reset_index(drop=True)


def latest_completed_row(frame: pd.DataFrame, timestamp_utc: pd.Timestamp) -> pd.Series | None:
    prepared = ensure_utc_sorted(frame)
    timestamp = pd.Timestamp(timestamp_utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    eligible = prepared[prepared["timestamp_utc"] <= timestamp]
    if eligible.empty:
        return None
    return eligible.iloc[-1]


def latest_completed_position(frame: pd.DataFrame, timestamp_utc: pd.Timestamp) -> int | None:
    prepared = ensure_utc_sorted(frame)
    timestamp = pd.Timestamp(timestamp_utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    eligible = prepared.index[prepared["timestamp_utc"] <= timestamp]
    if len(eligible) == 0:
        return None
    return int(eligible[-1])


def context_symbol(data_context: dict[str, Any]) -> str:
    return str(data_context.get("symbol", "XAUUSD"))


def context_point_size(data_context: dict[str, Any]) -> float:
    return float(data_context.get("point_size", 0.01))


def value_available(*values: Any) -> bool:
    return all(pd.notna(value) for value in values)

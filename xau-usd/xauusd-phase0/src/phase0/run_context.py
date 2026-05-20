from __future__ import annotations

from datetime import timedelta
from typing import Any

import pandas as pd

from phase0.config import (
    ConfigError,
    ProjectConfig,
    get_symbol_details,
    parse_utc_datetime,
    resolve_symbol,
    validate_true_holdout_access,
)


def context_with_symbol_metadata(config: ProjectConfig, context: dict[str, Any], symbol: str) -> dict[str, Any]:
    canonical = resolve_symbol(config, symbol)
    details = get_symbol_details(config, canonical)
    result = dict(context)
    result["symbol"] = canonical
    result["point_size"] = float(details["point_size"])
    return result


def filter_context_by_time(
    context: dict[str, Any],
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in context.items():
        if isinstance(value, pd.DataFrame) and "timestamp_utc" in value.columns:
            timestamps = pd.to_datetime(value["timestamp_utc"], utc=True)
            mask = (timestamps >= start) & (timestamps <= end)
            result[key] = value.loc[mask].reset_index(drop=True).copy()
        else:
            result[key] = value
    return result


def guarded_config_period(
    config: ProjectConfig,
    start_key: str,
    end_key: str,
    unlock_true_holdout: bool = False,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    periods = config.phase0["periods"]
    start = parse_utc_datetime(periods[start_key], f"phase0.yaml periods.{start_key}")
    end = parse_utc_datetime(periods[end_key], f"phase0.yaml periods.{end_key}")
    validate_true_holdout_access(config, start, end, unlock_true_holdout)
    return pd.Timestamp(start), pd.Timestamp(end)


def guarded_or_trimmed_period(
    config: ProjectConfig,
    start_key: str,
    end_key: str,
    unlock_true_holdout: bool = False,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    try:
        return guarded_config_period(config, start_key, end_key, unlock_true_holdout)
    except ConfigError:
        if unlock_true_holdout:
            raise

    periods = config.phase0["periods"]
    start = parse_utc_datetime(periods[start_key], f"phase0.yaml periods.{start_key}")
    end = parse_utc_datetime(periods[end_key], f"phase0.yaml periods.{end_key}")
    holdout = config.true_holdout["true_holdout"]
    holdout_start = parse_utc_datetime(holdout["start"], "true_holdout_period.yaml true_holdout.start")
    trimmed_end = min(end, holdout_start - timedelta(seconds=1))
    if trimmed_end < start:
        raise ConfigError(
            f"Configured period {start_key}/{end_key} is fully inside the true holdout window."
        )
    return pd.Timestamp(start), pd.Timestamp(trimmed_end)


def split_period(
    start: pd.Timestamp,
    end: pd.Timestamp,
    parts: int,
) -> list[tuple[int, pd.Timestamp, pd.Timestamp]]:
    if parts <= 0:
        raise ConfigError("parts must be positive.")
    if end <= start:
        raise ConfigError(f"Period end {end} must be after start {start}.")
    duration = end - start
    segments: list[tuple[int, pd.Timestamp, pd.Timestamp]] = []
    for index in range(parts):
        segment_start = start + duration * index / parts
        segment_end = start + duration * (index + 1) / parts
        if index == parts - 1:
            segment_end = end
        segments.append((index + 1, segment_start, segment_end))
    return segments

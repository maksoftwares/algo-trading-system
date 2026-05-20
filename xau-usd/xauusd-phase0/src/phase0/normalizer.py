from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from phase0.bar_builder import TIMEFRAME_FREQ, bars_output_path
from phase0.config import ConfigError, ProjectConfig, get_symbol_details, resolve_symbol
from phase0.data_loader import (
    find_raw_bar_files,
    find_raw_tick_files,
    processed_ticks_dir,
    read_csv,
    write_csv,
)
from phase0.data_validator import (
    BAR_REQUIRED_COLUMNS,
    ValidationReport,
    validate_bars,
    validate_ticks,
    write_validation_artifacts,
)

NORMALIZED_TICK_COLUMNS = (
    "timestamp_utc",
    "broker",
    "symbol",
    "bid",
    "ask",
    "mid",
    "spread_price",
    "spread_points",
    "volume",
    "source_file",
    "row_number",
)

TIMESTAMP_ALIASES = ("timestamp_utc", "timestamp", "time", "ticktime", "datetime", "date_time")
BID_ALIASES = ("bid",)
ASK_ALIASES = ("ask",)
VOLUME_ALIASES = ("volume", "tick_volume", "tickvol", "vol")
ASK_VOLUME_ALIASES = ("askvolume", "ask_volume")
BID_VOLUME_ALIASES = ("bidvolume", "bid_volume")
DATE_ALIASES = ("date", "day")
TIME_ALIASES = ("time", "bar_time")
BAR_TIMESTAMP_ALIASES = ("timestamp_utc", "timestamp", "ticktime", "datetime", "date_time")
BAR_START_ALIASES = ("bar_start_utc", "bar_start", "open_time", "opentime")
BAR_END_ALIASES = ("bar_end_utc", "bar_end", "close_time", "closetime")
OPEN_ALIASES = ("open", "o")
HIGH_ALIASES = ("high", "h")
LOW_ALIASES = ("low", "l")
CLOSE_ALIASES = ("close", "c")
SPREAD_POINTS_ALIASES = ("spread_points", "spread", "spreadpoints")
SPREAD_PRICE_ALIASES = ("spread_price", "spreadprice")


class NormalizationError(ConfigError):
    """Raised when a broker source file cannot be normalized."""


def normalize_tick_dataframe(
    raw: pd.DataFrame,
    broker: str,
    symbol: str,
    point_size: float,
    source_file: str,
) -> pd.DataFrame:
    if raw.empty:
        raise NormalizationError(f"{source_file} contains no rows.")

    lookup = {_canonical_column(column): column for column in raw.columns}
    timestamp_column = _find_column(lookup, TIMESTAMP_ALIASES, source_file)
    bid_column = _find_column(lookup, BID_ALIASES, source_file)
    ask_column = _find_column(lookup, ASK_ALIASES, source_file)

    bid = pd.to_numeric(raw[bid_column], errors="coerce")
    ask = pd.to_numeric(raw[ask_column], errors="coerce")
    timestamp = pd.to_datetime(raw[timestamp_column], utc=True, errors="coerce")
    volume = _extract_volume(raw, lookup)
    spread_price = ask - bid
    normalized = pd.DataFrame(
        {
            "timestamp_utc": timestamp.dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "broker": broker,
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "mid": (bid + ask) / 2.0,
            "spread_price": spread_price,
            "spread_points": spread_price / point_size,
            "volume": volume,
            "source_file": source_file,
            "row_number": raw.index.astype(int) + 2,
        }
    )
    return normalized.loc[:, NORMALIZED_TICK_COLUMNS]


def normalize_raw_tick_file(config: ProjectConfig, broker: str, symbol: str, path: Path) -> pd.DataFrame:
    canonical_symbol = resolve_symbol(config, symbol)
    details = get_symbol_details(config, canonical_symbol)
    raw = read_csv(path)
    return normalize_tick_dataframe(
        raw=raw,
        broker=broker,
        symbol=canonical_symbol,
        point_size=float(details["point_size"]),
        source_file=str(path),
    )


def normalize_bar_dataframe(
    raw: pd.DataFrame,
    broker: str,
    symbol: str,
    timeframe: str,
    point_size: float,
    source_file: str,
    timestamp_is: str = "bar_start",
) -> pd.DataFrame:
    if raw.empty:
        raise NormalizationError(f"{source_file} contains no rows.")
    if timeframe not in TIMEFRAME_FREQ:
        raise NormalizationError(f"Unsupported timeframe {timeframe!r}.")
    if timestamp_is not in {"bar_start", "bar_end"}:
        raise NormalizationError("timestamp_is must be 'bar_start' or 'bar_end'.")

    lookup = {_canonical_column(column): column for column in raw.columns}
    timestamp, inferred_timestamp_is = _extract_bar_timestamp(raw, lookup, source_file)
    source_timestamp_is = timestamp_is if inferred_timestamp_is == "generic" else inferred_timestamp_is
    offset = pd.tseries.frequencies.to_offset(TIMEFRAME_FREQ[timeframe])
    if source_timestamp_is == "bar_start":
        bar_start = timestamp
        bar_end = timestamp + offset
    else:
        bar_end = timestamp
        bar_start = timestamp - offset

    open_ = _numeric_required(raw, lookup, OPEN_ALIASES, source_file)
    high = _numeric_required(raw, lookup, HIGH_ALIASES, source_file)
    low = _numeric_required(raw, lookup, LOW_ALIASES, source_file)
    close = _numeric_required(raw, lookup, CLOSE_ALIASES, source_file)
    spread_points = _extract_spread_points(raw, lookup, point_size)
    spread_price = spread_points * point_size
    has_spread = spread_points.notna()
    half_spread = spread_price / 2.0
    volume = _extract_volume(raw, lookup)
    tick_count = volume.where(volume > 0, 1).fillna(1)

    normalized = pd.DataFrame(
        {
            "timestamp_utc": bar_end,
            "bar_start_utc": bar_start,
            "bar_end_utc": bar_end,
            "broker": broker,
            "symbol": symbol,
            "timeframe": timeframe,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "mid_open": open_,
            "mid_high": high,
            "mid_low": low,
            "mid_close": close,
            "bid_open": (open_ - half_spread).where(has_spread, pd.NA),
            "bid_high": (high - half_spread).where(has_spread, pd.NA),
            "bid_low": (low - half_spread).where(has_spread, pd.NA),
            "bid_close": (close - half_spread).where(has_spread, pd.NA),
            "ask_open": (open_ + half_spread).where(has_spread, pd.NA),
            "ask_high": (high + half_spread).where(has_spread, pd.NA),
            "ask_low": (low + half_spread).where(has_spread, pd.NA),
            "ask_close": (close + half_spread).where(has_spread, pd.NA),
            "spread_open_points": spread_points,
            "spread_close_points": spread_points,
            "spread_median_points": spread_points,
            "spread_p95_points": spread_points,
            "tick_count": tick_count,
            "volume_sum": volume.fillna(0.0),
        }
    )
    normalized = normalized.sort_values("timestamp_utc").reset_index(drop=True)
    return _format_bar_datetime_columns(normalized.loc[:, BAR_REQUIRED_COLUMNS])


def normalize_raw_bar_file(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    timeframe: str,
    path: Path,
    timestamp_is: str = "bar_start",
) -> pd.DataFrame:
    canonical_symbol = resolve_symbol(config, symbol)
    details = get_symbol_details(config, canonical_symbol)
    raw = read_csv(path)
    return normalize_bar_dataframe(
        raw=raw,
        broker=broker,
        symbol=canonical_symbol,
        timeframe=timeframe,
        point_size=float(details["point_size"]),
        source_file=str(path),
        timestamp_is=timestamp_is,
    )


def normalize_broker_bars(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    timeframe: str,
    timestamp_is: str = "bar_start",
    require_timeframe_token: bool = False,
) -> list[Path]:
    canonical_symbol = resolve_symbol(config, symbol)
    raw_files = find_raw_bar_files(
        config,
        broker,
        canonical_symbol,
        timeframe,
        require_timeframe_token=require_timeframe_token,
    )
    return normalize_broker_bar_files(
        config,
        broker,
        canonical_symbol,
        timeframe,
        raw_files,
        timestamp_is=timestamp_is,
    )


def normalize_broker_bar_files(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    timeframe: str,
    raw_files: Iterable[Path],
    timestamp_is: str = "bar_start",
) -> list[Path]:
    canonical_symbol = resolve_symbol(config, symbol)
    written: list[Path] = []
    reports: list[ValidationReport] = []
    for raw_file in raw_files:
        normalized = normalize_raw_bar_file(
            config,
            broker,
            canonical_symbol,
            timeframe,
            raw_file,
            timestamp_is=timestamp_is,
        )
        reports.append(validate_bars(normalized, name=str(raw_file)))
        output_path = bars_output_path(config, broker, canonical_symbol, timeframe, normalized)
        written.append(write_csv(normalized, output_path))

    write_validation_artifacts(config, reports, broker, canonical_symbol)
    return written


def normalize_broker_ticks(config: ProjectConfig, broker: str, symbol: str) -> list[Path]:
    canonical_symbol = resolve_symbol(config, symbol)
    written: list[Path] = []
    reports: list[ValidationReport] = []
    for raw_file in find_raw_tick_files(config, broker, canonical_symbol):
        normalized = normalize_raw_tick_file(config, broker, canonical_symbol, raw_file)
        reports.append(validate_ticks(normalized, name=str(raw_file)))
        output_path = normalized_tick_output_path(config, broker, canonical_symbol, normalized)
        written.append(write_csv(normalized, output_path))

    write_validation_artifacts(config, reports, broker, canonical_symbol)
    return written


def normalized_tick_output_path(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    normalized: pd.DataFrame,
) -> Path:
    timestamps = pd.to_datetime(normalized["timestamp_utc"], utc=True, errors="coerce")
    if timestamps.isna().any():
        raise NormalizationError("Cannot build output path because one or more timestamps are invalid.")
    start = timestamps.min().strftime("%Y%m%d")
    end = timestamps.max().strftime("%Y%m%d")
    return processed_ticks_dir(config, broker, symbol) / f"{symbol}_{broker}_ticks_{start}_{end}.csv"


def validate_raw_files_without_writing(
    config: ProjectConfig,
    broker: str,
    symbol: str,
) -> list[ValidationReport]:
    canonical_symbol = resolve_symbol(config, symbol)
    reports: list[ValidationReport] = []
    for raw_file in find_raw_tick_files(config, broker, canonical_symbol):
        normalized = normalize_raw_tick_file(config, broker, canonical_symbol, raw_file)
        reports.append(validate_ticks(normalized, name=str(raw_file), fail_on_error=False))
    write_validation_artifacts(config, reports, broker, canonical_symbol)
    if any(report.error_count for report in reports):
        first_report = next(report for report in reports if report.error_count)
        first_issue = next(issue for issue in first_report.issues if issue.severity == "ERROR")
        raise NormalizationError(
            f"{first_report.name} failed validation at row {first_issue.row_number or 'n/a'}, "
            f"column {first_issue.column}: {first_issue.message}"
        )
    return reports


def _extract_bar_timestamp(
    raw: pd.DataFrame,
    lookup: dict[str, str],
    source_file: str,
) -> tuple[pd.Series, str]:
    start_column = _find_optional_column(lookup, BAR_START_ALIASES)
    if start_column is not None:
        return pd.to_datetime(raw[start_column], utc=True, errors="coerce"), "bar_start"

    end_column = _find_optional_column(lookup, BAR_END_ALIASES)
    if end_column is not None:
        return pd.to_datetime(raw[end_column], utc=True, errors="coerce"), "bar_end"

    generic_column = _find_optional_column(lookup, BAR_TIMESTAMP_ALIASES)
    if generic_column is not None:
        return pd.to_datetime(raw[generic_column], utc=True, errors="coerce"), "generic"

    date_column = _find_optional_column(lookup, DATE_ALIASES)
    time_column = _find_optional_column(lookup, TIME_ALIASES)
    if date_column is not None and time_column is not None:
        combined = raw[date_column].astype(str).str.strip() + " " + raw[time_column].astype(str).str.strip()
        return pd.to_datetime(combined, utc=True, errors="coerce"), "generic"
    if date_column is not None:
        return pd.to_datetime(raw[date_column], utc=True, errors="coerce"), "generic"

    raise NormalizationError(
        f"{source_file} is missing a timestamp column. Tried timestamp/bar_start/bar_end, "
        "or date + time columns."
    )


def _numeric_required(
    raw: pd.DataFrame,
    lookup: dict[str, str],
    aliases: tuple[str, ...],
    source_file: str,
) -> pd.Series:
    column = _find_column(lookup, aliases, source_file)
    return pd.to_numeric(raw[column], errors="coerce")


def _extract_spread_points(raw: pd.DataFrame, lookup: dict[str, str], point_size: float) -> pd.Series:
    spread_points_column = _find_optional_column(lookup, SPREAD_POINTS_ALIASES)
    if spread_points_column is not None:
        return pd.to_numeric(raw[spread_points_column], errors="coerce")

    spread_price_column = _find_optional_column(lookup, SPREAD_PRICE_ALIASES)
    if spread_price_column is not None:
        return pd.to_numeric(raw[spread_price_column], errors="coerce") / point_size
    return pd.Series(pd.NA, index=raw.index, dtype="Float64")


def _format_bar_datetime_columns(bars: pd.DataFrame) -> pd.DataFrame:
    formatted = bars.copy()
    for column in ("timestamp_utc", "bar_start_utc", "bar_end_utc"):
        formatted[column] = pd.to_datetime(
            formatted[column],
            utc=True,
            errors="coerce",
        ).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return formatted


def _find_column(lookup: dict[str, str], aliases: tuple[str, ...], source_file: str) -> str:
    for alias in aliases:
        canonical = _canonical_column(alias)
        if canonical in lookup:
            return lookup[canonical]
    raise NormalizationError(
        f"{source_file} is missing required column. Tried aliases: {', '.join(aliases)}."
    )


def _find_optional_column(lookup: dict[str, str], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        column = lookup.get(_canonical_column(alias))
        if column is not None:
            return column
    return None


def _extract_volume(raw: pd.DataFrame, lookup: dict[str, str]) -> pd.Series:
    for alias in VOLUME_ALIASES:
        column = lookup.get(_canonical_column(alias))
        if column is not None:
            return pd.to_numeric(raw[column], errors="coerce").fillna(0.0)

    ask_volume = lookup.get(_canonical_column("askvolume")) or lookup.get(_canonical_column("ask_volume"))
    bid_volume = lookup.get(_canonical_column("bidvolume")) or lookup.get(_canonical_column("bid_volume"))
    if ask_volume is not None and bid_volume is not None:
        return (
            pd.to_numeric(raw[ask_volume], errors="coerce").fillna(0.0)
            + pd.to_numeric(raw[bid_volume], errors="coerce").fillna(0.0)
        )
    return pd.Series(0.0, index=raw.index)


def _canonical_column(column: str) -> str:
    cleaned = str(column).strip().strip("<>")
    return re.sub(r"[^a-z0-9]+", "", cleaned.lower())

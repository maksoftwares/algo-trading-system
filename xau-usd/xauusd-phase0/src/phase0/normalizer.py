from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, get_symbol_details, resolve_symbol
from phase0.data_loader import find_raw_tick_files, processed_ticks_dir, read_csv, write_csv
from phase0.data_validator import ValidationReport, validate_ticks, write_validation_artifacts

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
VOLUME_ALIASES = ("volume", "tick_volume", "vol")
ASK_VOLUME_ALIASES = ("askvolume", "ask_volume")
BID_VOLUME_ALIASES = ("bidvolume", "bid_volume")


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


def _find_column(lookup: dict[str, str], aliases: tuple[str, ...], source_file: str) -> str:
    for alias in aliases:
        canonical = _canonical_column(alias)
        if canonical in lookup:
            return lookup[canonical]
    raise NormalizationError(
        f"{source_file} is missing required column. Tried aliases: {', '.join(aliases)}."
    )


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

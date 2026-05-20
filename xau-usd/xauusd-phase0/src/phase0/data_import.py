from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from phase0.config import ConfigError, ProjectConfig
from phase0.data_availability import REQUIRED_BACKTEST_TIMEFRAMES, required_broker_symbols
from phase0.normalizer import normalize_broker_bars


@dataclass(frozen=True)
class RequiredBarImportResult:
    broker: str
    symbol: str
    timeframe: str
    status: str
    files_written: tuple[Path, ...]
    message: str


@dataclass(frozen=True)
class RequiredBarImportOutput:
    results: tuple[RequiredBarImportResult, ...]
    report_path: Path


BAR_IMPORT_REPORT_COLUMNS = (
    "broker",
    "symbol",
    "timeframe",
    "status",
    "files_written",
    "message",
)


def import_required_bar_exports(
    config: ProjectConfig,
    include_multisymbol: bool = True,
    timestamp_is: str = "bar_start",
) -> RequiredBarImportOutput:
    results: list[RequiredBarImportResult] = []
    for broker, symbol in required_broker_symbols(config, include_multisymbol):
        for timeframe in REQUIRED_BACKTEST_TIMEFRAMES:
            results.append(
                _import_one_required_set(
                    config,
                    broker,
                    symbol,
                    timeframe,
                    timestamp_is,
                )
            )
    report_path = write_bar_import_report(config, results)
    return RequiredBarImportOutput(tuple(results), report_path)


def write_bar_import_report(
    config: ProjectConfig,
    results: list[RequiredBarImportResult] | tuple[RequiredBarImportResult, ...],
) -> Path:
    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "PHASE0_BAR_IMPORT_REPORT.csv"
    with report_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BAR_IMPORT_REPORT_COLUMNS)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "broker": result.broker,
                    "symbol": result.symbol,
                    "timeframe": result.timeframe,
                    "status": result.status,
                    "files_written": ";".join(path.as_posix() for path in result.files_written),
                    "message": result.message,
                }
            )
    return report_path


def _import_one_required_set(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    timeframe: str,
    timestamp_is: str,
) -> RequiredBarImportResult:
    try:
        written = normalize_broker_bars(
            config,
            broker,
            symbol,
            timeframe,
            timestamp_is=timestamp_is,
            require_timeframe_token=True,
        )
    except ConfigError as exc:
        status = "MISSING" if _is_missing_raw_data_error(exc) else "FAILED"
        return RequiredBarImportResult(
            broker=broker,
            symbol=symbol,
            timeframe=timeframe,
            status=status,
            files_written=(),
            message=str(exc),
        )

    return RequiredBarImportResult(
        broker=broker,
        symbol=symbol,
        timeframe=timeframe,
        status="IMPORTED",
        files_written=tuple(written),
        message=f"Imported {len(written)} file(s).",
    )


def _is_missing_raw_data_error(exc: ConfigError) -> bool:
    message = str(exc)
    return "No raw bar CSV files found" in message or "Raw data directory does not exist" in message

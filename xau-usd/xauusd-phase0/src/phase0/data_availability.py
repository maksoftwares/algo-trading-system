from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, build_cell_configs, resolve_symbol
from phase0.constants import COMPARISON_SYMBOLS
from phase0.data_loader import processed_bars_dir
from phase0.data_validator import BAR_REQUIRED_COLUMNS, validate_bars


REQUIRED_BACKTEST_TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1")


@dataclass(frozen=True)
class DataAvailabilityCheck:
    broker: str
    symbol: str
    timeframe: str
    directory: Path
    file_count: int
    candidate_file_count: int
    issues: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return self.file_count > 0


def check_processed_data_availability(
    config: ProjectConfig,
    include_multisymbol: bool = True,
) -> list[DataAvailabilityCheck]:
    checks: list[DataAvailabilityCheck] = []
    for broker, symbol in _required_broker_symbols(config, include_multisymbol):
        for timeframe in REQUIRED_BACKTEST_TIMEFRAMES:
            directory = processed_bars_dir(config, broker, symbol, timeframe)
            files = sorted(directory.glob("*.csv")) if directory.exists() else []
            valid_files, issues = _valid_bar_files(files)
            checks.append(
                DataAvailabilityCheck(
                    broker=broker,
                    symbol=symbol,
                    timeframe=timeframe,
                    directory=directory,
                    file_count=len(valid_files),
                    candidate_file_count=len(files),
                    issues=tuple(issues),
                )
            )
    return checks


def assert_processed_data_available(
    config: ProjectConfig,
    include_multisymbol: bool = True,
) -> list[DataAvailabilityCheck]:
    checks = check_processed_data_availability(config, include_multisymbol)
    missing = [check for check in checks if not check.available]
    if missing:
        lines = [_availability_error_line(check) for check in missing]
        raise ConfigError(
            "Missing processed bars required for Phase 0 real-data run:\n"
            + "\n".join(lines)
            + "\nRun normalize-data and build-bars for each listed broker/symbol first, "
            "or pass --synthetic-sample for a smoke test."
        )
    return checks


def generate_data_readiness_report(
    config: ProjectConfig,
    include_multisymbol: bool = True,
) -> Path:
    checks = check_processed_data_availability(config, include_multisymbol)
    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "PHASE0_DATA_READINESS.md"
    output_path.write_text(
        _render_data_readiness_report(config, checks, include_multisymbol),
        encoding="utf-8",
    )
    return output_path


def _required_broker_symbols(
    config: ProjectConfig,
    include_multisymbol: bool,
) -> list[tuple[str, str]]:
    required: set[tuple[str, str]] = {
        (cell.broker, resolve_symbol(config, cell.symbol))
        for cell in build_cell_configs(config, symbol="XAUUSD")
    }
    if include_multisymbol:
        for symbol in COMPARISON_SYMBOLS:
            required.add(("capital_com", resolve_symbol(config, symbol)))
    return sorted(required)


def _render_data_readiness_report(
    config: ProjectConfig,
    checks: list[DataAvailabilityCheck],
    include_multisymbol: bool,
) -> str:
    ready = [check for check in checks if check.available]
    missing = [check for check in checks if not check.available]
    broker_symbols = _required_broker_symbols(config, include_multisymbol)
    status = "PASS" if not missing else "BLOCKED"
    lines = [
        "# Phase 0 Data Readiness",
        "",
        f"Status: {status}",
        f"Required timeframe sets: {len(checks)}",
        f"Ready timeframe sets: {len(ready)}",
        f"Blocked timeframe sets: {len(missing)}",
        "",
        "## Required Broker/Symbol Inputs",
        "",
        "| Broker | Symbol | Raw CSV candidates | Required processed timeframes |",
        "| --- | --- | --- | --- |",
    ]
    for broker, symbol in broker_symbols:
        lines.append(
            f"| {broker} | {symbol} | {_raw_csv_candidate_count(config, broker, symbol)} | "
            f"{', '.join(REQUIRED_BACKTEST_TIMEFRAMES)} |"
        )

    lines.extend(["", "## Blocked Processed Bar Sets", ""])
    if not missing:
        lines.append("None.")
    else:
        lines.extend(
            [
                "| Broker | Symbol | Timeframe | Valid CSVs | Candidate CSVs | Directory | First issue |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for check in missing:
            first_issue = check.issues[0] if check.issues else "no candidate CSV files"
            lines.append(
                f"| {check.broker} | {check.symbol} | {check.timeframe} | {check.file_count} | "
                f"{check.candidate_file_count} | {check.directory} | {first_issue} |"
            )
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            "Add raw broker CSVs, run validate-data, normalize-data, build-bars for each broker/symbol, then rerun check-data-availability.",
            "",
        ]
    )
    return "\n".join(lines)


def _raw_csv_candidate_count(config: ProjectConfig, broker: str, symbol: str) -> int:
    raw_dir = config.root / str(config.broker_sources["brokers"][broker]["raw_dir"])
    if not raw_dir.exists():
        return 0
    aliases = {symbol.lower(), *(alias.lower() for alias in config.symbols["symbols"][symbol].get("aliases", []))}
    return sum(1 for path in raw_dir.rglob("*.csv") if any(alias in path.name.lower() for alias in aliases))


def _valid_bar_files(files: list[Path]) -> tuple[list[Path], list[str]]:
    valid: list[Path] = []
    issues: list[str] = []
    for path in files:
        try:
            frame = pd.read_csv(path, nrows=1)
        except Exception as exc:
            issues.append(f"{path.name}: unreadable CSV ({exc})")
            continue
        missing_columns = [column for column in BAR_REQUIRED_COLUMNS if column not in frame.columns]
        if missing_columns:
            issues.append(f"{path.name}: missing columns {', '.join(missing_columns[:5])}")
            continue
        if frame.empty:
            issues.append(f"{path.name}: no rows")
            continue
        report = validate_bars(frame, name=path.name, fail_on_error=False)
        if report.error_count:
            issue = next(issue for issue in report.issues if issue.severity == "ERROR")
            issues.append(f"{path.name}: {issue.column} {issue.message}")
            continue
        valid.append(path)
    return valid, issues


def _availability_error_line(check: DataAvailabilityCheck) -> str:
    base = (
        f"- broker={check.broker}, symbol={check.symbol}, timeframe={check.timeframe}, "
        f"dir={check.directory}, valid_files={check.file_count}, "
        f"candidate_files={check.candidate_file_count}"
    )
    if not check.issues:
        return base
    return base + f", first_issue={check.issues[0]}"

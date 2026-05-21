from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, build_cell_configs, resolve_symbol
from phase0.constants import COMPARISON_SYMBOLS
from phase0.data_loader import processed_bars_dir
from phase0.data_validator import (
    BAR_REQUIRED_COLUMNS,
    MAX_ALLOWED_BAR_GAPS,
    bar_identity_issues,
    largest_bar_gap_issue,
    validate_bars,
)
from phase0.run_context import guarded_or_trimmed_period


REQUIRED_BACKTEST_TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1")
DATA_REQUIREMENT_COLUMNS = (
    "broker",
    "symbol",
    "timeframe",
    "required_start_utc",
    "required_end_utc",
    "raw_dir",
    "suggested_raw_filename",
)


@dataclass(frozen=True)
class RequiredCoverageWindow:
    broker: str
    symbol: str
    label: str
    start_utc: pd.Timestamp
    end_utc: pd.Timestamp


@dataclass(frozen=True)
class DataAvailabilityCheck:
    broker: str
    symbol: str
    timeframe: str
    directory: Path
    file_count: int
    candidate_file_count: int
    required_start_utc: str
    required_end_utc: str
    coverage_start_utc: str = ""
    coverage_end_utc: str = ""
    issues: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return self.file_count > 0 and not self.issues


def check_processed_data_availability(
    config: ProjectConfig,
    include_multisymbol: bool = True,
) -> list[DataAvailabilityCheck]:
    checks: list[DataAvailabilityCheck] = []
    coverage = _required_coverage_by_broker_symbol(config, include_multisymbol)
    for broker, symbol in required_broker_symbols(config, include_multisymbol):
        required_start, required_end = _coverage_bounds(coverage[(broker, symbol)])
        for timeframe in REQUIRED_BACKTEST_TIMEFRAMES:
            directory = processed_bars_dir(config, broker, symbol, timeframe)
            files = sorted(directory.glob("*.csv")) if directory.exists() else []
            valid_files, issues, coverage_start, coverage_end = _valid_bar_files(
                files,
                broker,
                symbol,
                timeframe,
                required_start,
                required_end,
            )
            checks.append(
                DataAvailabilityCheck(
                    broker=broker,
                    symbol=symbol,
                    timeframe=timeframe,
                    directory=directory,
                    file_count=len(valid_files),
                    candidate_file_count=len(files),
                    required_start_utc=_timestamp_text(required_start),
                    required_end_utc=_timestamp_text(required_end),
                    coverage_start_utc=_timestamp_text(coverage_start) if coverage_start is not None else "",
                    coverage_end_utc=_timestamp_text(coverage_end) if coverage_end is not None else "",
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
            + "\nRun import-required-bars for direct OHLC bar exports, or "
            "normalize-data and build-bars for tick exports. Use generate-data-readiness "
            "for a full blocker report, or pass --synthetic-sample for a smoke test."
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


def generate_data_requirements_csv(
    config: ProjectConfig,
    include_multisymbol: bool = True,
) -> Path:
    coverage = _required_coverage_by_broker_symbol(config, include_multisymbol)
    rows: list[dict[str, str]] = []
    for broker, symbol in required_broker_symbols(config, include_multisymbol):
        required_start, required_end = _coverage_bounds(coverage[(broker, symbol)])
        raw_dir = config.root / str(config.broker_sources["brokers"][broker]["raw_dir"])
        for timeframe in REQUIRED_BACKTEST_TIMEFRAMES:
            rows.append(
                {
                    "broker": broker,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "required_start_utc": _timestamp_text(required_start),
                    "required_end_utc": _timestamp_text(required_end),
                    "raw_dir": str(raw_dir),
                    "suggested_raw_filename": _suggested_raw_filename(
                        broker,
                        symbol,
                        timeframe,
                        required_start,
                        required_end,
                    ),
                }
            )

    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "PHASE0_DATA_REQUIREMENTS.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=DATA_REQUIREMENT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def required_broker_symbols(
    config: ProjectConfig,
    include_multisymbol: bool,
) -> list[tuple[str, str]]:
    return sorted(_required_coverage_by_broker_symbol(config, include_multisymbol))


def required_coverage_windows(
    config: ProjectConfig,
    include_multisymbol: bool,
) -> list[RequiredCoverageWindow]:
    windows: list[RequiredCoverageWindow] = []
    for cell in build_cell_configs(config, symbol="XAUUSD"):
        windows.append(
            RequiredCoverageWindow(
                broker=cell.broker,
                symbol=resolve_symbol(config, cell.symbol),
                label=f"matrix_cell_{cell.cell_id}",
                start_utc=pd.Timestamp(cell.start_utc),
                end_utc=pd.Timestamp(cell.end_utc),
            )
        )

    decile_start, decile_end = guarded_or_trimmed_period(config, "decile_start", "decile_end")
    windows.append(
        RequiredCoverageWindow(
            broker="capital_com",
            symbol=resolve_symbol(config, "XAUUSD"),
            label="decile_tests",
            start_utc=decile_start,
            end_utc=decile_end,
        )
    )

    if include_multisymbol:
        multisymbol_start, multisymbol_end = guarded_or_trimmed_period(
            config,
            "multisymbol_start",
            "multisymbol_end",
        )
        for symbol in COMPARISON_SYMBOLS:
            windows.append(
                RequiredCoverageWindow(
                    broker="capital_com",
                    symbol=resolve_symbol(config, symbol),
                    label="multisymbol_check",
                    start_utc=multisymbol_start,
                    end_utc=multisymbol_end,
                )
            )
    return windows


def _render_data_readiness_report(
    config: ProjectConfig,
    checks: list[DataAvailabilityCheck],
    include_multisymbol: bool,
) -> str:
    ready = [check for check in checks if check.available]
    missing = [check for check in checks if not check.available]
    broker_symbols = required_broker_symbols(config, include_multisymbol)
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
                "| Broker | Symbol | Timeframe | Required Start | Required End | Coverage Start | Coverage End | Valid CSVs | Candidate CSVs | Directory | First issue |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for check in missing:
            first_issue = check.issues[0] if check.issues else "no candidate CSV files"
            lines.append(
                f"| {check.broker} | {check.symbol} | {check.timeframe} | "
                f"{check.required_start_utc} | {check.required_end_utc} | "
                f"{check.coverage_start_utc} | {check.coverage_end_utc} | "
                f"{check.file_count} | {check.candidate_file_count} | {check.directory} | {first_issue} |"
            )
        lines.extend(["", "## Suggested Direct Bar Import Commands", "", "```powershell"])
        lines.extend(_normalize_bar_command(check) for check in missing)
        lines.append("```")
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            "Add raw broker CSVs, run import-required-bars for direct bar exports or normalize-data/build-bars for tick exports, then rerun check-data-availability.",
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


def _normalize_bar_command(check: DataAvailabilityCheck) -> str:
    return (
        f"python -m phase0 normalize-bars --broker {check.broker} "
        f"--symbol {check.symbol} --timeframe {check.timeframe}"
    )


def _valid_bar_files(
    files: list[Path],
    broker: str,
    symbol: str,
    timeframe: str,
    required_start: pd.Timestamp,
    required_end: pd.Timestamp,
) -> tuple[list[Path], list[str], pd.Timestamp | None, pd.Timestamp | None]:
    valid: list[Path] = []
    issues: list[str] = []
    coverage_starts: list[pd.Timestamp] = []
    coverage_ends: list[pd.Timestamp] = []
    coverage_points: list[pd.Series] = []
    for path in files:
        try:
            frame = pd.read_csv(path)
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
        identity_issues = bar_identity_issues(frame, broker, symbol, timeframe)
        if identity_issues:
            issues.append(f"{path.name}: {identity_issues[0]}")
            continue
        starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce").dropna()
        ends = pd.to_datetime(frame["bar_end_utc"], utc=True, errors="coerce").dropna()
        if starts.empty or ends.empty:
            issues.append(f"{path.name}: no valid bar_start_utc/bar_end_utc coverage")
            continue
        valid.append(path)
        coverage_starts.append(pd.Timestamp(starts.min()))
        coverage_ends.append(pd.Timestamp(ends.max()))
        coverage_points.append(ends)

    coverage_start = min(coverage_starts) if coverage_starts else None
    coverage_end = max(coverage_ends) if coverage_ends else None
    allowed_boundary_gap = MAX_ALLOWED_BAR_GAPS[timeframe]
    if (
        valid
        and coverage_start is not None
        and coverage_start > required_start
        and coverage_start - required_start > allowed_boundary_gap
    ):
        issues.append(
            f"coverage starts {_timestamp_text(coverage_start)}, required <= {_timestamp_text(required_start)}"
        )
    if (
        valid
        and coverage_end is not None
        and coverage_end < required_end
        and required_end - coverage_end > allowed_boundary_gap
    ):
        issues.append(
            f"coverage ends {_timestamp_text(coverage_end)}, required >= {_timestamp_text(required_end)}"
        )
    if valid:
        combined_points = pd.concat(coverage_points)
        duplicate_issue = _duplicate_coverage_timestamp_issue(combined_points)
        if duplicate_issue:
            issues.append(duplicate_issue)
        gap_issue = largest_bar_gap_issue(combined_points, timeframe)
        if gap_issue:
            issues.append(gap_issue)
    return valid, issues, coverage_start, coverage_end


def _duplicate_coverage_timestamp_issue(timestamps: pd.Series) -> str:
    values = pd.to_datetime(timestamps, utc=True, errors="coerce").dropna()
    duplicates = values[values.duplicated(keep=False)]
    if duplicates.empty:
        return ""
    first_values = [_timestamp_text(value) for value in duplicates.drop_duplicates().sort_values().head(5)]
    return f"duplicate timestamp_utc across processed files: {', '.join(first_values)}"


def _availability_error_line(check: DataAvailabilityCheck) -> str:
    base = (
        f"- broker={check.broker}, symbol={check.symbol}, timeframe={check.timeframe}, "
        f"dir={check.directory}, valid_files={check.file_count}, "
        f"candidate_files={check.candidate_file_count}"
    )
    if not check.issues:
        return base
    return base + f", first_issue={check.issues[0]}"


def _required_coverage_by_broker_symbol(
    config: ProjectConfig,
    include_multisymbol: bool,
) -> dict[tuple[str, str], list[RequiredCoverageWindow]]:
    coverage: dict[tuple[str, str], list[RequiredCoverageWindow]] = {}
    for window in required_coverage_windows(config, include_multisymbol):
        coverage.setdefault((window.broker, window.symbol), []).append(window)
    return coverage


def _coverage_bounds(windows: list[RequiredCoverageWindow]) -> tuple[pd.Timestamp, pd.Timestamp]:
    return (
        min(window.start_utc for window in windows),
        max(window.end_utc for window in windows),
    )


def _timestamp_text(value: pd.Timestamp) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def _suggested_raw_filename(
    broker: str,
    symbol: str,
    timeframe: str,
    required_start: pd.Timestamp,
    required_end: pd.Timestamp,
) -> str:
    start = pd.Timestamp(required_start).strftime("%Y%m%d")
    end = pd.Timestamp(required_end).strftime("%Y%m%d")
    return f"{symbol}_{timeframe}_{start}_{end}_{broker}.csv"

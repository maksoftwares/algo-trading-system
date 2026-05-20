from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig

TICK_REQUIRED_COLUMNS = (
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

BAR_REQUIRED_COLUMNS = (
    "timestamp_utc",
    "bar_start_utc",
    "bar_end_utc",
    "broker",
    "symbol",
    "timeframe",
    "open",
    "high",
    "low",
    "close",
    "mid_open",
    "mid_high",
    "mid_low",
    "mid_close",
    "bid_open",
    "bid_high",
    "bid_low",
    "bid_close",
    "ask_open",
    "ask_high",
    "ask_low",
    "ask_close",
    "spread_open_points",
    "spread_close_points",
    "spread_median_points",
    "spread_p95_points",
    "tick_count",
    "volume_sum",
)


class DataValidationError(ConfigError):
    """Raised when market data violates the Phase 0 data contract."""


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    row_number: int | None
    column: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    name: str
    rows_checked: int
    issues: tuple[ValidationIssue, ...]

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "WARNING")


def validate_ticks(
    df: pd.DataFrame,
    name: str = "ticks",
    max_reasonable_spread_points: float = 1000.0,
    fail_on_error: bool = True,
) -> ValidationReport:
    issues: list[ValidationIssue] = []
    _check_required_columns(df, TICK_REQUIRED_COLUMNS, issues)
    if issues:
        return _finish_report(name, df, issues, fail_on_error)

    timestamps = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    _flag_invalid_mask(timestamps.isna(), "timestamp_utc", "Timestamp is not parseable.", df, issues)
    if not timestamps.isna().any() and not timestamps.is_monotonic_increasing:
        issues.append(ValidationIssue("ERROR", None, "timestamp_utc", "Timestamps are not sorted ascending."))

    duplicate_mask = timestamps.duplicated(keep=False)
    _flag_invalid_mask(duplicate_mask, "timestamp_utc", "Duplicate timestamp.", df, issues, severity="WARNING")

    bid = pd.to_numeric(df["bid"], errors="coerce")
    ask = pd.to_numeric(df["ask"], errors="coerce")
    spread = pd.to_numeric(df["spread_points"], errors="coerce")
    _flag_invalid_mask(bid.isna() | (bid <= 0), "bid", "Bid must be positive numeric.", df, issues)
    _flag_invalid_mask(ask.isna() | (ask <= 0), "ask", "Ask must be positive numeric.", df, issues)
    _flag_invalid_mask(ask < bid, "ask", "Ask must be greater than or equal to bid.", df, issues)
    _flag_invalid_mask(spread < 0, "spread_points", "Spread points must not be negative.", df, issues)
    _flag_invalid_mask(
        spread > max_reasonable_spread_points,
        "spread_points",
        f"Spread exceeds {max_reasonable_spread_points} points.",
        df,
        issues,
        severity="WARNING",
    )
    return _finish_report(name, df, issues, fail_on_error)


def validate_bars(df: pd.DataFrame, name: str = "bars", fail_on_error: bool = True) -> ValidationReport:
    issues: list[ValidationIssue] = []
    _check_required_columns(df, BAR_REQUIRED_COLUMNS, issues)
    if issues:
        return _finish_report(name, df, issues, fail_on_error)

    timestamps = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    starts = pd.to_datetime(df["bar_start_utc"], utc=True, errors="coerce")
    ends = pd.to_datetime(df["bar_end_utc"], utc=True, errors="coerce")
    _flag_invalid_mask(timestamps.isna(), "timestamp_utc", "Timestamp is not parseable.", df, issues)
    _flag_invalid_mask(starts.isna(), "bar_start_utc", "Bar start is not parseable.", df, issues)
    _flag_invalid_mask(ends.isna(), "bar_end_utc", "Bar end is not parseable.", df, issues)
    _flag_invalid_mask(timestamps != ends, "timestamp_utc", "timestamp_utc must equal bar_end_utc.", df, issues)
    _flag_invalid_mask(ends <= starts, "bar_end_utc", "bar_end_utc must be after bar_start_utc.", df, issues)

    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    open_ = pd.to_numeric(df["open"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")
    _flag_invalid_mask(
        high < open_.where(open_ >= close, close),
        "high",
        "Bar high must be >= max(open, close).",
        df,
        issues,
    )
    _flag_invalid_mask(
        low > open_.where(open_ <= close, close),
        "low",
        "Bar low must be <= min(open, close).",
        df,
        issues,
    )
    _flag_invalid_mask(pd.to_numeric(df["tick_count"], errors="coerce") <= 0, "tick_count", "tick_count must be positive.", df, issues)
    return _finish_report(name, df, issues, fail_on_error)


def write_validation_artifacts(
    config: ProjectConfig,
    reports: list[ValidationReport],
    broker: str,
    symbol: str,
) -> tuple[Path, Path]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    details_path = output_dir / f"data_validation_{broker}_{symbol}_{stamp}.csv"
    summary_path = output_dir / "data_validation_summary.md"

    with details_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=("name", "severity", "row_number", "column", "message"),
        )
        writer.writeheader()
        for report in reports:
            if not report.issues:
                writer.writerow(
                    {
                        "name": report.name,
                        "severity": "OK",
                        "row_number": "",
                        "column": "",
                        "message": f"{report.rows_checked} rows checked.",
                    }
                )
            for issue in report.issues:
                writer.writerow(
                    {
                        "name": report.name,
                        "severity": issue.severity,
                        "row_number": "" if issue.row_number is None else issue.row_number,
                        "column": issue.column,
                        "message": issue.message,
                    }
                )

    lines = ["# Data Validation Summary", ""]
    for report in reports:
        lines.append(
            f"- {report.name}: {report.rows_checked} rows, "
            f"{report.error_count} error(s), {report.warning_count} warning(s)"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return details_path, summary_path


def _check_required_columns(
    df: pd.DataFrame,
    required_columns: tuple[str, ...],
    issues: list[ValidationIssue],
) -> None:
    missing = [column for column in required_columns if column not in df.columns]
    for column in missing:
        issues.append(ValidationIssue("ERROR", None, column, f"Missing required column: {column}."))


def _flag_invalid_mask(
    mask: pd.Series,
    column: str,
    message: str,
    df: pd.DataFrame,
    issues: list[ValidationIssue],
    severity: str = "ERROR",
) -> None:
    invalid = mask.fillna(False)
    for index in df.index[invalid]:
        row_number = int(df.loc[index, "row_number"]) if "row_number" in df.columns else int(index) + 2
        issues.append(ValidationIssue(severity, row_number, column, message))


def _finish_report(
    name: str,
    df: pd.DataFrame,
    issues: list[ValidationIssue],
    fail_on_error: bool,
) -> ValidationReport:
    report = ValidationReport(name=name, rows_checked=len(df), issues=tuple(issues))
    if fail_on_error and report.error_count:
        first = next(issue for issue in report.issues if issue.severity == "ERROR")
        raise DataValidationError(
            f"{name} failed validation at row {first.row_number or 'n/a'}, "
            f"column {first.column}: {first.message}"
        )
    return report

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, build_cell_configs
from phase0.data_availability import DataAvailabilityCheck, _valid_bar_files
from phase0.data_loader import processed_bars_dir
from phase0.data_validator import bar_identity_issues, largest_bar_gap_issue, validate_bars


EXPERT_NAME = "xau_xag_relative_value_v0"
RELATIVE_SYMBOL = "XAGUSD"
RELATIVE_TIMEFRAME = "H1"
REQUIREMENT_COLUMNS = (
    "broker",
    "symbol",
    "timeframe",
    "required_start_utc",
    "required_end_utc",
    "raw_dir",
    "suggested_raw_filename",
    "required_for",
    "strict_authoritative_use",
)


@dataclass(frozen=True)
class XauXagRelativeDataReadiness:
    status: str
    checks: tuple[DataAvailabilityCheck, ...]
    report_path: Path
    requirements_path: Path

    @property
    def ready_count(self) -> int:
        return sum(1 for check in self.checks if check.available)


def check_xau_xag_relative_data(config: ProjectConfig) -> list[DataAvailabilityCheck]:
    checks: list[DataAvailabilityCheck] = []
    for broker, (required_start, required_end) in _matrix_windows_by_broker(config).items():
        directory = processed_bars_dir(config, broker, RELATIVE_SYMBOL, RELATIVE_TIMEFRAME)
        files = sorted(directory.glob("*.csv")) if directory.exists() else []
        valid_files, issues, coverage_start, coverage_end = _valid_bar_files(
            files,
            broker,
            RELATIVE_SYMBOL,
            RELATIVE_TIMEFRAME,
            required_start,
            required_end,
        )
        checks.append(
            DataAvailabilityCheck(
                broker=broker,
                symbol=RELATIVE_SYMBOL,
                timeframe=RELATIVE_TIMEFRAME,
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


def generate_xau_xag_relative_data_readiness(config: ProjectConfig) -> XauXagRelativeDataReadiness:
    checks = check_xau_xag_relative_data(config)
    status = "PASS" if all(check.available for check in checks) else "BLOCKED"
    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "XAU_XAG_RELATIVE_VALUE_V0_DATA_READINESS.md"
    requirements_path = output_dir / "XAU_XAG_RELATIVE_VALUE_V0_DATA_REQUIREMENTS.csv"

    report_path.write_text(_render_report(status, checks), encoding="utf-8")
    _write_requirements_csv(config, checks, requirements_path)
    return XauXagRelativeDataReadiness(
        status=status,
        checks=tuple(checks),
        report_path=report_path,
        requirements_path=requirements_path,
    )


def load_xau_xag_relative_h1_context(
    config: ProjectConfig,
    broker: str,
    required_start: object,
    required_end: object,
) -> dict[str, pd.DataFrame]:
    start = _utc_timestamp(required_start)
    end = _utc_timestamp(required_end)
    directory = processed_bars_dir(config, broker, RELATIVE_SYMBOL, RELATIVE_TIMEFRAME)
    files = sorted(directory.glob("*.csv")) if directory.exists() else []
    if not files:
        raise ConfigError(
            f"{EXPERT_NAME} requires processed {broker} {RELATIVE_SYMBOL} "
            f"{RELATIVE_TIMEFRAME} bars in {directory} before any real research matrix run."
        )
    frame = _load_h1_relative_files(files, broker)
    _assert_h1_relative_coverage(frame, directory, start, end)
    return {RELATIVE_SYMBOL: frame}


def _render_report(status: str, checks: list[DataAvailabilityCheck]) -> str:
    missing = [check for check in checks if not check.available]
    lines = [
        "# xau_xag_relative_value_v0 Data Readiness",
        "",
        f"Status: {status}",
        f"Ready XAGUSD H1 sets: {len(checks) - len(missing)}/{len(checks)}",
        "",
        "## Boundary",
        "",
        (
            "This report is for a research-only candidate. It does not alter active "
            "Phase 1 soak, Phase 2 readiness, or approved expert status."
        ),
        "",
        "## Required XAGUSD H1 Sets",
        "",
        "| Broker | Symbol | Required Start | Required End | Coverage Start | Coverage End | Valid CSVs | Candidate CSVs | Status | First Issue |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for check in checks:
        lines.append(
            f"| {check.broker} | {check.symbol} | {check.required_start_utc} | "
            f"{check.required_end_utc} | {check.coverage_start_utc} | {check.coverage_end_utc} | "
            f"{check.file_count} | {check.candidate_file_count} | "
            f"{'PASS' if check.available else 'BLOCKED'} | "
            f"{check.issues[0] if check.issues else ('none' if check.available else 'no candidate CSV files')} |"
        )

    lines.extend(
        [
            "",
            "## Strict Rule",
            "",
            (
                "Authoritative Phase 0 results must use broker-consistent XAGUSD H1 data. "
                "Do not substitute Dukascopy, Pepperstone, or another vendor for Capital.com cells."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _write_requirements_csv(
    config: ProjectConfig,
    checks: list[DataAvailabilityCheck],
    output_path: Path,
) -> None:
    raw_dirs = config.broker_sources.get("brokers", {})
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIREMENT_COLUMNS)
        writer.writeheader()
        for check in checks:
            writer.writerow(
                {
                    "broker": check.broker,
                    "symbol": check.symbol,
                    "timeframe": check.timeframe,
                    "required_start_utc": check.required_start_utc,
                    "required_end_utc": check.required_end_utc,
                    "raw_dir": str(raw_dirs.get(check.broker, {}).get("raw_dir", "")),
                    "suggested_raw_filename": _suggested_raw_filename(check),
                    "required_for": f"{EXPERT_NAME}_matrix_relative_value",
                    "strict_authoritative_use": "present_locally"
                    if check.available
                    else "missing_required",
                }
            )


def _matrix_windows_by_broker(config: ProjectConfig) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    grouped: dict[str, list[tuple[pd.Timestamp, pd.Timestamp]]] = {}
    for cell in build_cell_configs(config, symbol="XAUUSD"):
        grouped.setdefault(cell.broker, []).append(
            (pd.Timestamp(cell.start_utc), pd.Timestamp(cell.end_utc))
        )
    return {
        broker: (min(start for start, _ in windows), max(end for _, end in windows))
        for broker, windows in grouped.items()
    }


def _suggested_raw_filename(check: DataAvailabilityCheck) -> str:
    start = pd.Timestamp(check.required_start_utc).strftime("%Y%m%d")
    end = pd.Timestamp(check.required_end_utc).strftime("%Y%m%d")
    return f"{check.symbol}_{check.timeframe}_{start}_{end}_{check.broker}.csv"


def _load_h1_relative_files(files: list[Path], broker: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in files:
        try:
            frames.append(pd.read_csv(path))
        except Exception as exc:
            raise ConfigError(f"Failed to read {EXPERT_NAME} relative-value file {path}: {exc}") from exc

    combined = pd.concat(frames, ignore_index=True)
    if "timestamp_utc" in combined.columns:
        timestamps = pd.to_datetime(combined["timestamp_utc"], utc=True, errors="coerce")
        combined = (
            combined.assign(_phase0_sort_timestamp=timestamps)
            .sort_values("_phase0_sort_timestamp", na_position="last")
            .drop(columns="_phase0_sort_timestamp")
            .reset_index(drop=True)
        )

    report = validate_bars(
        combined,
        name=f"{broker} {RELATIVE_SYMBOL} {RELATIVE_TIMEFRAME} relative-value bars",
        fail_on_error=False,
    )
    if report.error_count:
        first_issue = next(issue for issue in report.issues if issue.severity == "ERROR")
        raise ConfigError(
            f"{EXPERT_NAME} relative-value bars failed validation: "
            f"{first_issue.column} {first_issue.message}"
        )

    identity_issues = bar_identity_issues(combined, broker, RELATIVE_SYMBOL, RELATIVE_TIMEFRAME)
    if identity_issues:
        raise ConfigError(
            f"{EXPERT_NAME} relative-value bars failed identity check: {identity_issues[0]}."
        )

    gap_issue = largest_bar_gap_issue(combined["bar_end_utc"], RELATIVE_TIMEFRAME)
    if gap_issue:
        raise ConfigError(f"{EXPERT_NAME} relative-value bars failed continuity check: {gap_issue}.")
    return combined


def _assert_h1_relative_coverage(
    frame: pd.DataFrame,
    source: Path,
    required_start: pd.Timestamp,
    required_end: pd.Timestamp,
) -> None:
    starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce").dropna()
    ends = pd.to_datetime(frame["bar_end_utc"], utc=True, errors="coerce").dropna()
    if starts.empty or ends.empty:
        raise ConfigError(f"{EXPERT_NAME} relative-value bars in {source} have no valid coverage timestamps.")
    coverage_start = pd.Timestamp(starts.min())
    coverage_end = pd.Timestamp(ends.max())
    allowed_gap = pd.Timedelta(days=7)
    if coverage_start > required_start and coverage_start - required_start > allowed_gap:
        raise ConfigError(
            f"{EXPERT_NAME} relative-value bars in {source} start {coverage_start.isoformat()}, "
            f"but required {required_start.isoformat()}."
        )
    if coverage_end < required_end and required_end - coverage_end > allowed_gap:
        raise ConfigError(
            f"{EXPERT_NAME} relative-value bars in {source} end {coverage_end.isoformat()}, "
            f"but required {required_end.isoformat()}."
        )


def _timestamp_text(value: pd.Timestamp) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")

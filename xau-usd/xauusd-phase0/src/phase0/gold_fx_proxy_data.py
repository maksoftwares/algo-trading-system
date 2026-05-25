from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from phase0.config import ConfigError, ProjectConfig, build_cell_configs
from phase0.constants import COMPARISON_SYMBOLS
from phase0.data_availability import DataAvailabilityCheck, _valid_bar_files
from phase0.data_loader import processed_bars_dir
from phase0.data_validator import bar_identity_issues, largest_bar_gap_issue, validate_bars


EXPERT_NAME = "gold_fx_proxy_divergence_v0"
PROXY_TIMEFRAME = "H1"
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
class GoldFxProxyDataReadiness:
    status: str
    checks: tuple[DataAvailabilityCheck, ...]
    report_path: Path
    requirements_path: Path

    @property
    def ready_count(self) -> int:
        return sum(1 for check in self.checks if check.available)


def check_gold_fx_proxy_data(config: ProjectConfig) -> list[DataAvailabilityCheck]:
    checks: list[DataAvailabilityCheck] = []
    for broker, (required_start, required_end) in _matrix_windows_by_broker(config).items():
        for symbol in COMPARISON_SYMBOLS:
            directory = processed_bars_dir(config, broker, symbol, PROXY_TIMEFRAME)
            files = sorted(directory.glob("*.csv")) if directory.exists() else []
            valid_files, issues, coverage_start, coverage_end = _valid_bar_files(
                files,
                broker,
                symbol,
                PROXY_TIMEFRAME,
                required_start,
                required_end,
            )
            checks.append(
                DataAvailabilityCheck(
                    broker=broker,
                    symbol=symbol,
                    timeframe=PROXY_TIMEFRAME,
                    directory=directory,
                    file_count=len(valid_files),
                    candidate_file_count=len(files),
                    required_start_utc=_timestamp_text(required_start),
                    required_end_utc=_timestamp_text(required_end),
                    coverage_start_utc=_timestamp_text(coverage_start)
                    if coverage_start is not None
                    else "",
                    coverage_end_utc=_timestamp_text(coverage_end) if coverage_end is not None else "",
                    issues=tuple(issues),
                )
            )
    return checks


def generate_gold_fx_proxy_data_readiness(config: ProjectConfig) -> GoldFxProxyDataReadiness:
    checks = check_gold_fx_proxy_data(config)
    status = "PASS" if all(check.available for check in checks) else "BLOCKED"
    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "GOLD_FX_PROXY_DIVERGENCE_V0_DATA_READINESS.md"
    requirements_path = output_dir / "GOLD_FX_PROXY_DIVERGENCE_V0_DATA_REQUIREMENTS.csv"

    report_path.write_text(_render_report(status, checks), encoding="utf-8")
    _write_requirements_csv(config, checks, requirements_path)
    return GoldFxProxyDataReadiness(
        status=status,
        checks=tuple(checks),
        report_path=report_path,
        requirements_path=requirements_path,
    )


def load_gold_fx_proxy_h1_context(
    config: ProjectConfig,
    broker: str,
    required_start: object,
    required_end: object,
) -> dict[str, pd.DataFrame]:
    proxy: dict[str, pd.DataFrame] = {}
    start = _utc_timestamp(required_start)
    end = _utc_timestamp(required_end)
    for symbol in COMPARISON_SYMBOLS:
        directory = processed_bars_dir(config, broker, symbol, PROXY_TIMEFRAME)
        files = sorted(directory.glob("*.csv")) if directory.exists() else []
        if not files:
            raise ConfigError(
                f"{EXPERT_NAME} requires processed {broker} {symbol} {PROXY_TIMEFRAME} proxy bars "
                f"in {directory} before any real research matrix run."
            )
        frame = _load_h1_proxy_files(files, broker, symbol)
        _assert_h1_proxy_coverage(frame, directory, start, end)
        proxy[symbol] = frame
    return proxy


def _render_report(status: str, checks: list[DataAvailabilityCheck]) -> str:
    missing = [check for check in checks if not check.available]
    lines = [
        "# gold_fx_proxy_divergence_v0 Data Readiness",
        "",
        f"Status: {status}",
        f"Ready proxy sets: {len(checks) - len(missing)}/{len(checks)}",
        "",
        "## Boundary",
        "",
        (
            "This report is for a research-only candidate. It does not alter active Phase 1 soak, "
            "Phase 2 readiness, or approved expert status."
        ),
        "",
        "## Proxy H1 Sets",
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
            "Authoritative Phase 0 results must use broker-consistent proxy data. Capital.com EURUSD/USDJPY may not be substituted for Pepperstone or Dukascopy cells.",
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
                    "required_for": f"{EXPERT_NAME}_matrix_proxy",
                    "strict_authoritative_use": "present_locally"
                    if check.available
                    else "missing_required",
                }
            )


def _load_h1_proxy_files(files: list[Path], broker: str, symbol: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in files:
        try:
            frames.append(pd.read_csv(path))
        except Exception as exc:
            raise ConfigError(f"Failed to read {EXPERT_NAME} proxy file {path}: {exc}") from exc

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
        name=f"{broker} {symbol} {PROXY_TIMEFRAME} proxy bars",
        fail_on_error=False,
    )
    if report.error_count:
        first_issue = next(issue for issue in report.issues if issue.severity == "ERROR")
        raise ConfigError(
            f"{EXPERT_NAME} proxy bars failed validation: {first_issue.column} {first_issue.message}"
        )

    identity_issues = bar_identity_issues(combined, broker, symbol, PROXY_TIMEFRAME)
    if identity_issues:
        raise ConfigError(f"{EXPERT_NAME} proxy bars failed identity check: {identity_issues[0]}.")

    gap_issue = largest_bar_gap_issue(combined["bar_end_utc"], PROXY_TIMEFRAME)
    if gap_issue:
        raise ConfigError(f"{EXPERT_NAME} proxy bars failed continuity check: {gap_issue}.")
    return combined


def _assert_h1_proxy_coverage(
    frame: pd.DataFrame,
    source: Path,
    required_start: pd.Timestamp,
    required_end: pd.Timestamp,
) -> None:
    starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce").dropna()
    ends = pd.to_datetime(frame["bar_end_utc"], utc=True, errors="coerce").dropna()
    if starts.empty or ends.empty:
        raise ConfigError(f"{EXPERT_NAME} proxy bars in {source} have no valid coverage timestamps.")
    coverage_start = pd.Timestamp(starts.min())
    coverage_end = pd.Timestamp(ends.max())
    allowed_gap = pd.Timedelta(days=7)
    if coverage_start > required_start and coverage_start - required_start > allowed_gap:
        raise ConfigError(
            f"{EXPERT_NAME} proxy bars in {source} start {coverage_start.isoformat()}, "
            f"but required {required_start.isoformat()}."
        )
    if coverage_end < required_end and required_end - coverage_end > allowed_gap:
        raise ConfigError(
            f"{EXPERT_NAME} proxy bars in {source} end {coverage_end.isoformat()}, "
            f"but required {required_end.isoformat()}."
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


def _timestamp_text(value: pd.Timestamp) -> str:
    return pd.Timestamp(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")

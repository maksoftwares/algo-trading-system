from __future__ import annotations

import hashlib
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ProjectConfig, get_broker_details, resolve_symbol
from phase0.data_loader import find_raw_tick_files, processed_bars_dir, processed_ticks_dir
from phase0.data_validator import ValidationReport


@dataclass(frozen=True)
class FileManifestRow:
    path: str
    sha256: str
    row_count: int
    start_timestamp_utc: str
    end_timestamp_utc: str


@dataclass(frozen=True)
class ResultManifestRow:
    path: str
    artifact_type: str
    sha256: str
    size_bytes: int
    modified_at_utc: str


RESULT_MANIFEST_COLUMNS = (
    "path",
    "artifact_type",
    "sha256",
    "size_bytes",
    "modified_at_utc",
)

RESULT_ARTIFACT_ROOTS = {
    ("outputs", "hashes"): "hypothesis_hashes",
    ("outputs", "matrix_results"): "matrix_results",
    ("outputs", "decile_results"): "decile_results",
    ("outputs", "multisymbol_results"): "multisymbol_results",
    ("outputs", "adversarial_review"): "adversarial_review",
    ("outputs", "reports"): "reports",
}


def generate_data_manifest(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    validation_reports: list[ValidationReport] | None = None,
    prepared_by: str = "phase0",
) -> Path:
    canonical_symbol = resolve_symbol(config, symbol)
    raw_files = find_raw_tick_files(config, broker, canonical_symbol)
    processed_files = _processed_files(config, broker, canonical_symbol)
    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "PHASE0_DATA_MANIFEST.md"
    output_path.write_text(
        _render_manifest(
            config=config,
            broker=broker,
            symbol=canonical_symbol,
            raw_rows=[_file_row(config, path) for path in raw_files],
            processed_rows=[_file_row(config, path) for path in processed_files],
            validation_reports=validation_reports or [],
            prepared_by=prepared_by,
        ),
        encoding="utf-8",
    )
    return output_path


def generate_result_manifest(config: ProjectConfig) -> Path:
    output_dir = config.root / "outputs" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "PHASE0_RESULT_MANIFEST.csv"
    rows = _result_manifest_rows(config)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_MANIFEST_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "path": row.path,
                    "artifact_type": row.artifact_type,
                    "sha256": row.sha256,
                    "size_bytes": row.size_bytes,
                    "modified_at_utc": row.modified_at_utc,
                }
            )
    return output_path


def _processed_files(config: ProjectConfig, broker: str, symbol: str) -> list[Path]:
    roots = [
        processed_ticks_dir(config, broker, symbol),
        processed_bars_dir(config, broker, symbol),
    ]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(sorted(path for path in root.rglob("*.csv") if path.is_file()))
    return files


def _result_manifest_rows(config: ProjectConfig) -> list[ResultManifestRow]:
    rows: list[ResultManifestRow] = []
    for relative_root, artifact_type in RESULT_ARTIFACT_ROOTS.items():
        root = config.root.joinpath(*relative_root)
        if not root.exists():
            continue
        for path in _iter_result_artifacts(root):
            stat = path.stat()
            rows.append(
                ResultManifestRow(
                    path=path.relative_to(config.root).as_posix(),
                    artifact_type=artifact_type,
                    sha256=_sha256(path),
                    size_bytes=stat.st_size,
                    modified_at_utc=datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                    .replace(microsecond=0)
                    .isoformat(),
                )
            )
    return sorted(rows, key=lambda row: row.path)


def _iter_result_artifacts(root: Path) -> list[Path]:
    ignored_parts = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv"}
    ignored_suffixes = {".pyc", ".pyo"}
    ignored_names = {".gitkeep"}
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name in ignored_names:
            continue
        if any(part in ignored_parts for part in path.parts):
            continue
        if path.suffix in ignored_suffixes:
            continue
        files.append(path)
    return files


def _render_manifest(
    *,
    config: ProjectConfig,
    broker: str,
    symbol: str,
    raw_rows: list[FileManifestRow],
    processed_rows: list[FileManifestRow],
    validation_reports: list[ValidationReport],
    prepared_by: str,
) -> str:
    broker_details = get_broker_details(config, broker)
    warnings = _warnings(validation_reports)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return "\n".join(
        [
            "# Phase 0 Data Manifest",
            "",
            f"Prepared by: {prepared_by}",
            f"Prepared date UTC: {generated_at}",
            f"Data source: {broker_details.get('display_name', broker)}",
            f"Broker: {broker}",
            f"Symbol: {symbol}",
            "",
            "## Raw Files",
            "",
            _markdown_table(raw_rows),
            "",
            "## Processed Files",
            "",
            _markdown_table(processed_rows),
            "",
            "## Known Gaps",
            "",
            "Not automatically detected. Review validation artifacts and broker coverage manually.",
            "",
            "## Known Quality Warnings",
            "",
            "\n".join(f"- {warning}" for warning in warnings) if warnings else "None recorded.",
            "",
        ]
    )


def _file_row(config: ProjectConfig, path: Path) -> FileManifestRow:
    stats = _csv_stats(path)
    return FileManifestRow(
        path=path.relative_to(config.root).as_posix(),
        sha256=_sha256(path),
        row_count=stats["row_count"],
        start_timestamp_utc=stats["start_timestamp_utc"],
        end_timestamp_utc=stats["end_timestamp_utc"],
    )


def _csv_stats(path: Path) -> dict[str, Any]:
    try:
        frame = pd.read_csv(path)
    except Exception:
        return {"row_count": 0, "start_timestamp_utc": "", "end_timestamp_utc": ""}

    timestamp_column = _timestamp_column(frame)
    if timestamp_column is None or frame.empty:
        return {"row_count": len(frame), "start_timestamp_utc": "", "end_timestamp_utc": ""}
    timestamps = pd.to_datetime(frame[timestamp_column], utc=True, errors="coerce").dropna()
    if timestamps.empty:
        return {"row_count": len(frame), "start_timestamp_utc": "", "end_timestamp_utc": ""}
    return {
        "row_count": len(frame),
        "start_timestamp_utc": timestamps.min().isoformat(),
        "end_timestamp_utc": timestamps.max().isoformat(),
    }


def _timestamp_column(frame: pd.DataFrame) -> str | None:
    aliases = {"timestamp_utc", "timestamp", "time", "ticktime", "datetime", "date_time", "date"}
    for column in frame.columns:
        canonical = str(column).strip().strip("<>").lower().replace(" ", "_")
        if canonical in aliases:
            return column
    return None


def _warnings(validation_reports: list[ValidationReport]) -> list[str]:
    warnings: list[str] = []
    for report in validation_reports:
        for issue in report.issues:
            if issue.severity == "WARNING":
                row = "n/a" if issue.row_number is None else str(issue.row_number)
                warnings.append(f"{report.name} row {row} {issue.column}: {issue.message}")
    return warnings


def _markdown_table(rows: list[FileManifestRow]) -> str:
    columns = ("path", "sha256", "row_count", "start_timestamp_utc", "end_timestamp_utc")
    if not rows:
        return "No files found."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(
            str(getattr(row, column)).replace("|", "\\|")
            for column in columns
        )
        + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

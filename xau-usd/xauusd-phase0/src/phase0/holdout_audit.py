from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.config import ProjectConfig, parse_utc_datetime
from phase0.holdout import write_run_context_manifest


TIMESTAMP_COLUMNS = (
    "time_window_start",
    "time_window_end",
    "start_utc",
    "end_utc",
    "entry_time_utc",
    "exit_time_utc",
    "timestamp_utc",
    "signal_time_utc",
)

RESULT_ROOTS = (
    ("outputs", "matrix_results"),
    ("outputs", "decile_results"),
    ("outputs", "multisymbol_results"),
    ("outputs", "adversarial_review"),
    ("outputs", "reports"),
)


@dataclass(frozen=True)
class HoldoutAuditCheck:
    name: str
    status: str
    message: str


@dataclass(frozen=True)
class HoldoutAuditOutput:
    status: str
    report_path: Path
    manifest_path: Path
    checks: tuple[HoldoutAuditCheck, ...]


def audit_true_holdout(config: ProjectConfig) -> HoldoutAuditOutput:
    holdout = config.true_holdout["true_holdout"]
    holdout_start = parse_utc_datetime(holdout["start"], "true_holdout_period.yaml true_holdout.start")
    holdout_end = parse_utc_datetime(holdout["end"], "true_holdout_period.yaml true_holdout.end")
    run_context_path = write_run_context_manifest(config)
    scanned = _scan_result_timestamps(config, holdout_start, holdout_end)
    checks = [
        _check_holdout_enabled(config),
        _check_unlock_file_absent(config),
        _check_run_context(run_context_path),
        _check_result_timestamps(scanned),
        _check_trimmed_boundary(scanned, holdout_start),
    ]
    status = "PASS" if all(check.status in {"PASS", "WARN"} for check in checks) else "FAIL"

    report_path = config.root / "outputs" / "reports" / "PHASE0_TRUE_HOLDOUT_AUDIT.md"
    manifest_path = config.root / "outputs" / "manifests" / "PHASE0_TRUE_HOLDOUT_AUDIT_MANIFEST.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_report(status, holdout_start, holdout_end, checks, scanned),
        encoding="utf-8",
    )
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "holdout_start": holdout_start.isoformat(),
        "holdout_end": holdout_end.isoformat(),
        "report_path": str(report_path.relative_to(config.root)),
        "run_context_path": str(run_context_path.relative_to(config.root)),
        "report_sha256": _sha256(report_path),
        "run_context_sha256": _sha256(run_context_path),
        "checks": [check.__dict__ for check in checks],
        "scanned_files": scanned["scanned_files"],
        "files_with_overlap": scanned["files_with_overlap"],
        "latest_result_timestamp_utc": scanned["latest_result_timestamp_utc"],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return HoldoutAuditOutput(status, report_path, manifest_path, tuple(checks))


def _check_holdout_enabled(config: ProjectConfig) -> HoldoutAuditCheck:
    enabled = bool(config.phase0.get("true_holdout", {}).get("enabled", False))
    return HoldoutAuditCheck(
        "true_holdout_enabled",
        "PASS" if enabled else "FAIL",
        "True holdout guard is enabled in phase0.yaml." if enabled else "True holdout guard is disabled.",
    )


def _check_unlock_file_absent(config: ProjectConfig) -> HoldoutAuditCheck:
    holdout = config.true_holdout["true_holdout"]
    unlock_file = config.root / str(holdout["unlock_requires_file"])
    if not unlock_file.exists():
        return HoldoutAuditCheck(
            "unlock_file_absent",
            "PASS",
            f"Unlock file is absent: {unlock_file.relative_to(config.root)}",
        )
    return HoldoutAuditCheck(
        "unlock_file_absent",
        "FAIL",
        f"Unlock file exists: {unlock_file.relative_to(config.root)}",
    )


def _check_run_context(path: Path) -> HoldoutAuditCheck:
    if not path.exists():
        return HoldoutAuditCheck("run_context_locked", "FAIL", f"Missing {path}.")
    data = json.loads(path.read_text(encoding="utf-8"))
    unlocked = bool(data.get("true_holdout_unlocked"))
    unlock_file_present = bool(data.get("true_holdout_unlock_file_present"))
    if unlocked or unlock_file_present:
        return HoldoutAuditCheck(
            "run_context_locked",
            "FAIL",
            f"Run context is unlocked={unlocked}, unlock_file_present={unlock_file_present}.",
        )
    overlap = bool(data.get("true_holdout_overlap_detected"))
    message = "Run context remains locked."
    if overlap:
        message += " Configured periods overlap the holdout calendar, so result rows were audited for trimming."
    return HoldoutAuditCheck("run_context_locked", "PASS", message)


def _check_result_timestamps(scanned: dict[str, Any]) -> HoldoutAuditCheck:
    overlaps = scanned["files_with_overlap"]
    if overlaps:
        return HoldoutAuditCheck(
            "result_rows_exclude_holdout",
            "FAIL",
            f"Result files contain timestamps inside the holdout window: {len(overlaps)} file(s).",
        )
    return HoldoutAuditCheck(
        "result_rows_exclude_holdout",
        "PASS",
        f"No holdout-window timestamps found in {scanned['scanned_files']} scanned result CSV file(s).",
    )


def _check_trimmed_boundary(scanned: dict[str, Any], holdout_start: datetime) -> HoldoutAuditCheck:
    latest = scanned.get("latest_result_timestamp_utc")
    if not latest:
        return HoldoutAuditCheck("latest_result_boundary", "WARN", "No result timestamps were found to audit.")
    latest_timestamp = pd.Timestamp(latest)
    if latest_timestamp.tzinfo is None:
        latest_timestamp = latest_timestamp.tz_localize("UTC")
    if latest_timestamp < pd.Timestamp(holdout_start):
        return HoldoutAuditCheck(
            "latest_result_boundary",
            "PASS",
            f"Latest audited result timestamp is {latest}, before holdout start {holdout_start.isoformat()}.",
        )
    return HoldoutAuditCheck(
        "latest_result_boundary",
        "FAIL",
        f"Latest audited result timestamp is {latest}, which reaches the holdout window.",
    )


def _scan_result_timestamps(
    config: ProjectConfig,
    holdout_start: datetime,
    holdout_end: datetime,
) -> dict[str, Any]:
    scanned_files = 0
    files_with_overlap: list[dict[str, object]] = []
    latest: pd.Timestamp | None = None
    for path in _result_csv_files(config):
        try:
            frame = pd.read_csv(path)
        except Exception:
            continue
        columns = [column for column in TIMESTAMP_COLUMNS if column in frame.columns]
        if not columns:
            continue
        scanned_files += 1
        for column in columns:
            timestamps = pd.to_datetime(frame[column], utc=True, errors="coerce").dropna()
            if timestamps.empty:
                continue
            column_latest = pd.Timestamp(timestamps.max())
            latest = column_latest if latest is None else max(latest, column_latest)
            overlap_mask = (timestamps >= pd.Timestamp(holdout_start)) & (timestamps <= pd.Timestamp(holdout_end))
            overlap_count = int(overlap_mask.sum())
            if overlap_count:
                files_with_overlap.append(
                    {
                        "path": path.relative_to(config.root).as_posix(),
                        "column": column,
                        "overlap_count": overlap_count,
                        "first_overlap": pd.Timestamp(timestamps[overlap_mask].min()).isoformat(),
                    }
                )
    return {
        "scanned_files": scanned_files,
        "files_with_overlap": files_with_overlap,
        "latest_result_timestamp_utc": "" if latest is None else latest.isoformat(),
    }


def _result_csv_files(config: ProjectConfig) -> list[Path]:
    files: list[Path] = []
    for relative_root in RESULT_ROOTS:
        root = config.root.joinpath(*relative_root)
        if root.exists():
            files.extend(path for path in root.rglob("*.csv") if path.is_file())
    return sorted(set(files))


def _render_report(
    status: str,
    holdout_start: datetime,
    holdout_end: datetime,
    checks: list[HoldoutAuditCheck],
    scanned: dict[str, Any],
) -> str:
    overlap_section = "No holdout-window result rows found."
    if scanned["files_with_overlap"]:
        overlap_section = _markdown_table(
            [
                {
                    "Path": str(item["path"]),
                    "Column": str(item["column"]),
                    "Rows": str(item["overlap_count"]),
                    "First Overlap": str(item["first_overlap"]),
                }
                for item in scanned["files_with_overlap"]
            ],
            ["Path", "Column", "Rows", "First Overlap"],
        )
    return "\n".join(
        [
            "# Phase 0 True Holdout Audit",
            "",
            f"Overall status: {status}",
            "",
            "## Holdout Window",
            "",
            _markdown_table(
                [
                    {"Field": "start", "Value": holdout_start.isoformat()},
                    {"Field": "end", "Value": holdout_end.isoformat()},
                    {"Field": "latest_result_timestamp_utc", "Value": scanned["latest_result_timestamp_utc"] or "n/a"},
                    {"Field": "scanned_result_csv_files", "Value": str(scanned["scanned_files"])},
                ],
                ["Field", "Value"],
            ),
            "",
            "## Checks",
            "",
            _markdown_table(
                [{"Check": check.name, "Status": check.status, "Message": check.message} for check in checks],
                ["Check", "Status", "Message"],
            ),
            "",
            "## Overlap Findings",
            "",
            overlap_section,
            "",
            "## Interpretation",
            "",
            "A PASS means generated result artifacts exclude the reserved holdout window and the unlock controls remain closed. It does not unlock the holdout for future testing.",
            "",
        ]
    )


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(str(row.get(column, "")).replace("|", "\\|") for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

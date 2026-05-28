from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_REPORT = Path("outputs") / "reports" / "PHASE2_VPS_FIRST_DAY_VERIFICATION.md"
DEFAULT_JSON = Path("outputs") / "reports" / "PHASE2_VPS_FIRST_DAY_VERIFICATION.json"
DEFAULT_TERMINAL = Path("C:/MT5PortableGoldMission/terminal64.exe")
DEFAULT_DATA_PATH = Path("C:/MT5PortableGoldMission")
DEFAULT_FILES_DIR = Path("C:/MT5PortableGoldMission/MQL5/Files")
DEFAULT_COMPILE_LOG = Path("C:/MT5PortableGoldMission/compile_Phase1DryRunShell.log")
DEFAULT_NTP_EVIDENCE = Path("outputs") / "reports" / "vps_ntp_sync.txt"
DEFAULT_BACKUP_EVIDENCE = Path("outputs") / "reports" / "vps_backup_config.txt"
DEFAULT_RECOVERY_EVIDENCE = Path("outputs") / "reports" / "vps_rdp_recovery.txt"
DEFAULT_SCHEDULER_EVIDENCE = Path("outputs") / "reports" / "vps_periodic_task.txt"
DEFAULT_VPS_SELECTION_MATRIX = Path("docs") / "PHASE2_VPS_SELECTION_MATRIX.md"
VPS_SELECTION_REQUIRED_FIELDS = (
    "selected_provider",
    "selected_region",
    "selected_plan",
    "monthly_cost",
    "backup_method",
    "monitoring_endpoint_or_scheduler",
    "recovery_access_owner",
    "latency_evidence_path",
    "decision_date",
    "owner_acceptance",
)


@dataclass(frozen=True)
class VpsFirstDayCheck:
    name: str
    status: str
    evidence: str


@dataclass(frozen=True)
class VpsFirstDayOutput:
    status: str
    report_path: Path
    json_path: Path
    checks: tuple[VpsFirstDayCheck, ...]


def generate_phase2_vps_first_day_verification(
    root: Path,
    report_path: Path | None = None,
    json_path: Path | None = None,
    terminal_path: Path = DEFAULT_TERMINAL,
    data_path: Path = DEFAULT_DATA_PATH,
    files_dir: Path = DEFAULT_FILES_DIR,
    compile_log: Path = DEFAULT_COMPILE_LOG,
    ntp_evidence_path: Path | None = None,
    backup_evidence_path: Path | None = None,
    recovery_evidence_path: Path | None = None,
    scheduler_evidence_path: Path | None = None,
) -> VpsFirstDayOutput:
    root = root.resolve()
    report_path = (root / DEFAULT_REPORT if report_path is None else report_path).resolve()
    json_path = (root / DEFAULT_JSON if json_path is None else json_path).resolve()
    report_dir = root / "outputs" / "reports"
    repo_root = root.parents[1]
    decision_log = files_dir / "decision_log.csv"
    startup_log = files_dir / "startup_log.csv"
    latency_report = report_dir / "PHASE2_VPS_LATENCY_REPORT.md"
    external_health = report_dir / "PHASE1_EXTERNAL_HEALTH.json"
    status_summary = report_dir / "PHASE1_STATUS_SUMMARY.json"
    readiness_report = report_dir / "PHASE2_READINESS_REPORT.md"
    ntp_evidence_path = (root / DEFAULT_NTP_EVIDENCE if ntp_evidence_path is None else ntp_evidence_path).resolve()
    backup_evidence_path = (
        root / DEFAULT_BACKUP_EVIDENCE if backup_evidence_path is None else backup_evidence_path
    ).resolve()
    recovery_evidence_path = (
        root / DEFAULT_RECOVERY_EVIDENCE if recovery_evidence_path is None else recovery_evidence_path
    ).resolve()
    scheduler_evidence_path = (
        root / DEFAULT_SCHEDULER_EVIDENCE if scheduler_evidence_path is None else scheduler_evidence_path
    ).resolve()

    checks = [
        _repo_commit_check(repo_root),
        _path_check("mt5_terminal_path", terminal_path, "MT5 terminal path exists."),
        _path_check("mt5_data_path", data_path, "MT5 data path exists."),
        _compile_log_check(compile_log),
        _csv_row_check("latest_startup_log_row", startup_log),
        _csv_row_check("latest_decision_log_row", decision_log),
        _json_status_check("external_health", external_health, required="PASS"),
        _status_summary_check(status_summary),
        _report_exists_check("phase2_readiness_report", readiness_report),
        _vps_latency_report_check(latency_report),
        _selected_vps_consistency_check(
            root / DEFAULT_VPS_SELECTION_MATRIX,
            latency_report,
            root,
            (ntp_evidence_path, backup_evidence_path, recovery_evidence_path, scheduler_evidence_path),
        ),
        _manual_evidence_check(
            "ntp_time_sync_evidence",
            ntp_evidence_path,
            required_fields={
                "evidence_status": "verified",
                "owner_verified": "true",
                "time_sync_enabled": "true",
            },
        ),
        _manual_evidence_check(
            "backup_configuration_evidence",
            backup_evidence_path,
            required_fields={
                "evidence_status": "verified",
                "owner_verified": "true",
                "backup_configured": "true",
                "restore_owner_confirmed": "true",
            },
        ),
        _manual_evidence_check(
            "rdp_recovery_login_evidence",
            recovery_evidence_path,
            required_fields={
                "evidence_status": "verified",
                "owner_verified": "true",
                "recovery_login_verified": "true",
            },
            reject_secret_values=True,
        ),
        _manual_evidence_check(
            "periodic_scheduler_evidence",
            scheduler_evidence_path,
            required_fields={
                "evidence_status": "verified",
                "owner_verified": "true",
                "task_registered": "true",
                "last_run_verified": "true",
            },
        ),
    ]
    status = _overall_status(checks)
    payload = {
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "phase2_paper_mode_authorized": False,
        "demo_trading_authorized": False,
        "live_trading_authorized": False,
        "checks": [check.__dict__ for check in checks],
        "paths": {
            "terminal_path": str(terminal_path),
            "data_path": str(data_path),
            "files_dir": str(files_dir),
            "compile_log": str(compile_log),
            "ntp_evidence_path": str(ntp_evidence_path),
            "backup_evidence_path": str(backup_evidence_path),
            "recovery_evidence_path": str(recovery_evidence_path),
            "scheduler_evidence_path": str(scheduler_evidence_path),
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report_path.write_text(_render_markdown(payload), encoding="utf-8")
    return VpsFirstDayOutput(status, report_path, json_path, tuple(checks))


def _repo_commit_check(repo_root: Path) -> VpsFirstDayCheck:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return VpsFirstDayCheck("repo_commit_hash", "PENDING", f"Could not run git: {exc}.")
    commit = result.stdout.strip()
    if result.returncode == 0 and len(commit) >= 12:
        return VpsFirstDayCheck("repo_commit_hash", "PASS", f"Repository commit hash captured: {commit}.")
    return VpsFirstDayCheck("repo_commit_hash", "PENDING", "Repository commit hash is not available yet.")


def _path_check(name: str, path: Path, evidence: str) -> VpsFirstDayCheck:
    if path.exists():
        return VpsFirstDayCheck(name, "PASS", f"{evidence} `{path}`.")
    return VpsFirstDayCheck(name, "PENDING", f"Missing `{path}`.")


def _compile_log_check(path: Path) -> VpsFirstDayCheck:
    if not path.exists():
        return VpsFirstDayCheck("compile_log", "PENDING", f"Missing `{path}`.")
    text = _read_text_lossy(path)
    if "0 errors, 0 warnings" in text:
        return VpsFirstDayCheck("compile_log", "PASS", f"`{path}` shows 0 errors, 0 warnings.")
    if "error" in text.lower():
        return VpsFirstDayCheck("compile_log", "FAIL", f"`{path}` contains compiler error text.")
    return VpsFirstDayCheck("compile_log", "PENDING", f"`{path}` exists but clean compile result was not found.")


def _csv_row_check(name: str, path: Path) -> VpsFirstDayCheck:
    if not path.exists():
        return VpsFirstDayCheck(name, "PENDING", f"Missing `{path}`.")
    rows = _read_csv_rows(path)
    if not rows:
        return VpsFirstDayCheck(name, "PENDING", f"`{path}` has no data rows.")
    return VpsFirstDayCheck(name, "PASS", f"`{path}` has data rows; latest row captured.")


def _json_status_check(name: str, path: Path, required: str) -> VpsFirstDayCheck:
    if not path.exists():
        return VpsFirstDayCheck(name, "PENDING", f"Missing `{path}`.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return VpsFirstDayCheck(name, "FAIL", f"`{path}` is not valid JSON: {exc}.")
    status = str(data.get("status", ""))
    if status == required:
        return VpsFirstDayCheck(name, "PASS", f"`{path}` status is {status}.")
    if status in {"PENDING", "WARN", ""}:
        return VpsFirstDayCheck(name, "PENDING", f"`{path}` status is {status or 'missing'}; required {required}.")
    return VpsFirstDayCheck(name, "FAIL", f"`{path}` status is {status}; required {required}.")


def _status_summary_check(path: Path) -> VpsFirstDayCheck:
    if not path.exists():
        return VpsFirstDayCheck("phase1_status_summary", "PENDING", f"Missing `{path}`.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return VpsFirstDayCheck("phase1_status_summary", "FAIL", f"`{path}` is not valid JSON: {exc}.")
    latest = data.get("runtime", {}).get("latest_row", {})
    if (
        str(latest.get("dry_run", "")).lower() == "true"
        and str(latest.get("trade_permission", "")).lower() == "false"
        and str(latest.get("server_time_status", "")) == "CLOCK_OK"
    ):
        return VpsFirstDayCheck(
            "phase1_status_summary",
            "PASS",
            f"`{path}` latest bar {latest.get('bar_time', 'n/a')} keeps dry_run=true and trade_permission=false.",
        )
    return VpsFirstDayCheck("phase1_status_summary", "FAIL", f"`{path}` latest runtime boundary is unsafe or unclear.")


def _report_exists_check(name: str, path: Path) -> VpsFirstDayCheck:
    if path.exists() and path.stat().st_size > 0:
        status = _read_markdown_status(path) or "UNKNOWN"
        return VpsFirstDayCheck(name, "PASS", f"`{path}` exists; current status is {status}.")
    return VpsFirstDayCheck(name, "PENDING", f"Missing or empty `{path}`.")


def _markdown_status_check(name: str, path: Path, required: str) -> VpsFirstDayCheck:
    if not path.exists():
        return VpsFirstDayCheck(name, "PENDING", f"Missing `{path}`.")
    status = _read_markdown_status(path)
    if status == required:
        return VpsFirstDayCheck(name, "PASS", f"`{path}` status is {status}.")
    if status in {"PENDING", "WARN", "REVIEW", ""}:
        return VpsFirstDayCheck(name, "PENDING", f"`{path}` status is {status or 'missing'}; required {required}.")
    return VpsFirstDayCheck(name, "FAIL", f"`{path}` status is {status}; required {required}.")


def _vps_latency_report_check(path: Path) -> VpsFirstDayCheck:
    base = _markdown_status_check("vps_latency_report", path, required="PASS")
    if base.status != "PASS":
        return base
    text = _read_text_lossy(path)
    if "| local_baseline_comparison | PASS |" not in text:
        return VpsFirstDayCheck(
            "vps_latency_report",
            "FAIL",
            f"`{path}` is PASS but does not prove local_baseline_comparison PASS.",
        )
    if "Local MT5 baseline:" not in text:
        return VpsFirstDayCheck(
            "vps_latency_report",
            "FAIL",
            f"`{path}` is PASS but is missing the local MT5 baseline evidence path.",
        )
    return VpsFirstDayCheck(
        "vps_latency_report",
        "PASS",
        f"`{path}` status is PASS and includes local baseline comparison.",
    )


def _selected_vps_consistency_check(
    selection_path: Path,
    latency_report_path: Path,
    root: Path,
    manual_evidence_paths: tuple[Path, ...],
) -> VpsFirstDayCheck:
    if not selection_path.exists():
        return VpsFirstDayCheck(
            "selected_vps_consistency",
            "PENDING",
            f"Missing VPS selection matrix `{selection_path}`.",
        )

    selection_text = _read_text_lossy(selection_path)
    selection_status = _read_markdown_status(selection_path)
    if selection_status in {"", "PENDING", "WARN", "REVIEW"}:
        return VpsFirstDayCheck(
            "selected_vps_consistency",
            "PENDING",
            f"`{selection_path}` status is {selection_status or 'missing'}; required PASS.",
        )
    if selection_status != "PASS":
        return VpsFirstDayCheck(
            "selected_vps_consistency",
            "FAIL",
            f"`{selection_path}` status is {selection_status}; required PASS.",
        )

    decision_fields = _parse_decision_record_fields(selection_text)
    missing = [field for field in VPS_SELECTION_REQUIRED_FIELDS if not decision_fields.get(field)]
    if missing:
        return VpsFirstDayCheck(
            "selected_vps_consistency",
            "PENDING",
            f"`{selection_path}` is PASS but missing decision record field(s): {', '.join(missing)}.",
        )
    placeholders = [
        field
        for field in VPS_SELECTION_REQUIRED_FIELDS
        if _is_placeholder_value(decision_fields.get(field, ""))
    ]
    if placeholders:
        return VpsFirstDayCheck(
            "selected_vps_consistency",
            "PENDING",
            f"`{selection_path}` is PASS but still has placeholder decision field(s): {', '.join(placeholders)}.",
        )

    latency_candidate = _parse_latency_candidate(latency_report_path)
    if not latency_candidate:
        return VpsFirstDayCheck(
            "selected_vps_consistency",
            "FAIL",
            f"`{latency_report_path}` is missing a candidate provider/region table for selected-VPS comparison.",
        )

    mismatches: list[str] = []
    selected_provider = decision_fields.get("selected_provider", "")
    selected_region = decision_fields.get("selected_region", "")
    if not _compatible_label(selected_provider, latency_candidate.get("provider", "")):
        mismatches.append(
            f"latency provider {latency_candidate.get('provider', '') or 'missing'} != selected provider {selected_provider}"
        )
    if not _compatible_label(selected_region, latency_candidate.get("region", "")):
        mismatches.append(
            f"latency region {latency_candidate.get('region', '') or 'missing'} != selected region {selected_region}"
        )
    if not _path_value_matches(decision_fields.get("latency_evidence_path", ""), latency_report_path, root):
        mismatches.append(
            f"latency_evidence_path {decision_fields.get('latency_evidence_path', '')} does not point to `{latency_report_path}`"
        )

    manual_status, manual_details = _manual_provider_region_consistency(
        manual_evidence_paths,
        selected_provider,
        selected_region,
    )
    if manual_status == "PENDING":
        return VpsFirstDayCheck(
            "selected_vps_consistency",
            "PENDING",
            "Manual VPS evidence is not ready for selected-provider comparison: " + "; ".join(manual_details) + ".",
        )
    mismatches.extend(manual_details)
    if mismatches:
        return VpsFirstDayCheck(
            "selected_vps_consistency",
            "FAIL",
            "Selected VPS evidence mismatch: " + "; ".join(mismatches) + ".",
        )

    return VpsFirstDayCheck(
        "selected_vps_consistency",
        "PASS",
        f"Selected VPS decision record, latency report, and manual evidence all reference {selected_provider} / {selected_region}.",
    )


def _parse_decision_record_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    in_decision_record = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_decision_record = line.strip().lower() == "## decision record"
            continue
        if not in_decision_record or not line.startswith("| ") or line.startswith("| ---") or line.startswith("| Field |"):
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 2:
            continue
        key = parts[0].strip().lower().replace(" ", "_").replace("-", "_")
        fields[key] = parts[1].strip().strip("`")
    return fields


def _parse_latency_candidate(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    tables = _parse_markdown_tables(_read_text_lossy(path))
    for table in tables:
        if not table:
            continue
        first = table[0]
        if {"provider", "region"}.issubset(first):
            return {
                "provider": first.get("provider", "").strip(),
                "region": first.get("region", "").strip(),
            }
    return {}


def _parse_markdown_tables(text: str) -> list[list[dict[str, str]]]:
    tables: list[list[dict[str, str]]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith("| "):
            index += 1
            continue
        header = _split_markdown_row(line)
        if index + 1 >= len(lines) or not _is_markdown_separator(lines[index + 1]):
            index += 1
            continue
        index += 2
        rows: list[dict[str, str]] = []
        while index < len(lines) and lines[index].startswith("| "):
            values = _split_markdown_row(lines[index])
            rows.append(
                {
                    _normalize_key(header[column]): values[column] if column < len(values) else ""
                    for column in range(len(header))
                }
            )
            index += 1
        tables.append(rows)
    return tables


def _split_markdown_row(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def _is_markdown_separator(line: str) -> bool:
    cells = _split_markdown_row(line)
    return bool(cells) and all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells)


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_").replace("-", "_")


def _is_placeholder_value(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"", "pending", "n/a", "none", "tbd", "todo", "unknown"}:
        return True
    if "pending owner selection" in normalized or "pending selection" in normalized:
        return True
    if "pending" in normalized and "outputs/reports/phase2_vps_latency_report.md" not in normalized:
        return True
    return "<" in normalized and ">" in normalized


def _compatible_label(left: str, right: str) -> bool:
    left_norm = _normalize_compare(left)
    right_norm = _normalize_compare(right)
    if not left_norm or not right_norm:
        return False
    return left_norm == right_norm or left_norm in right_norm or right_norm in left_norm


def _path_value_matches(value: str, actual_path: Path, root: Path) -> bool:
    expected = _normalize_compare(value)
    if not expected:
        return False
    actual_absolute = _normalize_compare(str(actual_path))
    try:
        actual_relative = _normalize_compare(str(actual_path.resolve().relative_to(root.resolve())))
    except ValueError:
        actual_relative = actual_absolute
    return expected in {actual_absolute, actual_relative} or actual_absolute.endswith(expected)


def _manual_provider_region_consistency(
    paths: tuple[Path, ...],
    selected_provider: str,
    selected_region: str,
) -> tuple[str, list[str]]:
    pending: list[str] = []
    mismatches: list[str] = []
    for path in paths:
        if not path.exists():
            pending.append(f"{path.name} missing")
            continue
        fields = _parse_key_value_evidence(_read_text_lossy(path))
        if fields.get("evidence_status", "").lower() != "verified" or fields.get("owner_verified", "").lower() != "true":
            pending.append(f"{path.name} not owner-verified")
            continue
        provider = fields.get("provider", "")
        region = fields.get("region", "")
        if not _compatible_label(selected_provider, provider):
            mismatches.append(f"{path.name} provider {provider or 'missing'} != selected provider {selected_provider}")
        if not _compatible_label(selected_region, region):
            mismatches.append(f"{path.name} region {region or 'missing'} != selected region {selected_region}")
    if pending:
        return "PENDING", pending
    return "PASS", mismatches


def _normalize_compare(value: str) -> str:
    return value.strip().strip("`").lower().replace("\\", "/")


def _manual_evidence_check(
    name: str,
    path: Path,
    required_fields: dict[str, str],
    reject_secret_values: bool = False,
) -> VpsFirstDayCheck:
    if not path.exists() or path.stat().st_size == 0:
        return VpsFirstDayCheck(name, "PENDING", f"Missing or empty `{path}`.")

    text = _read_text_lossy(path)
    fields = _parse_key_value_evidence(text)
    missing = [key for key in required_fields if key not in fields]
    if missing:
        return VpsFirstDayCheck(
            name,
            "PENDING",
            f"`{path}` is missing required field(s): {', '.join(missing)}.",
        )

    mismatches = [
        f"{key}={fields[key]}"
        for key, expected in required_fields.items()
        if fields[key].lower() != expected.lower()
    ]
    if mismatches:
        return VpsFirstDayCheck(
            name,
            "PENDING",
            f"`{path}` has unverified required field(s): {', '.join(mismatches)}.",
        )

    placeholder = _first_placeholder_token(text)
    if placeholder:
        return VpsFirstDayCheck(name, "PENDING", f"`{path}` still contains placeholder token `{placeholder}`.")

    if reject_secret_values:
        secret_key = _first_secret_value_key(fields)
        if secret_key:
            return VpsFirstDayCheck(
                name,
                "FAIL",
                f"`{path}` appears to contain a non-redacted `{secret_key}` value. Remove secrets and keep proof only.",
            )

    return VpsFirstDayCheck(name, "PASS", f"Verified structured evidence captured in `{path}`.")


def _parse_key_value_evidence(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip().lower()] = value.strip()
    return fields


def _first_placeholder_token(text: str) -> str:
    lowered = text.lower()
    for token in ("todo", "tbd", "replace_me", "pending"):
        if token in lowered:
            return token.upper()
    for line in text.splitlines():
        if "<" in line and ">" in line:
            return "<...>"
    return ""


def _first_secret_value_key(fields: dict[str, str]) -> str:
    redacted_values = {"", "none", "n/a", "redacted", "[redacted]", "***", "not stored"}
    for key, value in fields.items():
        if key in {"password", "secret", "token", "api_key", "private_key"} and value.strip().lower() not in redacted_values:
            return key
    return ""


def _overall_status(checks: list[VpsFirstDayCheck]) -> str:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "PENDING" for check in checks):
        return "PENDING"
    return "PASS"


def _render_markdown(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Phase 2 VPS First-Day Verification",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Authority",
            "",
            "| Field | Value |",
            "| --- | --- |",
            f"| Phase 2 paper-mode authorized | {str(payload['phase2_paper_mode_authorized']).lower()} |",
            f"| Demo trading authorized | {str(payload['demo_trading_authorized']).lower()} |",
            f"| Live trading authorized | {str(payload['live_trading_authorized']).lower()} |",
            "",
            "## Checks",
            "",
            _markdown_table(payload["checks"], ["name", "status", "evidence"]),
            "",
            "## Captured Paths",
            "",
            _markdown_table(
                [{"path": key, "value": value} for key, value in payload["paths"].items()],
                ["path", "value"],
            ),
            "",
            "## Manual Evidence Still Needed",
            "",
            "- Copy `docs/templates/vps_ntp_sync.template.txt` to `outputs/reports/vps_ntp_sync.txt`, then set `evidence_status: VERIFIED`, `owner_verified: true`, and `time_sync_enabled: true` after VPS setup.",
            "- Copy `docs/templates/vps_backup_config.template.txt` to `outputs/reports/vps_backup_config.txt`, then set `evidence_status: VERIFIED`, `owner_verified: true`, `backup_configured: true`, and `restore_owner_confirmed: true` after backup/recovery proof.",
            "- Copy `docs/templates/vps_rdp_recovery.template.txt` to `outputs/reports/vps_rdp_recovery.txt`, then set `evidence_status: VERIFIED`, `owner_verified: true`, and `recovery_login_verified: true` without storing passwords, secrets, tokens, or keys.",
            "- Copy `docs/templates/vps_periodic_task.template.txt` to `outputs/reports/vps_periodic_task.txt`, then set `evidence_status: VERIFIED`, `owner_verified: true`, `task_registered: true`, and `last_run_verified: true` after the scheduled readiness check has run once.",
            "",
        ]
    )


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_markdown_status(path: Path) -> str:
    for line in _read_text_lossy(path).splitlines():
        if line.startswith("Overall status:") or line.startswith("Status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_escape(str(row.get(column, ""))) for column in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, separator, *body])


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _read_text_lossy(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").replace("\x00", "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 2 VPS first-day verification packet.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--terminal-path", type=Path, default=DEFAULT_TERMINAL)
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH)
    parser.add_argument("--files-dir", type=Path, default=DEFAULT_FILES_DIR)
    parser.add_argument("--compile-log", type=Path, default=DEFAULT_COMPILE_LOG)
    parser.add_argument("--ntp-evidence", type=Path, default=None)
    parser.add_argument("--backup-evidence", type=Path, default=None)
    parser.add_argument("--recovery-evidence", type=Path, default=None)
    parser.add_argument("--scheduler-evidence", type=Path, default=None)
    args = parser.parse_args(argv)
    output = generate_phase2_vps_first_day_verification(
        root=args.root,
        report_path=args.report,
        json_path=args.json,
        terminal_path=args.terminal_path,
        data_path=args.data_path,
        files_dir=args.files_dir,
        compile_log=args.compile_log,
        ntp_evidence_path=args.ntp_evidence,
        backup_evidence_path=args.backup_evidence,
        recovery_evidence_path=args.recovery_evidence,
        scheduler_evidence_path=args.scheduler_evidence,
    )
    print(f"Phase 2 VPS first-day verification: {output.status}")
    print(output.report_path)
    return 0 if output.status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

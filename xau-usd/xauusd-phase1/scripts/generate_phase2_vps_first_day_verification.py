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
        _markdown_status_check("vps_latency_report", latency_report, required="PASS"),
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
    return VpsFirstDayCheck(name, "PASS", f"`{path}` has {len(rows)} row(s); latest row captured.")


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
    )
    print(f"Phase 2 VPS first-day verification: {output.status}")
    print(output.report_path)
    return 0 if output.status != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())

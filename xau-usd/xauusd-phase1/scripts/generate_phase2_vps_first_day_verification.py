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
        _optional_evidence_check("ntp_time_sync_evidence", ntp_evidence_path),
        _optional_evidence_check("backup_configuration_evidence", backup_evidence_path),
        _optional_evidence_check("rdp_recovery_login_evidence", recovery_evidence_path),
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
            "ntp_evidence_path": str(ntp_evidence_path or ""),
            "backup_evidence_path": str(backup_evidence_path or ""),
            "recovery_evidence_path": str(recovery_evidence_path or ""),
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


def _optional_evidence_check(name: str, path: Path | None) -> VpsFirstDayCheck:
    if path is None:
        return VpsFirstDayCheck(name, "PENDING", "Evidence file path was not provided.")
    if path.exists() and path.stat().st_size > 0:
        return VpsFirstDayCheck(name, "PASS", f"Evidence captured in `{path}`.")
    return VpsFirstDayCheck(name, "PENDING", f"Missing or empty `{path}`.")


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
            "- `vps_ntp_sync.txt`: text or screenshot notes proving NTP/time sync is enabled.",
            "- `vps_backup_config.txt`: backup configuration and restore owner notes.",
            "- `vps_rdp_recovery.txt`: recovery-login confirmation without secrets.",
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

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from analyze_phase1_soak import analyze_phase1_soak
from audit_phase1_safety import audit_phase1_tree
from deploy_phase1_mt5 import _read_compile_log
from generate_phase1_runtime_health_report import generate_phase1_runtime_health_report
from generate_phase1_would_signal_report import generate_phase1_would_signal_report
from phase1_soak_streak import CODE_FREEZE_MARKER_NAME, calculate_soak_streak, read_code_freeze_marker
from verify_phase1_logs import verify_phase1_logs


DECISION_LOG = "decision_log.csv"
REQUIRED_SOAK_DAYS = 5
DEFAULT_MAX_FRESH_MINUTES = 15


@dataclass(frozen=True)
class AcceptanceItem:
    gate: str
    status: str
    evidence: str


@dataclass(frozen=True)
class AcceptanceOutput:
    status: str
    report_path: Path
    items: tuple[AcceptanceItem, ...]


def generate_phase1_acceptance_report(
    files_dir: Path,
    report_path: Path | None = None,
    compile_log: Path | None = None,
    source_root: Path | None = None,
    soak_history_report: Path | None = None,
    runtime_health_report: Path | None = None,
    now: datetime | None = None,
    max_fresh_minutes: int = DEFAULT_MAX_FRESH_MINUTES,
) -> AcceptanceOutput:
    files_dir = files_dir.resolve()
    if report_path is None:
        report_path = Path.cwd() / "outputs" / "reports" / "PHASE1_ACCEPTANCE_REPORT.md"
    if source_root is None:
        source_root = Path(__file__).resolve().parents[1]
    if now is None:
        now = datetime.now()

    log_report = report_path.parent / "PHASE1_DRY_RUN_LOG_REPORT.md"
    soak_report = report_path.parent / "PHASE1_SOAK_DRIFT_REPORT.md"
    would_signal_report = report_path.parent / "PHASE1_WOULD_SIGNAL_REPORT.md"
    if soak_history_report is None:
        soak_history_report = report_path.parent / "PHASE1_SOAK_HISTORY_REPORT.md"
    if runtime_health_report is None:
        runtime_health_report = report_path.parent / "PHASE1_RUNTIME_HEALTH_REPORT.md"
    log_verification = verify_phase1_logs(files_dir, log_report)
    soak_analysis = analyze_phase1_soak(files_dir, soak_report, now=now, max_fresh_minutes=max_fresh_minutes)
    runtime_health = generate_phase1_runtime_health_report(
        files_dir,
        runtime_health_report,
        now=now,
        max_fresh_minutes=max_fresh_minutes,
    )
    would_signals = generate_phase1_would_signal_report(files_dir, would_signal_report)
    decision_rows = _read_csv(files_dir / DECISION_LOG)

    items = [
        _compile_item(compile_log),
        _source_safety_item(source_root),
        AcceptanceItem("Runtime log verification", log_verification.status, f"Report: `{log_verification.report_path}`"),
        AcceptanceItem("Soak/drift analysis", soak_analysis.status, f"Report: `{soak_analysis.report_path}`"),
        AcceptanceItem("Runtime health", runtime_health.status, f"Report: `{runtime_health.report_path}`"),
        AcceptanceItem(
            "Would-signal evidence",
            would_signals.status,
            (
                f"Rows: {would_signals.signal_count}; clusters: {would_signals.cluster_count}; "
                f"report: `{would_signals.report_path}`; csv: `{would_signals.csv_path}`"
            ),
        ),
        _soak_history_item(soak_history_report),
        _dry_run_item(decision_rows),
        _permission_item(decision_rows),
        _freshness_item(decision_rows, now, max_fresh_minutes),
        _latest_row_item(decision_rows),
        _active_market_soak_item(decision_rows, files_dir, now),
        _process_code_freeze_item(decision_rows, files_dir, now),
        _soak_duration_item(decision_rows),
    ]

    status = _overall_status(items)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(status, files_dir, items, decision_rows), encoding="utf-8")
    return AcceptanceOutput(status=status, report_path=report_path, items=tuple(items))


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _compile_item(compile_log: Path | None) -> AcceptanceItem:
    if compile_log is None:
        return AcceptanceItem("MT5 compile", "WARN", "No compile log path supplied.")
    compile_log = compile_log.resolve()
    if not compile_log.exists():
        return AcceptanceItem("MT5 compile", "WARN", f"Compile log missing: `{compile_log}`")
    text = _read_compile_log(compile_log)
    if "Result: 0 errors, 0 warnings" in text or "Result: 0 errors, 0 warning" in text:
        return AcceptanceItem("MT5 compile", "PASS", f"Compile log passed: `{compile_log}`")
    if "error" in text.lower():
        return AcceptanceItem("MT5 compile", "FAIL", f"Compile log contains errors: `{compile_log}`")
    return AcceptanceItem("MT5 compile", "WARN", f"Compile result unclear: `{compile_log}`")


def _source_safety_item(source_root: Path) -> AcceptanceItem:
    findings = audit_phase1_tree(source_root.resolve())
    if findings:
        first = findings[0]
        evidence = f"Findings: {len(findings)}; first: `{first.path}:{first.line_number}`"
        return AcceptanceItem("Source safety audit", "FAIL", evidence)
    return AcceptanceItem("Source safety audit", "PASS", f"No findings under `{source_root.resolve()}`.")


def _soak_history_item(report_path: Path) -> AcceptanceItem:
    report_path = report_path.resolve()
    if not report_path.exists():
        return AcceptanceItem("Soak history ledger", "WARN", f"History report missing: `{report_path}`")
    text = report_path.read_text(encoding="utf-8")
    status = _read_report_status(text)
    if status == "PASS":
        return AcceptanceItem("Soak history ledger", "PASS", f"History report passed: `{report_path}`")
    if status == "WARN":
        return AcceptanceItem("Soak history ledger", "WARN", f"History report has warnings: `{report_path}`")
    if status == "FAIL":
        return AcceptanceItem("Soak history ledger", "FAIL", f"History report failed: `{report_path}`")
    return AcceptanceItem("Soak history ledger", "WARN", f"History report status unclear: `{report_path}`")


def _dry_run_item(rows: list[dict[str, str]]) -> AcceptanceItem:
    if not rows:
        return AcceptanceItem("Dry-run state", "FAIL", "No decision rows found.")
    bad = [
        row.get("run_id", "")
        for row in rows
        if row.get("dry_run", "").lower() != "true" or row.get("lifecycle_state", "") != "DRY_RUN"
    ]
    if bad:
        return AcceptanceItem("Dry-run state", "FAIL", f"Rows outside dry-run state: {len(bad)}")
    return AcceptanceItem("Dry-run state", "PASS", "All decision rows are in dry-run state.")


def _permission_item(rows: list[dict[str, str]]) -> AcceptanceItem:
    if not rows:
        return AcceptanceItem("Permission lock", "FAIL", "No decision rows found.")
    bad = [row.get("run_id", "") for row in rows if row.get("trade_permission", "").lower() != "false"]
    if bad:
        return AcceptanceItem("Permission lock", "FAIL", f"Rows with permission not false: {len(bad)}")
    return AcceptanceItem("Permission lock", "PASS", "All decision rows keep permission false.")


def _freshness_item(rows: list[dict[str, str]], now: datetime, max_fresh_minutes: int) -> AcceptanceItem:
    if not rows:
        return AcceptanceItem("Runtime freshness", "FAIL", "No decision rows found.")
    latest = rows[-1]
    latest_time = _parse_mt5_datetime(latest.get("timestamp_local", "")) or _parse_mt5_datetime(
        latest.get("timestamp_broker", "")
    )
    if latest_time is None:
        return AcceptanceItem("Runtime freshness", "WARN", "Latest row has no parseable local or broker timestamp.")
    age_minutes = (now - latest_time).total_seconds() / 60
    if age_minutes < -2:
        return AcceptanceItem(
            "Runtime freshness",
            "WARN",
            f"Latest row timestamp is {abs(age_minutes):.1f} minute(s) ahead of local clock.",
        )
    if age_minutes <= max_fresh_minutes:
        return AcceptanceItem(
            "Runtime freshness",
            "PASS",
            f"Latest row age is {max(age_minutes, 0):.1f} minute(s); limit {max_fresh_minutes}.",
        )
    return AcceptanceItem(
        "Runtime freshness",
        "WARN",
        f"Latest row age is {age_minutes:.1f} minute(s); limit {max_fresh_minutes}.",
    )


def _latest_row_item(rows: list[dict[str, str]]) -> AcceptanceItem:
    if not rows:
        return AcceptanceItem("Latest runtime row", "FAIL", "No decision rows found.")
    latest = rows[-1]
    evidence = (
        f"run_id={latest.get('run_id', 'n/a')}; "
        f"bar_time={latest.get('bar_time', 'n/a')}; "
        f"risk={latest.get('risk_state', 'n/a')}; "
        f"server_time={latest.get('server_time_status', 'n/a')}; "
        f"observer={latest.get('br_stage', 'n/a')}/{latest.get('br_direction', 'n/a')}; "
        f"would_signal={latest.get('br_would_signal', 'n/a')}"
    )
    return AcceptanceItem("Latest runtime row", "PASS", evidence)


def _soak_duration_item(rows: list[dict[str, str]]) -> AcceptanceItem:
    parsed = sorted(
        {value for value in (_parse_mt5_datetime(row.get("bar_time", "")) for row in rows) if value}
    )
    if len(parsed) < 2:
        return AcceptanceItem("Five trading day soak", "PENDING", "Not enough unique bar times yet.")
    span_seconds = (parsed[-1] - parsed[0]).total_seconds()
    span_days = span_seconds / 86400
    evidence = f"Observed unique-bar span: {span_days:.2f} calendar day(s), from {parsed[0]} to {parsed[-1]}."
    if span_days >= REQUIRED_SOAK_DAYS:
        return AcceptanceItem("Five trading day soak", "PASS", evidence)
    return AcceptanceItem("Five trading day soak", "PENDING", evidence)


def _active_market_soak_item(rows: list[dict[str, str]], files_dir: Path, now: datetime) -> AcceptanceItem:
    if not rows:
        return AcceptanceItem("Active-market 72-hour soak", "PENDING", "No decision rows found.")
    streak = calculate_soak_streak(
        rows,
        code_freeze_started_at=read_code_freeze_marker(files_dir / CODE_FREEZE_MARKER_NAME),
        now=now,
    )
    evidence = (
        f"Longest active streak: {streak.longest_streak_hours:.2f}h; "
        f"current active streak: {streak.current_streak_hours:.2f}h; "
        f"required: {streak.required_uninterrupted_streak_hours:.0f}h; "
        f"last restart UTC: {streak.last_restart_utc or 'n/a'}; "
        f"weekend policy: {streak.weekend_policy}."
    )
    if streak.uninterrupted_soak_pass:
        return AcceptanceItem("Active-market 72-hour soak", "PASS", evidence)
    return AcceptanceItem("Active-market 72-hour soak", "PENDING", evidence)


def _process_code_freeze_item(rows: list[dict[str, str]], files_dir: Path, now: datetime) -> AcceptanceItem:
    if not rows:
        return AcceptanceItem("Process/code-freeze 96-hour gate", "PENDING", "No decision rows found.")
    marker_path = files_dir / CODE_FREEZE_MARKER_NAME
    streak = calculate_soak_streak(
        rows,
        code_freeze_started_at=read_code_freeze_marker(marker_path),
        now=now,
    )
    evidence = (
        f"Process uptime streak: {streak.process_uptime_streak_hours:.2f}h; "
        f"code-freeze hours: {streak.code_freeze_hours:.2f}h; "
        f"required: {streak.required_code_freeze_hours:.0f}h; "
        f"marker: {streak.code_freeze_started_at or 'missing'}; "
        f"marker path: `{marker_path}`."
    )
    if streak.process_code_freeze_pass:
        return AcceptanceItem("Process/code-freeze 96-hour gate", "PASS", evidence)
    return AcceptanceItem("Process/code-freeze 96-hour gate", "PENDING", evidence)


def _parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


def _read_report_status(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("Overall status:"):
            return line.split(":", 1)[1].strip()
    return ""


def _overall_status(items: list[AcceptanceItem]) -> str:
    if any(item.status == "FAIL" for item in items):
        return "FAIL"
    if any(item.status in {"WARN", "PENDING"} for item in items):
        return "PENDING"
    return "PASS"


def _render_report(
    status: str,
    files_dir: Path,
    items: list[AcceptanceItem],
    decision_rows: list[dict[str, str]],
) -> str:
    return "\n".join(
        [
            "# Phase 1 Acceptance Report",
            "",
            f"Overall status: {status}",
            "",
            f"Files directory: `{files_dir}`",
            "",
            "## Acceptance Gates",
            "",
            _markdown_table(
                [{"Gate": item.gate, "Status": item.status, "Evidence": item.evidence} for item in items],
                ["Gate", "Status", "Evidence"],
            ),
            "",
            "## Decision",
            "",
            _decision_text(status),
            "",
            "## Runtime Rows",
            "",
            f"- Decision rows analyzed: {len(decision_rows)}",
            f"- Unique run IDs: {len({row.get('run_id', '') for row in decision_rows})}",
            "",
        ]
    )


def _decision_text(status: str) -> str:
    if status == "PASS":
        return "Phase 1 acceptance evidence is complete for the current dry-run scope."
    if status == "FAIL":
        return "Phase 1 acceptance evidence has a failing gate. Keep the shell in dry-run mode and resolve the finding."
    return "Phase 1 is progressing, but final acceptance remains pending until the required wall-clock soak is complete."


def _markdown_table(rows: list[dict[str, str]], columns: list[str]) -> str:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Phase 1 dry-run acceptance report.")
    parser.add_argument("--files-dir", type=Path, required=True, help="MT5 MQL5/Files directory.")
    parser.add_argument("--max-fresh-minutes", type=int, default=DEFAULT_MAX_FRESH_MINUTES)
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_ACCEPTANCE_REPORT.md",
        help="Markdown report path.",
    )
    parser.add_argument(
        "--compile-log",
        type=Path,
        default=Path("C:/MT5PortableGoldMission/compile_Phase1DryRunShell.log"),
        help="MetaEditor compile log path.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Phase 1 source root for the safety audit.",
    )
    parser.add_argument(
        "--soak-history-report",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_SOAK_HISTORY_REPORT.md",
        help="Optional soak-history markdown report path.",
    )
    parser.add_argument(
        "--runtime-health-report",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_RUNTIME_HEALTH_REPORT.md",
        help="Optional runtime health markdown report path.",
    )
    args = parser.parse_args(argv)

    output = generate_phase1_acceptance_report(
        args.files_dir,
        args.report,
        args.compile_log,
        args.source_root,
        args.soak_history_report,
        args.runtime_health_report,
        max_fresh_minutes=args.max_fresh_minutes,
    )
    print(f"Phase 1 acceptance report: {output.status}")
    print(output.report_path)
    for item in output.items:
        print(f"{item.status}: {item.gate} - {item.evidence}")
    return 1 if output.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

try:
    from atomic_write import atomic_write_text
except ModuleNotFoundError:  # pragma: no cover - supports direct importlib test loading
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from atomic_write import atomic_write_text
from analyze_phase1_soak import analyze_phase1_soak
from generate_phase1_acceptance_report import generate_phase1_acceptance_report
from generate_phase1_runtime_health_report import generate_phase1_runtime_health_report
from generate_phase1_would_signal_report import generate_phase1_would_signal_report
from phase1_soak_streak import CODE_FREEZE_MARKER_NAME, calculate_soak_streak, read_code_freeze_marker
from verify_phase1_logs import verify_phase1_logs


DECISION_LOG = "decision_log.csv"
REQUIRED_SOAK_DAYS = 5


def generate_phase1_status_summary(
    files_dir: Path,
    output_path: Path | None = None,
    compile_log: Path | None = None,
    source_root: Path | None = None,
    now: datetime | None = None,
    log_status=None,
    soak_status=None,
    runtime_health_status=None,
    would_signal_status=None,
    acceptance_status=None,
) -> Path:
    files_dir = files_dir.resolve()
    if output_path is None:
        output_path = Path.cwd() / "outputs" / "reports" / "PHASE1_STATUS_SUMMARY.json"
    if source_root is None:
        source_root = Path(__file__).resolve().parents[1]
    default_now = now is None
    if now is None:
        now = datetime.now()
    soak_now = datetime.now(timezone.utc) if default_now else now

    report_dir = output_path.parent
    if log_status is None:
        log_status = verify_phase1_logs(files_dir, report_dir / "PHASE1_DRY_RUN_LOG_REPORT.md")
    if soak_status is None:
        soak_status = analyze_phase1_soak(files_dir, report_dir / "PHASE1_SOAK_DRIFT_REPORT.md", now=now)
    if runtime_health_status is None:
        runtime_health_status = generate_phase1_runtime_health_report(
            files_dir,
            report_dir / "PHASE1_RUNTIME_HEALTH_REPORT.md",
            now=now,
        )
    if would_signal_status is None:
        would_signal_status = generate_phase1_would_signal_report(
            files_dir,
            report_dir / "PHASE1_WOULD_SIGNAL_REPORT.md",
        )
    if acceptance_status is None:
        acceptance_status = generate_phase1_acceptance_report(
            files_dir,
            report_dir / "PHASE1_ACCEPTANCE_REPORT.md",
            compile_log,
            source_root,
            now=now,
        )
    rows = _read_csv(files_dir / DECISION_LOG)
    latest = rows[-1] if rows else {}
    soak_days = _soak_days(rows)
    soak_streak = calculate_soak_streak(
        rows,
        code_freeze_started_at=read_code_freeze_marker(files_dir / CODE_FREEZE_MARKER_NAME),
        now=soak_now,
    )

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "files_dir": str(files_dir),
        "status": {
            "log_verification": log_status.status,
            "soak_analysis": soak_status.status,
            "runtime_health": runtime_health_status.status,
            "would_signal": would_signal_status.status,
            "acceptance": acceptance_status.status,
        },
        "runtime": {
            "decision_rows": len(rows),
            "unique_run_ids": len({row.get("run_id", "") for row in rows}),
            "latest_row": {
                "run_id": latest.get("run_id", ""),
                "timestamp_broker": latest.get("timestamp_broker", ""),
                "timestamp_local": latest.get("timestamp_local", ""),
                "bar_time": latest.get("bar_time", ""),
                "risk_state": latest.get("risk_state", ""),
                "trade_permission": latest.get("trade_permission", ""),
                "dry_run": latest.get("dry_run", ""),
                "server_time_status": latest.get("server_time_status", ""),
                "br_stage": latest.get("br_stage", ""),
                "br_direction": latest.get("br_direction", ""),
                "br_would_signal": latest.get("br_would_signal", ""),
                "sbr_stage": latest.get("sbr_stage", ""),
                "sbr_direction": latest.get("sbr_direction", ""),
                "sbr_would_signal": latest.get("sbr_would_signal", ""),
            },
        },
        "would_signal": {
            "rows": would_signal_status.signal_count,
            "clusters": would_signal_status.cluster_count,
            "report_path": str(would_signal_status.report_path),
            "csv_path": str(would_signal_status.csv_path),
        },
        "soak": {
            "required_days": REQUIRED_SOAK_DAYS,
            "observed_days": round(soak_days, 4),
            "progress_pct": round(min(soak_days / REQUIRED_SOAK_DAYS, 1.0) * 100, 2),
            **asdict(soak_streak),
        },
        "reports": {
            "log_report": str(log_status.report_path),
            "soak_report": str(soak_status.report_path),
            "runtime_health_report": str(runtime_health_status.report_path),
            "would_signal_report": str(would_signal_status.report_path),
            "acceptance_report": str(acceptance_status.report_path),
        },
    }

    atomic_write_text(output_path, json.dumps(summary, indent=2, sort_keys=True))
    return output_path


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _soak_days(rows: list[dict[str, str]]) -> float:
    parsed = sorted(
        {value for value in (_parse_mt5_datetime(row.get("bar_time", "")) for row in rows) if value}
    )
    if len(parsed) < 2:
        return 0.0
    return (parsed[-1] - parsed[0]).total_seconds() / 86400


def _parse_mt5_datetime(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y.%m.%d %H:%M:%S")
    except ValueError:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a machine-readable Phase 1 status summary.")
    parser.add_argument("--files-dir", type=Path, required=True, help="MT5 MQL5/Files directory.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs") / "reports" / "PHASE1_STATUS_SUMMARY.json",
        help="JSON summary path.",
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
    args = parser.parse_args(argv)

    path = generate_phase1_status_summary(args.files_dir, args.output, args.compile_log, args.source_root)
    print(f"Phase 1 status summary: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

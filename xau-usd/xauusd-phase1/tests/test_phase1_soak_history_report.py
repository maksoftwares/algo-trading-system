from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_soak_history_report_passes_clean_history(tmp_path):
    module = _load_module()
    history_path = tmp_path / "PHASE1_SOAK_HISTORY.csv"
    report_path = tmp_path / "PHASE1_SOAK_HISTORY_REPORT.md"
    _write_history(history_path)

    output = module.generate_phase1_soak_history_report(history_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert output.rows_analyzed == 2
    assert "Phase 1 Soak History Report" in report
    assert "Latest M5 bar: 2026.05.21 19:55:00" in report
    assert "Recent History" in report
    assert "No historical acceptance `FAIL` rows recorded." in report


def test_soak_history_report_fails_when_latest_permission_is_not_locked(tmp_path):
    module = _load_module()
    history_path = tmp_path / "PHASE1_SOAK_HISTORY.csv"
    report_path = tmp_path / "PHASE1_SOAK_HISTORY_REPORT.md"
    _write_history(history_path, latest_permission="true")

    output = module.generate_phase1_soak_history_report(history_path, report_path)

    assert output.status == "FAIL"
    assert any(check.name == "latest_safety_state" and check.status == "FAIL" for check in output.checks)


def test_soak_history_report_calls_out_historical_acceptance_fail_rows(tmp_path):
    module = _load_module()
    history_path = tmp_path / "PHASE1_SOAK_HISTORY.csv"
    report_path = tmp_path / "PHASE1_SOAK_HISTORY_REPORT.md"
    _write_history(
        history_path,
        rows_override=[
            {
                "created_at_utc": "2026-05-21T22:14:43+00:00",
                "decision_rows": "95",
                "latest_bar_time": "2026.05.21 22:10:00",
                "soak_progress_pct": "7.01",
                "latest_trade_permission": "false",
                "log_verification": "PASS",
                "soak_analysis": "PASS",
                "runtime_health": "PASS",
                "would_signal": "PASS",
                "acceptance": "FAIL",
            },
            {
                "created_at_utc": "2026-05-21T22:15:28+00:00",
                "decision_rows": "96",
                "latest_bar_time": "2026.05.21 22:15:00",
                "soak_progress_pct": "7.08",
                "latest_trade_permission": "false",
                "log_verification": "PASS",
                "soak_analysis": "PASS",
                "runtime_health": "PASS",
                "would_signal": "PASS",
                "acceptance": "PENDING",
            },
        ],
    )

    output = module.generate_phase1_soak_history_report(history_path, report_path)

    report = report_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert "Historical acceptance `FAIL` rows: 1" in report
    assert "acceptance-only `FAIL`" in report
    assert "historical anomalies only" in report


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase1_soak_history_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase1_soak_history_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase1_soak_history_report"] = module
    spec.loader.exec_module(module)
    return module


def _write_history(path: Path, latest_permission: str = "false", rows_override: list[dict[str, str]] | None = None) -> None:
    fieldnames = [
        "created_at_utc",
        "files_dir",
        "log_verification",
        "soak_analysis",
        "runtime_health",
        "would_signal",
        "acceptance",
        "decision_rows",
        "unique_run_ids",
        "latest_run_id",
        "latest_bar_time",
        "latest_timestamp_broker",
        "latest_timestamp_local",
        "latest_risk_state",
        "latest_trade_permission",
        "latest_dry_run",
        "latest_server_time_status",
        "latest_br_stage",
        "latest_br_direction",
        "latest_br_would_signal",
        "would_signal_rows",
        "would_signal_clusters",
        "required_soak_days",
        "observed_soak_days",
        "soak_progress_pct",
        "summary_path",
        "log_report",
        "soak_report",
        "would_signal_report",
        "would_signal_csv",
        "acceptance_report",
    ]
    rows = rows_override or [
        {
            "created_at_utc": "2026-05-21T19:48:31+00:00",
            "decision_rows": "78",
            "latest_bar_time": "2026.05.21 19:45:00",
            "soak_progress_pct": "5.0",
            "latest_trade_permission": "false",
        },
        {
            "created_at_utc": "2026-05-21T19:55:41+00:00",
            "decision_rows": "80",
            "latest_bar_time": "2026.05.21 19:55:00",
            "soak_progress_pct": "5.14",
            "latest_trade_permission": latest_permission,
        },
    ]
    for row in rows:
        row.update(
            {
                "files_dir": "C:/MT5PortableGoldMission/MQL5/Files",
                "log_verification": row.get("log_verification", "PASS"),
                "soak_analysis": row.get("soak_analysis", "PASS"),
                "runtime_health": row.get("runtime_health", "PASS"),
                "would_signal": row.get("would_signal", "PASS"),
                "acceptance": row.get("acceptance", "PENDING"),
                "unique_run_ids": "5",
                "latest_run_id": "phase1-dry-run-v0.5",
                "latest_timestamp_broker": row["latest_bar_time"],
                "latest_timestamp_local": "2026.05.21 23:54:59",
                "latest_risk_state": "NORMAL",
                "latest_dry_run": "true",
                "latest_server_time_status": "CLOCK_OK",
                "latest_br_stage": "WAIT_LEVEL_BREAK_RETEST",
                "latest_br_direction": "SHORT",
                "latest_br_would_signal": "false",
                "would_signal_rows": "4",
                "would_signal_clusters": "4",
                "required_soak_days": "5",
                "observed_soak_days": "0.2569",
                "summary_path": "outputs/reports/PHASE1_STATUS_SUMMARY.json",
                "log_report": "outputs/reports/PHASE1_DRY_RUN_LOG_REPORT.md",
                "soak_report": "outputs/reports/PHASE1_SOAK_DRIFT_REPORT.md",
                "would_signal_report": "outputs/reports/PHASE1_WOULD_SIGNAL_REPORT.md",
                "would_signal_csv": "outputs/reports/PHASE1_WOULD_SIGNAL_REVIEW.csv",
                "acceptance_report": "outputs/reports/PHASE1_ACCEPTANCE_REPORT.md",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

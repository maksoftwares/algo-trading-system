from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_append_soak_history_flattens_status_summary_and_is_idempotent(tmp_path):
    module = _load_module()
    summary_path = tmp_path / "PHASE1_STATUS_SUMMARY.json"
    history_path = tmp_path / "PHASE1_SOAK_HISTORY.csv"
    _write_summary(summary_path)

    first = module.append_phase1_soak_history(summary_path=summary_path, history_path=history_path)
    second = module.append_phase1_soak_history(summary_path=summary_path, history_path=history_path)

    rows = _read_csv(history_path)
    assert first.appended is True
    assert second.appended is False
    assert first.row_count == 1
    assert second.row_count == 1
    assert rows[0]["created_at_utc"] == "2026-05-21T19:50:00+00:00"
    assert rows[0]["log_verification"] == "PASS"
    assert rows[0]["runtime_health"] == "PASS"
    assert rows[0]["acceptance"] == "PENDING"
    assert rows[0]["decision_rows"] == "78"
    assert rows[0]["latest_bar_time"] == "2026.05.21 19:45:00"
    assert rows[0]["latest_trade_permission"] == "false"
    assert rows[0]["latest_dry_run"] == "true"
    assert rows[0]["would_signal_rows"] == "4"
    assert rows[0]["would_signal_clusters"] == "4"
    assert rows[0]["observed_soak_days"] == "0.25"
    assert rows[0]["soak_progress_pct"] == "5.0"
    assert rows[0]["soak_current_streak_hours"] == "2.0"
    assert rows[0]["soak_longest_streak_hours"] == "2.0"
    assert rows[0]["soak_uninterrupted_pass"] == "False"
    assert rows[0]["summary_path"] == str(summary_path.resolve())


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "append_phase1_soak_history.py"
    spec = importlib.util.spec_from_file_location("append_phase1_soak_history", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["append_phase1_soak_history"] = module
    spec.loader.exec_module(module)
    return module


def _write_summary(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "created_at_utc": "2026-05-21T19:50:00+00:00",
                "files_dir": "C:/MT5PortableGoldMission/MQL5/Files",
                "status": {
                    "log_verification": "PASS",
                    "soak_analysis": "PASS",
                    "runtime_health": "PASS",
                    "would_signal": "PASS",
                    "acceptance": "PENDING",
                },
                "runtime": {
                    "decision_rows": 78,
                    "unique_run_ids": 5,
                    "latest_row": {
                        "run_id": "phase1-dry-run-v0.5",
                        "timestamp_broker": "2026.05.21 19:45:00",
                        "timestamp_local": "2026.05.21 23:44:59",
                        "bar_time": "2026.05.21 19:45:00",
                        "risk_state": "NORMAL",
                        "trade_permission": "false",
                        "dry_run": "true",
                        "server_time_status": "CLOCK_OK",
                        "br_stage": "WAIT_LEVEL_BREAK_RETEST",
                        "br_direction": "SHORT",
                        "br_would_signal": "false",
                    },
                },
                "would_signal": {
                    "rows": 4,
                    "clusters": 4,
                    "report_path": "outputs/reports/PHASE1_WOULD_SIGNAL_REPORT.md",
                    "csv_path": "outputs/reports/PHASE1_WOULD_SIGNAL_REVIEW.csv",
                },
                "soak": {
                    "required_days": 5,
                    "observed_days": 0.25,
                    "progress_pct": 5.0,
                    "current_streak_hours": 2.0,
                    "longest_streak_hours": 2.0,
                    "required_uninterrupted_streak_hours": 72.0,
                    "uninterrupted_soak_pass": False,
                    "last_restart_utc": "2026-05-21T08:00:00Z",
                },
                "reports": {
                    "log_report": "outputs/reports/PHASE1_DRY_RUN_LOG_REPORT.md",
                    "soak_report": "outputs/reports/PHASE1_SOAK_DRIFT_REPORT.md",
                    "would_signal_report": "outputs/reports/PHASE1_WOULD_SIGNAL_REPORT.md",
                    "acceptance_report": "outputs/reports/PHASE1_ACCEPTANCE_REPORT.md",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

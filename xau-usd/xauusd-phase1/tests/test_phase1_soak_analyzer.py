from __future__ import annotations

import csv
import importlib.util
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_soak_analyzer_passes_clean_sample(tmp_path):
    module = _load_soak_analyzer()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")

    output = module.analyze_phase1_soak(files_dir, tmp_path / "soak.md", now=datetime(2026, 5, 21, 12, 12))

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert output.rows_analyzed == 3
    assert "Phase 1 Soak Drift Report" in report
    assert "Spread Points" in report
    assert "Breakout-Retest Stage" in report
    assert any(check.name == "latest_row_freshness" and check.status == "PASS" for check in output.checks)


def test_soak_analyzer_fails_permission_true(tmp_path):
    module = _load_soak_analyzer()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_decision_log(files_dir / "decision_log.csv", force_permission="true")

    output = module.analyze_phase1_soak(files_dir, tmp_path / "soak.md", now=datetime(2026, 5, 21, 12, 12))

    assert output.status == "FAIL"
    assert any(check.name == "permission_state" and check.status == "FAIL" for check in output.checks)


def test_soak_analyzer_warns_when_latest_row_is_stale(tmp_path):
    module = _load_soak_analyzer()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")

    output = module.analyze_phase1_soak(files_dir, tmp_path / "soak.md", now=datetime(2026, 5, 21, 12, 40))

    assert output.status == "WARN"
    assert any(check.name == "latest_row_freshness" and check.status == "WARN" for check in output.checks)


def test_soak_analyzer_tolerates_stale_row_during_weekend_break(tmp_path):
    module = _load_soak_analyzer()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")

    output = module.analyze_phase1_soak(files_dir, tmp_path / "soak.md", now=datetime(2026, 5, 23, 17, 50))

    assert output.status == "PASS"
    assert any(check.name == "latest_row_freshness" and check.status == "PASS" for check in output.checks)


def test_soak_analyzer_tolerates_historical_clock_drift_and_weekend_gap(tmp_path):
    module = _load_soak_analyzer()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    decision_path = files_dir / "decision_log.csv"
    _write_decision_log(decision_path)
    with decision_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = rows[0].keys()
    rows[0]["server_time_status"] = "LOCAL_CLOCK_DRIFT"
    stale_weekend_row = rows[-1].copy()
    stale_weekend_row["timestamp_broker"] = "2026.05.23 12:18:20"
    stale_weekend_row["timestamp_utc"] = "2026.05.23 06:48:20"
    stale_weekend_row["timestamp_local"] = "2026.05.23 17:48:20"
    stale_weekend_row["bar_time"] = "2026.05.22 20:55:00"
    stale_weekend_row["session"] = "WEEKEND"
    stale_weekend_row["execution_state"] = "STALE_TICK"
    stale_weekend_row["stale_seconds"] = "55165"
    rows.append(stale_weekend_row)
    with decision_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output = module.analyze_phase1_soak(files_dir, tmp_path / "soak.md", now=datetime(2026, 5, 23, 17, 50))

    assert output.status == "PASS"
    assert any(check.name == "server_time_status" and check.status == "PASS" for check in output.checks)
    assert any(check.name == "per_run_bar_cadence" and check.status == "PASS" for check in output.checks)


def _load_soak_analyzer():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "analyze_phase1_soak.py"
    spec = importlib.util.spec_from_file_location("analyze_phase1_soak", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["analyze_phase1_soak"] = module
    spec.loader.exec_module(module)
    return module


def _write_startup_log(path: Path) -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "symbol",
        "dry_run_only",
        "magic_namespace_ok",
        "server_time_status",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "timestamp_broker": "2026.05.21 12:00:00",
                "timestamp_utc": "2026.05.21 08:00:00",
                "timestamp_local": "2026.05.21 12:00:00",
                "run_id": "phase1-dry-run-v0.5",
                "symbol": "XAUUSD",
                "dry_run_only": "true",
                "magic_namespace_ok": "true",
                "server_time_status": "CLOCK_OK",
            }
        )


def _write_shutdown_log(path: Path) -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "symbol",
        "shutdown_reason",
        "last_m5_bar_time",
        "last_decision_write_time",
        "lifecycle_state",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "timestamp_broker": "2026.05.21 12:15:00",
                "timestamp_utc": "2026.05.21 08:15:00",
                "timestamp_local": "2026.05.21 12:15:00",
                "run_id": "phase1-dry-run-v0.5",
                "symbol": "XAUUSD",
                "shutdown_reason": "9",
                "last_m5_bar_time": "2026.05.21 12:10:00",
                "last_decision_write_time": "2026.05.21 12:10:01",
                "lifecycle_state": "DRY_RUN",
            }
        )


def _write_decision_log(path: Path, force_permission: str = "false") -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "lifecycle_state",
        "symbol",
        "bid",
        "ask",
        "spread_points",
        "bar_time",
        "session",
        "risk_state",
        "execution_state",
        "server_time_status",
        "br_stage",
        "br_direction",
        "br_would_signal",
        "trade_permission",
        "dry_run",
        "stale_seconds",
    ]
    rows = []
    for index, minute in enumerate((0, 5, 10)):
        rows.append(
            {
                "timestamp_broker": f"2026.05.21 12:{minute:02d}:00",
                "timestamp_utc": f"2026.05.21 08:{minute:02d}:00",
                "timestamp_local": f"2026.05.21 12:{minute:02d}:00",
                "run_id": "phase1-dry-run-v0.5",
                "lifecycle_state": "DRY_RUN",
                "symbol": "XAUUSD",
                "bid": "4500.00",
                "ask": "4500.40",
                "spread_points": str(35 + index),
                "bar_time": f"2026.05.21 12:{minute:02d}:00",
                "session": "LONDON",
                "risk_state": "NORMAL",
                "execution_state": "EXECUTION_OK",
                "server_time_status": "CLOCK_OK",
                "br_stage": "WAIT_LEVEL_BREAK_RETEST",
                "br_direction": "LONG",
                "br_would_signal": "false",
                "trade_permission": force_permission if index == 0 else "false",
                "dry_run": "true",
                "stale_seconds": "0",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

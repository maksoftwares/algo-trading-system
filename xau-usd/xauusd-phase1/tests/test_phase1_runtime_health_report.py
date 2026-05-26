from __future__ import annotations

import csv
import importlib.util
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_health_report_passes_clean_runtime(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")

    output = module.generate_phase1_runtime_health_report(
        files_dir,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 21, 12, 12),
    )

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert output.rows_analyzed == 3
    assert "Phase 1 Runtime Health Report" in report
    assert "Larger-than-M5 gaps: 0" in report
    assert any(check.name == "permission_lock" and check.status == "PASS" for check in output.checks)


def test_runtime_health_report_fails_when_permission_not_locked(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_decision_log(files_dir / "decision_log.csv", force_permission="true")

    output = module.generate_phase1_runtime_health_report(
        files_dir,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 21, 12, 12),
    )

    assert output.status == "FAIL"
    assert any(check.name == "permission_lock" and check.status == "FAIL" for check in output.checks)


def test_runtime_health_report_warns_on_bar_gap(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_decision_log(files_dir / "decision_log.csv", minutes=(0, 5, 20))

    output = module.generate_phase1_runtime_health_report(
        files_dir,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 21, 12, 22),
    )

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "WARN"
    assert "Larger-than-M5 gaps: 1" in report
    assert any(check.name == "unique_bar_gaps" and check.status == "WARN" for check in output.checks)


def test_runtime_health_tolerates_stale_row_during_weekend_break(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")

    output = module.generate_phase1_runtime_health_report(
        files_dir,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 23, 17, 50),
    )

    assert output.status == "PASS"
    assert any(check.name == "latest_freshness" and check.status == "PASS" for check in output.checks)


def test_runtime_health_tolerates_extra_shutdown_rows(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv", rows=2)
    _write_decision_log(files_dir / "decision_log.csv")

    output = module.generate_phase1_runtime_health_report(
        files_dir,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 21, 12, 12),
    )

    assert output.status == "PASS"
    assert any(check.name == "startup_shutdown_rows" and check.status == "PASS" for check in output.checks)


def test_runtime_health_tolerates_historical_clock_drift_and_weekend_gap(tmp_path):
    module = _load_module()
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
    stale_weekend_row["block_reason"] = "STALE_TICK"
    rows.append(stale_weekend_row)
    with decision_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output = module.generate_phase1_runtime_health_report(
        files_dir,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 23, 17, 50),
    )

    assert output.status == "PASS"
    assert any(check.name == "server_time_status" and check.status == "PASS" for check in output.checks)
    assert any(check.name == "unique_bar_gaps" and check.status == "PASS" for check in output.checks)


def test_runtime_health_tolerates_weekend_reopen_bar_gap(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    decision_path = files_dir / "decision_log.csv"
    _write_decision_log(decision_path, minutes=(0, 5))
    with decision_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = rows[0].keys()
    rows[0]["timestamp_broker"] = "2026.05.22 20:55:00"
    rows[0]["timestamp_utc"] = "2026.05.22 16:55:00"
    rows[0]["timestamp_local"] = "2026.05.22 20:55:00"
    rows[0]["bar_time"] = "2026.05.22 20:55:00"
    rows[1]["timestamp_broker"] = "2026.05.25 00:05:00"
    rows[1]["timestamp_utc"] = "2026.05.24 20:05:00"
    rows[1]["timestamp_local"] = "2026.05.25 00:05:00"
    rows[1]["bar_time"] = "2026.05.25 00:05:00"
    rows[1]["session"] = "ASIA"
    rows[1]["execution_state"] = "EXECUTION_OK"
    with decision_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output = module.generate_phase1_runtime_health_report(
        files_dir,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 25, 0, 7),
    )

    assert output.status == "PASS"
    assert any(check.name == "unique_bar_gaps" and check.status == "PASS" for check in output.checks)


def test_runtime_health_tolerates_configured_daily_market_break_gap(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    decision_path = files_dir / "decision_log.csv"
    _write_decision_log(decision_path, minutes=(0, 5))
    with decision_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = rows[0].keys()
    rows[0]["timestamp_broker"] = "2026.05.25 18:25:00"
    rows[0]["timestamp_utc"] = "2026.05.25 18:25:00"
    rows[0]["timestamp_local"] = "2026.05.25 18:25:00"
    rows[0]["bar_time"] = "2026.05.25 18:25:00"
    rows[1]["timestamp_broker"] = "2026.05.25 22:00:00"
    rows[1]["timestamp_utc"] = "2026.05.25 22:00:00"
    rows[1]["timestamp_local"] = "2026.05.25 22:00:00"
    rows[1]["bar_time"] = "2026.05.25 22:00:00"
    rows[1]["session"] = "NEW_YORK"
    rows[1]["execution_state"] = "EXECUTION_OK"
    with decision_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output = module.generate_phase1_runtime_health_report(
        files_dir,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 25, 22, 2),
    )

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PASS"
    assert "Expected market-break gaps: 1" in report
    assert any(check.name == "unique_bar_gaps" and check.status == "PASS" for check in output.checks)


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase1_runtime_health_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase1_runtime_health_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase1_runtime_health_report"] = module
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


def _write_shutdown_log(path: Path, rows: int = 1) -> None:
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
        for index in range(rows):
            minute = 15 + index
            writer.writerow(
                {
                    "timestamp_broker": f"2026.05.21 12:{minute:02d}:00",
                    "timestamp_utc": f"2026.05.21 08:{minute:02d}:00",
                    "timestamp_local": f"2026.05.21 12:{minute:02d}:00",
                    "run_id": "phase1-dry-run-v0.5",
                    "symbol": "XAUUSD",
                    "shutdown_reason": "9",
                    "last_m5_bar_time": "2026.05.21 12:10:00",
                    "last_decision_write_time": "2026.05.21 12:10:01",
                    "lifecycle_state": "DRY_RUN",
                }
            )


def _write_decision_log(
    path: Path,
    force_permission: str = "false",
    minutes: tuple[int, ...] = (0, 5, 10),
) -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "lifecycle_state",
        "symbol",
        "bar_time",
        "session",
        "execution_state",
        "server_time_status",
        "br_stage",
        "dry_run",
        "trade_permission",
        "block_reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, minute in enumerate(minutes):
            writer.writerow(
                {
                    "timestamp_broker": f"2026.05.21 12:{minute:02d}:00",
                    "timestamp_utc": f"2026.05.21 08:{minute:02d}:00",
                    "timestamp_local": f"2026.05.21 12:{minute:02d}:00",
                    "run_id": "phase1-dry-run-v0.5",
                    "lifecycle_state": "DRY_RUN",
                    "symbol": "XAUUSD",
                    "bar_time": f"2026.05.21 12:{minute:02d}:00",
                    "session": "LONDON",
                    "execution_state": "EXECUTION_OK",
                    "server_time_status": "CLOCK_OK",
                    "br_stage": "WAIT_LEVEL_BREAK_RETEST",
                    "dry_run": "true",
                    "trade_permission": force_permission if index == 0 else "false",
                    "block_reason": "phase1_dry_run_only",
                }
            )

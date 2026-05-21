from __future__ import annotations

import csv
import importlib.util
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_acceptance_report_is_pending_until_soak_duration_is_complete(tmp_path):
    module = _load_acceptance_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")
    compile_log = tmp_path / "compile.log"
    compile_log.write_text("Result: 0 errors, 0 warnings\n", encoding="utf-8")

    output = module.generate_phase1_acceptance_report(
        files_dir,
        tmp_path / "acceptance.md",
        compile_log,
        ROOT,
        now=datetime(2026, 5, 21, 12, 12),
    )

    report = output.report_path.read_text(encoding="utf-8")
    assert output.status == "PENDING"
    assert "MT5 compile" in report
    assert "Source safety audit" in report
    assert "Runtime health" in report
    assert "Would-signal evidence" in report
    assert "Soak history ledger" in report
    assert "Five trading day soak" in report
    assert any(item.gate == "Source safety audit" and item.status == "PASS" for item in output.items)
    assert any(item.gate == "Permission lock" and item.status == "PASS" for item in output.items)
    assert any(item.gate == "Runtime freshness" and item.status == "PASS" for item in output.items)
    assert any(item.gate == "Runtime health" and item.status == "PASS" for item in output.items)
    assert any(item.gate == "Would-signal evidence" and item.status == "WARN" for item in output.items)
    assert any(item.gate == "Soak history ledger" and item.status == "WARN" for item in output.items)
    assert any(item.gate == "Five trading day soak" and item.status == "PENDING" for item in output.items)


def test_acceptance_report_fails_when_permission_not_locked(tmp_path):
    module = _load_acceptance_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_decision_log(files_dir / "decision_log.csv", force_permission="true")
    compile_log = tmp_path / "compile.log"
    compile_log.write_text("Result: 0 errors, 0 warnings\n", encoding="utf-8")

    output = module.generate_phase1_acceptance_report(
        files_dir,
        tmp_path / "acceptance.md",
        compile_log,
        ROOT,
        now=datetime(2026, 5, 21, 12, 12),
    )

    assert output.status == "FAIL"
    assert any(item.gate == "Permission lock" and item.status == "FAIL" for item in output.items)


def test_acceptance_report_fails_source_safety_findings(tmp_path):
    module = _load_acceptance_module()
    files_dir = tmp_path / "files"
    source_root = tmp_path / "source"
    files_dir.mkdir()
    source_root.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")
    compile_log = tmp_path / "compile.log"
    compile_log.write_text("Result: 0 errors, 0 warnings\n", encoding="utf-8")
    forbidden = "Order" + "Send"
    (source_root / "unsafe.mq5").write_text(f"void x() {{ {forbidden}; }}\n", encoding="utf-8")

    output = module.generate_phase1_acceptance_report(
        files_dir,
        tmp_path / "acceptance.md",
        compile_log,
        source_root,
        now=datetime(2026, 5, 21, 12, 12),
    )

    assert output.status == "FAIL"
    assert any(item.gate == "Source safety audit" and item.status == "FAIL" for item in output.items)


def test_acceptance_report_warns_when_runtime_is_stale(tmp_path):
    module = _load_acceptance_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")
    compile_log = tmp_path / "compile.log"
    compile_log.write_text("Result: 0 errors, 0 warnings\n", encoding="utf-8")

    output = module.generate_phase1_acceptance_report(
        files_dir,
        tmp_path / "acceptance.md",
        compile_log,
        ROOT,
        now=datetime(2026, 5, 21, 12, 40),
    )

    assert output.status == "PENDING"
    assert any(item.gate == "Runtime freshness" and item.status == "WARN" for item in output.items)


def test_acceptance_report_accepts_existing_soak_history_report(tmp_path):
    module = _load_acceptance_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")
    compile_log = tmp_path / "compile.log"
    compile_log.write_text("Result: 0 errors, 0 warnings\n", encoding="utf-8")
    history_report = tmp_path / "PHASE1_SOAK_HISTORY_REPORT.md"
    history_report.write_text("# History\n\nOverall status: PASS\n", encoding="utf-8")

    output = module.generate_phase1_acceptance_report(
        files_dir,
        tmp_path / "acceptance.md",
        compile_log,
        ROOT,
        history_report,
        tmp_path / "runtime_health.md",
        now=datetime(2026, 5, 21, 12, 12),
    )

    assert any(item.gate == "Soak history ledger" and item.status == "PASS" for item in output.items)


def _load_acceptance_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase1_acceptance_report.py"
    spec = importlib.util.spec_from_file_location("generate_phase1_acceptance_report", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase1_acceptance_report"] = module
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
        "bar_time",
        "session",
        "regime",
        "router_version",
        "risk_state",
        "risk_ok",
        "execution_state",
        "news_state",
        "expert_lifecycle_state",
        "magic_namespace_ok",
        "server_time_status",
        "br_stage",
        "br_direction",
        "br_would_signal",
        "br_reason_code",
        "br_level_found",
        "br_break_found",
        "br_retest_valid",
        "br_confirmation_valid",
        "br_level_kind",
        "br_level_price",
        "br_entry_price",
        "br_stop_loss",
        "br_take_profit",
        "br_stop_distance_points",
        "br_break_shift",
        "allowed_expert",
        "would_have_allowed_experts",
        "trade_permission",
        "block_reason",
        "dry_run",
        "spread_points",
        "stale_seconds",
    ]
    rows = []
    for minute in (0, 5, 10):
        rows.append(
            {
                "timestamp_broker": f"2026.05.21 12:{minute:02d}:00",
                "timestamp_utc": f"2026.05.21 08:{minute:02d}:00",
                "timestamp_local": f"2026.05.21 12:{minute:02d}:00",
                "run_id": "phase1-dry-run-v0.5",
                "lifecycle_state": "DRY_RUN",
                "symbol": "XAUUSD",
                "bar_time": f"2026.05.21 12:{minute:02d}:00",
                "session": "LONDON",
                "regime": "BREAKOUT_RETEST",
                "router_version": "phase1_router_v0.5",
                "risk_state": "NORMAL",
                "risk_ok": "true",
                "execution_state": "EXECUTION_OK",
                "news_state": "NO_NEWS_RISK",
                "expert_lifecycle_state": "DRY_RUN_ONLY",
                "magic_namespace_ok": "true",
                "server_time_status": "CLOCK_OK",
                "br_stage": "WAIT_LEVEL_BREAK_RETEST",
                "br_direction": "LONG",
                "br_would_signal": "false",
                "br_reason_code": "no_long_breakout_retest_candidate",
                "br_level_found": "true",
                "br_break_found": "false",
                "br_retest_valid": "false",
                "br_confirmation_valid": "false",
                "br_level_kind": "D1_HIGH",
                "br_level_price": "4505.00",
                "br_entry_price": "0.00",
                "br_stop_loss": "0.00",
                "br_take_profit": "0.00",
                "br_stop_distance_points": "0.00",
                "br_break_shift": "-1",
                "allowed_expert": "none",
                "would_have_allowed_experts": "breakout_retest",
                "trade_permission": force_permission if minute == 0 else "false",
                "block_reason": "phase1_dry_run_only",
                "dry_run": "true",
                "spread_points": "50.00",
                "stale_seconds": "0",
            }
        )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

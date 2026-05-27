from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION_SCHEMA_VERSION = "phase1_decision_schema_v2"
DECISION_SCHEMA_HASH = "ee45252876eff387cd75ddbd350230b15872b18316f0508a24a4a19dcc657e60"


def test_status_summary_writes_machine_readable_snapshot(tmp_path):
    module = _load_module()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv")
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")
    compile_log = tmp_path / "compile.log"
    compile_log.write_text("Result: 0 errors, 0 warnings\n", encoding="utf-8")

    output_path = module.generate_phase1_status_summary(
        files_dir,
        tmp_path / "summary.json",
        compile_log,
        ROOT,
        now=datetime(2026, 5, 21, 16, 12),
    )

    summary = json.loads(output_path.read_text(encoding="utf-8"))
    assert summary["status"]["log_verification"] == "WARN"
    assert summary["status"]["soak_analysis"] == "PASS"
    assert summary["status"]["runtime_health"] == "PASS"
    assert summary["status"]["would_signal"] == "PASS"
    assert summary["status"]["acceptance"] == "PENDING"
    assert summary["runtime"]["decision_rows"] == 3
    assert summary["would_signal"]["rows"] == 2
    assert summary["would_signal"]["clusters"] == 2
    assert summary["would_signal"]["observer_conflicts"]["both_same_direction"] == 1
    assert summary["soak"]["progress_pct"] > 0
    assert summary["soak"]["required_uninterrupted_streak_hours"] == 72.0
    assert summary["soak"]["current_streak_hours"] > 0
    assert summary["soak"]["longest_streak_hours"] > 0
    assert summary["soak"]["active_market_streak_hours"] > 0
    assert summary["soak"]["weekend_policy"] == "weekend_breaks_active_market_streak"
    assert summary["soak"]["process_uptime_streak_hours"] > 0
    assert summary["soak"]["required_code_freeze_hours"] == 96.0
    assert summary["soak"]["code_freeze_started_at"] == ""
    assert summary["soak"]["code_freeze_pass"] is False
    assert summary["soak"]["process_code_freeze_pass"] is False
    assert summary["soak"]["uninterrupted_soak_pass"] is False
    assert summary["soak"]["last_restart_utc"] == "2026-05-21T08:00:00Z"


def _load_module():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    path = scripts_dir / "generate_phase1_status_summary.py"
    spec = importlib.util.spec_from_file_location("generate_phase1_status_summary", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_phase1_status_summary"] = module
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
        "decision_schema_version",
        "decision_schema_hash",
        "decision_schema_rotation_performed",
        "decision_schema_rotation_reason",
        "decision_schema_archive_path",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "timestamp_broker": "2026.05.21 12:00:00",
                "timestamp_utc": "2026.05.21 08:00:00",
                "timestamp_local": "2026.05.21 16:00:00",
                "run_id": "phase1-dry-run-v0.5",
                "symbol": "XAUUSD",
                "dry_run_only": "true",
                "magic_namespace_ok": "true",
                "server_time_status": "CLOCK_OK",
                "decision_schema_version": DECISION_SCHEMA_VERSION,
                "decision_schema_hash": DECISION_SCHEMA_HASH,
                "decision_schema_rotation_performed": "false",
                "decision_schema_rotation_reason": "none",
                "decision_schema_archive_path": "",
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
                "timestamp_local": "2026.05.21 16:15:00",
                "run_id": "phase1-dry-run-v0.5",
                "symbol": "XAUUSD",
                "shutdown_reason": "9",
                "last_m5_bar_time": "2026.05.21 12:10:00",
                "last_decision_write_time": "2026.05.21 12:10:01",
                "lifecycle_state": "DRY_RUN",
            }
        )


def _write_decision_log(path: Path) -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "lifecycle_state",
        "decision_schema_version",
        "decision_schema_hash",
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
        "br_lifecycle_state",
        "sbr_lifecycle_state",
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
        "sbr_stage",
        "sbr_direction",
        "sbr_would_signal",
        "sbr_reason_code",
        "sbr_level_found",
        "sbr_break_found",
        "sbr_retest_valid",
        "sbr_confirmation_valid",
        "sbr_level_kind",
        "sbr_level_price",
        "sbr_entry_price",
        "sbr_stop_loss",
        "sbr_take_profit",
        "sbr_stop_distance_points",
        "sbr_break_shift",
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
        would_signal = minute == 5
        rows.append(
            {
                "timestamp_broker": f"2026.05.21 12:{minute:02d}:00",
                "timestamp_utc": f"2026.05.21 08:{minute:02d}:00",
                "timestamp_local": f"2026.05.21 16:{minute:02d}:00",
                "run_id": "phase1-dry-run-v0.5",
                "lifecycle_state": "DRY_RUN",
                "decision_schema_version": DECISION_SCHEMA_VERSION,
                "decision_schema_hash": DECISION_SCHEMA_HASH,
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
                "br_lifecycle_state": "DRY_RUN_ONLY",
                "sbr_lifecycle_state": "DRY_RUN_ONLY",
                "magic_namespace_ok": "true",
                "server_time_status": "CLOCK_OK",
                "br_stage": "WOULD_SIGNAL" if would_signal else "WAIT_LEVEL_BREAK_RETEST",
                "br_direction": "LONG",
                "br_would_signal": "true" if would_signal else "false",
                "br_reason_code": "dry_run_would_signal" if would_signal else "waiting",
                "br_level_found": "true",
                "br_break_found": "true" if would_signal else "false",
                "br_retest_valid": "true" if would_signal else "false",
                "br_confirmation_valid": "true" if would_signal else "false",
                "br_level_kind": "latest_swing_high",
                "br_level_price": "4515.35",
                "br_entry_price": "4519.82",
                "br_stop_loss": "4514.02",
                "br_take_profit": "4528.52",
                "br_stop_distance_points": "58.00",
                "br_break_shift": "4",
                "sbr_stage": "WOULD_SIGNAL" if would_signal else "WAIT_LEVEL_BREAK_RETEST",
                "sbr_direction": "LONG",
                "sbr_would_signal": "true" if would_signal else "false",
                "sbr_reason_code": "SWING_BREAKOUT_RETEST_LONG_DRY_RUN" if would_signal else "waiting",
                "sbr_level_found": "true",
                "sbr_break_found": "true" if would_signal else "false",
                "sbr_retest_valid": "true" if would_signal else "false",
                "sbr_confirmation_valid": "true" if would_signal else "false",
                "sbr_level_kind": "latest_swing_high",
                "sbr_level_price": "4515.35",
                "sbr_entry_price": "4519.82",
                "sbr_stop_loss": "4514.02",
                "sbr_take_profit": "4528.52",
                "sbr_stop_distance_points": "58.00",
                "sbr_break_shift": "4",
                "allowed_expert": "none",
                "would_have_allowed_experts": "breakout_retest;swing_breakout_retest_v0",
                "trade_permission": "false",
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

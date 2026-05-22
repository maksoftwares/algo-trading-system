from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase1_log_verifier_passes_complete_restart_sample(tmp_path):
    module = _load_log_verifier()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv", rows=2)
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv")

    output = module.verify_phase1_logs(files_dir, tmp_path / "report.md")

    assert output.status == "PASS"
    assert output.report_path.exists()
    assert "LOCKED_DAILY_LOSS" in output.report_path.read_text(encoding="utf-8")


def test_phase1_log_verifier_fails_duplicate_header(tmp_path):
    module = _load_log_verifier()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv", rows=2)
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    decision_path = files_dir / "decision_log.csv"
    _write_decision_log(decision_path)
    first_line = decision_path.read_text(encoding="utf-8").splitlines()[0]
    with decision_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(first_line + "\n")

    output = module.verify_phase1_logs(files_dir, tmp_path / "report.md")

    assert output.status == "FAIL"
    assert any(check.name == "decision_duplicate_headers" and check.status == "FAIL" for check in output.checks)


def test_phase1_log_verifier_fails_permission_true(tmp_path):
    module = _load_log_verifier()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv", rows=2)
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    _write_decision_log(files_dir / "decision_log.csv", force_permission="true")

    output = module.verify_phase1_logs(files_dir, tmp_path / "report.md")

    assert output.status == "FAIL"
    assert any(check.name == "trade_permission_locked" and check.status == "FAIL" for check in output.checks)


def test_phase1_log_verifier_allows_restart_same_bar(tmp_path):
    module = _load_log_verifier()
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    _write_startup_log(files_dir / "startup_log.csv", rows=2)
    _write_shutdown_log(files_dir / "shutdown_log.csv")
    decision_path = files_dir / "decision_log.csv"
    _write_decision_log(decision_path)
    with decision_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = rows[0].keys()
    restart_row = rows[0].copy()
    restart_row["timestamp_broker"] = "2026.05.21 12:01:00"
    restart_row["timestamp_utc"] = "2026.05.21 12:01:00"
    restart_row["timestamp_local"] = "2026.05.21 16:01:00"
    rows.insert(1, restart_row)
    with decision_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    output = module.verify_phase1_logs(files_dir, tmp_path / "report.md")

    assert output.status == "PASS"
    assert any(check.name == "bar_cadence" and check.status == "PASS" for check in output.checks)


def _load_log_verifier():
    path = ROOT / "scripts" / "verify_phase1_logs.py"
    spec = importlib.util.spec_from_file_location("verify_phase1_logs", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_phase1_logs"] = module
    spec.loader.exec_module(module)
    return module


def _write_startup_log(path: Path, rows: int) -> None:
    fieldnames = [
        "timestamp_broker",
        "timestamp_utc",
        "timestamp_local",
        "run_id",
        "symbol",
        "dry_run_only",
        "observe_breakout_retest",
        "max_spread_points",
        "max_risk_pct",
        "daily_loss_limit_pct",
        "weekly_loss_limit_pct",
        "monthly_loss_limit_pct",
        "manual_risk_lock",
        "magic_namespace_ok",
        "server_time_status",
        "broker_utc_offset_seconds",
        "local_utc_offset_seconds",
        "local_clock_drift_seconds",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index in range(rows):
            writer.writerow(
                {
                    "timestamp_broker": f"2026.05.21 12:0{index}:00",
                    "timestamp_utc": f"2026.05.21 12:0{index}:00",
                    "timestamp_local": f"2026.05.21 16:0{index}:00",
                    "run_id": "phase1-dry-run-v0.4",
                    "symbol": "XAUUSD",
                    "dry_run_only": "true",
                    "observe_breakout_retest": "true",
                    "max_spread_points": "80.00",
                    "max_risk_pct": "0.2500",
                    "daily_loss_limit_pct": "2.00",
                    "weekly_loss_limit_pct": "5.00",
                    "monthly_loss_limit_pct": "10.00",
                    "manual_risk_lock": "false",
                    "magic_namespace_ok": "true",
                    "server_time_status": "CLOCK_OK",
                    "broker_utc_offset_seconds": "4",
                    "local_utc_offset_seconds": "14400",
                    "local_clock_drift_seconds": "0",
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
                "timestamp_broker": "2026.05.21 12:10:00",
                "timestamp_utc": "2026.05.21 12:10:00",
                "timestamp_local": "2026.05.21 16:10:00",
                "run_id": "phase1-dry-run-v0.4",
                "symbol": "XAUUSD",
                "shutdown_reason": "9",
                "last_m5_bar_time": "2026.05.21 12:05:00",
                "last_decision_write_time": "2026.05.21 12:05:01",
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
        "regime",
        "router_version",
        "risk_state",
        "requested_risk_pct",
        "max_risk_pct",
        "simulated_daily_pnl_pct",
        "simulated_weekly_pnl_pct",
        "simulated_monthly_pnl_pct",
        "daily_loss_limit_pct",
        "weekly_loss_limit_pct",
        "monthly_loss_limit_pct",
        "manual_risk_lock",
        "risk_ok",
        "execution_state",
        "news_state",
        "expert_lifecycle_state",
        "magic_namespace_ok",
        "server_time_status",
        "broker_utc_offset_seconds",
        "local_utc_offset_seconds",
        "local_clock_drift_seconds",
        "feature_ok",
        "atr14_points",
        "m5_range_points",
        "m5_body_points",
        "m5_upper_wick_points",
        "m5_lower_wick_points",
        "m15_range_points",
        "h1_range_points",
        "compression_state",
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
        "tick_ok",
        "stale_seconds",
        "expert_name",
        "magic_number",
        "direction",
        "entry_price",
        "stop_loss",
        "take_profit",
        "risk_pct",
        "reason_code",
        "blocked_reason",
    ]
    rows = [
        _decision_row("phase1-dry-run-v0.4", "NORMAL", "0.00", "0.00", "0.00", "false", "true", "phase1_dry_run_only"),
        _decision_row("phase1-dry-run-v0.4-daily-lock-test", "LOCKED_DAILY_LOSS", "-2.50", "0.00", "0.00", "false", "false", "LOCKED_DAILY_LOSS"),
        _decision_row("phase1-dry-run-v0.4-weekly-lock-test", "LOCKED_WEEKLY_LOSS", "0.00", "-5.50", "0.00", "false", "false", "LOCKED_WEEKLY_LOSS"),
        _decision_row("phase1-dry-run-v0.4-monthly-lock-test", "LOCKED_MONTHLY_LOSS", "0.00", "0.00", "-10.50", "false", "false", "LOCKED_MONTHLY_LOSS"),
        _decision_row("phase1-dry-run-v0.4-manual-lock-test", "MANUAL_LOCK", "0.00", "0.00", "0.00", "true", "false", "MANUAL_LOCK"),
    ]
    for index, row in enumerate(rows):
        row["timestamp_broker"] = f"2026.05.21 12:{index * 5:02d}:00"
        row["timestamp_utc"] = f"2026.05.21 12:{index * 5:02d}:00"
        row["timestamp_local"] = f"2026.05.21 16:{index * 5:02d}:00"
        row["bar_time"] = f"2026.05.21 12:{index * 5:02d}:00"
    rows[0]["trade_permission"] = force_permission
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _decision_row(
    run_id: str,
    risk_state: str,
    daily: str,
    weekly: str,
    monthly: str,
    manual_lock: str,
    risk_ok: str,
    block_reason: str,
) -> dict[str, str]:
    return {
        "timestamp_broker": "2026.05.21 12:00:00",
        "timestamp_utc": "2026.05.21 12:00:00",
        "timestamp_local": "2026.05.21 16:00:00",
        "run_id": run_id,
        "lifecycle_state": "DRY_RUN",
        "symbol": "XAUUSD",
        "bid": "4500.00",
        "ask": "4500.50",
        "spread_points": "50.00",
        "bar_time": "2026.05.21 12:00:00",
        "session": "LONDON",
        "regime": "BREAKOUT_RETEST",
        "router_version": "phase1_router_v0.4",
        "risk_state": risk_state,
        "requested_risk_pct": "0.2500",
        "max_risk_pct": "0.2500",
        "simulated_daily_pnl_pct": daily,
        "simulated_weekly_pnl_pct": weekly,
        "simulated_monthly_pnl_pct": monthly,
        "daily_loss_limit_pct": "2.00",
        "weekly_loss_limit_pct": "5.00",
        "monthly_loss_limit_pct": "10.00",
        "manual_risk_lock": manual_lock,
        "risk_ok": risk_ok,
        "execution_state": "EXECUTION_OK",
        "news_state": "NO_NEWS_RISK",
        "expert_lifecycle_state": "DRY_RUN_ONLY",
        "magic_namespace_ok": "true",
        "server_time_status": "CLOCK_OK",
        "broker_utc_offset_seconds": "4",
        "local_utc_offset_seconds": "14400",
        "local_clock_drift_seconds": "0",
        "feature_ok": "true",
        "atr14_points": "100.00",
        "m5_range_points": "100.00",
        "m5_body_points": "50.00",
        "m5_upper_wick_points": "25.00",
        "m5_lower_wick_points": "25.00",
        "m15_range_points": "150.00",
        "h1_range_points": "300.00",
        "compression_state": "false",
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
        "sbr_stage": "WAIT_LEVEL_BREAK_RETEST",
        "sbr_direction": "LONG",
        "sbr_would_signal": "false",
        "sbr_reason_code": "no_long_swing_breakout_retest_candidate",
        "sbr_level_found": "true",
        "sbr_break_found": "false",
        "sbr_retest_valid": "false",
        "sbr_confirmation_valid": "false",
        "sbr_level_kind": "latest_swing_high",
        "sbr_level_price": "4505.00",
        "sbr_entry_price": "0.00",
        "sbr_stop_loss": "0.00",
        "sbr_take_profit": "0.00",
        "sbr_stop_distance_points": "0.00",
        "sbr_break_shift": "-1",
        "allowed_expert": "none",
        "would_have_allowed_experts": "breakout_retest;swing_breakout_retest_v0",
        "trade_permission": "false",
        "block_reason": block_reason,
        "dry_run": "true",
        "tick_ok": "true",
        "stale_seconds": "0",
        "expert_name": "breakout_retest",
        "magic_number": "910100",
        "direction": "NONE",
        "entry_price": "0.00",
        "stop_loss": "0.00",
        "take_profit": "0.00",
        "risk_pct": "0.0000",
        "reason_code": "approved_future_expert_reserved",
        "blocked_reason": "phase1_dry_run_only",
    }

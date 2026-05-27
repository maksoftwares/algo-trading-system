from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from migrate_phase1_decision_log_schema import migrate_decision_log_schema
from verify_phase1_logs import DECISION_REQUIRED_COLUMNS, DECISION_SCHEMA_VERSION, EXPECTED_DECISION_SCHEMA_HASH


def test_migrates_archived_rows_to_v2_schema_without_losing_soak_evidence(tmp_path):
    archived_path = tmp_path / "decision_log_archived_old_schema.csv"
    current_path = tmp_path / "decision_log.csv"
    fieldnames = [*DECISION_REQUIRED_COLUMNS, "bid", "ask", "tick_ok"]
    legacy_fieldnames = [
        field
        for field in fieldnames
        if field not in {"decision_schema_version", "decision_schema_hash", "br_lifecycle_state", "sbr_lifecycle_state"}
    ]
    legacy_row = _row(
        bar_time="2026.05.22 11:00:00",
        timestamp_utc="2026.05.22 11:03:44",
        router_version="phase1_router_v0.5",
        schema_version="",
        schema_hash="",
    )
    current_row = _row(
        bar_time="2026.05.27 00:30:00",
        timestamp_utc="2026.05.27 00:31:00",
        router_version="phase1_router_v0.6",
        schema_version=DECISION_SCHEMA_VERSION,
        schema_hash=EXPECTED_DECISION_SCHEMA_HASH,
    )
    _write_csv(archived_path, legacy_fieldnames, [legacy_row])
    _write_csv(current_path, fieldnames, [current_row])

    backup_path = migrate_decision_log_schema(archived_path, current_path)

    assert backup_path.exists()
    rows = _read_csv(current_path)
    assert [row["bar_time"] for row in rows] == ["2026.05.22 11:00:00", "2026.05.27 00:30:00"]
    assert rows[0]["decision_schema_version"] == DECISION_SCHEMA_VERSION
    assert rows[0]["decision_schema_hash"] == EXPECTED_DECISION_SCHEMA_HASH
    assert rows[0]["br_lifecycle_state"] == "DRY_RUN_ONLY"
    assert rows[0]["sbr_lifecycle_state"] == "DRY_RUN_ONLY"
    assert rows[0]["router_version"] == "phase1_router_v0.5"
    assert rows[1]["decision_schema_version"] == DECISION_SCHEMA_VERSION
    assert rows[1]["decision_schema_hash"] == EXPECTED_DECISION_SCHEMA_HASH


def _row(
    *,
    bar_time: str,
    timestamp_utc: str,
    router_version: str,
    schema_version: str,
    schema_hash: str,
) -> dict[str, str]:
    row = {field: "" for field in [*DECISION_REQUIRED_COLUMNS, "bid", "ask", "tick_ok"]}
    row.update(
        {
            "timestamp_broker": timestamp_utc,
            "timestamp_utc": timestamp_utc,
            "timestamp_local": timestamp_utc,
            "run_id": "phase1-dry-run-v0.6",
            "lifecycle_state": "DRY_RUN",
            "decision_schema_version": schema_version,
            "decision_schema_hash": schema_hash,
            "symbol": "XAUUSD",
            "bar_time": bar_time,
            "session": "LONDON",
            "regime": "BREAKOUT_RETEST",
            "router_version": router_version,
            "risk_state": "NORMAL",
            "risk_ok": "true",
            "execution_state": "EXECUTION_OK",
            "news_state": "NO_NEWS_RISK",
            "expert_lifecycle_state": "DRY_RUN_ONLY",
            "br_lifecycle_state": "DRY_RUN_ONLY" if schema_version else "",
            "sbr_lifecycle_state": "DRY_RUN_ONLY" if schema_version else "",
            "magic_namespace_ok": "true",
            "server_time_status": "CLOCK_OK",
            "br_stage": "WAIT_LEVEL_BREAK_RETEST",
            "br_direction": "LONG",
            "br_would_signal": "false",
            "br_reason_code": "no_long_breakout_retest_candidate",
            "br_level_found": "false",
            "br_break_found": "false",
            "br_retest_valid": "false",
            "br_confirmation_valid": "false",
            "br_level_kind": "none",
            "br_level_price": "0.00",
            "br_entry_price": "0.00",
            "br_stop_loss": "0.00",
            "br_take_profit": "0.00",
            "br_stop_distance_points": "0.00",
            "br_break_shift": "-1",
            "sbr_stage": "WAIT_LEVEL_BREAK_RETEST",
            "sbr_direction": "LONG",
            "sbr_would_signal": "false",
            "sbr_reason_code": "no_long_swing_breakout_retest_candidate",
            "sbr_level_found": "false",
            "sbr_break_found": "false",
            "sbr_retest_valid": "false",
            "sbr_confirmation_valid": "false",
            "sbr_level_kind": "none",
            "sbr_level_price": "0.00",
            "sbr_entry_price": "0.00",
            "sbr_stop_loss": "0.00",
            "sbr_take_profit": "0.00",
            "sbr_stop_distance_points": "0.00",
            "sbr_break_shift": "-1",
            "allowed_expert": "none",
            "would_have_allowed_experts": "breakout_retest;swing_breakout_retest_v0",
            "trade_permission": "false",
            "block_reason": "phase1_dry_run_only",
            "dry_run": "true",
            "bid": "4500.00",
            "ask": "4500.50",
            "tick_ok": "true",
        }
    )
    return row


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

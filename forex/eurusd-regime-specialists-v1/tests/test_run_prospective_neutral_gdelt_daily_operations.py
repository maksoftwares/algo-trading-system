from __future__ import annotations

from datetime import date, datetime, timezone

from run_prospective_neutral_gdelt_daily_operations import (
    ScheduledOperation,
    execute_operation,
    next_operation,
    operations_for_entry_date,
    verify_operations_lock,
)


def test_operations_contract_and_weekday_schedule_are_locked() -> None:
    lock = verify_operations_lock()
    assert lock["broker_action_allowed"] is False
    operations = operations_for_entry_date(date(2026, 7, 30))
    assert [row.name for row in operations] == [
        "PREWARM_OWNERSHIP",
        "PREWARM_OWNERSHIP",
        "PREWARM_OWNERSHIP",
        "CAPTURE_GDELT_SOURCE",
        "CAPTURE_NEUTRAL_OWNERSHIP",
        "EVALUATE_FROZEN_DECISION",
        "CAPTURE_CLOSED_TRADE_PATH",
        "VALIDATE_PROSPECTIVE_LEDGER",
    ]
    assert operations[0].due_at_utc.isoformat() == (
        "2026-07-29T21:01:00+00:00"
    )
    assert operations[-1].due_at_utc.isoformat() == (
        "2026-07-30T05:17:00+00:00"
    )
    assert operations_for_entry_date(date(2026, 8, 1)) == []


def test_next_operation_does_not_backfill_past_boundary() -> None:
    selected = next_operation(
        datetime(2026, 7, 29, 5, 25, tzinfo=timezone.utc)
    )
    assert selected.name == "PREWARM_OWNERSHIP"
    assert selected.entry_date_utc == date(2026, 7, 30)
    assert selected.due_at_utc.isoformat() == "2026-07-29T21:01:00+00:00"


def test_late_source_capture_is_skipped_without_network() -> None:
    operation = ScheduledOperation(
        datetime(2026, 7, 30, 0, 1, tzinfo=timezone.utc),
        "CAPTURE_GDELT_SOURCE",
        date(2026, 7, 30),
    )
    result = execute_operation(
        operation,
        now_utc=datetime(2026, 7, 30, 0, 15, 1, tzinfo=timezone.utc),
    )
    assert result["result"]["status"] == (
        "SKIPPED_MISSED_DECISION_DEADLINE_NO_BACKFILL"
    )
    assert result["result"]["network_request_made"] is False
    assert result["historical_eurusd_pnl_loaded"] is False
    assert result["broker_action_allowed"] is False

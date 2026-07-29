from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from run_prospective_neutral_swfx_validation_helper import (
    next_validation_clock,
    validate_and_snapshot,
    verify_operations_lock,
)


def test_validation_schedule_starts_after_first_capture_deadline() -> None:
    lock = verify_operations_lock()
    assert lock["network_request_allowed"] is False
    first = next_validation_clock(
        datetime(2026, 7, 29, 5, 45, tzinfo=timezone.utc)
    )
    assert first.isoformat() == "2026-07-29T06:38:00+00:00"
    next_clock = next_validation_clock(first)
    assert next_clock.isoformat() == "2026-07-29T07:08:00+00:00"


def test_snapshot_is_immutable_and_network_free(tmp_path: Path) -> None:
    result = validate_and_snapshot(
        "2026-07-29T06:38:00Z",
        tmp_path,
        now_utc="2026-07-29T06:38:01Z",
    )
    assert result["validation"]["expected_scheduled_captures_due"] == 1
    assert result["validation"]["immutable_manifests_replayed"] == 0
    assert result["validation"]["maximum_consecutive_failed_scheduled_captures"] == 1
    assert result["network_request_made"] is False
    assert result["broker_action_allowed"] is False
    repeated = validate_and_snapshot(
        "2026-07-29T06:38:00Z",
        tmp_path,
        now_utc="2026-07-29T06:39:00Z",
    )
    assert repeated["snapshot_sha256"] == result["snapshot_sha256"]
    assert repeated["snapshot_reused"] is True


def test_validation_before_clock_does_not_write(tmp_path: Path) -> None:
    result = validate_and_snapshot(
        "2026-07-29T06:38:00Z",
        tmp_path,
        now_utc="2026-07-29T06:37:59Z",
    )
    assert result["status"] == "WAITING_FOR_VALIDATION_CLOCK"
    assert result["network_request_made"] is False
    assert not list(tmp_path.rglob("*"))

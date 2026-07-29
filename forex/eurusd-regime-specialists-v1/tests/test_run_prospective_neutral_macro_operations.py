from __future__ import annotations

from datetime import datetime, timezone
from subprocess import CompletedProcess

import pytest

from run_prospective_neutral_macro_operations import (
    PlannedOperation,
    _validate_command,
    execute_operation,
    next_planned_operation,
    verify_operations_lock,
)


def _plan(stage: str, due_at: str) -> dict:
    return {
        "global_actions": [
            {
                "stage": "OWNERSHIP_CACHE_PREWARM",
                "status": "SCHEDULED",
                "due_at_utc": "2026-07-29T06:01:00Z",
            }
        ],
        "events": [
            {
                "family": "NFP",
                "event_time_utc": "2026-08-07T12:30:00Z",
                "stages": [
                    {
                        "stage": stage,
                        "status": "SCHEDULED",
                        "due_at_utc": due_at,
                    }
                ],
            }
        ],
        "ownership_dependency_gate": {
            "earliest_missing_ownership_date": "2026-08-07"
        },
    }


def test_lock_and_next_cache_operation_are_frozen() -> None:
    lock = verify_operations_lock()
    assert lock["broker_action_allowed"] is False
    operation = next_planned_operation(
        _plan("PRE_RELEASE_FORECAST", "2026-07-29T15:50:54Z")
    )
    assert operation is not None
    assert operation.stage == "OWNERSHIP_CACHE_PREWARM"
    assert operation.execute_at_utc.isoformat() == "2026-07-29T06:01:00+00:00"
    assert "--eligible-date 2026-08-07" in operation.command


def test_forecast_has_network_safety_lead() -> None:
    plan = _plan("PRE_RELEASE_FORECAST", "2026-07-29T15:50:54Z")
    plan["global_actions"] = []
    operation = next_planned_operation(plan)
    assert operation is not None
    assert operation.stage == "PRE_RELEASE_FORECAST"
    assert operation.execute_at_utc.isoformat() == (
        "2026-07-29T15:50:39+00:00"
    )


def test_non_frozen_command_is_rejected() -> None:
    with pytest.raises(RuntimeError, match="Rejected non-frozen"):
        _validate_command("PRE_RELEASE_FORECAST", "python arbitrary.py")


def test_late_forecast_is_skipped_without_a_process() -> None:
    operation = PlannedOperation(
        due_at_utc=datetime(2026, 8, 7, 12, 29, tzinfo=timezone.utc),
        execute_at_utc=datetime(2026, 8, 7, 12, 28, 45, tzinfo=timezone.utc),
        stage="PRE_RELEASE_FORECAST",
        family="NFP",
        event_time_utc=datetime(2026, 8, 7, 12, 30, tzinfo=timezone.utc),
        command=(
            "uv run --offline --with pandas --with numpy --with pyarrow "
            "--with scikit-learn python "
            "capture_prospective_tradingview_consensus.py capture "
            "--days-ahead 60"
        ),
    )

    def fail_if_called(*_args, **_kwargs) -> CompletedProcess[str]:
        raise AssertionError("late forecast must not launch a process")

    result = execute_operation(
        operation,
        now_utc="2026-08-07T12:29:01Z",
        runner=fail_if_called,
    )
    assert result["status"] == "SKIPPED_LATE_FORECAST_NO_BACKFILL"
    assert result["network_request_made"] is False
    assert result["broker_action_allowed"] is False

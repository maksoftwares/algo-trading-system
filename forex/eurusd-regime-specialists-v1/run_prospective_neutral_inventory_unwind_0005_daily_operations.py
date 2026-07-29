from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, time as datetime_time
from datetime import timedelta, timezone
from pathlib import Path
from typing import Any

from capture_prospective_neutral_inventory_unwind_0005 import (
    capture_source,
    evaluate,
    verify_preregistration,
)
from capture_prospective_neutral_inventory_unwind_0005_path import (
    capture_trade_path,
)
from capture_prospective_neutral_oracle_day import capture_oracle_date
from capture_prospective_neutral_ownership import (
    DEFAULT_OUTPUT_ROOT as OWNERSHIP_ROOT,
)
from capture_prospective_neutral_ownership import capture_ownership
from prewarm_prospective_neutral_ownership import prewarm_capture
from validate_prospective_neutral_inventory_unwind_0005 import (
    DEFAULT_ORACLE_ROOT,
    build_validation_status,
)


FIRST_ENTRY_DATE = date(2026, 7, 30)


@dataclass(frozen=True)
class ScheduledOperation:
    due_at_utc: datetime
    name: str
    entry_date_utc: date


def _at(
    day: date,
    hour: int,
    minute: int,
    second: int = 0,
) -> datetime:
    return datetime.combine(
        day,
        datetime_time(hour, minute, second),
        tzinfo=timezone.utc,
    )


def operations_for_entry_date(entry_date: date) -> list[ScheduledOperation]:
    if entry_date.weekday() >= 5 or entry_date < FIRST_ENTRY_DATE:
        return []
    prior = entry_date - timedelta(days=1)
    context_date = entry_date + timedelta(days=1)
    return [
        *[
            ScheduledOperation(
                _at(prior, hour, 2),
                "PREWARM_ENTRY_OWNERSHIP",
                entry_date,
            )
            for hour in (21, 22, 23)
        ],
        ScheduledOperation(
            _at(entry_date, 0, 2, 15),
            "CAPTURE_ENTRY_OWNERSHIP",
            entry_date,
        ),
        ScheduledOperation(
            _at(entry_date, 0, 3),
            "CAPTURE_INVENTORY_SOURCE",
            entry_date,
        ),
        ScheduledOperation(
            _at(entry_date, 0, 4),
            "EVALUATE_FROZEN_DECISION",
            entry_date,
        ),
        ScheduledOperation(
            _at(entry_date, 7, 16),
            "CAPTURE_CLOSED_TRADE_PATH",
            entry_date,
        ),
        ScheduledOperation(
            _at(entry_date, 7, 17),
            "VALIDATE_PROSPECTIVE_LEDGER",
            entry_date,
        ),
        *[
            ScheduledOperation(
                _at(entry_date, hour, 2),
                "PREWARM_ORACLE_CONTEXT",
                entry_date,
            )
            for hour in (21, 22, 23)
        ],
        ScheduledOperation(
            _at(context_date, 0, 2, 15),
            "CAPTURE_ORACLE_CONTEXT",
            entry_date,
        ),
        ScheduledOperation(
            _at(context_date, 12, 2),
            "CAPTURE_COMPLETED_ORACLE_DATE",
            entry_date,
        ),
        ScheduledOperation(
            _at(context_date, 12, 3),
            "VALIDATE_WITH_ORACLE",
            entry_date,
        ),
    ]


def next_operation(after_utc: datetime) -> ScheduledOperation:
    if after_utc.tzinfo is None:
        raise ValueError("Scheduler requires a timezone-aware timestamp")
    after = after_utc.astimezone(timezone.utc)
    candidates: list[ScheduledOperation] = []
    for offset in range(-2, 12):
        entry_date = after.date() + timedelta(days=offset)
        candidates.extend(operations_for_entry_date(entry_date))
    future = [row for row in candidates if row.due_at_utc > after]
    if not future:
        raise RuntimeError("No future inventory-unwind operation found")
    return min(
        future,
        key=lambda row: (
            row.due_at_utc,
            row.entry_date_utc,
            row.name,
        ),
    )


def _safe(value: Any) -> Any:
    if isinstance(value, (datetime, date, Path)):
        return (
            value.isoformat()
            if not isinstance(value, Path)
            else value.as_posix()
        )
    if isinstance(value, dict):
        return {str(key): _safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(item) for item in value]
    return value


def execute_operation(
    operation: ScheduledOperation,
    *,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    verify_preregistration()
    observed = (
        datetime.now(timezone.utc)
        if now_utc is None
        else now_utc.astimezone(timezone.utc)
    )
    entry_day = operation.entry_date_utc
    day_text = entry_day.isoformat()
    if operation.name == "PREWARM_ENTRY_OWNERSHIP":
        result = prewarm_capture(day_text)
    elif operation.name == "CAPTURE_ENTRY_OWNERSHIP":
        deadline = _at(entry_day, 0, 4)
        result = (
            capture_ownership(day_text)
            if observed <= deadline
            else {
                "status": "SKIPPED_LATE_OWNERSHIP_NO_BACKFILL",
                "network_request_made": False,
                "broker_action_allowed": False,
            }
        )
    elif operation.name == "CAPTURE_INVENTORY_SOURCE":
        result = capture_source(day_text)
    elif operation.name == "EVALUATE_FROZEN_DECISION":
        result = evaluate(day_text)
    elif operation.name == "CAPTURE_CLOSED_TRADE_PATH":
        result = capture_trade_path(day_text)
    elif operation.name in (
        "VALIDATE_PROSPECTIVE_LEDGER",
        "VALIDATE_WITH_ORACLE",
    ):
        result = build_validation_status(
            evaluated_at_utc=observed
        )
    elif operation.name == "PREWARM_ORACLE_CONTEXT":
        context = (entry_day + timedelta(days=1)).isoformat()
        result = prewarm_capture(context)
    elif operation.name == "CAPTURE_ORACLE_CONTEXT":
        context = (entry_day + timedelta(days=1)).isoformat()
        result = capture_ownership(context)
    elif operation.name == "CAPTURE_COMPLETED_ORACLE_DATE":
        result = capture_oracle_date(
            day_text,
            oracle_root=DEFAULT_ORACLE_ROOT,
            ownership_root=OWNERSHIP_ROOT,
        )
    else:
        raise ValueError(
            f"Unknown inventory-unwind operation: {operation.name}"
        )
    return _safe(
        {
            "schema_version": (
                "eurusd_neutral_prospective_inventory_operation_v1"
            ),
            "scheduled_operation": asdict(operation),
            "executed_at_utc": observed,
            "result": result,
            "historical_eurusd_pnl_loaded": False,
            "strategy_or_signal_logic_changed": False,
            "broker_action_allowed": False,
        }
    )


def main() -> int:
    lock = verify_preregistration()
    print(
        json.dumps(
            {
                "status": (
                    "PROSPECTIVE_INVENTORY_OPERATIONS_HELPER_STARTED"
                ),
                "started_at_utc": datetime.now(
                    timezone.utc
                ).isoformat(),
                "locked_at_utc": lock["locked_at_utc"],
                "historical_backtest_allowed": False,
                "broker_action_allowed": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    operation = next_operation(datetime.now(timezone.utc))
    while True:
        while True:
            remaining = (
                operation.due_at_utc - datetime.now(timezone.utc)
            ).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 30.0))
        try:
            result = execute_operation(operation)
        except Exception as exc:  # noqa: BLE001
            result = {
                "schema_version": (
                    "eurusd_neutral_prospective_inventory_operation_v1"
                ),
                "scheduled_operation": _safe(asdict(operation)),
                "executed_at_utc": datetime.now(
                    timezone.utc
                ).isoformat(),
                "status": "OPERATION_FAILED_CONTINUING",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "historical_eurusd_pnl_loaded": False,
                "broker_action_allowed": False,
            }
        print(json.dumps(result, sort_keys=True), flush=True)
        operation = next_operation(operation.due_at_utc)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from datetime import time as datetime_time
from pathlib import Path
from typing import Any

from capture_prospective_neutral_gdelt_relative_tone import capture
from capture_prospective_neutral_gdelt_trade_path import capture_trade_path
from capture_prospective_neutral_ownership import capture_ownership
from prewarm_prospective_neutral_ownership import prewarm_capture
from run_prospective_neutral_gdelt_relative_tone import evaluate
from validate_prospective_neutral_gdelt_relative_tone import (
    build_validation_status,
)

ROOT = Path(__file__).resolve().parent
OPERATIONS_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_GDELT_DAILY_OPERATIONS_"
    "2026_07_29.sha256.json"
)
FIRST_ENTRY_DATE = date(2026, 7, 29)


@dataclass(frozen=True)
class ScheduledOperation:
    due_at_utc: datetime
    name: str
    entry_date_utc: date


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_operations_lock() -> dict[str, Any]:
    lock = json.loads(OPERATIONS_LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_first_future_operation") is not True
        or lock.get("strategy_or_signal_logic_changed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("GDELT daily operations lock is incomplete")
    for relative, expected in lock["files"].items():
        if _sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"GDELT daily operations drift: {relative}")
    for reference in lock["existing_frozen_contracts"]:
        if _sha256_file(ROOT / reference["path"]) != reference["sha256"]:
            raise RuntimeError(
                "Referenced frozen GDELT contract or implementation drift"
            )
    return lock


def _at(day: date, hour: int, minute: int) -> datetime:
    return datetime.combine(
        day, datetime_time(hour, minute), tzinfo=timezone.utc
    )


def operations_for_entry_date(entry_date: date) -> list[ScheduledOperation]:
    if entry_date.weekday() >= 5 or entry_date < FIRST_ENTRY_DATE:
        return []
    prior = entry_date - timedelta(days=1)
    return [
        ScheduledOperation(
            _at(prior, hour, 1), "PREWARM_OWNERSHIP", entry_date
        )
        for hour in (21, 22, 23)
    ] + [
        ScheduledOperation(
            _at(entry_date, 0, 1), "CAPTURE_GDELT_SOURCE", entry_date
        ),
        ScheduledOperation(
            _at(entry_date, 0, 2), "CAPTURE_NEUTRAL_OWNERSHIP", entry_date
        ),
        ScheduledOperation(
            _at(entry_date, 0, 15), "EVALUATE_FROZEN_DECISION", entry_date
        ),
        ScheduledOperation(
            _at(entry_date, 5, 16), "CAPTURE_CLOSED_TRADE_PATH", entry_date
        ),
        ScheduledOperation(
            _at(entry_date, 5, 17), "VALIDATE_PROSPECTIVE_LEDGER", entry_date
        ),
    ]


def next_operation(after_utc: datetime) -> ScheduledOperation:
    if after_utc.tzinfo is None:
        raise ValueError("GDELT operations scheduler requires timezone-aware UTC")
    after = after_utc.astimezone(timezone.utc)
    candidates: list[ScheduledOperation] = []
    for offset in range(-1, 10):
        entry_date = after.date() + timedelta(days=offset)
        candidates.extend(operations_for_entry_date(entry_date))
    future = [row for row in candidates if row.due_at_utc > after]
    if not future:
        raise RuntimeError("No future GDELT daily operation found")
    return min(future, key=lambda row: row.due_at_utc)


def _safe_payload(value: Any) -> Any:
    if isinstance(value, (datetime, date, Path)):
        return value.isoformat() if not isinstance(value, Path) else str(value)
    if isinstance(value, dict):
        return {str(key): _safe_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_payload(item) for item in value]
    return value


def execute_operation(
    operation: ScheduledOperation,
    *,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    verify_operations_lock()
    observed = (
        datetime.now(timezone.utc)
        if now_utc is None
        else now_utc.astimezone(timezone.utc)
    )
    day = operation.entry_date_utc.isoformat()
    decision_deadline = _at(operation.entry_date_utc, 0, 15)
    midnight = _at(operation.entry_date_utc, 0, 0)
    if (
        operation.name == "PREWARM_OWNERSHIP"
        and observed >= midnight
    ):
        result: dict[str, Any] = {
            "status": "SKIPPED_LATE_PREWARM",
            "network_request_made": False,
        }
    elif (
        operation.name
        in ("CAPTURE_GDELT_SOURCE", "CAPTURE_NEUTRAL_OWNERSHIP")
        and observed > decision_deadline
    ):
        result = {
            "status": "SKIPPED_MISSED_DECISION_DEADLINE_NO_BACKFILL",
            "network_request_made": False,
        }
    elif operation.name == "PREWARM_OWNERSHIP":
        result = prewarm_capture(day)
    elif operation.name == "CAPTURE_GDELT_SOURCE":
        result = capture(day)
    elif operation.name == "CAPTURE_NEUTRAL_OWNERSHIP":
        result = capture_ownership(day)
    elif operation.name == "EVALUATE_FROZEN_DECISION":
        result = evaluate(day)
    elif operation.name == "CAPTURE_CLOSED_TRADE_PATH":
        result = capture_trade_path(day)
    elif operation.name == "VALIDATE_PROSPECTIVE_LEDGER":
        result = build_validation_status(evaluated_at_utc=observed)
    else:
        raise ValueError(f"Unknown GDELT daily operation: {operation.name}")
    return _safe_payload(
        {
            "schema_version": (
                "eurusd_neutral_prospective_gdelt_daily_operation_v1"
            ),
            "scheduled_operation": asdict(operation),
            "executed_at_utc": observed,
            "result": result,
            "strategy_or_signal_logic_changed": False,
            "historical_eurusd_pnl_loaded": False,
            "broker_action_allowed": False,
        }
    )


def main() -> int:
    lock = verify_operations_lock()
    print(
        json.dumps(
            {
                "status": "GDELT_DAILY_OPERATIONS_HELPER_STARTED",
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "operations_lock_sha256": _sha256_file(
                    OPERATIONS_LOCK_PATH
                ),
                "operations_locked_at_utc": lock["locked_at_utc"],
                "broker_action_allowed": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    anchor = datetime.now(timezone.utc)
    operation = next_operation(anchor)
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
                    "eurusd_neutral_prospective_gdelt_daily_operation_v1"
                ),
                "scheduled_operation": _safe_payload(asdict(operation)),
                "executed_at_utc": datetime.now(timezone.utc).isoformat(),
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

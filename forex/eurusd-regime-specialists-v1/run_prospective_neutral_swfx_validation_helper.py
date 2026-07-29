from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from validate_prospective_neutral_swfx_sentiment_source import (
    DEFAULT_EVIDENCE_ROOT,
    build_validation_status,
)

ROOT = Path(__file__).resolve().parent
OPERATIONS_LOCK_PATH = (
    ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_SWFX_SENTIMENT_VALIDATION_OPERATIONS_"
    "2026_07_29.sha256.json"
)
PROSPECTIVE_START = datetime(2026, 7, 29, 6, 30, tzinfo=timezone.utc)
VALIDATION_MINUTES = (8, 38)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise RuntimeError(
                f"Refusing to overwrite SWFX validation evidence: {path}"
            )


def verify_operations_lock() -> dict[str, Any]:
    lock = json.loads(OPERATIONS_LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_first_census_capture") is not True
        or lock.get("network_request_allowed") is not False
        or lock.get("strategy_or_signal_logic_changed") is not False
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("SWFX validation operations lock is incomplete")
    for relative, expected in lock["files"].items():
        if _sha256_file(ROOT / relative) != expected:
            raise RuntimeError(f"SWFX validation operations drift: {relative}")
    reference = lock["validation_implementation"]
    if _sha256_file(ROOT / reference["path"]) != reference["sha256"]:
        raise RuntimeError("SWFX validation implementation reference drift")
    return lock


def next_validation_clock(after_utc: Any) -> datetime:
    after = _utc(after_utc)
    start = max(after, PROSPECTIVE_START - timedelta(microseconds=1))
    for offset in range(8):
        day = start.date() + timedelta(days=offset)
        if day.weekday() >= 5:
            continue
        for hour in range(24):
            for minute in VALIDATION_MINUTES:
                clock = datetime(
                    day.year,
                    day.month,
                    day.day,
                    hour,
                    minute,
                    tzinfo=timezone.utc,
                )
                if clock > start:
                    return clock
    raise RuntimeError("Unable to find the next SWFX validation clock")


def _existing_snapshot(
    evidence_root: Path, scheduled_validation: datetime
) -> dict[str, Any] | None:
    prefix = scheduled_validation.strftime("STATUS_%Y%m%dT%H%M00Z_")
    matches = sorted(
        (evidence_root / "validation" / "status").glob(f"{prefix}*.json")
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError("Multiple SWFX validation snapshots for one clock")
    path = matches[0]
    payload = path.read_bytes()
    digest = _sha256_bytes(payload)
    if path.name != f"{prefix}{digest[:16]}.json":
        raise RuntimeError("SWFX validation snapshot filename/hash drift")
    result = json.loads(payload)
    if _utc(result["scheduled_validation_utc"]) != scheduled_validation:
        raise RuntimeError("SWFX validation snapshot clock drift")
    return {
        **result,
        "snapshot_relative_path": path.relative_to(
            evidence_root
        ).as_posix(),
        "snapshot_sha256": digest,
        "snapshot_reused": True,
    }


def validate_and_snapshot(
    scheduled_validation_utc: Any,
    evidence_root: Path = DEFAULT_EVIDENCE_ROOT,
    *,
    now_utc: Any | None = None,
) -> dict[str, Any]:
    lock = verify_operations_lock()
    scheduled = _utc(scheduled_validation_utc)
    if (
        scheduled.weekday() >= 5
        or scheduled.minute not in VALIDATION_MINUTES
        or scheduled.second != 0
        or scheduled.microsecond != 0
        or scheduled < PROSPECTIVE_START
    ):
        raise ValueError("Invalid frozen SWFX validation clock")
    observed = (
        datetime.now(timezone.utc) if now_utc is None else _utc(now_utc)
    )
    if observed < scheduled:
        return {
            "schema_version": (
                "eurusd_neutral_swfx_validation_operation_status_v1"
            ),
            "scheduled_validation_utc": scheduled.isoformat(),
            "status": "WAITING_FOR_VALIDATION_CLOCK",
            "network_request_made": False,
            "broker_action_allowed": False,
        }
    existing = _existing_snapshot(evidence_root, scheduled)
    if existing is not None:
        return existing
    validation = build_validation_status(
        evidence_root,
        evaluated_at_utc=scheduled,
    )
    snapshot = {
        "schema_version": (
            "eurusd_neutral_swfx_validation_operation_snapshot_v1"
        ),
        "scheduled_validation_utc": scheduled.isoformat(),
        "operation_observed_at_utc": observed.isoformat(),
        "operations_lock_sha256": _sha256_file(OPERATIONS_LOCK_PATH),
        "operations_locked_at_utc": lock["locked_at_utc"],
        "validation": validation,
        "strategy_or_signal_logic_changed": False,
        "historical_eurusd_pnl_loaded": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }
    payload = _json_bytes(snapshot)
    digest = _sha256_bytes(payload)
    relative = (
        Path("validation")
        / "status"
        / f"STATUS_{scheduled:%Y%m%dT%H%M00Z}_{digest[:16]}.json"
    )
    _write_immutable(evidence_root / relative, payload)
    return {
        **snapshot,
        "snapshot_relative_path": relative.as_posix(),
        "snapshot_sha256": digest,
        "snapshot_reused": False,
    }


def main() -> int:
    lock = verify_operations_lock()
    print(
        json.dumps(
            {
                "status": "SWFX_VALIDATION_HELPER_STARTED",
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "operations_lock_sha256": _sha256_file(
                    OPERATIONS_LOCK_PATH
                ),
                "operations_locked_at_utc": lock["locked_at_utc"],
                "network_request_allowed": False,
                "broker_action_allowed": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    clock = next_validation_clock(datetime.now(timezone.utc))
    while True:
        while True:
            remaining = (
                clock - datetime.now(timezone.utc)
            ).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 30.0))
        try:
            result = validate_and_snapshot(clock)
        except Exception as exc:  # noqa: BLE001
            result = {
                "schema_version": (
                    "eurusd_neutral_swfx_validation_operation_failure_v1"
                ),
                "scheduled_validation_utc": clock.isoformat(),
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "VALIDATION_OPERATION_FAILED_CONTINUING",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "network_request_made": False,
                "broker_action_allowed": False,
            }
        print(json.dumps(result, sort_keys=True), flush=True)
        clock = next_validation_clock(clock)


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import copy
import json
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path

import audit_prospective_neutral_inventory_operations as audit


def _write_lines(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _config(tmp_path: Path) -> dict:
    cfg = copy.deepcopy(audit.load_config())
    for name, component in cfg["components"].items():
        root = tmp_path / name
        component["stdout_globs"] = [(root / "*.stdout.log").as_posix()]
        component["stderr_globs"] = [(root / "*.stderr.log").as_posix()]
        _write_lines(
            root / "operations.stdout.log",
            [
                {
                    "status": component["startup_status"],
                    "started_at_utc": "2026-07-29T12:00:00Z",
                    "locked_at_utc": audit._component_lock_time(name),
                    "historical_backtest_allowed": False,
                    "broker_action_allowed": False,
                }
            ],
        )
        (root / "operations.stderr.log").write_bytes(b"")
    return cfg


def _receipt(operation, *, lag_seconds: int = 0, status: str | None = None) -> dict:
    due = audit._utc(asdict(operation)["due_at_utc"])
    row = {
        "schema_version": "eurusd_neutral_prospective_inventory_operation_v1",
        "scheduled_operation": audit._serialize(operation),
        "executed_at_utc": (due + timedelta(seconds=lag_seconds)).isoformat(),
        "result": {"status": "SOURCE_HOUR_PREWARMED"},
        "historical_eurusd_pnl_loaded": False,
        "strategy_or_signal_logic_changed": False,
        "broker_action_allowed": False,
    }
    if status is not None:
        row["status"] = status
    return row


def _append_primary(cfg: dict, tmp_path: Path, rows: list[dict]) -> None:
    path = tmp_path / "primary_0005" / "operations.stdout.log"
    existing = [json.loads(line) for line in path.read_text().splitlines()]
    _write_lines(path, existing + rows)


def test_contract_freezes_receipt_timing_and_boundaries() -> None:
    cfg = audit.load_config()
    contract = cfg["receipt_contract"]
    assert contract["missing_receipt_grace_seconds"] == 300
    assert contract["maximum_dispatch_lag_seconds"] == 60
    assert contract["duplicate_operation_receipts_forbidden"] is True
    assert cfg["network_requests_by_auditor_forbidden"] is True
    assert cfg["broker_action_allowed"] is False


def test_prestart_clean_startups_are_armed(tmp_path: Path) -> None:
    status = audit.build_status(
        evaluated_at_utc="2026-07-29T12:05:00Z",
        config=_config(tmp_path),
        verify_lock=False,
    )
    assert status["status"] == "ARMED_AWAITING_FIRST_OPERATION"
    assert status["operational_integrity_pass"] is True
    assert status["startup_receipt_is_process_liveness_proof"] is False


def test_exact_due_receipt_is_complete_after_grace(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    operation = audit.primary_ops.operations_for_entry_date(
        audit.date(2026, 7, 30)
    )[0]
    _append_primary(cfg, tmp_path, [_receipt(operation)])
    status = audit.build_status(
        evaluated_at_utc="2026-07-29T21:07:01Z",
        config=cfg,
        verify_lock=False,
    )
    primary = status["components"]["primary_0005"]
    assert status["operational_integrity_pass"] is True
    assert primary["operations_due"] == 1
    assert primary["complete_unique_due_receipts"] == 1


def test_missing_due_receipt_fails_closed(tmp_path: Path) -> None:
    status = audit.build_status(
        evaluated_at_utc="2026-07-29T21:07:01Z",
        config=_config(tmp_path),
        verify_lock=False,
    )
    assert status["status"] == "OPERATIONS_INTEGRITY_FAILURE"
    assert (
        status["components"]["primary_0005"]["issue_counts"]["missing_receipt"] == 1
    )


def test_duplicate_receipt_fails_closed(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    operation = audit.primary_ops.operations_for_entry_date(
        audit.date(2026, 7, 30)
    )[0]
    receipt = _receipt(operation)
    _append_primary(cfg, tmp_path, [receipt, receipt])
    status = audit.build_status(
        evaluated_at_utc="2026-07-29T21:07:01Z",
        config=cfg,
        verify_lock=False,
    )
    assert status["operational_integrity_pass"] is False
    assert (
        status["components"]["primary_0005"]["issue_counts"]["duplicate_receipt"] == 1
    )


def test_late_dispatch_fails_closed(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    operation = audit.primary_ops.operations_for_entry_date(
        audit.date(2026, 7, 30)
    )[0]
    _append_primary(cfg, tmp_path, [_receipt(operation, lag_seconds=61)])
    status = audit.build_status(
        evaluated_at_utc="2026-07-29T21:07:01Z",
        config=cfg,
        verify_lock=False,
    )
    problems = status["components"]["primary_0005"]["receipt_problems"]
    assert problems[0]["problems"] == ["DISPATCH_LATE"]


def test_operation_failure_and_nonempty_stderr_fail_closed(tmp_path: Path) -> None:
    cfg = _config(tmp_path)
    operation = audit.primary_ops.operations_for_entry_date(
        audit.date(2026, 7, 30)
    )[0]
    _append_primary(
        cfg,
        tmp_path,
        [_receipt(operation, status="OPERATION_FAILED_CONTINUING")],
    )
    (tmp_path / "primary_0005" / "operations.stderr.log").write_text(
        "traceback\n",
        encoding="utf-8",
    )
    status = audit.build_status(
        evaluated_at_utc="2026-07-29T21:07:01Z",
        config=cfg,
        verify_lock=False,
    )
    primary = status["components"]["primary_0005"]
    assert primary["issue_counts"]["stderr_nonempty"] == 1
    assert primary["receipt_problems"][0]["problems"] == [
        "OPERATION_FAILED_CONTINUING"
    ]


def test_operation_schema_and_broker_boundary_drift_fail_closed(
    tmp_path: Path,
) -> None:
    cfg = _config(tmp_path)
    operation = audit.primary_ops.operations_for_entry_date(
        audit.date(2026, 7, 30)
    )[0]
    receipt = _receipt(operation)
    receipt["schema_version"] = "changed"
    receipt["broker_action_allowed"] = True
    _append_primary(cfg, tmp_path, [receipt])
    status = audit.build_status(
        evaluated_at_utc="2026-07-29T21:07:01Z",
        config=cfg,
        verify_lock=False,
    )
    assert status["components"]["primary_0005"]["receipt_problems"][0][
        "problems"
    ] == ["OPERATION_SCHEMA_DRIFT", "BROKER_BOUNDARY_DRIFT"]


def test_operations_audit_lock_verifies() -> None:
    lock = audit.verify_preregistration()
    assert lock["locked_before_first_scheduled_operation"] is True
    assert lock["locked_with_zero_operation_receipts"] is True
    assert lock["broker_action_allowed"] is False

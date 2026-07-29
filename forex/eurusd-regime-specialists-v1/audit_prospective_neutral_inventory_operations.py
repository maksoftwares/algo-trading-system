from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta, timezone
from glob import glob
from pathlib import Path
from typing import Any

import prospective_neutral_inventory_clock_transfer as transfer_ops
import run_prospective_neutral_inventory_unwind_0005_daily_operations as primary_ops
import validate_prospective_neutral_inventory_clock_portfolio as portfolio
from eurusd_regime_specialists.research import PACKAGE_ROOT, sha256_file

CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_prospective_neutral_inventory_operations_audit_v1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PROSPECTIVE_INVENTORY_OPERATIONS_AUDIT_"
    "PREREG_2026_07_29.sha256.json"
)

SCHEDULES: dict[str, Callable[[date], list[Any]]] = {
    "primary_0005": primary_ops.operations_for_entry_date,
    "transfer_0605_1205": transfer_ops.operations_for_entry_date,
}


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_preregistration() -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    required = {
        "locked_before_first_scheduled_operation": True,
        "locked_with_zero_operation_receipts": True,
        "locked_with_zero_strategy_decisions": True,
        "locked_with_zero_trade_paths": True,
        "historical_backtest_allowed": False,
        "historical_eurusd_pnl_allowed": False,
        "network_request_allowed": False,
        "broker_action_allowed": False,
    }
    if any(lock.get(key) is not value for key, value in required.items()):
        raise RuntimeError("Operations-audit preregistration is incomplete")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"Operations-audit implementation drift: {relative}")
    portfolio.verify_preregistration()
    return lock


def _utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        result = value
    else:
        text = str(value)
        result = datetime.fromisoformat(
            text[:-1] + "+00:00" if text.endswith("Z") else text
        )
    if result.tzinfo is None:
        raise ValueError("Timestamp must be timezone-aware")
    return result.astimezone(timezone.utc)


def _iso(value: Any) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return _serialize(asdict(value))
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value


def operation_key(value: Any) -> tuple[str, str, str, str, str]:
    row = asdict(value) if is_dataclass(value) else dict(value)
    source_hour = row.get("source_hour_utc")
    return (
        _iso(row["due_at_utc"]),
        str(row["name"]),
        str(row["entry_date_utc"]),
        str(row.get("slot") or ""),
        _iso(source_hour) if source_hour else "",
    )


def _discover(patterns: Sequence[str]) -> list[Path]:
    return sorted({Path(match) for pattern in patterns for match in glob(pattern)})


def _read_json_lines(paths: Sequence[Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(
                {
                    "path": path.as_posix(),
                    "line": None,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    raise ValueError("JSON line is not an object")
            except (json.JSONDecodeError, ValueError) as exc:
                errors.append(
                    {
                        "path": path.as_posix(),
                        "line": line_number,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            payload["_audit_log_path"] = path.as_posix()
            payload["_audit_log_line"] = line_number
            records.append(payload)
    return records, errors


def _scheduled_operations(
    component: str,
    first_entry_date: date,
    evaluated_at_utc: datetime,
) -> list[Any]:
    operation_builder = SCHEDULES[component]
    rows: list[Any] = []
    current = first_entry_date
    final = evaluated_at_utc.date() + timedelta(days=1)
    while current <= final:
        rows.extend(operation_builder(current))
        current += timedelta(days=1)
    return rows


def _latest_startup(
    records: Sequence[Mapping[str, Any]],
    expected_status: str,
) -> Mapping[str, Any] | None:
    candidates = [
        row
        for row in records
        if row.get("status") == expected_status and row.get("started_at_utc")
    ]
    return (
        max(candidates, key=lambda row: _utc(row["started_at_utc"]))
        if candidates
        else None
    )


def _component_lock_time(component: str) -> str:
    lock = (
        primary_ops.verify_preregistration()
        if component == "primary_0005"
        else transfer_ops.verify_preregistration()
    )
    return _iso(lock["locked_at_utc"])


def _receipt_problem(
    receipt: Mapping[str, Any],
    *,
    due_at_utc: datetime,
    expected_schema: str,
    maximum_lag: float,
    maximum_early: float,
    failure_statuses: set[str],
) -> list[str]:
    problems: list[str] = []
    if receipt.get("schema_version") != expected_schema:
        problems.append("OPERATION_SCHEMA_DRIFT")
    executed = _utc(receipt["executed_at_utc"])
    lag = (executed - due_at_utc).total_seconds()
    if lag > maximum_lag:
        problems.append("DISPATCH_LATE")
    if lag < -maximum_early:
        problems.append("DISPATCH_EARLY")
    if receipt.get("status") == "OPERATION_FAILED_CONTINUING":
        problems.append("OPERATION_FAILED_CONTINUING")
    result = receipt.get("result")
    if isinstance(result, Mapping) and result.get("status") in failure_statuses:
        problems.append(str(result["status"]))
    if receipt.get("historical_eurusd_pnl_loaded") is not False:
        problems.append("HISTORICAL_PNL_BOUNDARY_DRIFT")
    if receipt.get("strategy_or_signal_logic_changed") is not False:
        problems.append("STRATEGY_LOGIC_BOUNDARY_DRIFT")
    if receipt.get("broker_action_allowed") is not False:
        problems.append("BROKER_BOUNDARY_DRIFT")
    return problems


def _audit_component(
    component: str,
    component_config: Mapping[str, Any],
    *,
    first_entry_date: date,
    evaluated_at_utc: datetime,
    contract: Mapping[str, Any],
    failure_statuses: set[str],
) -> dict[str, Any]:
    stdout_files = _discover(component_config["stdout_globs"])
    stderr_files = _discover(component_config["stderr_globs"])
    records, parse_errors = _read_json_lines(stdout_files)
    stderr_nonempty = [
        {"path": path.as_posix(), "bytes": path.stat().st_size}
        for path in stderr_files
        if path.stat().st_size > 0
    ]

    startup = _latest_startup(records, str(component_config["startup_status"]))
    startup_problems: list[str] = []
    if startup is None:
        startup_problems.append("MISSING_STARTUP_RECEIPT")
    else:
        if startup.get("historical_backtest_allowed") is not False:
            startup_problems.append("STARTUP_HISTORY_BOUNDARY_DRIFT")
        if startup.get("broker_action_allowed") is not False:
            startup_problems.append("STARTUP_BROKER_BOUNDARY_DRIFT")
        if _iso(startup["locked_at_utc"]) != _component_lock_time(component):
            startup_problems.append("STARTUP_COMPONENT_LOCK_DRIFT")

    scheduled = _scheduled_operations(component, first_entry_date, evaluated_at_utc)
    known = {operation_key(row): row for row in scheduled}
    grace = timedelta(seconds=float(contract["missing_receipt_grace_seconds"]))
    due = {
        key: row
        for key, row in known.items()
        if _utc(asdict(row)["due_at_utc"]) + grace <= evaluated_at_utc
    }

    receipt_index: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    malformed_receipts: list[dict[str, Any]] = []
    for record in records:
        if "scheduled_operation" not in record:
            continue
        try:
            key = operation_key(record["scheduled_operation"])
        except (KeyError, TypeError, ValueError) as exc:
            malformed_receipts.append(
                {
                    "path": record["_audit_log_path"],
                    "line": record["_audit_log_line"],
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        receipt_index[key].append(record)

    missing = [key for key in due if not receipt_index.get(key)]
    duplicates = {
        key: len(rows) for key, rows in receipt_index.items() if len(rows) > 1
    }
    unexpected = [key for key in receipt_index if key not in known]
    receipt_problems: list[dict[str, Any]] = []
    for key, expected in due.items():
        receipts = receipt_index.get(key, [])
        if len(receipts) != 1:
            continue
        problems = _receipt_problem(
            receipts[0],
            due_at_utc=_utc(asdict(expected)["due_at_utc"]),
            expected_schema=str(component_config["operation_schema_version"]),
            maximum_lag=float(contract["maximum_dispatch_lag_seconds"]),
            maximum_early=float(contract["maximum_dispatch_early_seconds"]),
            failure_statuses=failure_statuses,
        )
        if problems:
            receipt_problems.append(
                {
                    "operation": list(key),
                    "problems": problems,
                    "path": receipts[0]["_audit_log_path"],
                    "line": receipts[0]["_audit_log_line"],
                }
            )

    issue_counts = Counter(
        {
            "startup": len(startup_problems),
            "stdout_parse": len(parse_errors),
            "stderr_nonempty": len(stderr_nonempty),
            "malformed_receipt": len(malformed_receipts),
            "missing_receipt": len(missing),
            "duplicate_receipt": len(duplicates),
            "unexpected_receipt": len(unexpected),
            "receipt_boundary_or_timing": len(receipt_problems),
        }
    )
    clean = sum(issue_counts.values()) == 0
    next_operation = (
        primary_ops.next_operation(evaluated_at_utc)
        if component == "primary_0005"
        else transfer_ops.next_operation(evaluated_at_utc)
    )
    return {
        "component": component,
        "clean": clean,
        "stdout_files": [path.as_posix() for path in stdout_files],
        "stderr_files": [path.as_posix() for path in stderr_files],
        "startup_receipts": sum(
            row.get("status") == component_config["startup_status"] for row in records
        ),
        "latest_startup_at_utc": (
            _iso(startup["started_at_utc"]) if startup is not None else None
        ),
        "expected_operation_schema_version": component_config[
            "operation_schema_version"
        ],
        "startup_problems": startup_problems,
        "scheduled_receipts_observed": sum(len(rows) for rows in receipt_index.values()),
        "operations_due": len(due),
        "complete_unique_due_receipts": sum(
            len(receipt_index.get(key, [])) == 1 for key in due
        ),
        "missing_operations": [list(key) for key in missing],
        "duplicate_operations": [
            {"operation": list(key), "receipts": count}
            for key, count in duplicates.items()
        ],
        "unexpected_operations": [list(key) for key in unexpected],
        "receipt_problems": receipt_problems,
        "stdout_parse_errors": parse_errors,
        "malformed_receipts": malformed_receipts,
        "nonempty_stderr": stderr_nonempty,
        "issue_counts": dict(issue_counts),
        "next_operation": _serialize(next_operation),
    }


def build_status(
    *,
    evaluated_at_utc: Any | None = None,
    config: Mapping[str, Any] | None = None,
    verify_lock: bool = True,
) -> dict[str, Any]:
    if verify_lock:
        verify_preregistration()
    cfg = dict(load_config() if config is None else config)
    evaluated = (
        datetime.now(timezone.utc)
        if evaluated_at_utc is None
        else _utc(evaluated_at_utc)
    )
    first_entry = date.fromisoformat(str(cfg["first_entry_date_utc"]))
    contract = cfg["receipt_contract"]
    failure_statuses = set(cfg["fail_closed_result_statuses"])
    components = {
        name: _audit_component(
            name,
            component_cfg,
            first_entry_date=first_entry,
            evaluated_at_utc=evaluated,
            contract=contract,
            failure_statuses=failure_statuses,
        )
        for name, component_cfg in cfg["components"].items()
    }
    clean = all(row["clean"] for row in components.values())
    first_due = min(
        _utc(row["first_scheduled_operation_utc"])
        for row in cfg["components"].values()
    )
    if not clean:
        status = "OPERATIONS_INTEGRITY_FAILURE"
    elif evaluated < first_due:
        status = "ARMED_AWAITING_FIRST_OPERATION"
    else:
        status = "ACCUMULATING_WITH_COMPLETE_OPERATION_RECEIPTS"
    return {
        "schema_version": cfg["schema_version"],
        "status": status,
        "evaluated_at_utc": _iso(evaluated),
        "first_scheduled_operation_utc": _iso(first_due),
        "operational_integrity_pass": clean,
        "components": components,
        "startup_receipt_is_process_liveness_proof": False,
        "external_process_liveness_check_required_before_first_operation": True,
        "research_review_allowed": False,
        "controlled_demo_ready": False,
        "historical_eurusd_pnl_loaded": False,
        "network_request_made": False,
        "broker_action_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("status",))
    return parser.parse_args()


def main() -> int:
    parse_args()
    status = build_status()
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["operational_integrity_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

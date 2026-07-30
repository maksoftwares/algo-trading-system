from __future__ import annotations

import json
import math
import sys
import time
from collections.abc import Callable
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import prospective_neutral_inventory_clock_transfer as frozen


def json_safe(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


def execute_safely(
    operation: Any,
    *,
    executor: Callable[..., dict[str, Any]] = frozen.execute_operation,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    observed = datetime.now(timezone.utc) if now_utc is None else now_utc
    try:
        result = executor(operation, now_utc=observed)
        return json_safe(result)
    except Exception as exc:  # noqa: BLE001
        return {
            "schema_version": (
                "eurusd_neutral_prospective_inventory_clock_operation_v1"
            ),
            "scheduled_operation": json_safe(operation),
            "executed_at_utc": observed.isoformat(),
            "status": "OPERATION_FAILED_CONTINUING",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "historical_eurusd_pnl_loaded": False,
            "strategy_or_signal_logic_changed": False,
            "broker_action_allowed": False,
        }


def run_operations() -> int:
    lock = frozen.verify_preregistration()
    print(
        json.dumps(
            {
                "status": (
                    "PROSPECTIVE_INVENTORY_CLOCK_SAFE_WRAPPER_STARTED"
                ),
                "started_at_utc": datetime.now(timezone.utc).isoformat(),
                "locked_at_utc": lock["locked_at_utc"],
                "frozen_strategy_source_changed": False,
                "historical_backtest_allowed": False,
                "individual_clock_selection_allowed": False,
                "broker_action_allowed": False,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    operation = frozen.next_operation(datetime.now(timezone.utc))
    while True:
        while True:
            remaining = (
                operation.due_at_utc - datetime.now(timezone.utc)
            ).total_seconds()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 30.0))
        result = execute_safely(operation)
        print(json.dumps(result, sort_keys=True), flush=True)
        operation = frozen.next_operation(operation.due_at_utc)


if __name__ == "__main__":
    raise SystemExit(run_operations())

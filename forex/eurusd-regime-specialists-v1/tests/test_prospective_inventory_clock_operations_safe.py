from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from run_prospective_inventory_clock_operations_safe import (
    execute_safely,
    json_safe,
)


def test_json_safe_handles_nested_operation_types() -> None:
    observed = datetime(2026, 7, 30, 8, tzinfo=UTC)
    value = {
        "datetime": observed,
        "date": date(2026, 7, 30),
        "timestamp": pd.Timestamp(observed),
        "path": Path("evidence/file.json"),
        "integer": np.int64(4),
        "items": [np.float64(1.25)],
    }
    safe = json_safe(value)
    assert safe["datetime"] == "2026-07-30T08:00:00+00:00"
    assert safe["date"] == "2026-07-30"
    assert safe["timestamp"] == "2026-07-30T08:00:00+00:00"
    assert safe["path"] == "evidence/file.json"
    assert safe["integer"] == 4
    assert safe["items"] == [1.25]


def test_safe_wrapper_preserves_fail_closed_boundary() -> None:
    observed = datetime(2026, 7, 30, 8, tzinfo=UTC)

    def failing_executor(operation, *, now_utc):
        assert operation == {"name": "TEST"}
        assert now_utc == observed
        raise RuntimeError("expected test failure")

    result = execute_safely(
        {"name": "TEST"},
        executor=failing_executor,
        now_utc=observed,
    )
    assert result["status"] == "OPERATION_FAILED_CONTINUING"
    assert result["strategy_or_signal_logic_changed"] is False
    assert result["broker_action_allowed"] is False

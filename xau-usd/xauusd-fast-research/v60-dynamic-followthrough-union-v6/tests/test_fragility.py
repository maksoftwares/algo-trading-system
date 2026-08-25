from __future__ import annotations

import math
from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_experiment import upper_binomial_tail, veto_fragility_metrics


def test_upper_binomial_tail_is_exact() -> None:
    assert math.isclose(upper_binomial_tail(12, 13), 14 / 8192)
    assert upper_binomial_tail(0, 0) is None


def test_veto_fragility_clusters_months_and_removes_largest_benefit() -> None:
    rows = pd.DataFrame(
        [
            {
                "trade_id": "a",
                "entry_time_utc": "2026-01-01T00:00:00Z",
                "baseline_runtime_executed": True,
                "baseline_runtime_pnl_usd": -10.0,
            },
            {
                "trade_id": "b",
                "entry_time_utc": "2026-01-02T00:00:00Z",
                "baseline_runtime_executed": True,
                "baseline_runtime_pnl_usd": 2.0,
            },
            {
                "trade_id": "c",
                "entry_time_utc": "2026-02-01T00:00:00Z",
                "baseline_runtime_executed": True,
                "baseline_runtime_pnl_usd": -4.0,
            },
            {
                "trade_id": "not-executed",
                "entry_time_utc": "2026-03-01T00:00:00Z",
                "baseline_runtime_executed": False,
                "baseline_runtime_pnl_usd": None,
            },
        ]
    )

    result = veto_fragility_metrics(rows)

    assert result["executed_vetoes"] == 3
    assert result["beneficial_vetoes"] == 2
    assert result["harmful_vetoes"] == 1
    assert result["active_months"] == 2
    assert result["beneficial_months"] == 2
    assert result["harmful_months"] == 0
    assert result["avoided_pnl_usd"] == 12.0
    assert result["avoided_pnl_after_removing_largest_benefit_usd"] == 2.0
    assert result["evidence_status"].startswith("RETROSPECTIVE")


def test_veto_fragility_rejects_duplicate_executed_ids() -> None:
    rows = pd.DataFrame(
        [
            {
                "trade_id": "duplicate",
                "entry_time_utc": "2026-01-01T00:00:00Z",
                "baseline_runtime_executed": True,
                "baseline_runtime_pnl_usd": -1.0,
            },
            {
                "trade_id": "duplicate",
                "entry_time_utc": "2026-02-01T00:00:00Z",
                "baseline_runtime_executed": True,
                "baseline_runtime_pnl_usd": -1.0,
            },
        ]
    )

    try:
        veto_fragility_metrics(rows)
    except ValueError as error:
        assert "unique" in str(error)
    else:
        raise AssertionError("Duplicate executed veto IDs were accepted")

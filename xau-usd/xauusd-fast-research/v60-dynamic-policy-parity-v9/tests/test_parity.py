from __future__ import annotations

import pandas as pd
import numpy as np
from types import SimpleNamespace

from src.parity import (
    annual_comparison,
    closed_metrics,
    exact_set_difference,
    fixed_lifecycle_equity_drawdown,
    replacement_capacity_count,
)


def test_closed_metrics_and_annual_comparison() -> None:
    baseline = pd.DataFrame(
        {
            "entry_time_utc": ["2024-01-01T00:00:00Z", "2025-01-01T00:00:00Z"],
            "pnl_usd": [10.0, -4.0],
        }
    )
    challenger = baseline.iloc[[0]].copy()
    metrics = closed_metrics(baseline)
    assert metrics["net_pnl_usd"] == 6.0
    assert metrics["profit_factor"] == 2.5
    assert metrics["closed_drawdown_usd"] == 4.0
    annual = annual_comparison(baseline, challenger)
    assert annual[0]["delta_pnl_usd"] == 0.0
    assert annual[1]["delta_pnl_usd"] == 4.0


def test_replacement_capacity_and_set_difference_are_explicit() -> None:
    assert replacement_capacity_count(100, 5, 98) == 3
    assert exact_set_difference(["a", "b"], ["b", "c"]) == {
        "missing": ["a"],
        "unexpected": ["c"],
    }


def test_fixed_lifecycle_equity_marks_pre_and_post_events() -> None:
    candidate = SimpleNamespace(
        trade_id="t1",
        direction="LONG",
        entry_price=100.0,
        open_cost_usd=1.0,
    )
    events = [
        {
            "event": "ORDER_FILLED",
            "trade_id": "t1",
            "timestamp_utc": "1970-01-01T00:00:01Z",
            "basis_offset": 0.0,
        },
        {
            "event": "POSITION_CLOSED",
            "trade_id": "t1",
            "timestamp_utc": "1970-01-01T00:00:02Z",
            "pnl_usd": 9.0,
        },
    ]
    quotes = {
        "cycle_ms": np.asarray([1000, 2000], dtype=np.int64),
        "bid": np.asarray([100.0, 110.0]),
        "ask": np.asarray([101.0, 111.0]),
    }
    assert fixed_lifecycle_equity_drawdown(
        [candidate], events, quotes, ["t1"], starting_equity_usd=1000.0
    ) == 1.0
    assert fixed_lifecycle_equity_drawdown(
        [candidate], events, quotes, [], starting_equity_usd=1000.0
    ) == 0.0

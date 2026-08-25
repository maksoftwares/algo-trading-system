from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from run_experiment import apply_august_management, closed_metrics


POLICY = {
    "enabled": True,
    "arm_r": 1.5,
    "retain_r": 0.25,
    "giveback_r": None,
}


def test_august_management_uses_executable_side_and_preserves_entry_count() -> None:
    trades = pd.DataFrame(
        [
            {
                "candidate_id": "long",
                "broker_entry_ms": 0,
                "broker_exit_ms": 20_000,
                "direction": "LONG",
                "entry_price": 100.0,
                "entry_cost_usd": 0.0,
                "initial_risk_usd": 10.0,
                "volume_lots": 0.01,
                "broker_pnl_usd": -10.0,
            }
        ]
    )
    quotes = pd.DataFrame(
        {
            "cycle_ms": [5_000, 10_000, 15_000],
            "bid": [115.0, 110.0, 102.0],
            "ask": [115.2, 110.2, 102.2],
        }
    )
    managed = apply_august_management(trades, quotes, POLICY)
    assert len(managed) == 1
    assert bool(managed.iloc[0]["managed_close"])
    assert managed.iloc[0]["pnl_usd"] == 2.0
    assert managed.iloc[0]["close_ms"] == 15_000


def test_closed_metrics_orders_by_managed_close_time() -> None:
    frame = pd.DataFrame(
        [
            {"candidate_id": "later", "close_ms": 2, "pnl_usd": 5.0},
            {"candidate_id": "first", "close_ms": 1, "pnl_usd": -2.0},
        ]
    )
    result = closed_metrics(frame)
    assert result["net_pnl_usd"] == 3.0
    assert result["closed_drawdown_usd"] == 2.0

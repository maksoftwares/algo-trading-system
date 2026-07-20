from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from dataset import label_action  # noqa: E402
from evaluation import attempt_policies, model_specifications  # noqa: E402


def execution() -> dict[str, float | str]:
    return {
        "maximum_entry_gap_minutes": 10,
        "maximum_entry_spread_r": 0.20,
        "maximum_research_risk_usd": 50.0,
        "current_account_risk_usd": 10.0,
        "ounces_at_lot_size": 1.0,
        "extra_execution_cost_usd": 0.0,
        "holding_cost_per_24h_usd": 0.0,
        "stress_slippage_r": 0.0,
        "same_bar_priority": "STOP_FIRST",
    }


def arrays() -> dict[str, np.ndarray]:
    starts = np.array(
        ["2026-01-05T00:00", "2026-01-05T00:05", "2026-01-05T00:10"],
        dtype="datetime64[m]",
    )
    return {
        "starts": starts,
        "ends": starts + np.timedelta64(5, "m"),
        "bid_open": np.array([99.9, 100.0, 100.0]),
        "bid_high": np.array([100.0, 102.0, 100.2]),
        "bid_low": np.array([99.8, 98.0, 99.8]),
        "bid_close": np.array([99.9, 100.0, 100.0]),
        "ask_open": np.array([100.0, 100.1, 100.1]),
        "ask_high": np.array([100.1, 102.1, 100.3]),
        "ask_low": np.array([99.9, 98.1, 99.9]),
        "ask_close": np.array([100.0, 100.1, 100.1]),
    }


def test_label_enters_at_signal_time_and_scores_ambiguous_bar_stop_first() -> None:
    row = SimpleNamespace(
        signal_time=pd.Timestamp("2026-01-05T00:05:00Z"),
        direction="LONG",
        atr_m5=1.0,
    )
    action = {
        "action_id": "FAST_1R_4H",
        "stop_atr": 1.0,
        "minimum_stop_usd": 0.0,
        "target_r": 1.0,
        "maximum_hold_hours": 4.0,
    }
    result = label_action(arrays(), row, action, execution())
    assert result is not None
    assert result["entry_time"] == pd.Timestamp("2026-01-05T00:05:00Z")
    assert result["entry_price"] == 100.1
    assert result["exit_reason"] == "AMBIGUOUS_M5_STOP_FIRST"
    assert result["net_r"] == -1.0


def test_label_rejects_entry_gap_beyond_lock() -> None:
    row = SimpleNamespace(
        signal_time=pd.Timestamp("2026-01-04T23:00:00Z"),
        direction="LONG",
        atr_m5=1.0,
    )
    action = {
        "action_id": "FAST_1R_4H",
        "stop_atr": 1.0,
        "minimum_stop_usd": 0.0,
        "target_r": 1.0,
        "maximum_hold_hours": 4.0,
    }
    assert label_action(arrays(), row, action, execution()) is None


def test_search_budget_is_exact_and_model_specs_are_unique() -> None:
    search = {
        "model_specifications": 125,
        "score_quantiles": [0.30, 0.40, 0.50, 0.60],
        "score_floors": [None, 0.0],
    }
    policies = attempt_policies(search)
    specs = model_specifications(125, 314159)
    assert len(policies) == 1000
    assert len({policy.attempt_id for policy in policies}) == 1000
    assert len(specs) == 125
    assert len({spec["model_id"] for spec in specs}) == 125

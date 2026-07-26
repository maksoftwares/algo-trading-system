from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))

from step_4_bootstrap import primary_block_bootstrap  # noqa: E402
from step_4_metrics import (  # noqa: E402
    choose_threshold,
    economic_metrics,
    weighted_max_drawdown,
)


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": ["A", "B", "C", "D"],
            "structural_episode_id": ["E1", "E2", "E3", "E4"],
            "decision_time": pd.to_datetime(
                [
                    "2025-01-06T00:00Z",
                    "2025-01-07T00:00Z",
                    "2025-01-13T00:00Z",
                    "2025-01-14T00:00Z",
                ]
            ),
            "structural_weight": [1.0, 1.0, 1.0, 1.0],
            "stress_net_r": [1.0, -1.0, 2.0, -0.5],
            "target": [1, 0, 1, 0],
            "probability": [0.8, 0.2, 0.7, 0.3],
            "selected": [True, False, True, False],
        }
    )


def test_threshold_policy_cannot_select_a_tiny_tail() -> None:
    frame = _frame()
    policy = {
        "minimum_selected_rows": 2,
        "minimum_selected_fraction": 0.5,
        "candidate_probability_thresholds": [0.0, 0.75, 0.9],
    }
    threshold, audit = choose_threshold(frame, policy)
    assert threshold == 0.0
    assert [row["eligible"] for row in audit] == [True, False, False]


def test_weighted_drawdown_and_frequency_are_candidate_quality_metrics() -> None:
    frame = _frame()
    assert weighted_max_drawdown(frame) == 1.0
    metrics = economic_metrics(frame, frame["selected"], weekdays=10)
    assert metrics["rows"] == 2
    assert metrics["weighted_profit_factor"] is None
    assert metrics["raw_candidates_per_weekday"] == 0.2


def test_block_bootstrap_is_deterministic() -> None:
    contract = {
        "bootstrap": {
            "resamples": 100,
            "seed": 60104,
            "block_weekdays": 5,
            "confidence": 0.95,
        }
    }
    first = primary_block_bootstrap(_frame(), contract)
    second = primary_block_bootstrap(_frame(), contract)
    assert first == second
    assert first["weighted_roc_auc"]["lower"] == 1.0
    assert np.isfinite(first["selected_weighted_mean_stress_r"]["lower"])

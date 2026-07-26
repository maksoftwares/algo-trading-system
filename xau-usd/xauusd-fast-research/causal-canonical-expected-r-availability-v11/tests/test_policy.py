from __future__ import annotations

import numpy as np
import pandas as pd

from policy import apply_availability, bootstrap_statistics


def predictions() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": ["A", "B", "C", "D"],
            "fold_id": ["F1", "F1", "F2", "F2"],
            "family_id": ["X", "X", "X", "X"],
            "selected": [False, True, False, True],
            "model_score": [0.1, 0.9, 0.1, 0.9],
            "threshold": [0.5] * 4,
            "structural_weight": [1.0] * 4,
            "stress_net_r": [-1.0, 1.0, -1.0, 1.0],
            "stress_net_r_positive": [False, True, False, True],
            "structural_episode_id": ["E1", "E2", "E3", "E4"],
            "decision_time": pd.date_range("2025-01-01", periods=4, freq="D", tz="UTC"),
        }
    )


def test_unavailable_fold_abstains_and_retains_all() -> None:
    folds = pd.DataFrame({"fold_id": ["F1", "F2"], "fit_rows": [999, 1000]})
    result = apply_availability(predictions(), folds, minimum_fit_rows=1000)
    assert result.loc[result["fold_id"].eq("F1"), "selected"].all()
    assert result.loc[result["fold_id"].eq("F2"), "selected"].tolist() == [
        False,
        True,
    ]


def test_v10_selection_is_preserved() -> None:
    folds = pd.DataFrame({"fold_id": ["F1", "F2"], "fit_rows": [999, 1000]})
    result = apply_availability(predictions(), folds, minimum_fit_rows=1000)
    assert result["v10_selected"].tolist() == [False, True, False, True]


def test_bootstrap_statistics_match_manual_values() -> None:
    frame = predictions()
    values = bootstrap_statistics(frame)
    assert np.allclose(values[:3], [1.0, 0.0, 1.0])
    assert values[3] == float("inf")
    assert values[4] == 0.5

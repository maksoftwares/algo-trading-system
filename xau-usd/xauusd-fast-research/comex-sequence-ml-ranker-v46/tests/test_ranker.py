from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ranker import MODEL_FEATURES, build_model, prepare_matrix, select_threshold  # noqa: E402


def _candidates(rows: int = 8) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": [f"c{index}" for index in range(rows)],
            "feature_time_utc": pd.date_range(
                "2024-01-02T13:30:00Z", periods=rows, freq="1D"
            ),
            "direction": ["LONG", "SHORT"] * (rows // 2),
            "current_trade_count_5s": np.arange(rows) + 30,
            "prior_trade_count_30s": np.arange(rows) + 100,
            "current_volume_5s": np.arange(rows) + 40,
            "current_imbalance_5s": np.linspace(-0.8, 0.8, rows),
            "same_side_transition_share_5s": np.linspace(0.7, 0.9, rows),
            "arrival_acceleration": np.linspace(1.3, 3.0, rows),
            "terminal_run_trades": np.arange(rows) + 5,
            "terminal_run_volume": np.arange(rows) + 10,
            "current_directional_impulse_ticks": np.arange(rows) + 1,
            "terminal_run_sign": [1, -1] * (rows // 2),
        }
    )


def test_matrix_contains_only_locked_candidate_time_features() -> None:
    matrix = prepare_matrix(_candidates())
    assert list(matrix.columns) == MODEL_FEATURES
    assert np.isfinite(matrix.to_numpy()).all()
    assert not any(
        "pnl" in name or "label" in name or "exit" in name for name in matrix.columns
    )


def test_threshold_selection_uses_score_density_and_balance() -> None:
    candidates = _candidates()
    scores = np.linspace(0.1, 0.8, len(candidates))
    selection = {
        "minimum_candidates_per_full_weekday": 0.5,
        "maximum_candidates_per_full_weekday": 0.75,
        "target_candidates_per_full_weekday": 0.625,
        "minimum_active_day_share": 0.5,
        "minimum_minority_direction_share": 0.3,
    }
    selected = select_threshold(
        candidates,
        scores,
        eligible_dates=[f"d{i}" for i in range(8)],
        selection=selection,
    )
    assert selected is not None
    threshold, facts = selected
    assert threshold in scores
    assert 4 <= facts["accepted_candidates"] <= 6


def test_fixed_model_is_deterministic() -> None:
    config = {
        "model": {
            "learning_rate": 0.05,
            "max_iter": 20,
            "max_leaf_nodes": 3,
            "min_samples_leaf": 2,
            "l2_regularization": 1.0,
            "early_stopping": False,
            "random_state": 460046,
        }
    }
    matrix = prepare_matrix(_candidates())
    target = np.array([0, 1] * 4)
    first = build_model(config).fit(matrix, target).predict_proba(matrix)
    second = build_model(config).fit(matrix, target).predict_proba(matrix)
    np.testing.assert_array_equal(first, second)

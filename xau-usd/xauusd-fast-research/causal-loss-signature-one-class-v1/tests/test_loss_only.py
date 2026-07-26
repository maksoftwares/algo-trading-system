from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.loss_only import (  # noqa: E402
    fit_loss_model,
    loss_veto_metrics,
    partition_for,
    weighted_quantile,
)


def test_weighted_quantile_respects_weights() -> None:
    values = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 8.0, 1.0])
    assert weighted_quantile(values, weights, 0.5) == 2.0


def test_loss_model_refuses_winner_rows() -> None:
    frame = pd.DataFrame(
        {
            "x": [0.0, 1.0],
            "stress_net_r_positive": [False, True],
            "structural_weight": [1.0, 1.0],
        }
    )
    with pytest.raises(ValueError, match="Winning rows"):
        fit_loss_model(
            frame,
            features=["x"],
            model_config={
                "kind": "ISOLATION_FOREST",
                "n_estimators": 5,
                "max_samples": 2,
                "max_features": 1.0,
                "bootstrap": False,
                "contamination": "auto",
                "random_state": 1,
                "n_jobs": 1,
            },
        )


def test_partition_preserves_whole_structural_episodes() -> None:
    frame = pd.DataFrame(
        {
            "candidate_id": ["a", "b", "c"],
            "structural_episode_id": ["e1", "e1", "e2"],
            "signal_time": pd.to_datetime(
                ["2020-01-01", "2020-01-01", "2020-01-02"], utc=True
            ),
        }
    )
    splits = pd.DataFrame(
        {
            "fold_id": ["F1", "F1"],
            "structural_episode_id": ["e1", "e2"],
            "partition": ["FIT", "TEST"],
            "eligible": [True, True],
        }
    )
    selected = partition_for(frame, splits, fold_id="F1", partition="FIT")
    assert selected["candidate_id"].tolist() == ["a", "b"]


def test_loss_veto_metrics_measure_precision_and_collateral() -> None:
    frame = pd.DataFrame(
        {
            "candidate_id": ["a", "b", "c", "d"],
            "signal_time": pd.to_datetime(
                ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"],
                utc=True,
            ),
            "stress_net_r_positive": [False, False, True, True],
            "stress_net_r": [-1.0, -1.0, 1.0, 1.0],
            "structural_weight": [1.0, 1.0, 1.0, 1.0],
            "loss_similarity": [0.9, 0.8, 0.2, 0.1],
        }
    )
    metrics = loss_veto_metrics(frame, np.array([True, False, False, False]))
    assert metrics["flagged_loss_precision"] == 1.0
    assert metrics["loss_recall"] == 0.5
    assert metrics["winner_collateral_rate"] == 0.0
    assert metrics["retained_ev_lift_r"] == pytest.approx(1.0 / 3.0)

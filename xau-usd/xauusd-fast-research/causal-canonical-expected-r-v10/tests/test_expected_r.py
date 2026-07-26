from __future__ import annotations

import numpy as np
import pandas as pd

from src.expected_r import (
    PartialPoolingExpectedR,
    apply_thresholds,
    calibration_thresholds,
    comparison_metrics,
    weighted_quantile,
)


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": [f"C{index}" for index in range(12)],
            "family_id": ["A"] * 6 + ["B"] * 6,
            "x1": np.arange(12, dtype=float),
            "x2": [np.nan, 1.0, 2.0, 3.0, 4.0, 5.0] * 2,
            "stress_net_r": [-1.0, -0.5, 0.2, 0.5, 1.0, 1.5] * 2,
            "stress_net_r_positive": [False, False, True, True, True, True] * 2,
            "structural_weight": [1.0] * 12,
            "structural_episode_id": [f"E{index}" for index in range(12)],
            "decision_time": pd.date_range(
                "2025-01-01", periods=12, freq="D", tz="UTC"
            ),
        }
    )


def test_weighted_quantile_respects_weights() -> None:
    assert weighted_quantile([1.0, 2.0, 3.0], [1.0, 8.0, 1.0], 0.3) == 2.0


def test_partial_pooling_fit_and_design_are_deterministic() -> None:
    frame = sample_frame()
    model = PartialPoolingExpectedR.fit(
        frame,
        numeric_features=["x1", "x2"],
        families=["A", "B"],
        alpha=20.0,
        interaction_scale=0.25,
        target_clip=(-3.0, 3.0),
    )
    assert model.design(frame).shape == (12, 8)
    assert np.allclose(model.predict(frame), model.predict(frame))


def test_sparse_family_uses_pooled_threshold() -> None:
    frame = sample_frame().rename(columns={"stress_net_r": "model_score"})
    pooled, thresholds, rows = calibration_thresholds(
        frame,
        families=["A", "B", "C"],
        quantile=0.3,
        minimum_family_rows=7,
    )
    assert thresholds == {"A": pooled, "B": pooled, "C": pooled}
    assert {row["threshold_source"] for row in rows} == {"POOLED_FALLBACK"}


def test_apply_thresholds_is_inclusive() -> None:
    frame = pd.DataFrame(
        {
            "family_id": ["A", "A", "B"],
            "model_score": [0.5, 0.49, 0.2],
        }
    )
    result = apply_thresholds(frame, {"A": 0.5}, pooled_threshold=0.1)
    assert result["selected"].tolist() == [True, False, True]


def test_comparison_metrics_reports_positive_lift() -> None:
    frame = sample_frame()
    frame["model_score"] = frame["stress_net_r"]
    frame["threshold"] = 0.0
    frame["selected"] = frame["model_score"] >= frame["threshold"]
    metrics = comparison_metrics(frame)
    assert metrics["selected_mean_lift_r"] > 0.0
    assert metrics["selected_weight_coverage"] == 8 / 12

from __future__ import annotations

import pandas as pd

from src.consensus import (
    AUXILIARY_SCORES,
    apply_consensus,
    calibration_thresholds,
    weighted_quantile,
)


def test_weighted_quantile_is_deterministic() -> None:
    assert weighted_quantile([3.0, 1.0, 2.0], [1.0, 1.0, 1.0], 0.5) == 2.0


def test_consensus_requires_two_low_votes_and_b123_veto() -> None:
    frame = pd.DataFrame(
        {
            AUXILIARY_SCORES[0]: [0.0, 0.0, 0.0, 3.0],
            AUXILIARY_SCORES[1]: [0.0, 3.0, 0.0, 3.0],
            AUXILIARY_SCORES[2]: [3.0, 0.0, 0.0, 3.0],
            "b123_selected": [False, False, True, False],
        }
    )
    thresholds = {score: 1.0 for score in AUXILIARY_SCORES}
    result = apply_consensus(frame, thresholds, minimum_low_votes=2)
    assert result["auxiliary_low_votes"].tolist() == [2, 2, 3, 0]
    assert result["selected"].tolist() == [False, False, True, True]


def test_calibration_thresholds_cover_all_scores() -> None:
    frame = pd.DataFrame(
        {
            score: [0.0, 1.0, 2.0, 3.0] for score in AUXILIARY_SCORES
        }
    )
    frame["structural_weight"] = 1.0
    thresholds = calibration_thresholds(frame, 0.5)
    assert thresholds == {score: 1.0 for score in AUXILIARY_SCORES}

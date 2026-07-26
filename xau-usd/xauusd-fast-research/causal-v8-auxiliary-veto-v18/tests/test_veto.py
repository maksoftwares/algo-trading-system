from __future__ import annotations

import pandas as pd

from src.veto import (
    apply_v8_veto,
    weighted_quantile,
)


SPECIALIST = "V8_RETEST_HEALTH"


def test_weighted_quantile_is_deterministic() -> None:
    assert weighted_quantile([3.0, 1.0, 2.0], [1.0, 1.0, 1.0], 0.5) == 2.0


def test_veto_changes_only_b123_retained_v8_candidates() -> None:
    frame = pd.DataFrame(
        {
            "family_id": [SPECIALIST, SPECIALIST, "R4_CHOP", "R4_CHOP"],
            "b123_selected": [False, True, False, True],
            "v8_model_score": [0.5, -1.0, 9.0, -9.0],
        }
    )
    result = apply_v8_veto(
        frame,
        specialist_id=SPECIALIST,
        threshold=0.0,
    )
    assert result["v18_selected"].tolist() == [False, False, False, True]
    assert result["v8_additional_veto"].tolist() == [False, True, False, False]


def test_missing_threshold_preserves_b123() -> None:
    frame = pd.DataFrame(
        {
            "family_id": [SPECIALIST, "R4_CHOP"],
            "b123_selected": [False, False],
            "v8_model_score": [float("nan"), float("nan")],
        }
    )
    result = apply_v8_veto(
        frame,
        specialist_id=SPECIALIST,
        threshold=None,
    )
    assert result["v18_selected"].tolist() == [False, False]


def test_missing_score_fails_open_for_b123_retained_v8() -> None:
    frame = pd.DataFrame(
        {
            "family_id": [SPECIALIST],
            "b123_selected": [True],
            "v8_model_score": [float("nan")],
        }
    )
    result = apply_v8_veto(frame, specialist_id=SPECIALIST, threshold=0.0)
    assert result["v18_selected"].tolist() == [True]

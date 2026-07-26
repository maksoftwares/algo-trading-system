from __future__ import annotations

import numpy as np
import pandas as pd

from src.specialist import (
    AUXILIARY_SCORES,
    SpecialistExpectedR,
    apply_v57_confirmation,
    weighted_quantile,
)


SPECIALIST = "V57_BREAK_SWING_H4ADX_HIGH"


def test_weighted_quantile_is_deterministic() -> None:
    assert weighted_quantile([3.0, 1.0, 2.0], [1.0, 1.0, 1.0], 0.5) == 2.0


def test_specialist_model_produces_finite_scores() -> None:
    frame = pd.DataFrame(
        {
            AUXILIARY_SCORES[0]: [-1.0, 0.0, 1.0, 2.0],
            AUXILIARY_SCORES[1]: [-1.0, 0.0, 1.0, 2.0],
            AUXILIARY_SCORES[2]: [0.1, 0.3, 0.7, 0.9],
            "stress_net_r": [-1.0, -0.5, 1.0, 2.0],
            "structural_weight": [1.0, 1.0, 1.0, 1.0],
        }
    )
    model = SpecialistExpectedR.fit(
        frame, alpha=50.0, target_clip=(-3.0, 3.0)
    )
    assert np.isfinite(model.predict(frame)).all()


def test_confirmation_changes_only_v57_b123_vetoes() -> None:
    frame = pd.DataFrame(
        {
            "family_id": [SPECIALIST, SPECIALIST, "R4_CHOP", "R4_CHOP"],
            "b123_selected": [False, True, False, True],
            "v57_model_score": [0.5, -1.0, 9.0, -9.0],
        }
    )
    result = apply_v57_confirmation(
        frame,
        specialist_id=SPECIALIST,
        threshold=0.0,
        fallback_retain_all=True,
    )
    assert result["v17_selected"].tolist() == [True, True, False, True]


def test_fallback_re_admits_v57_only() -> None:
    frame = pd.DataFrame(
        {
            "family_id": [SPECIALIST, "R4_CHOP"],
            "b123_selected": [False, False],
            "v57_model_score": [np.nan, np.nan],
        }
    )
    result = apply_v57_confirmation(
        frame,
        specialist_id=SPECIALIST,
        threshold=None,
        fallback_retain_all=True,
    )
    assert result["v17_selected"].tolist() == [True, False]

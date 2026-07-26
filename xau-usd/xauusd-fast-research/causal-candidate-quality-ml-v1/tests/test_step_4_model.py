from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))

from step_4_model import (  # noqa: E402
    chronological_calibration_split,
    eligibility_mask,
    feature_names_for_blocks,
)


def test_inner_calibration_is_trailing_by_episode_and_purges_crossing_labels() -> None:
    frame = pd.DataFrame(
        {
            "candidate_id": ["A", "B", "C", "D", "E"],
            "structural_episode_id": ["E1", "E1", "E2", "E3", "E4"],
            "decision_time": pd.to_datetime(
                [
                    "2020-01-01T00:00Z",
                    "2020-01-01T00:00Z",
                    "2020-02-01T00:00Z",
                    "2020-03-01T00:00Z",
                    "2020-04-01T00:00Z",
                ]
            ),
            "label_end_time": pd.to_datetime(
                [
                    "2020-01-02T00:00Z",
                    "2020-04-15T00:00Z",
                    "2020-02-02T00:00Z",
                    "2020-03-02T00:00Z",
                    "2020-04-02T00:00Z",
                ]
            ),
        }
    )
    base, calibrator, purged = chronological_calibration_split(frame, 0.25)
    assert set(calibrator["structural_episode_id"]) == {"E4"}
    assert set(base["candidate_id"]) == {"C", "D"}
    assert purged == 2


def test_locked_primary_features_exclude_comex() -> None:
    step2b = json.loads(
        (PACKAGE / "config/step_2b_dataset_feature_contract_v1.json").read_text()
    )
    step4 = json.loads(
        (PACKAGE / "config/step_4_model_evaluation_contract_v1.json").read_text()
    )
    for spec in step4["models"]["specifications"]:
        names = feature_names_for_blocks(step2b, spec["feature_blocks"])
        assert not any(name.startswith("gc_") for name in names)
    primary = next(
        spec
        for spec in step4["models"]["specifications"]
        if spec["model_id"] == step4["models"]["primary_model_id"]
    )
    assert len(feature_names_for_blocks(step2b, primary["feature_blocks"])) == 40


def test_status_eligibility_fails_closed() -> None:
    frame = pd.DataFrame(
        {
            "label_status": ["RESOLVED_TARGET", "RESOLVED_STOP"],
            "xau_feature_status": ["PASS", "ABSTAIN_MISSING_MANDATORY_XAU"],
            "crossasset_feature_status": ["PASS", "PASS"],
        }
    )
    assert eligibility_mask(frame, "XAU_FEATURE_STATUS_PASS").tolist() == [True, False]
    assert eligibility_mask(frame, "XAU_AND_CROSSASSET_STATUS_PASS").tolist() == [
        True,
        False,
    ]


def test_probability_logit_is_finite_at_boundaries() -> None:
    from step_4_model import probability_logit

    values = probability_logit(np.array([0.0, 0.5, 1.0]), 1e-6)
    assert np.isfinite(values).all()
    assert values[1] == 0.0

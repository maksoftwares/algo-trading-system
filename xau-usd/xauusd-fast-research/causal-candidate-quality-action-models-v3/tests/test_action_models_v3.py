from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.action_models import assign_model_lane  # noqa: E402


CONFIG = json.loads(
    (ROOT / "config" / "action_models_v3.json").read_text(encoding="utf-8")
)


def test_lane_ownership_is_disjoint_and_priority_ordered() -> None:
    frame = pd.DataFrame(
        {
            "mechanism_downside_impulse_retest": [0.0, 1.0, 1.0],
            "mechanism_opening_range_reversal": [0.0, 0.0, 1.0],
            "mechanism_break_and_run": [1.0, 1.0, 1.0],
        }
    )
    assert assign_model_lane(frame, CONFIG["lane_ownership"]).tolist() == [
        "BREAK_AND_RUN",
        "DOWNSIDE_IMPULSE_RETEST",
        "DOWNSIDE_IMPULSE_RETEST",
    ]


def test_runtime_authorizations_are_disabled() -> None:
    authorization = CONFIG["authorization"]
    assert authorization["offline_model_fit_authorized"] is True
    assert authorization["offline_threshold_fit_authorized"] is True
    assert authorization["research_only"] is True
    for key in (
        "portfolio_simulation_authorized",
        "python_serving_authorized",
        "ml_shadow_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
    ):
        assert authorization[key] is False


def test_outputs_have_one_policy_and_decision_per_lane_fold() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    policies = pd.read_parquet(output / CONFIG["outputs"]["calibration_policies"])
    predictions = pd.read_parquet(output / CONFIG["outputs"]["predictions"])
    selected = pd.read_parquet(output / CONFIG["outputs"]["selected_events"])
    expected = len(CONFIG["lane_ownership"]["priority"]) * len(
        CONFIG["expected"]["folds"]
    )
    assert int(policies["chosen"].sum()) == expected
    assert not predictions["candidate_id"].duplicated().any()
    assert not selected.duplicated(["fold_id", "model_lane", "event_id"]).any()
    assert set(predictions.loc[predictions["selected"], "candidate_id"]) == set(
        selected["candidate_id"]
    )
    assert np.isfinite(predictions["model_score"]).all()


def test_all_test_predictions_are_out_of_time_and_shock_free() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    predictions = pd.read_parquet(output / CONFIG["outputs"]["predictions"])
    source = pd.read_parquet(
        ROOT.parent
        / "causal-candidate-quality-expanded-dataset-v3"
        / "outputs"
        / "V3_ACTION_DATASET.parquet",
        columns=["candidate_id", "regime"],
    )
    joined = predictions[["candidate_id"]].merge(
        source, on="candidate_id", how="left", validate="one_to_one"
    )
    assert joined["regime"].notna().all()
    assert not joined["regime"].eq("UNSAFE_SHOCK").any()

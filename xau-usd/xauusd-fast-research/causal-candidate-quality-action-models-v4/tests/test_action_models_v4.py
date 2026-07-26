from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.action_models import assign_model_lane, sha256_file  # noqa: E402
from src.replay_contract import assert_method_parity  # noqa: E402


CONFIG = json.loads(
    (ROOT / "config" / "action_models_v4.json").read_text(encoding="utf-8")
)
REPO_ROOT = ROOT.parents[2]


def test_methodology_exactly_matches_action_v3() -> None:
    reference_path = REPO_ROOT / CONFIG["inputs"]["previous_action_v3_config"]["path"]
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    assert assert_method_parity(CONFIG, reference)
    source = ROOT / "src" / "action_models.py"
    assert (
        sha256_file(source)
        == CONFIG["replay_contract"]["expected_shared_model_code_sha256"]
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


def test_dataset_change_is_limited_to_corrected_features() -> None:
    current = pd.read_parquet(
        REPO_ROOT / CONFIG["inputs"]["v4_action_dataset"]["path"]
    ).sort_values("candidate_id", kind="mergesort")
    reference = pd.read_parquet(
        ROOT.parent
        / "causal-candidate-quality-expanded-dataset-v3"
        / "outputs"
        / "V3_ACTION_DATASET.parquet"
    ).sort_values("candidate_id", kind="mergesort")
    assert current["candidate_id"].tolist() == reference["candidate_id"].tolist()
    allowed = set(CONFIG["replay_contract"]["allowed_dataset_corrections"])
    unchanged = [column for column in current.columns if column not in allowed]
    pd.testing.assert_frame_equal(
        current[unchanged].reset_index(drop=True),
        reference[unchanged].reset_index(drop=True),
        check_dtype=False,
        check_exact=True,
    )
    for column in allowed:
        assert not current[column].equals(reference[column])


def test_outputs_when_present() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    predictions_path = output / CONFIG["outputs"]["predictions"]
    if not predictions_path.is_file():
        return
    policies = pd.read_parquet(output / CONFIG["outputs"]["calibration_policies"])
    predictions = pd.read_parquet(predictions_path)
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
    source = pd.read_parquet(
        REPO_ROOT / CONFIG["inputs"]["v4_action_dataset"]["path"],
        columns=["candidate_id", "regime"],
    )
    joined = predictions[["candidate_id"]].merge(
        source, on="candidate_id", how="left", validate="one_to_one"
    )
    assert joined["regime"].notna().all()
    assert not joined["regime"].eq("UNSAFE_SHOCK").any()

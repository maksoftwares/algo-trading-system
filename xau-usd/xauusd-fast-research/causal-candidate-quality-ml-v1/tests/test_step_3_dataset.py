from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from step_3_dataset import (  # noqa: E402
    _serial_effective_size,
    assemble_canonical_dataset,
    assign_splits,
    validate_controls,
)


def test_step3_authorizes_dataset_build_but_keeps_models_and_runtime_closed() -> None:
    config = json.loads((PACKAGE_ROOT / "config" / "step_3_build_v1.json").read_text())
    validate_controls(config)
    assert config["controls"]["economic_outcomes_authorized"]
    assert config["controls"]["feature_value_build_authorized"]
    assert not config["controls"]["model_training_authorized"]
    assert not config["controls"]["runtime_change_authorized"]
    assert not config["controls"]["journey_rows_enter_primary_fit"]


def test_actual_episode_label_end_purges_all_siblings() -> None:
    canonical = pd.DataFrame(
        {
            "candidate_id": ["A", "B"],
            "family_id": ["R4_CHOP", "R4_CHOP"],
            "decision_time": pd.to_datetime(["2019-12-01T00:00Z", "2019-12-01T00:00Z"]),
            "planned_observation_end": pd.to_datetime(
                ["2019-12-02T00:00Z", "2019-12-02T00:00Z"]
            ),
            "structural_episode_id": ["E", "E"],
        }
    )
    labels = pd.DataFrame(
        {
            "candidate_id": ["A", "B"],
            "label_end_time": pd.to_datetime(
                ["2019-12-02T00:00Z", "2020-01-02T00:00Z"]
            ),
            "label_status": ["RESOLVED_TARGET", "RESOLVED_STOP"],
        }
    )
    plan = {
        "folds": [
            {
                "fold_id": "F",
                "calibration_start": "2020-01-01T00:00Z",
                "test_start": "2020-07-01T00:00Z",
                "test_end_exclusive": "2021-07-01T00:00Z",
                "outcome_blind_counts": {"fit": 2, "calibration": 0, "test": 0},
            }
        ]
    }
    assignments, audit = assign_splits(canonical, labels, plan)
    assert assignments["assignment"].tolist() == [
        "PURGED_LABEL_INTERVAL",
        "PURGED_LABEL_INTERVAL",
    ]
    assert audit[0]["purged_label_interval"] == 2


def test_geyer_serial_effective_size_is_bounded() -> None:
    independent, _ = _serial_effective_size(pd.Series([1, -1] * 50).to_numpy(), 60)
    correlated, retained = _serial_effective_size(pd.Series(range(100)).to_numpy(), 60)
    assert 0 < independent <= 100
    assert 0 < correlated < 100
    assert retained


def test_canonical_dataset_exposes_one_unsuffixed_family_feature() -> None:
    canonical = pd.DataFrame(
        {
            "candidate_id": ["A"],
            "population": ["CANONICAL"],
            "family_id": ["R4_CHOP"],
            "direction": ["LONG"],
            "source_id": ["SOURCE"],
            "source_available_at": pd.to_datetime(["2025-01-01T00:00Z"]),
            "signal_bar_end": pd.to_datetime(["2025-01-01T00:00Z"]),
            "decision_time": pd.to_datetime(["2025-01-01T00:00Z"]),
            "feature_cutoff_time": pd.to_datetime(["2025-01-01T00:00Z"]),
            "entry_eligible_time": pd.to_datetime(["2025-01-01T00:00Z"]),
            "structural_episode_id": ["E"],
            "conservative_episode_id": ["E"],
            "structural_weight": [1.0],
            "conservative_weight": [1.0],
            "broker_executable": [True],
            "historical_accept_state": ["ACCEPTED"],
            "historical_decision_reason": ["PASS"],
            "historical_portfolio_accepted": [True],
        }
    )
    features = pd.DataFrame(
        {"candidate_id": ["A"], "family_id": ["R4_CHOP"], "value": [1.0]}
    )
    labels = pd.DataFrame({"candidate_id": ["A"], "stress_net_r": [0.5]})
    result = assemble_canonical_dataset(canonical, features, labels)
    assert result["family_id"].tolist() == ["R4_CHOP"]
    assert "family_id_x" not in result
    assert "family_id_y" not in result

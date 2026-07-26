from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))

from diagnostic import (  # noqa: E402
    build_matched_pairs,
    utc_session,
    validate_feature_contract,
    walk_forward_feature_transfer,
    weighted_smd,
)


def _config() -> dict:
    return json.loads(
        (PACKAGE / "config" / "specialist_win_loss_v1.json").read_text(encoding="utf-8")
    )


def test_session_map_covers_every_utc_hour_once() -> None:
    sessions = _config()["matching"]["sessions"]
    observed = [utc_session(hour, sessions) for hour in range(24)]
    assert observed[:7] == ["ASIA"] * 7
    assert observed[7:13] == ["LONDON"] * 6
    assert observed[13:21] == ["NEW_YORK"] * 8
    assert observed[21:] == ["ROLLOVER"] * 3


def test_feature_contract_rejects_outcome_columns() -> None:
    config = _config()
    frame = pd.DataFrame({name: [1.0] for name in config["features"]})
    assert validate_feature_contract(frame, config) == config["features"]
    config["features"] = [*config["features"], "stress_net_r"]
    frame["stress_net_r"] = 1.0
    try:
        validate_feature_contract(frame, config)
    except ValueError as error:
        assert "forbidden" in str(error)
    else:
        raise AssertionError("Outcome feature was accepted")


def test_weighted_smd_is_positive_when_winners_are_higher() -> None:
    frame = pd.DataFrame(
        {
            "value": [2.0, 3.0, -1.0, 0.0],
            "stress_net_r_positive": [True, True, False, False],
            "structural_weight": [1.0, 1.0, 1.0, 1.0],
        }
    )
    result = weighted_smd(frame, "value")
    assert result["weighted_smd"] is not None
    assert float(result["weighted_smd"]) > 0.0


def test_matching_is_exact_stratum_and_without_replacement() -> None:
    config = _config()
    times = pd.to_datetime(
        [
            "2025-01-06T08:00:00Z",
            "2025-01-06T09:00:00Z",
            "2025-01-06T08:10:00Z",
            "2025-01-06T09:10:00Z",
        ],
        utc=True,
    )
    frame = pd.DataFrame(
        {
            "candidate_id": ["w1", "w2", "l1", "l2"],
            "structural_episode_id": ["ew1", "ew2", "el1", "el2"],
            "structural_weight": [1.0] * 4,
            "family_id": ["R1_UPTREND"] * 4,
            "direction": ["LONG"] * 4,
            "calendar_year": [2025] * 4,
            "utc_session": ["LONDON"] * 4,
            "stop_mode": ["FIXED"] * 4,
            "target_mode": ["FIXED"] * 4,
            "decision_time": times,
            "stress_net_r_positive": [True, True, False, False],
        }
    )
    pairs = build_matched_pairs(frame, config)
    assert len(pairs) == 2
    assert pairs["winner_candidate_id"].nunique() == 2
    assert pairs["failure_candidate_id"].nunique() == 2
    assert set(pairs["distance_hours"].round(6)) == {round(1.0 / 6.0, 6)}


def test_walk_forward_direction_is_learned_from_fit_only() -> None:
    config = _config()
    config["population"]["families"] = ["R1_UPTREND"]
    config["features"] = ["feature"]
    config["walk_forward"]["folds"] = ["F2025"]
    config["walk_forward"]["minimum_fit_rows"] = 20
    config["walk_forward"]["minimum_fit_rows_per_class"] = 10
    config["walk_forward"]["minimum_test_rows"] = 10
    config["walk_forward"]["minimum_test_rows_per_class"] = 5
    fit_target = np.array([False] * 10 + [True] * 10)
    test_target = np.array([False] * 5 + [True] * 5)
    frame = pd.DataFrame(
        {
            "candidate_id": [f"c{i}" for i in range(30)],
            "family_id": ["R1_UPTREND"] * 30,
            "feature": np.r_[
                np.arange(10),
                np.arange(20, 30),
                np.arange(20, 25),
                np.arange(5),
            ],
            "stress_net_r_positive": np.r_[fit_target, test_target],
            "structural_weight": np.ones(30),
        }
    )
    splits = pd.DataFrame(
        {
            "fold_id": ["F2025"] * 30,
            "candidate_id": frame["candidate_id"],
            "assignment": ["FIT"] * 20 + ["TEST"] * 10,
            "resolved_label": [True] * 30,
            "dataset_eligible": [True] * 30,
        }
    )
    folds, summary = walk_forward_feature_transfer(frame, splits, config)
    assert bool(folds.iloc[0]["eligible"])
    assert folds.iloc[0]["fit_direction"] == "WINNERS_HIGHER"
    assert float(summary.iloc[0]["walk_forward_auc"]) == 0.0

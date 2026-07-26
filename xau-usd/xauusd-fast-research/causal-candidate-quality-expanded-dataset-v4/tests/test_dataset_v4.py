from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.expanded_v4 import assert_correction_only  # noqa: E402


CONFIG = json.loads(
    (ROOT / "config" / "expanded_candidate_dataset_v4.json").read_text(encoding="utf-8")
)


def test_correction_and_authorization_are_narrow() -> None:
    assert CONFIG["correction"]["allowed_changed_columns"] == [
        "prior_events_1h",
        "prior_events_4h",
    ]
    assert CONFIG["authorization"]["research_only"] is True
    assert all(
        not value
        for key, value in CONFIG["authorization"].items()
        if key != "research_only"
    )


def test_feature_surface_excludes_forbidden_fields() -> None:
    assert len(CONFIG["model_features"]) == 58
    assert not set(CONFIG["model_features"]) & set(CONFIG["forbidden_model_columns"])


def test_correction_guard_rejects_unrelated_change() -> None:
    previous = pd.DataFrame(
        {
            "event_id": ["A", "B"],
            "prior_events_1h": [0, 1],
            "prior_events_4h": [0, 1],
            "label": [0.0, 1.0],
        }
    )
    current = previous.copy()
    current["prior_events_1h"] = [0, 2]
    current["prior_events_4h"] = [0, 2]
    changes = assert_correction_only(
        current,
        previous,
        keys=["event_id"],
        allowed_changed_columns=CONFIG["correction"]["allowed_changed_columns"],
        name="test frame",
    )
    assert changes == {"prior_events_1h": 1, "prior_events_4h": 1}
    current.loc[0, "label"] = 2.0
    try:
        assert_correction_only(
            current,
            previous,
            keys=["event_id"],
            allowed_changed_columns=CONFIG["correction"]["allowed_changed_columns"],
            name="test frame",
        )
    except ValueError as error:
        assert "outside the correction" in str(error)
    else:
        raise AssertionError("Unrelated correction was accepted")


def test_built_dataset_integrity_when_present() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    dataset_path = output / CONFIG["outputs"]["action_dataset"]
    if not dataset_path.is_file():
        return
    events = pd.read_parquet(output / CONFIG["outputs"]["event_registry"])
    dataset = pd.read_parquet(dataset_path)
    splits = pd.read_parquet(output / CONFIG["outputs"]["split_assignments"])
    assert len(events) == CONFIG["expected"]["hf_event_rows"]
    assert len(dataset) == CONFIG["expected"]["hf_action_rows"]
    assert (
        dataset["structural_episode_id"].nunique()
        == CONFIG["expected"]["structural_episodes"]
    )
    assert not dataset["candidate_id"].duplicated().any()
    assert np.isfinite(dataset[CONFIG["model_features"]].to_numpy(dtype=float)).all()
    weights = dataset.groupby("structural_episode_id")["structural_weight"].sum()
    assert np.allclose(weights.to_numpy(), 1.0, atol=1e-12)
    assert dataset["stress_net_r_positive"].equals(dataset["stress_net_r"].gt(0.0))
    assert (
        events["prior_events_1h"].max()
        <= CONFIG["correction"]["maximum_prior_events_1h"]
    )
    assert (
        events["prior_events_4h"].max()
        <= CONFIG["correction"]["maximum_prior_events_4h"]
    )
    assert not splits.duplicated(["fold_id", "structural_episode_id"]).any()

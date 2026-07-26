from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads(
    (ROOT / "config" / "expanded_candidate_dataset_v3.json").read_text(encoding="utf-8")
)


def test_authorization_is_research_only() -> None:
    assert CONFIG["authorization"]["research_only"] is True
    assert all(
        value is False
        for key, value in CONFIG["authorization"].items()
        if key != "research_only"
    )


def test_feature_surface_excludes_forbidden_fields() -> None:
    assert not set(CONFIG["model_features"]) & set(CONFIG["forbidden_model_columns"])
    assert len(CONFIG["model_features"]) == 58


def test_built_dataset_integrity() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    dataset = pd.read_parquet(output / CONFIG["outputs"]["action_dataset"])
    assert len(dataset) == CONFIG["expected"]["hf_action_rows"]
    assert not dataset["candidate_id"].duplicated().any()
    assert not dataset.duplicated(["event_id", "action_id"]).any()
    assert np.isfinite(dataset[CONFIG["model_features"]].to_numpy(dtype=float)).all()
    weights = dataset.groupby("structural_episode_id")["structural_weight"].sum()
    assert np.allclose(weights.to_numpy(), 1.0, atol=1e-12)
    assert dataset["stress_net_r_positive"].equals(dataset["stress_net_r"].gt(0.0))


def test_fold_partitions_are_purged_by_episode_label_end() -> None:
    output = ROOT / CONFIG["outputs"]["directory"]
    splits = pd.read_parquet(output / CONFIG["outputs"]["split_assignments"])
    boundaries: dict[tuple[str, str], pd.Timestamp] = {}
    for fold in CONFIG["folds"]:
        boundaries[(fold["fold_id"], "FIT")] = pd.Timestamp(fold["fit"][1])
        boundaries[(fold["fold_id"], "CALIBRATION")] = pd.Timestamp(
            fold["calibration"][1]
        )
        boundaries[(fold["fold_id"], "TEST")] = pd.Timestamp(fold["test"][1])
    eligible = splits.loc[splits["eligible"]]
    for row in eligible.itertuples(index=False):
        assert row.label_end_time < boundaries[(row.fold_id, row.partition)]

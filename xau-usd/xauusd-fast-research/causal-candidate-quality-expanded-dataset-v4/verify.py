from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from build_dataset import verify_lock
from src.expanded_v4 import (
    assert_correction_only,
    assert_exact_frame,
    resolve_inputs,
    sha256_file,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "expanded_candidate_dataset_v4.json"


def verify_purged_splits(splits: pd.DataFrame, config: dict) -> None:
    boundaries: dict[tuple[str, str], pd.Timestamp] = {}
    for fold in config["folds"]:
        boundaries[(fold["fold_id"], "FIT")] = pd.Timestamp(fold["fit"][1])
        boundaries[(fold["fold_id"], "CALIBRATION")] = pd.Timestamp(
            fold["calibration"][1]
        )
        boundaries[(fold["fold_id"], "TEST")] = pd.Timestamp(fold["test"][1])
    for row in splits.loc[splits["eligible"]].itertuples(index=False):
        if row.label_end_time >= boundaries[(row.fold_id, row.partition)]:
            raise ValueError("Expanded V4 split contains an unpurged episode label")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    verify_lock(config, lock)
    inputs = resolve_inputs(REPO_ROOT, config)
    manifest_path = output / config["outputs"]["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["definition_contract_sha256"] != lock["definition_contract_sha256"]:
        raise ValueError("Expanded V4 manifest references a different contract")
    for group in ("inputs", "artifacts"):
        for name, spec in manifest[group].items():
            actual = sha256_file(REPO_ROOT / spec["path"])
            if actual != spec["sha256"]:
                raise ValueError(f"Expanded V4 manifest mismatch: {group}.{name}")

    events = pd.read_parquet(output / config["outputs"]["event_registry"])
    dataset = pd.read_parquet(output / config["outputs"]["action_dataset"])
    splits = pd.read_parquet(output / config["outputs"]["split_assignments"])
    expected = config["expected"]
    if len(events) != int(expected["hf_event_rows"]):
        raise ValueError("Verified Expanded V4 event count changed")
    if len(dataset) != int(expected["hf_action_rows"]):
        raise ValueError("Verified Expanded V4 action count changed")
    if dataset["structural_episode_id"].nunique() != int(
        expected["structural_episodes"]
    ):
        raise ValueError("Verified Expanded V4 structural episode count changed")
    if events["event_id"].duplicated().any():
        raise ValueError("Verified Expanded V4 event IDs are duplicated")
    if dataset["candidate_id"].duplicated().any():
        raise ValueError("Verified Expanded V4 candidate IDs are duplicated")
    if dataset.duplicated(["event_id", "action_id"]).any():
        raise ValueError("Verified Expanded V4 event/action keys are duplicated")
    weights = dataset.groupby("structural_episode_id")["structural_weight"].sum()
    if not np.allclose(weights.to_numpy(), 1.0, atol=1e-12):
        raise ValueError("Verified Expanded V4 structural weights do not sum to one")
    features = config["model_features"]
    if not np.isfinite(dataset[features].to_numpy(dtype=float)).all():
        raise ValueError("Verified Expanded V4 model features are non-finite")
    if set(features) & set(config["forbidden_model_columns"]):
        raise ValueError("Verified Expanded V4 feature surface is forbidden")
    if not dataset["stress_net_r_positive"].equals(dataset["stress_net_r"].gt(0.0)):
        raise ValueError("Verified Expanded V4 stressed labels are inconsistent")

    allowed = list(config["correction"]["allowed_changed_columns"])
    event_changes = assert_correction_only(
        events,
        pd.read_parquet(inputs["previous_v3_events"]),
        keys=["event_id"],
        allowed_changed_columns=allowed,
        name="Verified Expanded event registry",
    )
    action_changes = assert_correction_only(
        dataset,
        pd.read_parquet(inputs["previous_v3_actions"]),
        keys=["candidate_id"],
        allowed_changed_columns=allowed,
        name="Verified Expanded action dataset",
    )
    assert_exact_frame(
        splits,
        pd.read_parquet(inputs["previous_v3_splits"]),
        keys=["fold_id", "structural_episode_id"],
        name="Verified Expanded split assignments",
    )
    if events["prior_events_1h"].max() > int(
        config["correction"]["maximum_prior_events_1h"]
    ):
        raise ValueError("Verified Expanded V4 one-hour count exceeds its bound")
    if events["prior_events_4h"].max() > int(
        config["correction"]["maximum_prior_events_4h"]
    ):
        raise ValueError("Verified Expanded V4 four-hour count exceeds its bound")
    verify_purged_splits(splits, config)
    if any(
        config["authorization"].get(key)
        for key in config["authorization"]
        if key != "research_only"
    ):
        raise ValueError("Expanded V4 runtime authority was enabled")

    print(
        json.dumps(
            {
                "decision": "V4_CORRECTED_EXPANDED_DATASET_VERIFICATION_PASS",
                "events": len(events),
                "actions": len(dataset),
                "episodes": int(dataset["structural_episode_id"].nunique()),
                "fold_assignment_rows": len(splits),
                "event_changed_rows": event_changes,
                "action_changed_rows": action_changes,
                "manifest_sha256": sha256_file(manifest_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.dataset_v3 import sha256_file


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "expanded_candidate_dataset_v3.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    manifest_path = output / config["outputs"]["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for group in ("inputs", "artifacts"):
        for name, spec in manifest[group].items():
            path = REPO_ROOT / spec["path"]
            actual = sha256_file(path)
            if actual != spec["sha256"]:
                raise ValueError(f"Manifest hash mismatch for {group}.{name}: {actual}")
    dataset = pd.read_parquet(output / config["outputs"]["action_dataset"])
    events = pd.read_parquet(output / config["outputs"]["event_registry"])
    splits = pd.read_parquet(output / config["outputs"]["split_assignments"])
    if len(events) != int(config["expected"]["hf_event_rows"]):
        raise ValueError("Verified event count changed")
    if len(dataset) != int(config["expected"]["hf_action_rows"]):
        raise ValueError("Verified action count changed")
    if dataset["candidate_id"].duplicated().any():
        raise ValueError("Verified candidate IDs are duplicated")
    if dataset.duplicated(["event_id", "action_id"]).any():
        raise ValueError("Verified event/action keys are duplicated")
    weights = dataset.groupby("structural_episode_id")["structural_weight"].sum()
    if not np.allclose(weights.to_numpy(), 1.0, atol=1e-12):
        raise ValueError("Verified structural weights do not sum to one")
    if not np.isfinite(dataset[config["model_features"]].to_numpy(dtype=float)).all():
        raise ValueError("Verified model features contain non-finite values")
    if set(config["model_features"]) & set(config["forbidden_model_columns"]):
        raise ValueError("Verified feature surface contains a forbidden column")
    eligible = splits.loc[splits["eligible"]]
    boundaries: dict[tuple[str, str], pd.Timestamp] = {}
    for fold in config["folds"]:
        boundaries[(fold["fold_id"], "FIT")] = pd.Timestamp(fold["fit"][1])
        boundaries[(fold["fold_id"], "CALIBRATION")] = pd.Timestamp(
            fold["calibration"][1]
        )
        boundaries[(fold["fold_id"], "TEST")] = pd.Timestamp(fold["test"][1])
    for row in eligible.itertuples(index=False):
        if row.label_end_time >= boundaries[(row.fold_id, row.partition)]:
            raise ValueError("A split contains an unpurged episode label")
    if any(
        config["authorization"].get(key)
        for key in config["authorization"]
        if key != "research_only"
    ):
        raise ValueError("Runtime authority was enabled")
    print(
        json.dumps(
            {
                "decision": "V3_VERIFICATION_PASS",
                "events": len(events),
                "actions": len(dataset),
                "episodes": int(dataset["structural_episode_id"].nunique()),
                "fold_assignment_rows": len(splits),
                "manifest_sha256": sha256_file(manifest_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

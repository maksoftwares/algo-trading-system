from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

from src.expanded_v4 import (
    assert_correction_only,
    assert_exact_frame,
    canonical_json_sha256,
    resolve_inputs,
    sha256_file,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
SHARED_SRC = ROOT.parent / "causal-candidate-quality-expanded-dataset-v3" / "src"
CONFIG_PATH = ROOT / "config" / "expanded_candidate_dataset_v4.json"
sys.path.insert(0, str(SHARED_SRC))

from dataset_v3 import (  # noqa: E402
    build_overlap_audit,
    build_population_audit,
    build_primary_population,
    build_split_assignments,
)


def verify_lock(config: dict[str, Any], lock: dict[str, Any]) -> None:
    definition = {
        key: value for key, value in lock.items() if key != "definition_contract_sha256"
    }
    if canonical_json_sha256(definition) != lock["definition_contract_sha256"]:
        raise ValueError("Expanded V4 contract digest is invalid")
    if sha256_file(CONFIG_PATH) != lock["config_sha256"]:
        raise ValueError("Expanded V4 config changed after lock")
    if sha256_file(ROOT / "PREREGISTRATION.md") != lock["preregistration_sha256"]:
        raise ValueError("Expanded V4 preregistration changed after lock")
    for name, record in lock["implementation"].items():
        if sha256_file(REPO_ROOT / record["path"]) != record["sha256"]:
            raise ValueError(f"Expanded V4 implementation changed: {name}")
    if canonical_json_sha256(config["model_features"]) != lock["model_feature_sha256"]:
        raise ValueError("Expanded V4 feature definition changed after lock")
    if canonical_json_sha256(config["folds"]) != lock["fold_definition_sha256"]:
        raise ValueError("Expanded V4 fold definition changed after lock")
    if config["correction"] != lock["correction"]:
        raise ValueError("Expanded V4 correction scope changed after lock")
    if config["authorization"] != lock["authorization"]:
        raise ValueError("Expanded V4 authorization changed after lock")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before Expanded V4")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    verify_lock(config, lock)
    inputs = resolve_inputs(REPO_ROOT, config)
    events = pd.read_parquet(inputs["hf_events"])
    actions = pd.read_parquet(inputs["hf_actions"])
    canonical = pd.read_parquet(inputs["canonical_benchmark"])
    journey = pd.read_parquet(inputs["journey_quarantine"])
    if len(canonical) != int(config["expected"]["canonical_rows"]):
        raise ValueError("Canonical benchmark row count changed")
    if len(journey) != int(config["expected"]["journey_rows"]):
        raise ValueError("Journey quarantine row count changed")

    event_registry, dataset = build_primary_population(events, actions, config)
    splits = build_split_assignments(dataset, config)
    audit = build_population_audit(event_registry, dataset, splits, config)
    audit["schema_version"] = config["schema_version"]
    audit["decision"] = "V4_CORRECTED_EXPANDED_DATASET_COMPLETE_RESEARCH_ONLY"
    overlap = build_overlap_audit(event_registry, dataset, canonical, journey)
    if audit["forbidden_features_present"]:
        raise ValueError("A forbidden field entered the V4 feature surface")
    if dataset["structural_episode_id"].nunique() != int(
        config["expected"]["structural_episodes"]
    ):
        raise ValueError("Expanded V4 structural episode count changed")

    allowed = list(config["correction"]["allowed_changed_columns"])
    event_changes = assert_correction_only(
        event_registry,
        pd.read_parquet(inputs["previous_v3_events"]),
        keys=["event_id"],
        allowed_changed_columns=allowed,
        name="Expanded event registry",
    )
    action_changes = assert_correction_only(
        dataset,
        pd.read_parquet(inputs["previous_v3_actions"]),
        keys=["candidate_id"],
        allowed_changed_columns=allowed,
        name="Expanded action dataset",
    )
    assert_exact_frame(
        splits,
        pd.read_parquet(inputs["previous_v3_splits"]),
        keys=["fold_id", "structural_episode_id"],
        name="Expanded split assignments",
    )
    if dataset["prior_events_1h"].max() > int(
        config["correction"]["maximum_prior_events_1h"]
    ) or dataset["prior_events_4h"].max() > int(
        config["correction"]["maximum_prior_events_4h"]
    ):
        raise ValueError("Expanded V4 corrected prior count exceeds its bound")

    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "contract_lock": lock_path,
        "event_registry": output / config["outputs"]["event_registry"],
        "action_dataset": output / config["outputs"]["action_dataset"],
        "split_assignments": output / config["outputs"]["split_assignments"],
        "population_audit": output / config["outputs"]["population_audit"],
        "overlap_audit": output / config["outputs"]["overlap_audit"],
    }
    event_registry.to_parquet(paths["event_registry"], index=False)
    dataset.to_parquet(paths["action_dataset"], index=False)
    splits.to_parquet(paths["split_assignments"], index=False)
    audit["changed_rows_vs_v3"] = {
        "event_registry": event_changes,
        "action_dataset": action_changes,
    }
    audit["split_assignments_match_v3"] = True
    write_json(paths["population_audit"], audit)
    write_json(paths["overlap_audit"], overlap)
    manifest = {
        "schema_version": config["schema_version"],
        "decision": audit["decision"],
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "inputs": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for name, path in inputs.items()
        },
        "artifacts": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for name, path in paths.items()
        },
        "counts": {
            "events": len(event_registry),
            "actions": len(dataset),
            "structural_episodes": dataset["structural_episode_id"].nunique(),
            "stressed_winners": int(dataset["stress_net_r_positive"].sum()),
            "stressed_failures": int((~dataset["stress_net_r_positive"]).sum()),
        },
        "authorization": config["authorization"],
    }
    manifest_path = output / config["outputs"]["manifest"]
    write_json(manifest_path, manifest)
    print(json.dumps(audit, indent=2, sort_keys=True, default=str))
    print(json.dumps(overlap, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

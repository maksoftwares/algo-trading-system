from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.dataset_v3 import (
    build_overlap_audit,
    build_population_audit,
    build_primary_population,
    build_split_assignments,
    resolve_inputs,
    sha256_file,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "expanded_candidate_dataset_v3.json"


def verify_lock(config: dict, lock: dict) -> None:
    if sha256_file(CONFIG_PATH) != lock["config_sha256"]:
        raise ValueError("V3 configuration changed after contract lock")
    if sha256_file(ROOT / "PREREGISTRATION.md") != lock["preregistration_sha256"]:
        raise ValueError("V3 preregistration changed after contract lock")
    for name, spec in lock["implementation"].items():
        path = REPO_ROOT / spec["path"]
        if sha256_file(path) != spec["sha256"]:
            raise ValueError(f"V3 implementation changed after lock: {name}")
    if any(
        config["authorization"].get(key)
        for key in config["authorization"]
        if key != "research_only"
    ):
        raise ValueError("V3 has an unexpected runtime authorization")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before building V3")
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
    overlap = build_overlap_audit(event_registry, dataset, canonical, journey)
    if audit["forbidden_features_present"]:
        raise ValueError("A forbidden field entered the model feature surface")

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

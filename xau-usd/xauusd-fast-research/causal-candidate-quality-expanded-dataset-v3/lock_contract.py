from __future__ import annotations

import json
from pathlib import Path

from src.dataset_v3 import (
    canonical_json_sha256,
    resolve_inputs,
    sha256_file,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "expanded_candidate_dataset_v3.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inputs = resolve_inputs(REPO_ROOT, config)
    implementation = {
        name: {
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": sha256_file(path),
        }
        for name, path in {
            "dataset_v3": ROOT / "src" / "dataset_v3.py",
            "build_dataset": ROOT / "build_dataset.py",
            "verify": ROOT / "verify.py",
        }.items()
    }
    payload = {
        "schema_version": config["schema_version"],
        "config_sha256": sha256_file(CONFIG_PATH),
        "preregistration_sha256": sha256_file(ROOT / "PREREGISTRATION.md"),
        "input_sha256": {name: sha256_file(path) for name, path in inputs.items()},
        "implementation": implementation,
        "model_feature_sha256": canonical_json_sha256(config["model_features"]),
        "fold_definition_sha256": canonical_json_sha256(config["folds"]),
        "episode_definition": {
            "gap_minutes": int(config["episode_gap_minutes"]),
            "weight": "ONE_DIV_RESOLVED_EVENTS_IN_EPISODE_DIV_ACTIONS_FOR_EVENT",
        },
        "authorization": config["authorization"],
    }
    payload["definition_contract_sha256"] = canonical_json_sha256(payload)
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    path = output / config["outputs"]["contract_lock"]
    write_json(path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

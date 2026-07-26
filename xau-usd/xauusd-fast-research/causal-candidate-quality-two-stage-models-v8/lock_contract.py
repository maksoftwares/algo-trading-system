from __future__ import annotations

import json
from pathlib import Path
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.action_models import (
    canonical_json_sha256,
    resolve_inputs,
    sha256_file,
    write_json,
)
from src.adaptive_models import assert_adaptive_v5_parity
from src.interaction_features import (
    ACTION_DESCRIPTOR_COLUMNS,
    INTERACTION_ACTIONS,
    event_feature_columns,
    interaction_feature_columns,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "two_stage_models_v8.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inputs = resolve_inputs(REPO_ROOT, config)
    v4_config = json.loads(inputs["v4_dataset_config"].read_text(encoding="utf-8"))
    reference = json.loads(
        inputs["reference_adaptive_v5_config"].read_text(encoding="utf-8")
    )
    base_method_hash = assert_adaptive_v5_parity(config, reference)
    base_features = list(v4_config["model_features"])
    base_feature_hash = canonical_json_sha256(base_features)
    if base_feature_hash != config["expected"]["base_model_feature_sha256"]:
        raise ValueError("Two-Stage V8 base model feature surface changed")
    interaction_contract = config["interaction_contract"]
    if list(ACTION_DESCRIPTOR_COLUMNS) != interaction_contract[
        "excluded_action_descriptors"
    ]:
        raise ValueError("Two-Stage V8 action descriptor contract changed")
    configured_actions = [
        (row["name"], row["indicator"])
        for row in interaction_contract["interaction_actions"]
    ]
    if list(INTERACTION_ACTIONS) != configured_actions:
        raise ValueError("Two-Stage V8 interaction action contract changed")
    event_features = event_feature_columns(base_features)
    interaction_features = interaction_feature_columns(base_features)
    features = [*base_features, *interaction_features]
    if len(event_features) != int(config["expected"]["event_feature_count"]):
        raise ValueError("Two-Stage V8 event feature count changed")
    event_feature_hash = canonical_json_sha256(event_features)
    if event_feature_hash != str(
        config["expected"]["event_model_feature_sha256"]
    ):
        raise ValueError("Two-Stage V8 event model feature surface changed")
    if len(interaction_features) != int(
        config["expected"]["interaction_feature_count"]
    ):
        raise ValueError("Two-Stage V8 interaction feature count changed")
    if len(features) != int(config["expected"]["model_feature_count"]):
        raise ValueError("Two-Stage V8 total feature count changed")
    feature_hash = canonical_json_sha256(features)
    expected_feature_hash = str(config["expected"]["model_feature_sha256"])
    if feature_hash != expected_feature_hash:
        raise ValueError("Two-Stage V8 model feature surface changed")
    shared_code_hash = sha256_file(ROOT / "src" / "action_models.py")
    if (
        shared_code_hash
        != config["adaptation_contract"]["expected_shared_model_code_sha256"]
    ):
        raise ValueError("Two-Stage V8 shared model mechanics differ from Adaptive V5")
    implementation_paths = {
        "action_models": ROOT / "src" / "action_models.py",
        "adaptive_models": ROOT / "src" / "adaptive_models.py",
        "interaction_features": ROOT / "src" / "interaction_features.py",
        "two_stage": ROOT / "src" / "two_stage.py",
        "run_evaluation": ROOT / "run_evaluation.py",
        "verify": ROOT / "verify.py",
    }
    payload = {
        "schema_version": config["schema_version"],
        "config_sha256": sha256_file(CONFIG_PATH),
        "preregistration_sha256": sha256_file(ROOT / "PREREGISTRATION.md"),
        "input_sha256": {name: sha256_file(path) for name, path in inputs.items()},
        "implementation": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for name, path in implementation_paths.items()
        },
        "model_feature_sha256": feature_hash,
        "event_model_feature_sha256": event_feature_hash,
        "base_model_feature_sha256": base_feature_hash,
        "expected_model_feature_sha256": expected_feature_hash,
        "base_method_contract_sha256": base_method_hash,
        "shared_model_code_sha256": shared_code_hash,
        "model_specification_sha256": canonical_json_sha256(config["ridge_model"]),
        "training_variant_sha256": canonical_json_sha256(config["training_variants"]),
        "lane_ownership_sha256": canonical_json_sha256(config["lane_ownership"]),
        "policy_sha256": canonical_json_sha256(
            {
                "tie_order": config["action_tie_order"],
                "retention_quantiles": config["retention_quantiles"],
                "calibration_gates": config["calibration_gates"],
            }
        ),
        "acceptance_gate_sha256": canonical_json_sha256(config["acceptance_gates"]),
        "incremental_gate_sha256": canonical_json_sha256(
            config["incremental_gates_vs_v5"]
        ),
        "interaction_contract_sha256": canonical_json_sha256(
            config["interaction_contract"]
        ),
        "interaction_feature_sha256": canonical_json_sha256(interaction_features),
        "two_stage_contract_sha256": canonical_json_sha256(
            config["two_stage_contract"]
        ),
        "bootstrap_sha256": canonical_json_sha256(config["bootstrap"]),
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
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

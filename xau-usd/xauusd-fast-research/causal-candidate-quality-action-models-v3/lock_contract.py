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


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "action_models_v3.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inputs = resolve_inputs(REPO_ROOT, config)
    v3_config = json.loads(inputs["v3_dataset_config"].read_text(encoding="utf-8"))
    feature_hash = canonical_json_sha256(v3_config["model_features"])
    expected_feature_hash = str(config["expected"]["model_feature_sha256"])
    if feature_hash != expected_feature_hash:
        raise ValueError("V3 model feature surface changed")
    implementation_paths = {
        "action_models": ROOT / "src" / "action_models.py",
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
        "expected_model_feature_sha256": expected_feature_hash,
        "model_specification_sha256": canonical_json_sha256(config["models"]),
        "lane_ownership_sha256": canonical_json_sha256(config["lane_ownership"]),
        "policy_sha256": canonical_json_sha256(
            {
                "tie_order": config["action_tie_order"],
                "retention_quantiles": config["retention_quantiles"],
                "calibration_gates": config["calibration_gates"],
            }
        ),
        "acceptance_gate_sha256": canonical_json_sha256(config["acceptance_gates"]),
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

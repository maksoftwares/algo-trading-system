from __future__ import annotations

import json
from pathlib import Path
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.loss_only import (
    canonical_json_sha256,
    resolve_inputs,
    sha256_file,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "loss_signature_one_class_v1.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inputs = resolve_inputs(REPO_ROOT, config)
    v4_config = json.loads(inputs["v4_dataset_config"].read_text(encoding="utf-8"))
    features = list(v4_config["model_features"])
    feature_hash = canonical_json_sha256(features)
    if len(features) != int(config["population"]["feature_count"]):
        raise ValueError("Feature count changed")
    if feature_hash != str(config["population"]["feature_sha256"]):
        raise ValueError("Feature surface changed")
    implementation_paths = {
        "loss_only": ROOT / "src" / "loss_only.py",
        "run_experiment": ROOT / "run_experiment.py",
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
        "feature_sha256": feature_hash,
        "model_sha256": canonical_json_sha256(config["training"]["model"]),
        "threshold_sha256": canonical_json_sha256(
            {
                "primary": config["training"]["primary_weighted_loss_quantile"],
                "diagnostics": config["training"]["diagnostic_weighted_loss_quantiles"],
            }
        ),
        "acceptance_sha256": canonical_json_sha256(config["acceptance_gates"]),
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
    write_json(output / config["outputs"]["contract_lock"], payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

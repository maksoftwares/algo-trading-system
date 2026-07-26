from __future__ import annotations

import json
from pathlib import Path
import platform

import joblib
import numpy as np
import pandas as pd
import sklearn

from src.expected_r import (
    canonical_json_sha256,
    feature_surface,
    resolve_inputs,
    sha256_file,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "canonical_expected_r_v10.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inputs = resolve_inputs(REPO_ROOT, config)
    step_2b = json.loads(inputs["step_2b_contract"].read_text(encoding="utf-8"))
    raw_features, numeric_features = feature_surface(step_2b, config)
    implementation_paths = {
        "expected_r": ROOT / "src" / "expected_r.py",
        "run_evaluation": ROOT / "run_evaluation.py",
        "score_candidates": ROOT / "score_candidates.py",
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
        "feature_sha256": canonical_json_sha256(
            {"raw": raw_features, "numeric": numeric_features}
        ),
        "raw_feature_count": len(raw_features),
        "numeric_feature_count": len(numeric_features),
        "model_sha256": canonical_json_sha256(config["model"]),
        "threshold_sha256": canonical_json_sha256(config["threshold"]),
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
    output = ROOT / str(config["outputs"]["directory"])
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / str(config["outputs"]["contract_lock"]), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

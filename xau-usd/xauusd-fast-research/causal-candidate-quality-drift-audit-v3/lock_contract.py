from __future__ import annotations

import json
import platform
from importlib.metadata import version
from pathlib import Path

from src.drift import canonical_json_sha256, resolve_inputs, sha256_file, write_json


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "drift_audit_v3.json"


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    inputs = resolve_inputs(REPO_ROOT, config)
    v3_config = json.loads(inputs["v3_dataset_config"].read_text(encoding="utf-8"))
    feature_sha256 = canonical_json_sha256(v3_config["model_features"])
    if feature_sha256 != config["expected"]["model_feature_sha256"]:
        raise ValueError("V3 model feature hash changed")
    implementation = {
        name: {
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": sha256_file(path),
        }
        for name, path in {
            "drift": ROOT / "src" / "drift.py",
            "run_audit": ROOT / "run_audit.py",
            "verify": ROOT / "verify.py",
        }.items()
    }
    versions = {
        "python": platform.python_version(),
        "joblib": version("joblib"),
        "numpy": version("numpy"),
        "pandas": version("pandas"),
        "scikit_learn": version("scikit-learn"),
        "scipy": version("scipy"),
    }
    input_sha256 = {name: sha256_file(path) for name, path in inputs.items()}
    definition = {
        "schema_version": config["schema_version"],
        "inputs": input_sha256,
        "feature_sha256": feature_sha256,
        "periods": config["periods"],
        "sessions_utc": config["sessions_utc"],
        "numeric_drift": config["numeric_drift"],
        "categorical_drift": config["categorical_drift"],
        "failure_rules": config["failure_rules"],
        "authorization": config["authorization"],
        "implementation": implementation,
        "versions": versions,
    }
    lock = {
        "schema_version": config["schema_version"],
        "config_sha256": sha256_file(CONFIG_PATH),
        "preregistration_sha256": sha256_file(ROOT / "PREREGISTRATION.md"),
        "input_sha256": input_sha256,
        "model_feature_sha256": feature_sha256,
        "implementation": implementation,
        "versions": versions,
        "definition_contract_sha256": canonical_json_sha256(definition),
        "authorization": config["authorization"],
    }
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    write_json(output / config["outputs"]["contract_lock"], lock)
    print(json.dumps(lock, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

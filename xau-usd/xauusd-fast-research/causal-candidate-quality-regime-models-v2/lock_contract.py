from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
V1_SRC = PACKAGE.parent / "causal-candidate-quality-ml-v1" / "src"
sys.path.insert(0, str(V1_SRC))

from step_3_common import (  # noqa: E402
    canonical_json_sha256,
    sha256_file,
    verify_bound_file,
    write_json,
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config_path = PACKAGE / "config" / "regime_models_v2.json"
    contract = load_json(config_path)
    controls = contract["controls"]
    required_true = ("offline_training_authorized",)
    required_false = (
        "hyperparameter_search_authorized",
        "test_driven_family_pooling_authorized",
        "journey_rows_enter_fit",
        "comex_used",
        "databento_api_access_authorized",
        "new_data_acquisition_authorized",
        "demo_outcomes_enter_fit",
        "runtime_change_authorized",
        "ml_shadow_or_execution_authorized",
    )
    failed = [name for name in required_true if not controls[name]]
    failed.extend(name for name in required_false if controls[name])
    if failed:
        raise ValueError(f"Regime V2 controls fail closed: {failed}")
    bound = {
        name: verify_bound_file(REPO, spec, name)
        for name, spec in contract["bound_inputs"].items()
    }
    if load_json(bound["step_4_result"])["decision"] != "MODEL_EVIDENCE_GATE_FAIL":
        raise ValueError("The bound V1 pooled-model result is not the recorded failure")

    implementation_paths = [
        "run_evaluation.py",
        "src/regime_model.py",
        "src/regime_runner.py",
        "../causal-candidate-quality-ml-v1/src/step_3_common.py",
        "../causal-candidate-quality-ml-v1/src/step_4_metrics.py",
        "../causal-candidate-quality-ml-v1/src/step_4_bootstrap.py",
    ]
    definition = {
        "config_sha256": sha256_file(config_path),
        "preregistration_sha256": sha256_file(PACKAGE / "PREREGISTRATION.md"),
        "requirements_sha256": sha256_file(PACKAGE / "requirements.txt"),
        "bound_inputs": {
            name: sha256_file(path) for name, path in sorted(bound.items())
        },
        "implementation_sha256": {
            relative: sha256_file((PACKAGE / relative).resolve())
            for relative in implementation_paths
        },
        "expected_trainable_folds": contract["availability"][
            "expected_trainable_folds"
        ],
        "features": contract["features"],
        "model": contract["model"],
        "threshold_policy": contract["threshold_policy"],
        "acceptance_gates": contract["acceptance_gates"],
        "runtime_authorized": False,
    }
    output_dir = PACKAGE / str(contract["outputs"]["directory"])
    lock_path = output_dir / str(contract["outputs"]["contract_lock"])
    result_path = output_dir / str(contract["outputs"]["result_json"])
    if result_path.exists():
        raise ValueError("Regime V2 result already exists; refusing to relock")
    payload = {
        "schema_version": "xauusd_regime_v2_contract_lock_v1",
        "decision": "REGIME_V2_CONTRACT_LOCKED",
        "locked_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": canonical_json_sha256(definition),
        "definition": definition,
        "historical_outcomes_already_exposed": True,
        "runtime_changed": False,
        "next_action": "RUN_LOCKED_REGIME_V2_EVALUATION",
    }
    if lock_path.exists():
        existing = load_json(lock_path)
        if existing["definition_contract_sha256"] == payload["definition_contract_sha256"]:
            print(json.dumps(existing, indent=2, sort_keys=True))
            return
        raise ValueError("Existing Regime V2 prelock differs")
    write_json(lock_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

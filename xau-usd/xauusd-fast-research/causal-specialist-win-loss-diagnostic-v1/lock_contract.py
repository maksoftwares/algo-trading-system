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
    config_path = PACKAGE / "config" / "specialist_win_loss_v1.json"
    config = load_json(config_path)
    controls = config["controls"]
    if not controls["historical_outcomes_already_exposed"]:
        raise ValueError("This package cannot claim outcome-blind preregistration")
    required_false = [
        "model_training_authorized",
        "threshold_fitting_authorized",
        "portfolio_simulation_authorized",
        "runtime_change_authorized",
        "ml_shadow_or_execution_authorized",
        "databento_api_access_authorized",
        "new_data_acquisition_authorized",
        "comex_features_authorized",
    ]
    if any(bool(controls[name]) for name in required_false):
        raise ValueError("Exploratory diagnostic controls do not fail closed")
    bound = {
        name: verify_bound_file(REPO, spec, name)
        for name, spec in config["bound_inputs"].items()
    }
    implementation_paths = [
        "run_analysis.py",
        "src/diagnostic.py",
        "../causal-candidate-quality-ml-v1/src/step_3_common.py",
    ]
    definition = {
        "config_sha256": sha256_file(config_path),
        "analysis_contract_sha256": sha256_file(
            PACKAGE / "EXPLORATORY_ANALYSIS_CONTRACT.md"
        ),
        "requirements_sha256": sha256_file(PACKAGE / "requirements.txt"),
        "bound_inputs": {
            name: sha256_file(path) for name, path in sorted(bound.items())
        },
        "implementation_sha256": {
            relative: sha256_file((PACKAGE / relative).resolve())
            for relative in implementation_paths
        },
        "features": config["features"],
        "matching": config["matching"],
        "walk_forward": config["walk_forward"],
        "bootstrap": config["bootstrap"],
        "lead_gates": config["lead_gates"],
        "historical_outcomes_already_exposed": True,
        "runtime_authorized": False,
    }
    outputs = config["outputs"]
    output_dir = PACKAGE / outputs["directory"]
    lock_path = output_dir / outputs["contract_lock"]
    result_path = output_dir / outputs["result_json"]
    if result_path.exists():
        raise ValueError("Diagnostic result already exists; refusing to relock")
    payload = {
        "schema_version": "xauusd_causal_specialist_win_loss_lock_v1",
        "decision": "SPECIALIST_WIN_LOSS_V1_EXPLORATORY_CONTRACT_LOCKED",
        "locked_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": canonical_json_sha256(definition),
        "definition": definition,
        "historical_outcomes_already_exposed": True,
        "runtime_changed": False,
        "next_action": "RUN_LOCKED_EXPLORATORY_DIAGNOSTIC",
    }
    if lock_path.exists():
        existing = load_json(lock_path)
        if (
            existing["definition_contract_sha256"]
            == payload["definition_contract_sha256"]
        ):
            print(json.dumps(existing, indent=2, sort_keys=True))
            return
        raise ValueError("Existing diagnostic lock differs")
    write_json(lock_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

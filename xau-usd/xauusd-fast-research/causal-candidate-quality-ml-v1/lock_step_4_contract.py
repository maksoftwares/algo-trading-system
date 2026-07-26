from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(PACKAGE / "src"))

from step_3_common import (  # noqa: E402
    canonical_json_sha256,
    sha256_file,
    verify_bound_file,
    write_json,
)
from step_4_model import feature_names_for_blocks  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    import sklearn

    config_path = PACKAGE / "config/step_4_model_evaluation_contract_v1.json"
    config = load_json(config_path)
    if "__" in config_path.read_text(encoding="utf-8"):
        raise ValueError("Step 4 contract still contains unbound placeholders")
    controls = config["controls"]
    required_true = (
        "model_training_authorized",
        "probability_calibration_authorized",
        "threshold_fitting_authorized",
        "untouched_test_evaluation_authorized",
    )
    required_false = (
        "hyperparameter_search_authorized",
        "comex_features_authorized",
        "databento_api_access_authorized",
        "new_data_acquisition_authorized",
        "journey_rows_enter_primary_fit",
        "portfolio_simulation_authorized",
        "runtime_change_authorized",
        "shadow_or_demo_activation_authorized",
    )
    failed = [name for name in required_true if not controls[name]]
    failed.extend(name for name in required_false if controls[name])
    if failed:
        raise ValueError(f"Step 4 controls fail closed: {failed}")

    bound = {
        name: verify_bound_file(REPO, spec, name)
        for name, spec in config["bound_inputs"].items()
    }
    step2b = load_json(bound["step_2b_contract"])
    step3 = load_json(bound["step_3_result"])
    if (
        step3["decision"]
        != "STEP_3_COUNTERFACTUAL_LABEL_AND_CAUSAL_FEATURE_BUILD_COMPLETE"
    ):
        raise ValueError("Step 3 is not complete")
    if step3["next_stage_authorized"] != config["stage"]:
        raise ValueError("Step 3 did not authorize this Step 4 stage")
    if step3["runtime_changed"] or step3["model_fitted"]:
        raise ValueError("Step 3 control state is inconsistent")

    forbidden: list[str] = []
    feature_counts: dict[str, int] = {}
    for spec in config["models"]["specifications"]:
        names = feature_names_for_blocks(step2b, spec["feature_blocks"])
        feature_counts[str(spec["model_id"])] = len(names)
        forbidden.extend(name for name in names if name.startswith("gc_"))
    if forbidden:
        raise ValueError(f"COMEX features entered Step 4: {sorted(set(forbidden))}")

    outputs = config["outputs"]
    output_dir = PACKAGE / str(outputs["directory"])
    lock_path = output_dir / str(outputs["contract_lock"])
    predictions = output_dir / str(outputs["fold_predictions"])
    if predictions.exists():
        raise ValueError("Model outcomes already exist; refusing to relock")
    implementation_paths = [
        "run_step_4.py",
        "src/step_3_common.py",
        "src/step_4_bootstrap.py",
        "src/step_4_metrics.py",
        "src/step_4_model.py",
        "src/step_4_runner.py",
    ]
    definition = {
        "config_sha256": sha256_file(config_path),
        "preregistration_sha256": sha256_file(PACKAGE / "STEP_4_PREREGISTRATION.md"),
        "requirements_sha256": sha256_file(PACKAGE / "requirements-step4.txt"),
        "bound_inputs": {
            name: sha256_file(path) for name, path in sorted(bound.items())
        },
        "scikit_learn_version": sklearn.__version__,
        "feature_counts": feature_counts,
        "implementation_sha256": {
            relative: sha256_file(PACKAGE / relative)
            for relative in implementation_paths
        },
        "primary_model_id": config["models"]["primary_model_id"],
        "comex_features_authorized": False,
        "databento_api_access_authorized": False,
    }
    payload = {
        "schema_version": "xauusd_step_4_model_evaluation_contract_lock_v1",
        "decision": "STEP_4_MODEL_EVALUATION_CONTRACT_LOCKED",
        "locked_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": canonical_json_sha256(definition),
        "definition": definition,
        "economic_outcomes_already_opened_in_step_3": True,
        "model_fitted": False,
        "test_predictions_opened": False,
        "runtime_changed": False,
        "next_action": "RUN_LOCKED_STEP_4_EVALUATION",
    }
    if lock_path.exists():
        existing = load_json(lock_path)
        if (
            existing["definition_contract_sha256"]
            == payload["definition_contract_sha256"]
        ):
            print(json.dumps(existing, indent=2, sort_keys=True))
            return
        model_dir = output_dir / str(outputs["model_directory"])
        if any(model_dir.glob("*.joblib")) or existing.get("model_fitted"):
            raise ValueError("Cannot supersede Step 4 lock after a model fit")
        old_sha = sha256_file(lock_path)
        write_json(
            output_dir / "STEP_4_PRELOCK_SUPERSESSION_1.json",
            {
                "schema_version": "xauusd_step_4_prelock_supersession_v1",
                "superseded_lock_sha256": old_sha,
                "reason": "PRE_MODEL_PREFLIGHT_BOUND_IMPLEMENTATION_AND_FIXED_SPLIT_MERGE",
                "model_fitted_before_supersession": False,
                "test_predictions_opened_before_supersession": False,
                "runtime_changed": False,
            },
        )
        payload["supersedes_lock_sha256"] = old_sha
    write_json(lock_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

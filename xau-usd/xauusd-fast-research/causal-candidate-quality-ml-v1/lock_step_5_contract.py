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
from step_5_portfolio import build_market_manifest  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config_path = (
        PACKAGE / "config" / "step_5_shared_account_portfolio_contract_v1.json"
    )
    contract = load_json(config_path)
    controls = contract["controls"]
    required_true = (
        "portfolio_simulation_authorized",
        "historical_outcomes_already_exposed",
    )
    required_false = (
        "post_result_policy_tuning_authorized",
        "ml_predictions_used",
        "ml_thresholds_used",
        "journey_rows_used",
        "comex_used",
        "databento_api_access_authorized",
        "new_data_acquisition_authorized",
        "runtime_change_authorized",
        "shadow_demo_or_live_authorized",
    )
    failed = [name for name in required_true if not controls[name]]
    failed.extend(name for name in required_false if controls[name])
    if failed:
        raise ValueError(f"Step 5 controls fail closed: {failed}")
    bound = {
        name: verify_bound_file(REPO, spec, name)
        for name, spec in contract["bound_inputs"].items()
    }
    step3 = load_json(bound["step_3_result"])
    step4 = load_json(bound["step_4_result"])
    acceptance4 = load_json(bound["step_4_acceptance"])
    if step3["decision"] != "STEP_3_COUNTERFACTUAL_LABEL_AND_CAUSAL_FEATURE_BUILD_COMPLETE":
        raise ValueError("Step 3 is not complete")
    if step4["decision"] != "MODEL_EVIDENCE_GATE_FAIL":
        raise ValueError("Step 4 failure decision is not frozen")
    if acceptance4["runtime_authorized"]:
        raise ValueError("Step 4 authorized runtime unexpectedly")

    output_dir = PACKAGE / str(contract["outputs"]["directory"])
    output_dir.mkdir(parents=True, exist_ok=True)
    lock_path = output_dir / str(contract["outputs"]["contract_lock"])
    result_path = output_dir / str(contract["outputs"]["result_json"])
    if result_path.exists():
        raise ValueError("Step 5 result already exists; refusing to relock")
    implementation_paths = [
        "run_step_5.py",
        "src/step_3_common.py",
        "src/step_5_metrics.py",
        "src/step_5_portfolio.py",
        "src/step_5_runner.py",
    ]
    market_manifest = build_market_manifest(contract["market_data"])
    definition = {
        "config_sha256": sha256_file(config_path),
        "preregistration_sha256": sha256_file(PACKAGE / "STEP_5_PREREGISTRATION.md"),
        "requirements_sha256": sha256_file(PACKAGE / "requirements-step5.txt"),
        "bound_inputs": {
            name: sha256_file(path) for name, path in sorted(bound.items())
        },
        "implementation_sha256": {
            relative: sha256_file(PACKAGE / relative)
            for relative in implementation_paths
        },
        "market_source_manifest": market_manifest,
        "primary_policy_id": contract["acceptance_gates"]["primary_policy_id"],
        "policy_ids": [policy["policy_id"] for policy in contract["policies"]],
        "ml_predictions_used": False,
        "databento_api_access_authorized": False,
    }
    payload = {
        "schema_version": "xauusd_step_5_shared_account_contract_lock_v1",
        "decision": "STEP_5_SHARED_ACCOUNT_CONTRACT_LOCKED",
        "locked_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": canonical_json_sha256(definition),
        "definition": definition,
        "candidate_outcomes_already_exposed": True,
        "portfolio_result_opened": False,
        "runtime_changed": False,
        "next_action": "RUN_LOCKED_STEP_5_PORTFOLIO_EVALUATION",
    }
    if lock_path.exists():
        existing = load_json(lock_path)
        if existing["definition_contract_sha256"] == payload["definition_contract_sha256"]:
            print(json.dumps(existing, indent=2, sort_keys=True))
            return
        raise ValueError("Existing Step 5 prelock differs; inspect before superseding")
    write_json(lock_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

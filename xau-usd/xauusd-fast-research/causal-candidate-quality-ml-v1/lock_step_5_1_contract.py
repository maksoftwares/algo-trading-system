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


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config_path = (
        PACKAGE / "config" / "step_5_1_account_currency_correction_v1.json"
    )
    contract = load_json(config_path)
    controls = contract["controls"]
    required_true = (
        "corrective_recalculation_authorized",
        "step_5_result_superseded_for_account_specific_claims",
    )
    required_false = (
        "strategy_or_governor_logic_change_authorized",
        "risk_fraction_change_authorized",
        "post_result_tuning_authorized",
        "ml_used",
        "comex_used",
        "databento_api_access_authorized",
        "new_market_data_acquisition_authorized",
        "broker_order_action_authorized",
        "runtime_change_authorized",
        "shadow_demo_or_live_authorized",
    )
    failed = [name for name in required_true if not controls[name]]
    failed.extend(name for name in required_false if controls[name])
    if failed:
        raise ValueError(f"Step 5.1 controls fail closed: {failed}")
    bound = {
        name: verify_bound_file(REPO, spec, name)
        for name, spec in contract["bound_inputs"].items()
    }
    step_5 = load_json(bound["step_5_result"])
    if step_5["decision"] != "STEP_5_HISTORICAL_PORTFOLIO_GATE_PASS_RESEARCH_ONLY":
        raise ValueError("Step 5 source result is unexpected")
    output_dir = PACKAGE / str(contract["outputs"]["directory"])
    snapshot_path = output_dir / str(contract["outputs"]["broker_snapshot"])
    if not snapshot_path.is_file():
        raise FileNotFoundError(snapshot_path)
    snapshot = load_json(snapshot_path)
    expected = contract["broker_snapshot"]
    if int(snapshot["account"]["login"]) != int(expected["expected_login"]):
        raise ValueError("Wrong broker snapshot login")
    if snapshot["account"]["server"] != expected["expected_server"]:
        raise ValueError("Wrong broker snapshot server")
    if snapshot["account"]["currency"] != expected["expected_account_currency"]:
        raise ValueError("Wrong broker snapshot currency")
    if snapshot["symbol"]["name"] != expected["expected_symbol"]:
        raise ValueError("Wrong broker snapshot symbol")
    if snapshot["symbol"]["currency_profit"] != expected["expected_symbol_profit_currency"]:
        raise ValueError("Wrong symbol profit currency")
    if snapshot["open_positions"] or snapshot["pending_orders"]:
        raise ValueError("Broker snapshot is not flat")
    if snapshot["broker_action_performed"]:
        raise ValueError("Broker snapshot performed an action")
    lock_path = output_dir / str(contract["outputs"]["contract_lock"])
    result_path = output_dir / str(contract["outputs"]["result_json"])
    if result_path.exists():
        raise ValueError("Step 5.1 result already exists; refusing to relock")
    implementation_paths = [
        "run_step_5_1.py",
        "src/step_3_common.py",
        "src/step_5_metrics.py",
        "src/step_5_portfolio.py",
        "src/step_5_1_account_currency.py",
        "src/step_5_1_runner.py",
    ]
    definition = {
        "config_sha256": sha256_file(config_path),
        "preregistration_sha256": sha256_file(PACKAGE / "STEP_5_1_PREREGISTRATION.md"),
        "requirements_sha256": sha256_file(PACKAGE / "requirements-step5-1.txt"),
        "broker_snapshot_sha256": sha256_file(snapshot_path),
        "bound_inputs": {
            name: sha256_file(path) for name, path in sorted(bound.items())
        },
        "implementation_sha256": {
            relative: sha256_file(PACKAGE / relative)
            for relative in implementation_paths
        },
        "account_login": snapshot["account"]["login"],
        "account_currency": snapshot["account"]["currency"],
        "starting_equity_account": min(
            snapshot["account"]["balance"], snapshot["account"]["equity"]
        ),
        "conversion": snapshot["conversion"],
        "primary_policy_id": contract["acceptance"]["primary_policy_id"],
        "broker_order_action_authorized": False,
    }
    payload = {
        "schema_version": "xauusd_step_5_1_account_currency_contract_lock_v1",
        "decision": "STEP_5_1_ACCOUNT_CURRENCY_CONTRACT_LOCKED",
        "locked_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": canonical_json_sha256(definition),
        "definition": definition,
        "historical_outcomes_already_exposed": True,
        "corrected_result_opened": False,
        "runtime_changed": False,
        "next_action": "RUN_LOCKED_STEP_5_1_AED_CORRECTION",
    }
    if lock_path.exists():
        existing = load_json(lock_path)
        if existing["definition_contract_sha256"] == payload["definition_contract_sha256"]:
            print(json.dumps(existing, indent=2, sort_keys=True))
            return
        raise ValueError("Existing Step 5.1 prelock differs")
    write_json(lock_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

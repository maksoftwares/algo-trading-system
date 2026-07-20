from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from evaluator import (  # noqa: E402
    canonical_hash,
    load_config,
    sha256_file,
    verify_source_contracts,
)


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_shared_account_forward_evaluator_v42.json",
    "src/__init__.py",
    "src/evaluator.py",
    "lock_contract.py",
    "run_evaluation.py",
    "tests/test_evaluator.py",
)


def record(path: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def main() -> int:
    config = load_config()
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("V42 contract already exists")
    package_paths = [ROOT / relative for relative in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    source_contracts = verify_source_contracts(config)
    v27 = config["sources"]["v27"]
    v27_root = (REPO_ROOT / str(v27["root"])).resolve()
    present_source_stages = [
        str(v27_root / str(v27[key]))
        for key in (
            "validation_audit",
            "validation_trades",
            "confirmation_audit",
            "confirmation_trades",
        )
        if (v27_root / str(v27[key])).exists()
    ]
    if present_source_stages:
        raise ValueError("V42 source stage economics existed before lock")
    for key in (
        "status",
        "validation_audit",
        "validation_trades",
        "confirmation_audit",
        "confirmation_trades",
    ):
        if (output / str(config["outputs"][key])).exists():
            raise ValueError(f"V42 output existed before lock: {key}")
    account = config["account_reference"]
    required_equity = float(
        account["historical_conservative_core_equity_drawdown_dollars"]
    ) / float(account["maximum_equity_drawdown_fraction"])
    if required_equity <= float(account["reference_equity_dollars"]):
        raise ValueError("V42 expected current account historical-risk failure changed")
    contract = {
        "schema_version": "xauusd_capital_shared_account_v42_contract_lock",
        "package_files": [record(path) for path in package_paths],
        "source_contracts": source_contracts,
        "source_stage_files_present_at_lock": present_source_stages,
        "forward_start_inclusive_utc": config["forward_start_inclusive_utc"],
        "portfolio": config["portfolio"],
        "account_reference": config["account_reference"],
        "stages": config["stages"],
        "research_gates": config["research_gates"],
        "historical_minimum_equity_required_dollars": required_equity,
        "economic_outcomes_present_at_lock": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(
        (json.dumps(contract, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    print(json.dumps(contract, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

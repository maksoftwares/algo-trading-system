from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from portfolio import (  # noqa: E402
    canonical_hash,
    load_config,
    sha256_file,
    verify_core_reference,
)


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_forward_family_portfolio_v27.json",
    "src/__init__.py",
    "src/portfolio.py",
    "lock_contract.py",
    "run_portfolio_evaluation.py",
    "tests/test_portfolio.py",
)


def record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(REPO.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def verify_component_contract(component: dict[str, Any]) -> Path:
    path = (REPO / component["contract_path"]).resolve()
    if sha256_file(path) != component["contract_file_sha256"]:
        raise ValueError(f"V27 component contract file changed: {path}")
    contract = json.loads(path.read_text(encoding="utf-8"))
    if canonical_hash(contract, "contract_sha256") != contract["contract_sha256"]:
        raise ValueError(f"V27 component contract self-hash changed: {path}")
    if contract["contract_sha256"] != component["contract_sha256"]:
        raise ValueError(f"V27 component contract identity changed: {path}")
    return path


def main() -> int:
    config = load_config(ROOT)
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V27 contract already exists")
    package_paths = [(ROOT / relative).resolve() for relative in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    component_contracts = [
        verify_component_contract(component)
        for component in config["components"].values()
    ]
    stage_paths = [
        (REPO / component[key]).resolve()
        for component in config["components"].values()
        for key in (
            "validation_audit",
            "validation_trades",
            "confirmation_audit",
            "confirmation_trades",
        )
    ]
    present_stage_paths = [
        path.relative_to(REPO).as_posix() for path in stage_paths if path.exists()
    ]
    if present_stage_paths:
        raise ValueError("V27 component stage economics existed before lock")
    for key in (
        "status",
        "validation_audit",
        "validation_trades",
        "confirmation_audit",
        "confirmation_trades",
    ):
        if (output / config["outputs"][key]).exists():
            raise ValueError(f"V27 output existed before lock: {key}")
    core_path = (REPO / config["core"]["ledger_path"]).resolve()
    if sha256_file(core_path) != config["core"]["ledger_sha256"]:
        raise ValueError("V27 frozen Core ledger changed")
    _, core_metrics = verify_core_reference(pd.read_parquet(core_path), config)
    multiple = config["multiple_testing"]
    expected_alpha = float(multiple["family_alpha"]) / int(
        multiple["registered_forward_claims"]
    )
    if abs(expected_alpha - float(multiple["maximum_one_sided_pvalue"])) > 1e-15:
        raise ValueError("V27 family alpha allocation is inconsistent")
    contract = {
        "schema_version": "xauusd_capital_forward_family_v27_contract_lock",
        "package_files": [record(path) for path in package_paths],
        "component_contracts": [record(path) for path in component_contracts],
        "core_ledger": record(core_path),
        "core_reference_metrics": core_metrics,
        "multiple_testing": multiple,
        "router": config["router"],
        "gates": config["gates"],
        "stages": config["stages"],
        "component_stage_files_present_at_lock": present_stage_paths,
        "component_economic_outcomes_present_at_lock": False,
        "portfolio_economic_outcomes_present_at_lock": False,
        "projected_frequency_uses_historical_core_reference": True,
        "floating_equity_drawdown_calculated": False,
        "same_version_tuning_authorized": False,
        "single_lane_fallback_authorized": False,
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

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from exhaustion_reversal import (  # noqa: E402
    canonical_hash,
    development_source_paths,
    frozen_v24_root,
    load_config,
    load_locked_v24,
    sha256_file,
)


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/capital_quote_exhaustion_reversal_v30.json",
    "src/__init__.py",
    "src/exhaustion_reversal.py",
    "prepare_calibration.py",
    "lock_contract.py",
    "run_development.py",
    "run_forward_evaluation.py",
    "tests/test_exhaustion_reversal.py",
)


def record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        label = resolved.relative_to(REPO.resolve()).as_posix()
    except ValueError:
        label = str(resolved).replace("\\", "/")
    return {
        "path": label,
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def main() -> int:
    config = load_config(ROOT)
    v24 = load_locked_v24(config)
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V30 contract already exists")
    calibration_path = output / config["outputs"]["calibration_audit"]
    candidate_path = output / config["outputs"]["calibration_candidates"]
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    if canonical_hash(calibration, "audit_sha256") != calibration["audit_sha256"]:
        raise ValueError("V30 calibration audit self-hash changed")
    if not calibration["calibration_structure_passed"]:
        raise ValueError("V30 calibration structure failed")
    forbidden = (
        calibration["post_candidate_prices_used_for_label_or_outcome"]
        or calibration["economic_outcomes_opened"]
        or calibration["pnl_calculated"]
    )
    if forbidden:
        raise ValueError("V30 calibration crossed its information boundary")
    if sha256_file(candidate_path) != calibration["candidate_file_sha256"]:
        raise ValueError("V30 calibration candidates changed")
    package_paths = [(ROOT / relative).resolve() for relative in PACKAGE_FILES]
    missing = [str(path) for path in package_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    development_paths = development_source_paths(config)
    if not development_paths:
        raise FileNotFoundError("V30 development packet is absent")
    for key in (
        "development_audit",
        "development_trades",
        "forward_inventory",
        "validation_trades",
        "confirmation_trades",
    ):
        path = output / config["outputs"][key]
        if path.exists():
            raise ValueError(f"V30 outcome existed before lock: {path}")
    for key in ("validation_audit", "confirmation_audit"):
        if (ROOT / config["forward"][key]).exists():
            raise ValueError(f"V30 outcome existed before lock: {key}")
    boundary = pd.Timestamp(config["forward"]["start_inclusive_utc"])
    forward_files = [
        str(path.resolve()).replace("\\", "/")
        for path in v24.discover_source_files(config)
        if v24.source_date(path) >= boundary
    ]
    if forward_files:
        raise ValueError("V30 forward source existed before contract lock")
    frozen = config["frozen_v24_1"]
    dependency_root = frozen_v24_root(config)
    dependency_paths = (
        dependency_root / str(frozen["config_relative"]),
        dependency_root / str(frozen["module_relative"]),
        dependency_root / str(frozen["contract_relative"]),
    )
    contract = {
        "schema_version": "xauusd_exhaustion_reversal_v30_contract_lock",
        "frozen_v24_1_contract_sha256": frozen["contract_sha256"],
        "candidate_definition": config["feature"],
        "episode_definition": config["episode"],
        "simulation_definition": config["simulation"],
        "data_quality_definition": config["data_quality"],
        "economic_gates": config["gates"],
        "multiple_testing": config["multiple_testing"],
        "package_files": [record(path) for path in package_paths],
        "dependency_files": [record(path) for path in dependency_paths],
        "development_source_files": [record(path) for path in development_paths],
        "calibration_candidates": record(candidate_path),
        "calibration_audit": record(calibration_path),
        "calibration_audit_sha256": calibration["audit_sha256"],
        "development_outcomes_opened_at_lock": False,
        "forward_start_inclusive_utc": config["forward"]["start_inclusive_utc"],
        "forward_files_present_at_lock": False,
        "hypothesis_count": 1,
        "parameter_grid_allowed": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    lock_path.write_bytes(
        (json.dumps(contract, allow_nan=False, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    print(json.dumps(contract, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

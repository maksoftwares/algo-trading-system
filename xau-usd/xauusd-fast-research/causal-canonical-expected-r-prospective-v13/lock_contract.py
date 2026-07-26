from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "expected_r_prospective_v13.json"
EVALUATOR_PATH = ROOT / "src" / "evaluator.py"


def load_evaluator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "expected_r_prospective_v13_lock_evaluator", EVALUATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(EVALUATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def record(path: Path, base: Path, evaluator: Any) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(base.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": evaluator.sha256_file(path),
    }


def main() -> int:
    evaluator = load_evaluator()
    config = evaluator.read_json(CONFIG_PATH)
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("Expected-R V13 contract already exists")
    now = datetime.now(timezone.utc)
    if (
        now
        >= evaluator.utc_timestamp(
            config["forward_start_inclusive_utc"]
        ).to_pydatetime()
    ):
        raise ValueError("Expected-R V13 must be locked before its boundary")

    package_files = (
        ".gitignore",
        "README.md",
        "PREREGISTRATION.md",
        "requirements.txt",
        "config/expected_r_prospective_v13.json",
        "src/__init__.py",
        "src/evaluator.py",
        "lock_contract.py",
        "run_evaluation.py",
        "verify.py",
        "tests/conftest.py",
        "tests/test_evaluator.py",
    )
    package_paths = [ROOT / value for value in package_files]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    dependencies = [REPO_ROOT / str(value) for value in config["contract_dependencies"]]
    if missing := [str(path) for path in dependencies if not path.is_file()]:
        raise FileNotFoundError(missing)
    evaluator.verify_config_hashes(config)
    payload = evaluator.load_model(config)
    if list(payload["families"]) != list(
        config["candidate_population"]["expected_model_families"]
    ):
        raise ValueError("Expected-R V13 model population changed before lock")
    prohibited = [
        key
        for key, value in config["research_controls"].items()
        if key.endswith("_authorized")
        and key != "individual_counterfactual_outcomes_authorized"
        and bool(value)
    ]
    if prohibited:
        raise ValueError(f"Prohibited authority enabled: {prohibited}")

    runtime = Path(str(config["runtime"]["directory"]))
    for key in (
        "score_ledger",
        "resolution_ledger",
        "day_quality_ledger",
        "validation_audit",
        "validation_trades",
        "confirmation_audit",
        "confirmation_trades",
    ):
        if (runtime / str(config["runtime"][key])).exists():
            raise ValueError(f"Prospective artifact existed before lock: {key}")

    contract = {
        "schema_version": "xauusd_expected_r_prospective_v13_contract",
        "created_at_utc": now.isoformat().replace("+00:00", "Z"),
        "forward_start_inclusive_utc": config["forward_start_inclusive_utc"],
        "package_files": [record(path, ROOT, evaluator) for path in package_paths],
        "dependencies": [
            record(path, REPO_ROOT, evaluator) for path in sorted(set(dependencies))
        ],
        "model": config["model"],
        "candidate_population": config["candidate_population"],
        "feature_geometry": config["feature_geometry"],
        "costs": config["costs"],
        "stages": config["stages"],
        "confidence": config["confidence"],
        "gates": config["gates"],
        "aggregate_economics_present_at_lock": False,
        "historical_model_refit_authorized": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "python_predictions_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    contract["contract_sha256"] = evaluator.canonical_hash(contract, "contract_sha256")
    output.mkdir(parents=True, exist_ok=True)
    evaluator.atomic_write_json(lock_path, contract)
    print(json.dumps(contract, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

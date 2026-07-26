from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src import evaluator

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG = ROOT / "config/macro_expected_r_prospective_v14.json"


def record(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(base.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": evaluator.sha256_file(path),
    }


def main() -> int:
    config = evaluator.read_json(CONFIG)
    boundary = evaluator.utc_timestamp(config["forward_start_inclusive_utc"])
    now = datetime.now(UTC)
    if now >= boundary.to_pydatetime():
        raise ValueError("V14 must be locked before its prospective boundary")
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("V14 contract already exists")
    package_files = (
        ".gitignore",
        "README.md",
        "PREREGISTRATION.md",
        "requirements.txt",
        "build_final_model.py",
        "config/macro_expected_r_prospective_v14.json",
        "src/__init__.py",
        "src/evaluator.py",
        "run_evaluation.py",
        "verify.py",
        "lock_contract.py",
        "tests/conftest.py",
        "tests/test_evaluator.py",
    )
    package_paths = [ROOT / value for value in package_files]
    dependencies = [REPO_ROOT / str(value) for value in config["contract_dependencies"]]
    missing = [
        str(path) for path in [*package_paths, *dependencies] if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(missing)
    evaluator.verify_config_hashes(config)
    payload = evaluator.load_model(config)
    if int(payload["fit_rows"]) < int(config["model"]["minimum_fit_rows"]):
        raise ValueError("V14 model fit is too small")
    if float(payload["fit_selected_weight_fraction"]) < float(
        config["model"]["minimum_fit_selected_weight_fraction"]
    ):
        raise ValueError("V14 model construction removed too much fit weight")
    controls = config["research_controls"]
    prohibited = [
        key
        for key, value in controls.items()
        if key.endswith("_authorized")
        and key != "prospective_research_scoring_authorized"
        and bool(value)
    ]
    if prohibited:
        raise ValueError(f"V14 prohibited authority enabled: {prohibited}")
    runtime = Path(str(config["runtime"]["directory"]))
    for key in ("score_ledger", "status", "upstream_prefix_state"):
        if (runtime / str(config["runtime"][key])).exists():
            raise ValueError(f"V14 prospective artifact existed before lock: {key}")
    contract = {
        "schema_version": "xauusd_macro_expected_r_prospective_v14_contract",
        "created_at_utc": now.isoformat().replace("+00:00", "Z"),
        "forward_start_inclusive_utc": config["forward_start_inclusive_utc"],
        "package_files": [record(path, ROOT) for path in package_paths],
        "dependencies": [record(path, REPO_ROOT) for path in sorted(set(dependencies))],
        "model": config["model"],
        "upstream": config["upstream"],
        "macro_source": config["macro_source"],
        "prospective_protocol": config["prospective_protocol"],
        "historical_outcomes_exposed_before_design": True,
        "post_outcome_parameter_selection_disclosed": True,
        "aggregate_economics_present_at_lock": False,
        "same_version_tuning_authorized": False,
        "model_refit_after_boundary_authorized": False,
        "prospective_research_scoring_authorized": True,
        "python_serving_authorized": False,
        "ml_shadow_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
    }
    contract["contract_sha256"] = evaluator.canonical_hash(contract, "contract_sha256")
    output.mkdir(parents=True, exist_ok=True)
    v13 = evaluator._load_v13(config)
    v13.atomic_write_json(lock_path, contract)
    print(json.dumps(contract, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

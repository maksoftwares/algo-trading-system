from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from absorption_release import (  # noqa: E402
    canonical_hash,
    development_source_paths,
    load_config,
    load_locked_transport,
    load_locked_v24,
    sha256_file,
)


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/absorption_release_v31.json",
    "src/__init__.py",
    "src/absorption_release.py",
    "prepare_calibration.py",
    "lock_contract.py",
    "run_development.py",
    "tests/test_absorption_release.py",
)


def record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(REPO.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def main() -> int:
    config = load_config(ROOT)
    load_locked_v24(config)
    load_locked_transport(config)
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V31 contract already exists")
    calibration_path = output / config["outputs"]["calibration_audit"]
    candidate_path = output / config["outputs"]["calibration_candidates"]
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    if canonical_hash(calibration, "audit_sha256") != calibration["audit_sha256"]:
        raise ValueError("V31 calibration audit changed")
    if not calibration["calibration_structure_passed"]:
        raise ValueError("V31 calibration structure failed")
    if (
        calibration["post_candidate_prices_used_for_label_or_outcome"]
        or calibration["economic_outcomes_opened"]
        or calibration["pnl_calculated"]
    ):
        raise ValueError("V31 calibration crossed its information boundary")
    if sha256_file(candidate_path) != calibration["candidate_file_sha256"]:
        raise ValueError("V31 calibration candidates changed")
    package_paths = [(ROOT / relative).resolve() for relative in PACKAGE_FILES]
    missing = [str(path) for path in package_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    development_paths = development_source_paths(config)
    if not development_paths:
        raise FileNotFoundError("V31 development packet is absent")
    for key in ("development_audit", "development_trades"):
        if (output / config["outputs"][key]).exists():
            raise ValueError("V31 development outcome existed before lock")
    dependency_paths: list[Path] = []
    for key in ("frozen_v24_1", "frozen_timestamp_adapter"):
        frozen = config[key]
        root = (ROOT / str(frozen["root_relative"])).resolve()
        for relative_key in (
            "config_relative",
            "module_relative",
            "contract_relative",
        ):
            if relative_key in frozen:
                dependency_paths.append(root / str(frozen[relative_key]))
    contract = {
        "schema_version": "xauusd_absorption_release_v31_contract_lock",
        "candidate_definition": config["feature"],
        "episode_definition": config["episode"],
        "simulation_definition": config["simulation"],
        "economic_gates": config["gates"],
        "multiple_testing": config["multiple_testing"],
        "package_files": [record(path) for path in package_paths],
        "dependency_files": [record(path) for path in dependency_paths],
        "development_source_files": [record(path) for path in development_paths],
        "calibration_candidates": record(candidate_path),
        "calibration_audit": record(calibration_path),
        "calibration_audit_sha256": calibration["audit_sha256"],
        "development_outcomes_opened_at_lock": False,
        "hypothesis_count": 1,
        "parameter_grid_allowed": False,
        "same_version_tuning_authorized": False,
        "model_training_authorized": False,
        "demo_authorized": False,
        "live_authorized": False,
        "broker_action_authorized": False,
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    lock_path.write_bytes(
        (
            json.dumps(contract, allow_nan=False, indent=2, sort_keys=True) + "\n"
        ).encode()
    )
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from catchup import canonical_hash, load_json, sha256_file  # noqa: E402


CONFIG = ROOT / "config" / "xag_xau_eventtime_catchup_v72.json"
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/xag_xau_eventtime_catchup_v72.json",
    "src/__init__.py",
    "src/catchup.py",
    "acquire_xag.py",
    "run_source_audit.py",
    "run_exam_source_audit.py",
    "run_calibration.py",
    "lock_contract.py",
    "run_stage.py",
    "tests/conftest.py",
    "tests/test_catchup.py",
)


def record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def build_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    package_paths = [ROOT / path for path in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    output = ROOT / str(config["outputs"]["directory"])
    source_path = output / str(config["outputs"]["source_audit"])
    calibration_path = output / str(config["outputs"]["calibration_audit"])
    source_audit = load_json(source_path)
    calibration = load_json(calibration_path)
    if (
        canonical_hash(source_audit, "audit_sha256") != source_audit.get("audit_sha256")
        or source_audit.get("decision") != "V72_SOURCE_AUDIT_PASS"
    ):
        raise ValueError("V72 source audit is invalid")
    if (
        canonical_hash(calibration, "audit_sha256") != calibration.get("audit_sha256")
        or calibration.get("decision") != "V72_CALIBRATION_POLICY_SELECTED"
        or calibration.get("selected_policy") is None
    ):
        raise ValueError("V72 calibration did not select a policy")
    feature_path = output / str(config["outputs"]["calibration_features"])
    grid_path = output / str(config["outputs"]["calibration_grid"])
    if sha256_file(feature_path) != calibration["feature_sha256"]:
        raise ValueError("V72 calibration feature cache changed")
    if sha256_file(grid_path) != calibration["grid_sha256"]:
        raise ValueError("V72 calibration grid changed")
    dependencies: list[dict[str, Any]] = []
    for dependency in config["locked_dependencies"].values():
        path = REPO_ROOT / str(dependency["path"])
        if sha256_file(path) != dependency["sha256"]:
            raise ValueError(f"V72 dependency changed: {path}")
        dependencies.append(record(path, REPO_ROOT))
    storage = Path(str(config["spot_source"]["default_storage_root"]))
    atr_path = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(atr_path) != config["spot_source"]["m5_feature_sha256"]:
        raise ValueError("V72 completed-M5 ATR cache changed")
    contract: dict[str, Any] = {
        "schema_version": "xauusd_xag_xau_v72_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "source_audit": record(source_path, ROOT),
        "calibration_audit": record(calibration_path, ROOT),
        "calibration_features": record(feature_path, ROOT),
        "calibration_grid": record(grid_path, ROOT),
        "selected_policy": calibration["selected_policy"],
        "dependencies": dependencies,
        "completed_m5_atr": record(atr_path, atr_path.parent),
        "splits": config["splits"],
        "candidate_rule": config["candidate_rule"],
        "execution": config["execution"],
        "families": config["families"],
        "gates": config["gates"],
        "development_outcomes_present_at_lock": False,
        "confirmation_outcomes_present_at_lock": False,
        "validation_outcomes_present_at_lock": False,
        "exam_outcomes_present_at_lock": False,
        "exam_source_present_at_lock": False,
        "exam_source_must_be_audited_after_validation_pass": True,
        **config["research_controls"],
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    return contract


def verify_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    lock_path = ROOT / str(config["outputs"]["directory"]) / str(
        config["outputs"]["contract_lock"]
    )
    lock = load_json(lock_path)
    expected = build_contract(config)
    if lock != expected:
        raise ValueError("V72 immutable contract verification failed")
    return lock


def main() -> int:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("V72 contract already exists")
    if list(output.glob("XAG_XAU_V72_*_AUDIT.json")):
        allowed = {
            str(config["outputs"]["source_audit"]),
            str(config["outputs"]["calibration_audit"]),
        }
        unexpected = [path for path in output.glob("XAG_XAU_V72_*_AUDIT.json") if path.name not in allowed]
        if unexpected:
            raise ValueError(f"V72 stage outputs existed before lock: {unexpected}")
    contract = build_contract(config)
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(
        (json.dumps(contract, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

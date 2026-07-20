from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from innovation import canonical_hash, load_json, sha256_file  # noqa: E402


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/comex_spot_receipt_innovation_v70.json",
    "src/__init__.py",
    "src/innovation.py",
    "run_calibration.py",
    "lock_contract.py",
    "run_stage.py",
    "tests/test_innovation.py",
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
    calibration_path = output / str(config["outputs"]["calibration_audit"])
    calibration = load_json(calibration_path)
    if canonical_hash(calibration, "audit_sha256") != str(
        calibration.get("audit_sha256")
    ):
        raise ValueError("V70 calibration audit self-hash changed")
    if calibration.get("decision") != "V70_CALIBRATION_POLICY_SELECTED":
        raise ValueError("V70 calibration did not select a policy")
    if calibration.get("selected_policy") is None:
        raise ValueError("V70 selected policy is missing")
    feature_path = output / str(config["outputs"]["calibration_features"])
    grid_path = output / str(config["outputs"]["calibration_grid"])
    if sha256_file(feature_path) != str(calibration["feature_sha256"]):
        raise ValueError("V70 calibration features changed")
    if sha256_file(grid_path) != str(calibration["grid_sha256"]):
        raise ValueError("V70 calibration grid changed")
    dependencies = []
    for dependency in config["locked_dependencies"].values():
        path = REPO_ROOT / str(dependency["path"])
        if sha256_file(path) != str(dependency["sha256"]):
            raise ValueError(f"V70 dependency changed: {dependency['path']}")
        dependencies.append(record(path, REPO_ROOT))
    manifest = Path(str(config["source"]["download_manifest"]))
    if sha256_file(manifest) != str(config["source"]["download_manifest_sha256"]):
        raise ValueError("V70 COMEX download manifest changed")
    spot_cache = Path(str(config["spot_source"]["default_storage_root"])) / str(
        config["spot_source"]["m5_feature_cache"]
    )
    if sha256_file(spot_cache) != str(config["spot_source"]["m5_feature_sha256"]):
        raise ValueError("V70 completed-M5 feature cache changed")
    contract = {
        "schema_version": "xauusd_comex_spot_receipt_v70_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "calibration_audit": record(calibration_path, ROOT),
        "calibration_features": record(feature_path, ROOT),
        "calibration_grid": record(grid_path, ROOT),
        "selected_policy": calibration["selected_policy"],
        "dependencies": dependencies,
        "comex_download_manifest": record(manifest, manifest.parent),
        "spot_feature_cache": record(spot_cache, spot_cache.parent),
        "splits": config["splits"],
        "candidate_rule": config["candidate_rule"],
        "execution": config["execution"],
        "families": config["families"],
        "gates": config["gates"],
        "development_outcomes_present_at_lock": False,
        "validation_outcomes_present_at_lock": False,
        "exam_outcomes_present_at_lock": False,
        **config["research_controls"],
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    return contract


def verify_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    output = ROOT / str(config["outputs"]["directory"])
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    expected = build_contract(config)
    if lock != expected:
        raise ValueError("V70 immutable contract verification failed")
    return lock


def main() -> int:
    config = load_json(ROOT / "config" / "comex_spot_receipt_innovation_v70.json")
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("V70 contract already exists")
    for stage in config["splits"]:
        if list(output.glob(f"COMEX_SPOT_RECEIPT_V70_{stage.upper()}_*")):
            raise ValueError(f"V70 {stage} outputs existed before lock")
    contract = build_contract(config)
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(
        (json.dumps(contract, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

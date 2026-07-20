from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from catchup import canonical_hash, load_json, sha256_file  # noqa: E402


CONFIG = ROOT / "config" / "fx_breadth_overreaction_fade_v81.json"
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/fx_breadth_overreaction_fade_v81.json",
    "src/__init__.py",
    "src/fx_breadth.py",
    "acquire_gbpusd.py",
    "run_source_audit.py",
    "run_calibration.py",
    "lock_contract.py",
    "run_stage.py",
    "tests/conftest.py",
    "tests/test_fx_breadth.py",
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
    calibration_source_path = output / str(
        config["outputs"]["calibration_source_audit"]
    )
    calibration_path = output / str(config["outputs"]["calibration_audit"])
    source_audit = load_json(source_path)
    calibration_source_audit = load_json(calibration_source_path)
    calibration = load_json(calibration_path)
    if (
        source_audit.get("decision") != "V81_SOURCE_AUDIT_PASS"
        or canonical_hash(source_audit, "audit_sha256")
        != source_audit.get("audit_sha256")
    ):
        raise ValueError("V81 source audit is invalid")
    if source_audit.get("symbols") != config["source"]["symbols"]:
        raise ValueError("V81 source audit symbol semantics changed")
    if source_audit.get("first_month") != config["source"]["first_month"]:
        raise ValueError("V81 source audit start month changed")
    if source_audit.get("last_month") != config["source"]["last_month"]:
        raise ValueError("V81 source audit end month changed")
    if (
        calibration_source_audit.get("decision")
        != "V81_CALIBRATION_SOURCE_AUDIT_PASS"
        or canonical_hash(calibration_source_audit, "audit_sha256")
        != calibration_source_audit.get("audit_sha256")
    ):
        raise ValueError("V81 calibration source audit is invalid")
    if calibration.get("source_audit_sha256") != sha256_file(
        calibration_source_path
    ):
        raise ValueError("V81 calibration source audit changed")
    if (
        calibration.get("decision") != "V81_CALIBRATION_POLICY_SELECTED"
        or calibration.get("selected_policy") is None
        or canonical_hash(calibration, "audit_sha256")
        != calibration.get("audit_sha256")
    ):
        raise ValueError("V81 calibration did not select a policy")
    if bool(calibration.get("post_decision_xau_outcomes_opened")):
        raise ValueError("V81 calibration opened post-entry outcomes")
    feature_path = output / str(config["outputs"]["calibration_features"])
    grid_path = output / str(config["outputs"]["calibration_grid"])
    if sha256_file(feature_path) != calibration["feature_sha256"]:
        raise ValueError("V81 calibration features changed")
    if sha256_file(grid_path) != calibration["grid_sha256"]:
        raise ValueError("V81 calibration grid changed")
    dependencies: list[dict[str, Any]] = []
    for dependency in config["locked_dependencies"].values():
        path = REPO_ROOT / str(dependency["path"])
        if sha256_file(path) != dependency["sha256"]:
            raise ValueError(f"V81 dependency changed: {path}")
        dependencies.append(record(path, REPO_ROOT))
    storage = Path(str(config["spot_source"]["default_storage_root"]))
    atr_path = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(atr_path) != config["spot_source"]["m5_feature_sha256"]:
        raise ValueError("V81 completed-M5 ATR cache changed")
    contract: dict[str, Any] = {
        "schema_version": "xauusd_fx_breadth_overreaction_v81_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "calibration_source_audit": record(calibration_source_path, ROOT),
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
        **config["research_controls"],
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    return contract


def verify_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    path = ROOT / str(config["outputs"]["directory"]) / str(
        config["outputs"]["contract_lock"]
    )
    lock = load_json(path)
    expected = build_contract(config)
    if lock != expected:
        raise ValueError("V81 immutable contract verification failed")
    return lock


def main() -> int:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["contract_lock"])
    if path.exists():
        raise FileExistsError("V81 contract already exists")
    if list(output.glob("FX_BREADTH_XAU_V81_*_DEVELOPMENT_*")):
        raise ValueError("V81 development outputs existed before lock")
    contract = build_contract(config)
    output.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(contract, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"contract_sha256": contract["contract_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

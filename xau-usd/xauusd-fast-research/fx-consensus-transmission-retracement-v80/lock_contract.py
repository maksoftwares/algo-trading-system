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
from run_calibration import verified_inheritance  # noqa: E402


CONFIG = ROOT / "config" / "fx_consensus_transmission_retracement_v80.json"
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/fx_consensus_transmission_retracement_v80.json",
    "src/__init__.py",
    "src/retracement.py",
    "run_calibration.py",
    "lock_contract.py",
    "run_stage.py",
    "tests/conftest.py",
    "tests/test_retracement.py",
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
    v78_contract = verified_inheritance(config)
    inherited_rule = dict(v78_contract["candidate_rule"])
    inherited_rule["family"] = config["candidate_rule"]["family"]
    if inherited_rule != config["candidate_rule"]:
        raise ValueError("V80 changed a V78 source-event rule")
    if v78_contract["execution"] != config["execution"]:
        raise ValueError("V80 execution differs from V78")
    if next(iter(v78_contract["families"].values())) != next(
        iter(config["families"].values())
    ):
        raise ValueError("V80 exit geometry differs from V78")
    for row in v78_contract["dependencies"]:
        path = REPO_ROOT / str(row["path"])
        if sha256_file(path) != row["sha256"]:
            raise ValueError(f"V80 inherited dependency changed: {path}")
    output = ROOT / str(config["outputs"]["directory"])
    calibration_path = output / str(config["outputs"]["calibration_audit"])
    pattern_path = output / str(config["outputs"]["calibration_patterns"])
    grid_path = output / str(config["outputs"]["calibration_grid"])
    calibration = load_json(calibration_path)
    if (
        calibration.get("decision") != "V80_CALIBRATION_POLICY_SELECTED"
        or calibration.get("selected_policy") is None
        or canonical_hash(calibration, "audit_sha256")
        != calibration.get("audit_sha256")
    ):
        raise ValueError("V80 calibration did not select a policy")
    if bool(calibration.get("post_decision_xau_outcomes_opened")):
        raise ValueError("V80 calibration opened post-entry outcomes")
    if sha256_file(pattern_path) != calibration["pattern_sha256"]:
        raise ValueError("V80 calibration patterns changed")
    if sha256_file(grid_path) != calibration["grid_sha256"]:
        raise ValueError("V80 calibration grid changed")
    storage = Path(str(config["spot_source"]["default_storage_root"]))
    atr_path = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(atr_path) != config["spot_source"]["m5_feature_sha256"]:
        raise ValueError("V80 completed-M5 ATR cache changed")
    contract: dict[str, Any] = {
        "schema_version": "xauusd_fx_consensus_v80_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "v78_contract": record(
            REPO_ROOT / str(config["inherited_v78"]["contract_path"]), REPO_ROOT
        ),
        "v78_source_audit": record(
            REPO_ROOT / str(config["inherited_v78"]["source_audit_path"]),
            REPO_ROOT,
        ),
        "v79_contract": record(
            REPO_ROOT / str(config["inherited_v79"]["contract_path"]), REPO_ROOT
        ),
        "v79_development_audit": record(
            REPO_ROOT / str(config["inherited_v79"]["development_audit_path"]),
            REPO_ROOT,
        ),
        "calibration_audit": record(calibration_path, ROOT),
        "calibration_patterns": record(pattern_path, ROOT),
        "calibration_grid": record(grid_path, ROOT),
        "source_policy": v78_contract["selected_policy"],
        "selected_timing_policy": calibration["selected_policy"],
        "dependencies": v78_contract["dependencies"],
        "completed_m5_atr": record(atr_path, atr_path.parent),
        "splits": config["splits"],
        "candidate_rule": config["candidate_rule"],
        "execution": config["execution"],
        "families": config["families"],
        "gates": config["gates"],
        "development_outcomes_present_at_lock": False,
        "validation_outcomes_present_at_lock": False,
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
        raise ValueError("V80 immutable contract verification failed")
    return lock


def main() -> int:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["contract_lock"])
    if path.exists():
        raise FileExistsError("V80 contract already exists")
    if list(output.glob("FX_CONSENSUS_XAU_V80_*_DEVELOPMENT_*")):
        raise ValueError("V80 development outputs existed before lock")
    contract = build_contract(config)
    output.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(contract, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"contract_sha256": contract["contract_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

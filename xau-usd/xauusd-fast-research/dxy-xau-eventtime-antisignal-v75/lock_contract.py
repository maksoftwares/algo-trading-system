from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
V74_ROOT = ROOT.parent / "dxy-xau-eventtime-catchup-v74"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from antisignal import without_minimum_sample  # noqa: E402
from catchup import canonical_hash, load_json, sha256_file  # noqa: E402


CONFIG = ROOT / "config" / "dxy_xau_eventtime_antisignal_v75.json"
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/dxy_xau_eventtime_antisignal_v75.json",
    "src/__init__.py",
    "src/antisignal.py",
    "lock_contract.py",
    "run_stage.py",
    "tests/conftest.py",
    "tests/test_antisignal.py",
)


def record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def verified_inheritance(config: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    inherited = config["inherited_v74"]
    mapping = {
        "contract_path": "contract_file_sha256",
        "source_audit_path": "source_audit_sha256",
        "development_audit_path": "development_audit_sha256",
        "inverse_module_path": "inverse_module_sha256",
    }
    paths = {key: REPO_ROOT / str(inherited[key]) for key in mapping}
    for key, hash_key in mapping.items():
        if sha256_file(paths[key]) != inherited[hash_key]:
            raise ValueError(f"V75 inherited V74 source changed: {paths[key]}")
    contract = load_json(paths["contract_path"])
    development = load_json(paths["development_audit_path"])
    if canonical_hash(contract, "contract_sha256") != contract.get("contract_sha256"):
        raise ValueError("V74 inherited contract self-hash changed")
    config_record = next(
        (
            row
            for row in contract["package_files"]
            if row["path"] == "config/dxy_xau_eventtime_catchup_v74.json"
        ),
        None,
    )
    if config_record is None:
        raise ValueError("V74 contract does not lock its source configuration")
    v74_config_path = V74_ROOT / str(config_record["path"])
    if sha256_file(v74_config_path) != config_record["sha256"]:
        raise ValueError("V74 locked source configuration changed")
    v74_config = load_json(v74_config_path)
    inherited_source = {
        key: v74_config["source"][key]
        for key in (
            "storage_environment_variable",
            "default_storage_root",
            "symbols",
            "payment_authorized",
        )
    }
    if config["source"] != inherited_source:
        raise ValueError("V75 source semantics differ from V74")
    if config["spot_source"] != v74_config["spot_source"]:
        raise ValueError("V75 completed-M5 source semantics differ from V74")
    if (
        development.get("decision") != "V74_DEVELOPMENT_FAIL_TERMINAL"
        or canonical_hash(development, "audit_sha256") != development.get("audit_sha256")
    ):
        raise ValueError("V74 terminal development audit is invalid")
    exposed_end = pd.to_datetime(inherited["exposed_end_exclusive"], utc=True)
    dates = [
        pd.to_datetime(row["date_utc"], utc=True)
        for row in development["session_quality"]
    ]
    if dates and max(dates) >= exposed_end:
        raise ValueError("V74 outcomes overlap V75 development")
    if pd.to_datetime(config["splits"]["development"][0], utc=True) != exposed_end:
        raise ValueError("V75 development does not begin at the fresh boundary")
    return contract, development


def build_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    package_paths = [ROOT / path for path in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    v74, development = verified_inheritance(config)
    inherited_rule = dict(v74["candidate_rule"])
    inherited_rule["family"] = config["candidate_rule"]["family"]
    if inherited_rule != config["candidate_rule"]:
        raise ValueError("V75 changed a V74 candidate rule")
    if v74["execution"] != config["execution"]:
        raise ValueError("V75 execution differs from V74")
    if next(iter(v74["families"].values())) != next(iter(config["families"].values())):
        raise ValueError("V75 exit geometry differs from V74")
    if without_minimum_sample(v74["gates"]) != without_minimum_sample(config["gates"]):
        raise ValueError("V75 changed a V74 economic gate")
    for row in v74["dependencies"]:
        path = REPO_ROOT / str(row["path"])
        if sha256_file(path) != row["sha256"]:
            raise ValueError(f"V75 inherited dependency changed: {path}")
    storage = Path(str(config["spot_source"]["default_storage_root"]))
    atr_path = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(atr_path) != config["spot_source"]["m5_feature_sha256"]:
        raise ValueError("V75 completed-M5 ATR cache changed")
    contract: dict[str, Any] = {
        "schema_version": "xauusd_dxy_xau_v75_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "v74_contract": record(
            REPO_ROOT / str(config["inherited_v74"]["contract_path"]), REPO_ROOT
        ),
        "v74_source_audit": record(
            REPO_ROOT / str(config["inherited_v74"]["source_audit_path"]), REPO_ROOT
        ),
        "v74_development_audit": record(
            REPO_ROOT / str(config["inherited_v74"]["development_audit_path"]), REPO_ROOT
        ),
        "selected_policy": v74["selected_policy"],
        "v74_terminal_decision": development["decision"],
        "direction_transform": {"LONG": "SHORT", "SHORT": "LONG"},
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
        raise ValueError("V75 immutable contract verification failed")
    return lock


def main() -> int:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    path = output / str(config["outputs"]["contract_lock"])
    if path.exists():
        raise FileExistsError("V75 contract already exists")
    if list(output.glob("DXY_XAU_V75_*_AUDIT.json")):
        raise ValueError("V75 stage outputs existed before lock")
    contract = build_contract(config)
    output.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(contract, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"contract_sha256": contract["contract_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

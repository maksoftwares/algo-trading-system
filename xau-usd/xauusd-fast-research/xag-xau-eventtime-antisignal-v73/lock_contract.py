from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from antisignal import without_minimum_sample  # noqa: E402
from catchup import canonical_hash, load_json, sha256_file  # noqa: E402


CONFIG = ROOT / "config" / "xag_xau_eventtime_antisignal_v73.json"
PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/xag_xau_eventtime_antisignal_v73.json",
    "src/__init__.py",
    "src/antisignal.py",
    "lock_contract.py",
    "run_stage.py",
    "run_exam_source_audit.py",
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
    inherited = config["inherited_v72"]
    paths = {
        key: REPO_ROOT / str(inherited[key])
        for key in (
            "contract_path",
            "source_audit_path",
            "development_audit_path",
            "catchup_module_path",
        )
    }
    expected_hashes = {
        "contract_path": "contract_file_sha256",
        "source_audit_path": "source_audit_sha256",
        "development_audit_path": "development_audit_sha256",
        "catchup_module_path": "catchup_module_sha256",
    }
    for key, path in paths.items():
        if sha256_file(path) != inherited[expected_hashes[key]]:
            raise ValueError(f"V73 inherited V72 source changed: {path}")
    contract = load_json(paths["contract_path"])
    development = load_json(paths["development_audit_path"])
    if canonical_hash(contract, "contract_sha256") != contract.get("contract_sha256"):
        raise ValueError("V72 inherited contract self-hash changed")
    if (
        canonical_hash(development, "audit_sha256") != development.get("audit_sha256")
        or development.get("decision") != "V72_DEVELOPMENT_FAIL_TERMINAL"
    ):
        raise ValueError("V72 terminal development audit is invalid")
    dates = [
        pd.to_datetime(row["date_utc"], utc=True)
        for row in development["session_quality"]
    ]
    exposed_end = pd.to_datetime(str(inherited["exposed_end_exclusive"]), utc=True)
    if dates and max(dates) >= exposed_end:
        raise ValueError("V72 exposed outcomes overlap the V73 start")
    if pd.to_datetime(config["splits"]["development"][0], utc=True) != exposed_end:
        raise ValueError("V73 development does not begin at the fresh boundary")
    return contract, development


def build_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    package_paths = [ROOT / path for path in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    v72, development = verified_inheritance(config)
    inherited_rule = dict(v72["candidate_rule"])
    inherited_rule["family"] = config["candidate_rule"]["family"]
    if inherited_rule != config["candidate_rule"]:
        raise ValueError("V73 changed a V72 candidate rule beyond family identity")
    if v72["execution"] != config["execution"]:
        raise ValueError("V73 execution differs from V72")
    inherited_family = next(iter(v72["families"].values()))
    if inherited_family != next(iter(config["families"].values())):
        raise ValueError("V73 stop, target, or hold differs from V72")
    if without_minimum_sample(v72["gates"]) != without_minimum_sample(config["gates"]):
        raise ValueError("V73 changed a V72 economic gate")
    for row in v72["dependencies"]:
        path = REPO_ROOT / str(row["path"])
        if sha256_file(path) != row["sha256"]:
            raise ValueError(f"V73 inherited runtime dependency changed: {path}")
    storage = Path(str(config["spot_source"]["default_storage_root"]))
    atr_path = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(atr_path) != config["spot_source"]["m5_feature_sha256"]:
        raise ValueError("V73 completed-M5 ATR cache changed")
    contract: dict[str, Any] = {
        "schema_version": "xauusd_xag_xau_v73_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "v72_contract": record(
            REPO_ROOT / str(config["inherited_v72"]["contract_path"]), REPO_ROOT
        ),
        "v72_source_audit": record(
            REPO_ROOT / str(config["inherited_v72"]["source_audit_path"]), REPO_ROOT
        ),
        "v72_development_audit": record(
            REPO_ROOT / str(config["inherited_v72"]["development_audit_path"]), REPO_ROOT
        ),
        "selected_policy": v72["selected_policy"],
        "v72_terminal_decision": development["decision"],
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
        "exam_source_present_at_lock": False,
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
        raise ValueError("V73 immutable contract verification failed")
    return lock


def main() -> int:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("V73 contract already exists")
    if list(output.glob("XAG_XAU_V73_*_AUDIT.json")):
        raise ValueError("V73 stage outputs existed before lock")
    contract = build_contract(config)
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(
        (json.dumps(contract, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps({"contract_sha256": contract["contract_sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

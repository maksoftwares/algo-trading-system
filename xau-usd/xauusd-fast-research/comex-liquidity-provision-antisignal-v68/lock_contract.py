from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from antisignal import canonical_hash, load_json, sha256_file  # noqa: E402


PACKAGE_FILES = (
    "README.md",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/comex_liquidity_provision_antisignal_v68.json",
    "src/__init__.py",
    "src/antisignal.py",
    "lock_contract.py",
    "run_stage.py",
    "tests/test_antisignal.py",
)


def matching_artifacts(root: Path, prefix: str) -> list[Path]:
    prefix_path = root / prefix
    return list(prefix_path.parent.glob(prefix_path.name + "*"))


def record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def verify_source_hypothesis(
    name: str, source: Mapping[str, Any]
) -> list[dict[str, Any]]:
    root = REPO_ROOT / str(source["root"])
    contract_path = root / str(source["contract"])
    audit_path = root / str(source["development_audit"])
    if sha256_file(contract_path) != str(source["contract_file_sha256"]):
        raise ValueError(f"V68 {name} contract file changed")
    contract = load_json(contract_path)
    if canonical_hash(contract, "contract_sha256") != str(
        contract.get("contract_sha256")
    ):
        raise ValueError(f"V68 {name} contract self-hash changed")
    if str(contract["contract_sha256"]) != str(source["contract_sha256"]):
        raise ValueError(f"V68 {name} contract identity changed")
    if contract["selected_policy"] != source["selected_policy"]:
        raise ValueError(f"V68 {name} selected policy changed")
    if sha256_file(audit_path) != str(source["development_audit_file_sha256"]):
        raise ValueError(f"V68 {name} development audit file changed")
    audit = load_json(audit_path)
    if canonical_hash(audit, "audit_sha256") != str(audit.get("audit_sha256")):
        raise ValueError(f"V68 {name} development audit self-hash changed")
    if str(audit["audit_sha256"]) != str(source["development_audit_sha256"]):
        raise ValueError(f"V68 {name} development audit identity changed")
    if bool(audit.get("gate_passed")) or "FAIL_TERMINAL" not in str(
        audit.get("decision")
    ):
        raise ValueError(f"V68 {name} hypothesis origin is not a terminal failure")
    for prefix_key in ("validation_prefix", "exam_prefix"):
        prefix = str(source[prefix_key])
        if matching_artifacts(root, prefix):
            raise ValueError(f"V68 {name} later-stage artifacts already exist")
    return [record(contract_path, REPO_ROOT), record(audit_path, REPO_ROOT)]


def build_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    package_paths = [ROOT / path for path in PACKAGE_FILES]
    if missing := [str(path) for path in package_paths if not path.is_file()]:
        raise FileNotFoundError(missing)
    source_records: list[dict[str, Any]] = []
    for name, source in config["source_hypotheses"].items():
        source_records.extend(verify_source_hypothesis(name, source))
    dependency_records = []
    for dependency in config["locked_dependencies"].values():
        path = REPO_ROOT / str(dependency["path"])
        if sha256_file(path) != str(dependency["sha256"]):
            raise ValueError(f"V68 dependency changed: {dependency['path']}")
        dependency_records.append(record(path, REPO_ROOT))
    manifest = Path(str(config["source"]["download_manifest"]))
    if sha256_file(manifest) != str(config["source"]["download_manifest_sha256"]):
        raise ValueError("V68 COMEX download manifest changed")
    spot_cache = Path(str(config["spot_source"]["default_storage_root"])) / str(
        config["spot_source"]["m5_feature_cache"]
    )
    if sha256_file(spot_cache) != str(config["spot_source"]["m5_feature_sha256"]):
        raise ValueError("V68 spot feature cache changed")
    contract = {
        "schema_version": "xauusd_comex_liquidity_provision_v68_contract_lock",
        "package_files": [record(path, ROOT) for path in package_paths],
        "source_hypothesis_records": source_records,
        "dependency_records": dependency_records,
        "comex_download_manifest": {
            "path": str(manifest),
            "bytes": int(manifest.stat().st_size),
            "sha256": sha256_file(manifest),
        },
        "spot_feature_cache": {
            "path": str(spot_cache),
            "bytes": int(spot_cache.stat().st_size),
            "sha256": sha256_file(spot_cache),
        },
        "splits": config["splits"],
        "router": config["router"],
        "execution": config["execution"],
        "families": config["families"],
        "gates": config["gates"],
        "development_antisignal_outcomes_present_at_lock": False,
        "validation_antisignal_outcomes_present_at_lock": False,
        "exam_antisignal_outcomes_present_at_lock": False,
        **config["research_controls"],
    }
    contract["contract_sha256"] = canonical_hash(contract, "contract_sha256")
    return contract


def verify_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    output = ROOT / str(config["outputs"]["directory"])
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    expected = build_contract(config)
    if lock != expected:
        raise ValueError("V68 immutable contract verification failed")
    return lock


def main() -> int:
    config = load_json(
        ROOT / "config" / "comex_liquidity_provision_antisignal_v68.json"
    )
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if lock_path.exists():
        raise FileExistsError("V68 contract already exists")
    for stage in config["splits"]:
        if list(output.glob(f"COMEX_LIQUIDITY_PROVISION_V68_{stage.upper()}_*")):
            raise ValueError(f"V68 {stage} outputs existed before lock")
    contract = build_contract(config)
    output.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(
        (json.dumps(contract, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps(contract, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

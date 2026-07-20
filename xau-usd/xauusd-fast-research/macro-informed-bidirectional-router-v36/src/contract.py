from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "macro_informed_bidirectional_router_v36.json"

CONTRACT_FILES = (
    ".gitattributes",
    "README.md",
    "PREREGISTRATION.md",
    "PRE_OUTCOME_AMENDMENT.md",
    "requirements.txt",
    "config/macro_informed_bidirectional_router_v36.json",
    "build_dataset.py",
    "run_router.py",
    "lock_contract.py",
    "src/__init__.py",
    "src/contract.py",
    "src/evaluation.py",
    "src/macro_features.py",
    "src/router.py",
    "tests/test_v36.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def resolve_relative(value: str) -> Path:
    return (ROOT / value).resolve()


def macro_root(config: dict[str, Any]) -> Path:
    source = config["macro_source"]
    return Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    )


def dependency_paths(config: dict[str, Any]) -> dict[str, tuple[Path, str]]:
    dependencies: dict[str, tuple[Path, str]] = {}
    for name in (
        "base_actions",
        "base_evidence",
        "baseline_config",
        "baseline_router_source",
        "baseline_result",
        "baseline_evaluation_source",
        "core_ledger",
    ):
        dependencies[name] = (
            resolve_relative(str(config["sources"][name])),
            str(config["sources"][f"{name}_sha256"]),
        )
    root = macro_root(config)
    dependencies["macro_feature_cache"] = (
        root / str(config["macro_source"]["feature_cache"]),
        str(config["macro_source"]["feature_sha256"]),
    )
    dependencies["macro_feature_manifest"] = (
        root / str(config["macro_source"]["feature_manifest"]),
        str(config["macro_source"]["manifest_sha256"]),
    )
    return dependencies


def current_contract() -> dict[str, Any]:
    config = load_config()
    dependencies = {}
    for name, (path, expected) in dependency_paths(config).items():
        observed = sha256_file(path)
        if observed != expected:
            raise ValueError(
                f"Configured dependency hash mismatch for {name}: {observed}"
            )
        dependencies[name] = {"path": str(path), "sha256": observed}
    files = {name: sha256_file(ROOT / name) for name in CONTRACT_FILES}
    return {
        "schema_version": config["schema_version"],
        "contract_files": files,
        "dependencies": dependencies,
    }


def verify_contract_lock() -> dict[str, Any]:
    config = load_config()
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    locked = json.loads(path.read_text(encoding="utf-8"))
    current = current_contract()
    if locked != current:
        raise ValueError(
            "V36 contract lock does not match current files or dependencies"
        )
    return locked

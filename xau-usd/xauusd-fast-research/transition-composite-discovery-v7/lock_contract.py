from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]

PACKAGE_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/transition_composite_discovery_v7.json",
    "src/__init__.py",
    "src/composite.py",
    "prepare_manifest.py",
    "lock_contract.py",
    "run_discovery.py",
    "tests/test_composite.py",
)

DEPENDENCIES = (
    "../macro-regime-routing-v1/src/campaign.py",
    "../macro-regime-routing-v1/src/foundation.py",
    "../independent-specialists-v1/src/data.py",
    "../independent-specialists-v1/src/research.py",
    "../adaptive-h4-specialists-v1/src/adaptive.py",
    "../m15-regime-target-campaign-v1/src/campaign.py",
    "../intraday-macro-specialists-v1/src/data.py",
    "../m15-regime-target-campaign-v2/src/correction.py",
    "../walkforward-state-action-router-v1/src/router.py",
    "../regime-mechanism-campaign-v1/src/campaign.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    resolved.relative_to(base.resolve())
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def _self_hash(payload: Mapping[str, Any]) -> str:
    work = {key: value for key, value in payload.items() if key != "contract_sha256"}
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "transition_composite_discovery_v7.json").read_text(
            encoding="utf-8"
        )
    )
    source_root = (ROOT / config["source_campaign"]["directory"]).resolve()
    source_config_path = source_root / config["source_campaign"]["config"]
    source_config = json.loads(source_config_path.read_text(encoding="utf-8"))
    source_lock_path = source_root / config["source_campaign"]["contract_lock"]
    source_lock = json.loads(source_lock_path.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    manifest = output / config["outputs"]["manifest"]
    evidence = output / config["outputs"]["manifest_evidence"]
    evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
    if sha256_file(manifest) != str(evidence_payload["manifest_sha256"]):
        raise ValueError("Composite manifest differs from preflight evidence")
    source_names = (
        config["source_campaign"]["config"],
        config["source_campaign"]["contract_lock"],
        config["source_campaign"]["metrics"],
        config["source_campaign"]["result"],
        config["source_campaign"]["selected_trades"],
    )
    storage = Path(
        os.environ.get(
            str(source_config["source"]["storage_environment_variable"]),
            str(source_config["source"]["default_storage_root"]),
        )
    ).resolve()
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V7 contract lock already exists")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_transition_composite_discovery_v7_contract",
        "component_pool": config["component_pool"],
        "selection": config["selection"],
        "windows": config["windows"],
        "execution": config["execution"],
        "economic_gates": config["economic_gates"],
        "manifest_file": _record(manifest, REPO),
        "manifest_evidence": _record(evidence, REPO),
        "package_files": [
            _record((ROOT / name).resolve(), REPO) for name in PACKAGE_FILES
        ],
        "dependency_files": [
            _record((ROOT / name).resolve(), REPO) for name in DEPENDENCIES
        ],
        "source_campaign_files": [
            _record((source_root / name).resolve(), REPO) for name in source_names
        ],
        "external_files": source_lock["external_files"],
        "external_storage_root": str(storage),
        "components_selected_after_outcomes": True,
        "composite_outcomes_opened": False,
        "subset_search_count": int(config["selection"]["subset_search_count"]),
        "paid_data_used": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    payload["contract_sha256"] = _self_hash(payload)
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(payload["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


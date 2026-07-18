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
    "config/crossasset_residual_regime_campaign_v6.json",
    "src/__init__.py",
    "src/campaign.py",
    "prepare_manifest.py",
    "lock_contract.py",
    "run_screen.py",
    "tests/test_campaign.py",
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
        (ROOT / "config" / "crossasset_residual_regime_campaign_v6.json").read_text(
            encoding="utf-8"
        )
    )
    controls = config["research_controls"]
    prohibited = (
        "same_version_post_outcome_tuning_authorized",
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
        "training_authorized",
        "execution_authorized",
    )
    if any(bool(controls[key]) for key in prohibited):
        raise ValueError("A prohibited research control is enabled")
    output = ROOT / config["outputs"]["directory"]
    manifest = output / config["outputs"]["manifest"]
    evidence = output / "CROSSASSET_RESIDUAL_V6_MANIFEST_EVIDENCE.json"
    evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
    if sha256_file(manifest) != str(evidence_payload["manifest_sha256"]):
        raise ValueError("Manifest differs from its preflight evidence")
    package_paths = [(ROOT / name).resolve() for name in PACKAGE_FILES]
    dependencies = [(ROOT / name).resolve() for name in DEPENDENCIES]
    storage = Path(
        os.environ.get(
            str(config["source"]["storage_environment_variable"]),
            str(config["source"]["default_storage_root"]),
        )
    ).resolve()
    external_paths = [
        storage / str(config["source"]["feature_cache"]),
        storage / str(config["source"]["feature_manifest"]),
        storage / str(config["macro_source"]["feature_cache"]),
        storage / str(config["macro_source"]["feature_manifest"]),
    ]
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V6 contract lock already exists")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_crossasset_residual_regime_campaign_v6_contract",
        "selection": config["selection"],
        "windows": config["windows"],
        "residual_features": config["residual_features"],
        "geometries": config["geometries"],
        "execution": config["execution"],
        "economic_gates": config["economic_gates"],
        "manifest_file": _record(manifest, REPO),
        "manifest_evidence": _record(evidence, REPO),
        "package_files": [_record(path, REPO) for path in package_paths],
        "dependency_files": [_record(path, REPO) for path in dependencies],
        "external_files": [_record(path, storage) for path in external_paths],
        "outcomes_opened": False,
        "manifest_coverage_uses_no_outcomes": True,
        "same_version_tuning_authorized": False,
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


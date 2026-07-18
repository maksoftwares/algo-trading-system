from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

PACKAGE_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/chop_anchor_target_campaign_v12.json",
    "src/__init__.py",
    "src/campaign.py",
    "prepare_manifest.py",
    "lock_contract.py",
    "run_screen.py",
    "tests/test_campaign.py",
)

DEPENDENCIES = (
    "../independent-specialists-v1/src/data.py",
    "../independent-specialists-v1/src/research.py",
    "../adaptive-h4-specialists-v1/src/adaptive.py",
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
        (ROOT / "config" / "chop_anchor_target_campaign_v12.json").read_text(
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
    evidence = output / config["outputs"]["manifest_evidence"]
    evidence_payload = json.loads(evidence.read_text(encoding="utf-8"))
    if sha256_file(manifest) != str(evidence_payload["manifest_sha256"]):
        raise ValueError("Manifest differs from preflight evidence")
    storage = Path(
        os.environ.get(
            str(config["source"]["storage_environment_variable"]),
            str(config["source"]["default_storage_root"]),
        )
    ).resolve()
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V12 contract lock already exists")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_chop_anchor_target_v12_contract",
        "selection": config["selection"],
        "windows": config["windows"],
        "regime": config["regime"],
        "signal": config["signal"],
        "geometries": config["geometries"],
        "execution": config["execution"],
        "economic_gates": config["economic_gates"],
        "manifest_file": _record(manifest, REPO),
        "manifest_evidence": _record(evidence, REPO),
        "package_files": [_record(ROOT / name, REPO) for name in PACKAGE_FILES],
        "dependency_files": [_record(ROOT / name, REPO) for name in DEPENDENCIES],
        "external_files": [
            _record(storage / config["source"]["feature_cache"], storage),
            _record(storage / config["source"]["feature_manifest"], storage),
        ],
        "outcomes_opened": False,
        "manifest_membership_uses_signal_counts_only": True,
        "same_version_tuning_authorized": False,
        "paid_data_used": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    payload["contract_sha256"] = _self_hash(payload)
    with lock_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        )
    print(payload["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

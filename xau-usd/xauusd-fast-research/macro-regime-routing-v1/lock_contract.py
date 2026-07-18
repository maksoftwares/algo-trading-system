from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": resolved.relative_to(base.resolve()).as_posix(),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def self_hash(payload: dict[str, Any]) -> str:
    work = dict(payload)
    work.pop("contract_sha256", None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    config_path = ROOT / "config" / "macro_regime_routing_v1.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / config["outputs"]["manifest"]
    if not manifest_path.is_file():
        raise FileNotFoundError("Run generate_manifest.py before locking")
    manifest = pd.read_csv(manifest_path)
    if len(manifest) != int(config["selection"]["total_attempts"]):
        raise ValueError("Manifest count differs from config")

    package_relative = (
        "PREREGISTRATION.md",
        "requirements.txt",
        "generate_manifest.py",
        "lock_contract.py",
        "run_screen.py",
        "config/macro_regime_routing_v1.json",
        "src/__init__.py",
        "src/campaign.py",
        "src/foundation.py",
        "tests/test_campaign.py",
    )
    dependency_relative = (
        "xau-usd/xauusd-fast-research/independent-specialists-v1/src/data.py",
        "xau-usd/xauusd-fast-research/independent-specialists-v1/src/research.py",
        "xau-usd/xauusd-fast-research/adaptive-h4-specialists-v1/src/adaptive.py",
        "xau-usd/xauusd-fast-research/m15-regime-target-campaign-v1/src/campaign.py",
        "xau-usd/xauusd-fast-research/m15-regime-target-campaign-v2/src/correction.py",
        "xau-usd/xauusd-fast-research/intraday-macro-specialists-v1/src/data.py",
        "xau-usd/xauusd-fast-research/walkforward-state-action-router-v1/src/router.py",
        "xau-usd/xauusd-fast-research/regime-mechanism-campaign-v1/src/campaign.py",
    )
    storage = Path(
        os.environ.get(
            str(config["source"]["storage_environment_variable"]),
            str(config["source"]["default_storage_root"]),
        )
    ).resolve()
    external_relative = (
        str(config["source"]["feature_cache"]),
        str(config["source"]["feature_manifest"]),
        str(config["macro_source"]["feature_cache"]),
        str(config["macro_source"]["feature_manifest"]),
    )
    payload = {
        "schema_version": "xauusd_macro_regime_routing_v1_contract_lock",
        "attempt_count": int(len(manifest)),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "manifest_sha256": sha256_file(manifest_path),
        "package_files": [record(ROOT / item, REPO) for item in package_relative],
        "dependency_files": [record(REPO / item, REPO) for item in dependency_relative],
        "external_files": [
            record(storage / item, storage) for item in external_relative
        ],
        "research_controls": config["research_controls"],
    }
    payload["contract_sha256"] = self_hash(payload)
    lock_path = output / config["outputs"]["contract_lock"]
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(payload["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

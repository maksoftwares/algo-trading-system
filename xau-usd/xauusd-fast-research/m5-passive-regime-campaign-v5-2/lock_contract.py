from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]
V5_ROOT = RESEARCH_ROOT / "m5-passive-regime-campaign-v5"
sys.path.insert(0, str(ROOT / "src"))

from streaming import load_config, sha256_file  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PASSIVE = load_module("m5_passive_v52_lock_base", V5_ROOT / "src" / "passive.py")
R2 = load_module(
    "m5_passive_v52_lock_r2",
    RESEARCH_ROOT / "r2-downtrend-portability-v2" / "src" / "downtrend.py",
)


PACKAGE_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/m5_passive_regime_campaign_v5_2.json",
    "src/__init__.py",
    "src/streaming.py",
    "lock_contract.py",
    "run_screen.py",
    "tests/test_streaming.py",
)

DEPENDENCIES = (
    "../m5-passive-regime-campaign-v5-1/config/m5_passive_regime_campaign_v5_1.json",
    "../m5-passive-regime-campaign-v5-1/src/clock.py",
    "../m5-passive-regime-campaign-v5-1/run_screen.py",
    "../m5-passive-regime-campaign-v5-1/outputs/M5_PASSIVE_REGIME_V5_1_CONTRACT_LOCK.json",
    "../m5-passive-regime-campaign-v5-1/outputs/M5_PASSIVE_REGIME_V5_1_MANIFEST.csv",
    "../m5-passive-regime-campaign-v5-1/outputs/M5_PASSIVE_REGIME_V5_1_INVALIDATION.json",
    "../m5-passive-regime-campaign-v5/config/m5_passive_regime_campaign_v5.json",
    "../m5-passive-regime-campaign-v5/src/passive.py",
    "../m5-passive-regime-campaign-v5/outputs/M5_PASSIVE_REGIME_V5_MANIFEST.csv",
    "../m15-regime-target-campaign-v1/src/campaign.py",
    "../m15-regime-target-campaign-v1/config/m15_regime_target_campaign_v1.json",
    "../regime-mechanism-campaign-v1/src/campaign.py",
    "../r2-downtrend-portability-v2/src/downtrend.py",
    "../independent-specialists-v1/src/data.py",
    "../independent-specialists-v1/src/research.py",
    "../adaptive-h4-specialists-v1/src/adaptive.py",
)


def _record(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(base.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": R2.sha256_file(path),
    }


def _self_hash(payload: dict[str, Any]) -> str:
    work = dict(payload)
    work.pop("contract_sha256", None)
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _external_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    old_contract_path = (ROOT / str(source["old_final_contract"])).resolve()
    if R2.sha256_file(old_contract_path) != str(source["old_final_contract_sha256"]):
        raise ValueError("Old final contract hash mismatch")
    old_contract = json.loads(old_contract_path.read_text(encoding="utf-8"))
    old_m5 = [
        item
        for item in old_contract["external_files"]
        if "/dukascopy-replay/bars/XAUUSD/" in str(item["path"])
        and "/M5/" in str(item["path"])
    ]
    if len(old_m5) != 234:
        raise ValueError(f"Expected 234 old M5 records, found {len(old_m5)}")
    records = list(old_m5)
    for key in ("new_feature_cache", "new_feature_manifest"):
        records.append(_record(storage / str(source[key]), storage))
    return sorted(records, key=lambda item: str(item["path"]))


def build_lock(config: dict[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    manifest_path = output / config["outputs"]["manifest"]
    output.mkdir(parents=True, exist_ok=True)
    PASSIVE.generate_manifest(config["selection"]).to_csv(
        manifest_path, index=False, lineterminator="\n"
    )
    expected_manifest_hash = str(config["base"]["unchanged_manifest_sha256"])
    if sha256_file(manifest_path) != expected_manifest_hash:
        raise ValueError("V5.2 manifest differs from V5")

    local_paths = [(ROOT / value).resolve() for value in PACKAGE_FILES]
    dependency_paths = [(ROOT / value).resolve() for value in DEPENDENCIES]
    missing = [
        str(path)
        for path in local_paths + dependency_paths + [manifest_path]
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(missing)
    payload: dict[str, Any] = {
        "schema_version": "xauusd_m5_passive_regime_campaign_v5_2_contract",
        "attempt_first": int(config["selection"]["attempt_first"]),
        "attempt_last": int(config["selection"]["attempt_last"]),
        "attempt_count": int(config["selection"]["total_attempts"]),
        "manifest_sha256": sha256_file(manifest_path),
        "cache_block_policies": int(config["streaming"]["cache_block_policies"]),
        "package_files": [_record(path, REPO) for path in local_paths],
        "dependency_files": [_record(path, REPO) for path in dependency_paths],
        "external_files": _external_records(config),
        "resource_only_correction": True,
        "strategy_definitions_changed": False,
        "execution_rules_changed": False,
        "economic_gates_changed": False,
        "clock_rules_changed": False,
        "selection_bias_acknowledged": True,
        "historical_periods_are_discovery_only": True,
        "exact_tick_confirmation_required": True,
        "prospective_shadow_required": True,
        "training_authorized": False,
        "execution_authorized": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    payload["contract_sha256"] = _self_hash(payload)
    return payload


def main() -> int:
    config = load_config(ROOT)
    lock = build_lock(config)
    path = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    path.write_text(
        json.dumps(lock, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(lock["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

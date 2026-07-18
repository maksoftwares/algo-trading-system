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
sys.path.insert(0, str(ROOT / "src"))

from router import generate_manifest  # noqa: E402


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R2 = load_module(
    "state_action_router_lock_r2",
    RESEARCH_ROOT / "r2-downtrend-portability-v2" / "src" / "downtrend.py",
)

PACKAGE_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/walkforward_state_action_router_v1.json",
    "src/__init__.py",
    "src/router.py",
    "lock_contract.py",
    "run_screen.py",
    "tests/test_router.py",
)

DEPENDENCIES = (
    "../m15-regime-target-campaign-v1/src/campaign.py",
    "../m15-regime-target-campaign-v2/src/correction.py",
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
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / config["outputs"]["manifest"]
    manifest = generate_manifest(config)
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")
    local_paths = [(ROOT / value).resolve() for value in PACKAGE_FILES]
    dependency_paths = [(ROOT / value).resolve() for value in DEPENDENCIES]
    missing = [
        str(path)
        for path in (*local_paths, *dependency_paths, manifest_path)
        if not path.is_file()
    ]
    if missing:
        raise FileNotFoundError(missing)
    payload: dict[str, Any] = {
        "schema_version": "xauusd_walkforward_state_action_router_v1_contract",
        "attempt_first": int(config["selection"]["attempt_first"]),
        "attempt_last": int(config["selection"]["attempt_last"]),
        "attempt_count": int(len(manifest)),
        "manifest_sha256": R2.sha256_file(manifest_path),
        "package_files": [_record(path, REPO) for path in local_paths],
        "dependency_files": [_record(path, REPO) for path in dependency_paths],
        "external_files": _external_records(config),
        "feature_bins_selected_without_outcomes": True,
        "historical_periods_are_discovery_only": True,
        "exact_raw_tick_confirmation_required": True,
        "implementation_parity_required": True,
        "prospective_shadow_required": True,
        "shock_is_abstain": True,
        "same_version_post_outcome_tuning_authorized": False,
        "training_authorized": False,
        "execution_authorized": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    payload["contract_sha256"] = _self_hash(payload)
    return payload


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "walkforward_state_action_router_v1.json").read_text(
            encoding="utf-8"
        )
    )
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

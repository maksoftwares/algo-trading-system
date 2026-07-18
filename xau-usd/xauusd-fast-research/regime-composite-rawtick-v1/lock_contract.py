from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


R2_SOURCE = RESEARCH_ROOT / "r2-downtrend-portability-v2" / "src"
package_spec = importlib.util.spec_from_file_location(
    "regime_composite_lock_r2_package",
    R2_SOURCE / "__init__.py",
    submodule_search_locations=[str(R2_SOURCE)],
)
if package_spec is None or package_spec.loader is None:
    raise ImportError(R2_SOURCE)
package = importlib.util.module_from_spec(package_spec)
sys.modules[package_spec.name] = package
package_spec.loader.exec_module(package)
R2 = load_module(
    f"{package_spec.name}.downtrend", R2_SOURCE / "downtrend.py"
)
R2_CONTRACT = load_module(
    f"{package_spec.name}.contract", R2_SOURCE / "contract.py"
)


PACKAGE_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/regime_composite_rawtick_v1.json",
    "src/__init__.py",
    "src/composite.py",
    "prepare_candidates.py",
    "lock_contract.py",
    "run_confirmation.py",
    "tests/test_composite.py",
)

DEPENDENCIES = (
    "../r2-downtrend-portability-v2/src/downtrend.py",
    "../r2-downtrend-portability-v2/src/contract.py",
    "../independent-specialists-v1/src/data.py",
    "../independent-specialists-v1/src/research.py",
    "../adaptive-h4-specialists-v1/src/adaptive.py",
    "../regime-mechanism-campaign-v1/src/campaign.py",
    "../regime-mechanism-campaign-v1/config/regime_mechanism_campaign_v1.json",
    "../regime-mechanism-campaign-v1/outputs/REGIME_MECHANISM_CAMPAIGN_V1_MANIFEST.csv",
    "../regime-mechanism-campaign-v1/outputs/REGIME_MECHANISM_CAMPAIGN_V1_METRICS.csv",
    "../regime-mechanism-campaign-v1/outputs/REGIME_MECHANISM_CAMPAIGN_V1_RESULT.json",
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


def build_lock(config: dict[str, Any]) -> dict[str, Any]:
    output = ROOT / config["outputs"]["directory"]
    candidates = output / config["outputs"]["candidates"]
    candidate_manifest = output / config["outputs"]["candidate_manifest"]
    local_paths = [(ROOT / value).resolve() for value in PACKAGE_FILES]
    dependencies = [(ROOT / value).resolve() for value in DEPENDENCIES]
    required = local_paths + dependencies + [candidates, candidate_manifest]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(missing)
    manifest = json.loads(candidate_manifest.read_text(encoding="utf-8"))
    if R2.sha256_file(candidates) != str(manifest["candidate_sha256"]):
        raise ValueError("Candidate parquet does not match its manifest")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_regime_composite_rawtick_v1_contract",
        "attempt_first": int(config["selection"]["attempt_first"]),
        "attempt_last": int(config["selection"]["attempt_last"]),
        "attempt_count": int(config["selection"]["attempt_count"]),
        "composites": config["composites"],
        "candidate_file": _record(candidates, REPO),
        "candidate_manifest": _record(candidate_manifest, REPO),
        "package_files": [_record(path, REPO) for path in local_paths],
        "dependency_files": [_record(path, REPO) for path in dependencies],
        "external_files": R2_CONTRACT.external_records(config),
        "selected_after_v1_outcomes": True,
        "raw_tick_result_can_be_independent_holdout": False,
        "prospective_shadow_required": True,
        "training_authorized": False,
        "execution_authorized": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    payload["contract_sha256"] = _self_hash(payload)
    return payload


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "regime_composite_rawtick_v1.json").read_text(
            encoding="utf-8"
        )
    )
    lock = build_lock(config)
    output = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    output.write_text(
        json.dumps(lock, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(lock["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

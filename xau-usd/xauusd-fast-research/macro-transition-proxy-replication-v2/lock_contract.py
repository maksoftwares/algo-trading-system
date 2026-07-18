from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any


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
    resolved.relative_to(base.resolve())
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    return {
        "path": str(resolved.relative_to(base.resolve())).replace("\\", "/"),
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


def source_candidate(metrics_path: Path, attempt_no: int) -> dict[str, Any]:
    with metrics_path.open("r", encoding="utf-8", newline="") as handle:
        matches = [
            row for row in csv.DictReader(handle) if int(row["attempt_no"]) == attempt_no
        ]
    if len(matches) != 1:
        raise ValueError(f"Expected one source row for attempt {attempt_no}")
    row = matches[0]
    return {
        "attempt_no": int(row["attempt_no"]),
        "variant_id": row["variant_id"],
        "regime_owner": row["regime_owner"],
        "mechanic": row["mechanic"],
        "geometry_id": row["geometry_id"],
        "parameters_json": row["parameters_json"],
        "whole_trades": int(row["whole_trades"]),
        "whole_stress_net_r": float(row["whole_stress_net_r"]),
        "whole_stress_pf": float(row["whole_stress_pf"]),
        "minimum_era_trades": int(row["minimum_era_trades"]),
        "minimum_era_stress_pf": float(row["minimum_era_stress_pf"]),
    }


def main() -> int:
    config_path = ROOT / "config" / "macro_transition_proxy_replication_v2.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    proxy_source = config["proxy_source"]
    if str(proxy_source["cache_sha256"]).startswith("TO_BE_") or str(
        proxy_source["cache_manifest_sha256"]
    ).startswith("TO_BE_"):
        raise ValueError("Prepare the proxy cache and lock its hashes before contract lock")

    package_names = [
        "PREREGISTRATION.md",
        "requirements.txt",
        "config/macro_transition_proxy_replication_v2.json",
        "src/proxy_data.py",
        "src/replication.py",
        "tests/test_proxy_data.py",
        "tests/test_replication.py",
        "acquire_proxy_data.py",
        "prepare_proxy_cache.py",
        "lock_contract.py",
        "run_replication.py",
    ]
    dependency_names = [
        "xau-usd/xauusd-fast-research/independent-specialists-v1/src/data.py",
        "xau-usd/xauusd-fast-research/independent-specialists-v1/src/research.py",
        "xau-usd/xauusd-fast-research/adaptive-h4-specialists-v1/src/adaptive.py",
        "xau-usd/xauusd-fast-research/m15-regime-target-campaign-v1/src/campaign.py",
        "xau-usd/xauusd-fast-research/m15-regime-target-campaign-v2/src/correction.py",
        "xau-usd/xauusd-fast-research/walkforward-state-action-router-v1/src/router.py",
        "xau-usd/xauusd-fast-research/macro-regime-routing-v1/src/campaign.py",
        "xau-usd/xauusd-fast-research/macro-regime-routing-v1/outputs/MACRO_REGIME_ROUTING_V1_CONTRACT_LOCK.json",
        "xau-usd/xauusd-fast-research/macro-regime-routing-v1/outputs/MACRO_REGIME_ROUTING_V1_METRICS.csv",
        "xau-usd/xauusd-fast-research/macro-regime-routing-v1/outputs/MACRO_REGIME_ROUTING_V1_RESULT.json",
    ]
    storage = Path(
        os.environ.get(
            config["source"]["storage_environment_variable"],
            config["source"]["default_storage_root"],
        )
    ).resolve()
    proxy_root = Path(str(proxy_source["root"]))
    external_names = [
        Path(str(config["source"]["feature_cache"])),
        Path(str(config["source"]["feature_manifest"])),
        proxy_root / str(proxy_source["acquisition_manifest"]),
        proxy_root / str(proxy_source["cache"]),
        proxy_root / str(proxy_source["cache_manifest"]),
        proxy_root / "metadata" / "DOLLARIDXUSD.json",
        proxy_root / "metadata" / "TLTUSD.json",
        proxy_root / "metadata" / "IEFUSD.json",
    ]
    if sha256_file(storage / proxy_root / str(proxy_source["cache"])) != str(
        proxy_source["cache_sha256"]
    ):
        raise ValueError("Configured proxy cache hash differs from the source file")
    if sha256_file(storage / proxy_root / str(proxy_source["cache_manifest"])) != str(
        proxy_source["cache_manifest_sha256"]
    ):
        raise ValueError("Configured proxy cache manifest hash differs from the source file")

    metrics_path = (
        REPO
        / "xau-usd/xauusd-fast-research/macro-regime-routing-v1/outputs/"
        "MACRO_REGIME_ROUTING_V1_METRICS.csv"
    )
    candidate = source_candidate(metrics_path, int(config["candidate"]["source_attempt_no"]))
    expected_parameters = json.dumps(
        config["candidate"]["parameters"], sort_keys=True, separators=(",", ":")
    )
    identity_checks = {
        "variant_id": candidate["variant_id"] == config["candidate"]["source_variant_id"],
        "regime_owner": candidate["regime_owner"] == config["candidate"]["regime_owner"],
        "mechanic": candidate["mechanic"] == config["candidate"]["mechanic"],
        "geometry_id": candidate["geometry_id"] == config["candidate"]["geometry_id"],
        "parameters": candidate["parameters_json"] == expected_parameters,
    }
    if not all(identity_checks.values()):
        raise ValueError(f"Fixed candidate differs from its V1 source: {identity_checks}")

    output = ROOT / config["outputs"]["directory"]
    output.mkdir(parents=True, exist_ok=True)
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V2 contract lock already exists")
    payload = {
        "schema_version": "xauusd_macro_transition_proxy_replication_v2_contract",
        "contract_sha256": "",
        "package_files": [record(ROOT / name, REPO) for name in package_names],
        "dependency_files": [record(REPO / name, REPO) for name in dependency_names],
        "external_files": [record(storage / name, storage) for name in external_names],
        "fixed_candidate": candidate,
        "candidate_identity_checks": identity_checks,
        "proxy_symbols": sorted(config["windows"]),
        "candidate_count": int(config["research_controls"]["candidate_count"]),
        "parameter_sets_per_candidate": int(
            config["research_controls"]["parameter_sets_per_candidate"]
        ),
        "outcomes_opened": False,
        "paid_data_used": False,
    }
    payload["contract_sha256"] = self_hash(payload)
    lock_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"lock": str(lock_path), "contract_sha256": payload["contract_sha256"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import calendar
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]

PACKAGE_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/transition_weighted_rawtick_confirmation_v9.json",
    "src/__init__.py",
    "src/confirmation.py",
    "prepare_candidates.py",
    "lock_contract.py",
    "run_confirmation.py",
    "tests/test_confirmation.py",
)

DEPENDENCIES = (
    "../macro-regime-routing-v1/src/campaign.py",
    "../macro-regime-routing-v1/src/foundation.py",
    "../crossasset-residual-regime-campaign-v6/src/campaign.py",
    "../transition-weighted-portfolio-v8/src/portfolio.py",
    "../macro-transition-rawtick-confirmation-v3/src/transition.py",
    "../r2-downtrend-portability-v2/src/downtrend.py",
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


def _source_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for source_name in (
        "macro_source_campaign",
        "residual_source_campaign",
        "portfolio_source",
    ):
        source = config[source_name]
        source_root = (ROOT / source["directory"]).resolve()
        for key, name in source.items():
            if key != "directory":
                records.append(_record(source_root / name, REPO))
    return records


def _external_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    macro_root = (ROOT / config["macro_source_campaign"]["directory"]).resolve()
    macro_config = json.loads(
        (macro_root / config["macro_source_campaign"]["config"]).read_text(
            encoding="utf-8"
        )
    )
    paths = [
        storage / str(source["feature_cache"]),
        storage / str(source["feature_manifest"]),
        storage / str(macro_config["macro_source"]["feature_cache"]),
        storage / str(macro_config["macro_source"]["feature_manifest"]),
    ]
    records = [_record(path, storage) for path in paths]
    start = pd.Timestamp(source["raw_manifest_start_utc"]).tz_localize(None).to_period("M")
    end = (
        pd.Timestamp(source["end_exclusive_utc"]).tz_localize(None).to_period("M")
        - 1
    )
    raw_records: list[dict[str, Any]] = []
    raw_root = storage / str(source["raw_tick_root"])
    for period in pd.period_range(start, end, freq="M"):
        path = (
            raw_root
            / f"year={period.year:04d}"
            / f"month={period.month:02d}"
            / "_FROZEN_MANIFEST.json"
        )
        payload = json.loads(path.read_text(encoding="utf-8"))
        expected_hours = calendar.monthrange(period.year, period.month)[1] * 24
        if (
            payload.get("symbol") != "XAUUSD"
            or payload.get("month") != str(period)
            or not bool(payload.get("complete"))
            or not bool(payload.get("frozen"))
            or int(payload.get("expected_hour_files", -1)) != expected_hours
            or int(payload.get("observed_hour_files", -1)) != expected_hours
        ):
            raise ValueError(f"Raw tick month is not complete and frozen: {path}")
        record = _record(path, storage)
        record["files_sha256"] = str(payload["files_sha256"])
        raw_records.append(record)
    if len(raw_records) != int(source["raw_tick_manifest_count"]):
        raise ValueError("Unexpected raw manifest count")
    return sorted(records + raw_records, key=lambda item: str(item["path"]))


def main() -> int:
    config = json.loads(
        (
            ROOT
            / "config"
            / "transition_weighted_rawtick_confirmation_v9.json"
        ).read_text(encoding="utf-8")
    )
    output = ROOT / config["outputs"]["directory"]
    candidate_path = output / config["outputs"]["candidates"]
    manifest_path = output / config["outputs"]["candidate_manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if sha256_file(candidate_path) != str(manifest["candidate_sha256"]):
        raise ValueError("Candidate file differs from its manifest")
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists():
        raise FileExistsError("V9 contract lock already exists")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_transition_weighted_rawtick_v9_contract",
        "portfolio": config["portfolio"],
        "execution": config["execution"],
        "windows": config["windows"],
        "economic_gates": config["economic_gates"],
        "candidate_file": _record(candidate_path, REPO),
        "candidate_manifest": _record(manifest_path, REPO),
        "package_files": [
            _record((ROOT / name).resolve(), REPO) for name in PACKAGE_FILES
        ],
        "dependency_files": [
            _record((ROOT / name).resolve(), REPO) for name in DEPENDENCIES
        ],
        "source_campaign_files": _source_records(config),
        "external_files": _external_records(config),
        "selected_after_v8_outcomes": True,
        "raw_tick_result_can_be_independent_holdout": False,
        "prospective_shadow_required": True,
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


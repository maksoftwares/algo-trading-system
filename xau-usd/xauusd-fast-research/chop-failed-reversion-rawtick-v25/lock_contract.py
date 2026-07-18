from __future__ import annotations

import calendar
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parent
REPO = ROOT.parents[2]

PACKAGE_FILES = (
    ".gitattributes",
    "PREREGISTRATION.md",
    "requirements.txt",
    "config/chop_failed_reversion_rawtick_v25.json",
    "src/__init__.py",
    "src/confirmation.py",
    "prepare_candidates.py",
    "lock_contract.py",
    "run_confirmation.py",
    "tests/test_confirmation.py",
)

DEPENDENCIES = (
    "../chop-failed-reversion-envelope-v24/src/campaign.py",
    "../chop-failed-reversion-envelope-v24/config/chop_failed_reversion_envelope_v24.json",
    "../chop-failed-reversion-envelope-v24/outputs/CHOP_FAILED_REVERSION_ENVELOPE_V24_MANIFEST.csv",
    "../chop-failed-reversion-envelope-v24/outputs/CHOP_FAILED_REVERSION_ENVELOPE_V24_METRICS.csv",
    "../chop-failed-reversion-envelope-v24/outputs/CHOP_FAILED_REVERSION_ENVELOPE_V24_RESULT.json",
    "../chop-failed-reversion-envelope-v24/outputs/CHOP_FAILED_REVERSION_ENVELOPE_V24_SELECTED_TRADES.parquet",
    "../independent-specialists-v1/src/data.py",
    "../independent-specialists-v1/src/research.py",
    "../m5-microstructure-mechanics-v1/src/campaign.py",
    "../regime-mechanism-campaign-v1/src/campaign.py",
    "../r2-downtrend-portability-v2/src/downtrend.py",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _record(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(base.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


def _self_hash(payload: Mapping[str, Any]) -> str:
    work = {key: value for key, value in payload.items() if key != "contract_sha256"}
    encoded = json.dumps(
        work, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _storage_root(config: Mapping[str, Any]) -> Path:
    source = config["source"]
    return Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()


def _external_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    root = _storage_root(config)
    source = config["source"]
    paths = [
        root / str(source["feature_cache"]),
        root / str(source["feature_manifest"]),
    ]
    records = [_record(path, root) for path in paths]
    start = pd.Timestamp(source["raw_manifest_start_utc"]).tz_localize(None).to_period("M")
    end = (
        pd.Timestamp(source["end_exclusive_utc"]).tz_localize(None).to_period("M")
        - 1
    )
    raw_records: list[dict[str, Any]] = []
    raw_root = root / str(source["raw_tick_root"])
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
        record = _record(path, root)
        record["files_sha256"] = str(payload["files_sha256"])
        raw_records.append(record)
    if len(raw_records) != int(source["raw_tick_manifest_count"]):
        raise ValueError(f"Unexpected raw manifest count: {len(raw_records)}")
    return sorted(records + raw_records, key=lambda item: str(item["path"]))


def build_lock(config: dict[str, Any]) -> dict[str, Any]:
    controls = config["research_controls"]
    prohibited = (
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
        "training_authorized",
        "execution_authorized",
    )
    if any(bool(controls[key]) for key in prohibited):
        raise ValueError("A prohibited research control is enabled")
    if bool(config["selection"]["same_version_post_outcome_tuning_authorized"]):
        raise ValueError("Same-version post-outcome tuning is enabled")
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
    if sha256_file(candidates) != str(manifest["candidate_sha256"]):
        raise ValueError("Candidate parquet does not match its manifest")
    parity = manifest["independent_signal_parity"]
    if (
        not bool(parity["mask_equal"])
        or not bool(parity["direction_equal"])
        or str(parity["independent_signal_sha256"])
        != str(parity["reference_signal_sha256"])
    ):
        raise ValueError("Independent V25 signal logic does not match V24")
    payload: dict[str, Any] = {
        "schema_version": "xauusd_chop_failed_reversion_rawtick_v25_contract",
        "candidate_definition": config["candidate"],
        "selection": config["selection"],
        "windows": config["windows"],
        "execution": config["execution"],
        "economic_gates": config["economic_gates"],
        "candidate_file": _record(candidates, REPO),
        "candidate_manifest": _record(candidate_manifest, REPO),
        "package_files": [_record(path, REPO) for path in local_paths],
        "dependency_files": [_record(path, REPO) for path in dependencies],
        "external_files": _external_records(config),
        "selected_after_origin_outcomes": True,
        "raw_tick_result_can_be_independent_holdout": False,
        "independent_signal_logic_parity_required": True,
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
        (ROOT / "config" / "chop_failed_reversion_rawtick_v25.json").read_text(
            encoding="utf-8"
        )
    )
    lock = build_lock(config)
    output = ROOT / config["outputs"]["directory"] / config["outputs"]["contract_lock"]
    if output.exists():
        raise FileExistsError("Contract lock already exists")
    output.write_text(
        json.dumps(lock, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    print(lock["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

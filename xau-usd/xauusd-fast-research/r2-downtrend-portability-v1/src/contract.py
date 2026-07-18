from __future__ import annotations

import calendar
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from . import downtrend


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
CONFIG_PATH = PACKAGE / "config" / "r2_downtrend_portability_v1.json"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def output_path(config: Mapping[str, Any], key: str) -> Path:
    return PACKAGE / str(config["outputs"]["directory"]) / str(config["outputs"][key])


def definition_lock_path(config: Mapping[str, Any]) -> Path:
    return output_path(config, "definition_lock")


def outcome_marker_path(config: Mapping[str, Any]) -> Path:
    return output_path(config, "outcome_marker")


def _record(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(base.resolve()).as_posix(),
        "bytes": int(path.stat().st_size),
        "sha256": downtrend.sha256_file(path),
    }


def package_files() -> list[Path]:
    relative = (
        "README.md",
        "PREREGISTRATION.md",
        "requirements.txt",
        "config/r2_downtrend_portability_v1.json",
        "src/__init__.py",
        "src/downtrend.py",
        "src/contract.py",
        "lock_contract.py",
        "run_research.py",
        "tests/test_downtrend.py",
        "tests/test_contract.py",
    )
    paths = [(PACKAGE / value).resolve() for value in relative]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Definition files missing: {missing}")
    return sorted(paths)


def dependency_files(config: Mapping[str, Any]) -> list[Path]:
    reference = config["mt5_reference"]
    values = [
        str(config["source"]["old_final_contract"]),
        str(config["source"]["decoder_reference"]),
        str(reference["source_ea"]),
        str(reference["pullback_report"]),
        str(reference["impulse_report"]),
    ]
    paths = [(PACKAGE / value).resolve() for value in values]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Dependency files missing: {missing}")
    return sorted(paths)


def _old_external_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    final_path = (PACKAGE / str(config["source"]["old_final_contract"])).resolve()
    if downtrend.sha256_file(final_path) != str(
        config["source"]["old_final_contract_sha256"]
    ):
        raise ValueError("Old final-contract file hash changed")
    final = json.loads(final_path.read_text(encoding="utf-8"))
    expected = str(final.get("final_contract_sha256", ""))
    unsigned = {key: value for key, value in final.items() if key != "final_contract_sha256"}
    if downtrend.canonical_json_sha256(unsigned) != expected:
        raise ValueError("Old final-contract self hash is invalid")
    return list(final["external_files"])


def _old_m5_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = [
        item
        for item in _old_external_records(config)
        if "/dukascopy-replay/bars/XAUUSD/" in str(item["path"])
        and "/M5/" in str(item["path"])
    ]
    if len(records) != 78 * 3:
        raise ValueError(f"Expected 234 old M5 bar records, found {len(records)}")
    return records


def _old_tick_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = [
        item
        for item in _old_external_records(config)
        if "/dukascopy-replay/normalized/XAUUSD/" in str(item["path"])
        and str(item["path"]).endswith("/ticks.parquet")
    ]
    if len(records) != 78:
        raise ValueError(f"Expected 78 old tick records, found {len(records)}")
    return records


def _raw_manifest_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    source = config["source"]
    root = downtrend.storage_root(config)
    raw_root = root / str(source["raw_tick_root"])
    start = pd.Timestamp(source["raw_tick_start_utc"]).tz_localize(None).to_period("M")
    end = (
        pd.Timestamp(source["end_exclusive_utc"])
        .tz_localize(None)
        .to_period("M")
        - 1
    )
    records: list[dict[str, Any]] = []
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
            raise ValueError(f"Raw tick manifest is not complete and frozen: {path}")
        record = _record(path, root)
        record["files_sha256"] = str(payload["files_sha256"])
        records.append(record)
    if len(records) != int(source["raw_tick_manifest_count"]):
        raise ValueError(f"Unexpected raw tick manifest count: {len(records)}")
    if downtrend.canonical_json_sha256(records) != str(
        source["raw_tick_manifest_digest"]
    ):
        raise ValueError("Raw tick manifest digest mismatch")
    return records


def external_records(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    root = downtrend.storage_root(config)
    records = _old_m5_records(config) + _old_tick_records(config)
    records.extend(_raw_manifest_records(config))
    new_cache = root / str(config["source"]["new_feature_cache"])
    new_manifest = root / str(config["source"]["new_feature_manifest"])
    records.extend([_record(new_cache, root), _record(new_manifest, root)])
    return sorted(records, key=lambda item: str(item["path"]))


def _verify_records(
    records: Iterable[Mapping[str, Any]], base: Path, label: str
) -> None:
    for record in records:
        path = (base / str(record["path"])).resolve()
        try:
            path.relative_to(base.resolve())
        except ValueError as exc:
            raise ValueError(f"{label} path escaped root: {path}") from exc
        if not path.is_file():
            raise FileNotFoundError(path)
        if int(path.stat().st_size) != int(record["bytes"]):
            raise ValueError(f"{label} size mismatch: {record['path']}")
        if downtrend.sha256_file(path) != str(record["sha256"]):
            raise ValueError(f"{label} hash mismatch: {record['path']}")


def _self_hash(payload: Mapping[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "definition_contract_sha256"}
    return downtrend.canonical_json_sha256(unsigned)


def build_definition_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    controls = config["research_controls"]
    for key in (
        "same_version_post_outcome_tuning_authorized",
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
        "training_authorized",
        "execution_authorized",
    ):
        if bool(controls[key]):
            raise ValueError(f"Prohibited research control: {key}")
    attempts = [int(item["attempt_no"]) for item in config["attempts"]]
    if attempts != list(
        range(
            int(controls["new_attempt_first"]),
            int(controls["new_attempt_last"]) + 1,
        )
    ):
        raise ValueError("Attempt ledger is not contiguous")
    root = downtrend.storage_root(config)
    lock: dict[str, Any] = {
        "schema_version": "xauusd_r2_downtrend_portability_definition_lock_v1",
        "locked_utc": datetime.now(UTC).isoformat(),
        "config_sha256": downtrend.sha256_file(CONFIG_PATH),
        "attempts": config["attempts"],
        "windows": config["windows"],
        "gates": config["gates"],
        "repository_files": [
            _record(path, REPO) for path in package_files() + dependency_files(config)
        ],
        "external_files": external_records(config),
        "outcomes_opened": False,
        "parameter_search_count": 0,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
        "training_authorized": False,
        "execution_authorized": False,
        "storage_root": str(root),
        "raw_tick_execution": True,
        "raw_tick_manifest_digest": config["source"]["raw_tick_manifest_digest"],
    }
    lock["definition_contract_sha256"] = _self_hash(lock)
    return lock


def validate_definition_lock(
    lock: Mapping[str, Any], config: Mapping[str, Any]
) -> None:
    if lock.get("schema_version") != "xauusd_r2_downtrend_portability_definition_lock_v1":
        raise ValueError("Unexpected definition-lock schema")
    if str(lock.get("definition_contract_sha256")) != _self_hash(lock):
        raise ValueError("Definition-lock self hash mismatch")
    if str(lock.get("config_sha256")) != downtrend.sha256_file(CONFIG_PATH):
        raise ValueError("Config changed after definition lock")
    if lock.get("attempts") != config["attempts"]:
        raise ValueError("Attempts changed after definition lock")
    if lock.get("windows") != config["windows"] or lock.get("gates") != config["gates"]:
        raise ValueError("Windows or gates changed after definition lock")
    for key in (
        "outcomes_opened",
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
        "training_authorized",
        "execution_authorized",
    ):
        if bool(lock.get(key)):
            raise ValueError(f"Definition lock has prohibited flag: {key}")
    _verify_records(lock["repository_files"], REPO, "repository")
    _verify_records(lock["external_files"], downtrend.storage_root(config), "external")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

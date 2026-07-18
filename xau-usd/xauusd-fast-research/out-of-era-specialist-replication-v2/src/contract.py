from __future__ import annotations

from datetime import UTC, datetime
import importlib.metadata
import json
import hashlib
import os
from pathlib import Path
import platform
from typing import Any, Iterable, Mapping

import pandas as pd


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]
CONFIG_PATH = PACKAGE / "config" / "out_of_era_specialist_replication_v2.json"
DEFINITION_LOCK_PATH = PACKAGE / "outputs" / "OUT_OF_ERA_SPECIALIST_DEFINITION_LOCK.json"
FINAL_LOCK_PATH = PACKAGE / "outputs" / "OUT_OF_ERA_SPECIALIST_FINAL_CONTRACT_LOCK.json"
OUTCOME_MARKER_PATH = PACKAGE / "outputs" / "OUT_OF_ERA_SPECIALIST_OUTCOMES_OPENED.json"
RESULT_PATH = PACKAGE / "outputs" / "OUT_OF_ERA_SPECIALIST_RESULT.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def storage_root(config: Mapping[str, Any]) -> Path:
    source = config["source"]
    return Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()


def expected_months(config: Mapping[str, Any]) -> list[str]:
    source = config["source"]
    start = pd.Timestamp(source["start_utc"])
    end = pd.Timestamp(source["end_exclusive_utc"])
    months = pd.period_range(
        start.tz_localize(None).to_period("M"),
        (end - pd.Timedelta(days=1)).tz_localize(None).to_period("M"),
        freq="M",
    ).astype(str).tolist()
    if len(months) != int(source["expected_months"]):
        raise ValueError("Expected-month count disagrees with date boundary")
    return months


def _assert_controls(config: Mapping[str, Any]) -> None:
    controls = config["research_controls"]
    if int(controls["registered_candidate_count"]) != len(config["candidates"]):
        raise ValueError("Registered candidate count mismatch")
    if len(config["candidates"]) != 5:
        raise ValueError("V2 must contain exactly five fixed candidates")
    candidate_ids = [str(item["candidate_id"]) for item in config["candidates"]]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("Duplicate candidate ID")
    if int(controls["parameter_search_count"]) != 0:
        raise ValueError("Out-of-era replication cannot search parameters")
    if not bool(controls["single_outcome_opening"]):
        raise ValueError("V2 must use one outcome opening")
    if not bool(controls["research_only"]):
        raise ValueError("V2 must remain research-only")
    prohibited = (
        "paid_data_request_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "model_training_authorized",
        "ea_consumption_authorized",
    )
    if any(bool(controls[name]) for name in prohibited):
        raise ValueError("A prohibited research authority is enabled")
    attempts = sorted(
        int(item["attempt_no"])
        for item in config["candidates"]
        if "attempt_no" in item
    )
    expected_attempts = list(
        range(
            int(controls["new_attempt_first"]),
            int(controls["new_attempt_last"]) + 1,
        )
    )
    if attempts != expected_attempts:
        raise ValueError("New FOMC attempt numbers are not contiguous")


def _record(path: Path, base: Path) -> dict[str, Any]:
    resolved = path.resolve()
    return {
        "path": str(resolved.relative_to(base.resolve())).replace("\\", "/"),
        "bytes": int(resolved.stat().st_size),
        "sha256": sha256_file(resolved),
    }


def _verify_records(
    records: Iterable[Mapping[str, Any]], base: Path, label: str
) -> None:
    seen: set[str] = set()
    for record in records:
        relative = str(record["path"])
        if relative in seen:
            raise ValueError(f"Duplicate {label} contract path: {relative}")
        seen.add(relative)
        path = (base / relative).resolve()
        try:
            path.relative_to(base.resolve())
        except ValueError as exc:
            raise ValueError(f"{label} path escaped contract root: {path}") from exc
        if not path.is_file():
            raise FileNotFoundError(path)
        if int(path.stat().st_size) != int(record["bytes"]):
            raise ValueError(f"{label} size mismatch: {relative}")
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"{label} hash mismatch: {relative}")


def repository_paths(config: Mapping[str, Any]) -> list[Path]:
    scope = config["contract_scope"]
    paths = {
        (PACKAGE / relative).resolve() for relative in scope["repository_files"]
    }
    suffixes = {".py", ".json", ".yaml", ".yml", ".md", ".txt"}
    for relative in scope["repository_roots"]:
        root = (PACKAGE / relative).resolve()
        if not root.is_dir():
            raise FileNotFoundError(root)
        paths.update(
            path.resolve()
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower() in suffixes
            and "__pycache__" not in path.parts
        )
    paths.add((PACKAGE / config["base_regime_config"]).resolve())
    for candidate in config["candidates"]:
        for key in ("source_config", "source_code", "regime_code"):
            value = candidate.get(key)
            if value:
                paths.add((PACKAGE / str(value)).resolve())
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Definition files missing: {missing[:3]}")
    for path in paths:
        try:
            path.relative_to(REPO)
        except ValueError as exc:
            raise ValueError(f"Definition file escaped repository: {path}") from exc
    return sorted(paths)


def public_input_paths(config: Mapping[str, Any]) -> list[Path]:
    root = storage_root(config)
    public_root = root / config["source"]["public_input_root"]
    manifest_path = public_root / "OFFICIAL_FOMC_SOURCE_MANIFEST.json"
    calendar_path = public_root / "OFFICIAL_FOMC_CALENDAR_2010_2016.csv"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "xauusd_official_fomc_sources_v2":
        raise ValueError("Unexpected official FOMC manifest schema")
    for flag in (
        "contains_outcomes",
        "strategy_scoring_performed",
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
    ):
        if bool(manifest.get(flag)):
            raise ValueError(f"Official FOMC manifest has prohibited flag: {flag}")
    expected = int(config["official_fomc"]["expected_regular_events"])
    if int(manifest["calendar_rows"]) != expected:
        raise ValueError("Official FOMC event count mismatch")
    if sha256_file(calendar_path) != manifest["calendar_sha256"]:
        raise ValueError("Official FOMC calendar hash mismatch")
    calendar = pd.read_csv(calendar_path, parse_dates=["event_time_utc"])
    if len(calendar) != expected or calendar["event_id"].duplicated().any():
        raise ValueError("Official FOMC calendar is duplicated or incomplete")
    if not calendar["event_time_utc"].is_monotonic_increasing:
        raise ValueError("Official FOMC calendar is not sorted")
    start = pd.Timestamp(config["source"]["start_utc"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    if calendar["event_time_utc"].lt(start).any() or calendar["event_time_utc"].ge(end).any():
        raise ValueError("Official FOMC event escaped the sealed window")
    paths = [manifest_path, calendar_path]
    for name, record in manifest["sources"].items():
        path = (public_root / str(record["path"])).resolve()
        try:
            path.relative_to(public_root.resolve())
        except ValueError as exc:
            raise ValueError(f"Official source escaped public root: {name}") from exc
        if not path.is_file():
            raise FileNotFoundError(path)
        if int(path.stat().st_size) != int(record["bytes"]):
            raise ValueError(f"Official source size mismatch: {name}")
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"Official source hash mismatch: {name}")
        paths.append(path)
    if len([name for name in manifest["sources"] if name.startswith("statement/")]) != expected:
        raise ValueError("Official statement source count mismatch")
    return sorted(set(paths))


def _validate_self_hash(
    payload: Mapping[str, Any], hash_key: str, label: str
) -> None:
    claimed = str(payload.get(hash_key, ""))
    body = dict(payload)
    body.pop(hash_key, None)
    if not claimed or canonical_hash(body) != claimed:
        raise ValueError(f"{label} canonical hash mismatch")


def build_definition_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    _assert_controls(config)
    if DEFINITION_LOCK_PATH.exists():
        raise RuntimeError("Out-of-era specialist definitions were already locked")
    if OUTCOME_MARKER_PATH.exists() or RESULT_PATH.exists():
        raise RuntimeError("Cannot lock definitions after outcomes")
    repository = [_record(path, REPO) for path in repository_paths(config)]
    root = storage_root(config)
    external = [_record(path, root) for path in public_input_paths(config)]
    lock: dict[str, Any] = {
        "schema_version": "xauusd_out_of_era_specialist_definition_lock_v2",
        "locked_utc": datetime.now(UTC).isoformat(),
        "config_sha256": sha256_file(CONFIG_PATH),
        "repository_files": repository,
        "public_input_files": external,
        "registered_candidates": [
            str(item["candidate_id"]) for item in config["candidates"]
        ],
        "new_attempt_first": int(config["research_controls"]["new_attempt_first"]),
        "new_attempt_last": int(config["research_controls"]["new_attempt_last"]),
        "gates": config["gates"],
        "independence": config["independence"],
        "parameter_search_count": 0,
        "normalized_data_ready": False,
        "outcomes_opened": False,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    lock["definition_contract_sha256"] = canonical_hash(lock)
    return lock


def validate_definition_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    if not DEFINITION_LOCK_PATH.is_file():
        raise FileNotFoundError(DEFINITION_LOCK_PATH)
    lock = json.loads(DEFINITION_LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("schema_version") != "xauusd_out_of_era_specialist_definition_lock_v2":
        raise ValueError("Unexpected specialist definition-lock schema")
    _validate_self_hash(lock, "definition_contract_sha256", "Definition contract")
    _assert_controls(config)
    if lock["config_sha256"] != sha256_file(CONFIG_PATH):
        raise ValueError("Configuration changed after definition lock")
    if lock["gates"] != config["gates"] or lock["independence"] != config["independence"]:
        raise ValueError("Decision gates changed after definition lock")
    registered = [str(item["candidate_id"]) for item in config["candidates"]]
    if lock["registered_candidates"] != registered:
        raise ValueError("Candidate definitions changed after lock")
    _verify_records(lock["repository_files"], REPO, "repository")
    _verify_records(lock["public_input_files"], storage_root(config), "public input")
    for flag in (
        "outcomes_opened",
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
        "training_authorized",
        "execution_authorized",
    ):
        if bool(lock.get(flag)):
            raise ValueError(f"Definition lock has prohibited flag: {flag}")
    return lock


def _validate_collection_status(
    config: Mapping[str, Any], root: Path, months: list[str]
) -> Path:
    path = root / config["source"]["extension_status"]
    status = json.loads(path.read_text(encoding="utf-8"))
    if status.get("schema_version") != "dukascopy_xau_tick_extension_v2":
        raise ValueError("Unexpected extension status schema")
    if status.get("months_complete_this_run") != months:
        raise ValueError("Dukascopy extension is not exactly complete")
    if int(status.get("months_total", -1)) != len(months):
        raise ValueError("Dukascopy extension month count mismatch")
    if status.get("months_incomplete_this_run"):
        raise ValueError("Dukascopy extension contains incomplete months")
    for flag in (
        "paid_data_request_made",
        "broker_action_performed",
        "strategy_scoring_performed",
    ):
        if bool(status.get(flag)):
            raise ValueError(f"Collection status has prohibited flag: {flag}")
    return path


def _bar_record(
    manifest: Mapping[str, Any], basis: str, timeframe: str
) -> Mapping[str, Any]:
    matches = [
        row
        for row in manifest["result"]["bars"]
        if str(row["basis"]).lower() == basis.lower()
        and str(row["timeframe"]).upper() == timeframe.upper()
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected one {basis} {timeframe} artifact")
    return matches[0]


def _validate_normalized_inputs(
    config: Mapping[str, Any], root: Path, months: list[str]
) -> tuple[Path, list[Path], list[Path]]:
    replay_root = root / config["source"]["replay_root"]
    status_path = replay_root / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    if status.get("schema_version") != "xauusd_out_of_era_normalization_status_v1":
        raise ValueError("Unexpected normalization status schema")
    if status.get("normalized_months") != months or status.get("ready_months_seen") != months:
        raise ValueError("Normalization is not exactly complete")
    if int(status.get("expected_months", -1)) != len(months):
        raise ValueError("Normalization month count mismatch")
    for flag in ("strategy_scoring_performed", "outcomes_opened", "paid_data_request_made"):
        if bool(status.get(flag)):
            raise ValueError(f"Normalization status has prohibited flag: {flag}")
    manifests: list[Path] = []
    consumed: list[Path] = []
    scope = config["contract_scope"]
    timeframe = str(scope["consumed_timeframe"])
    for month in months:
        manifest_path = replay_root / "manifests" / f"{month}.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("month") != month:
            raise ValueError(f"Normalized manifest month mismatch: {month}")
        if bool(manifest.get("outcomes_opened")) or bool(manifest.get("strategy_scoring_performed")):
            raise ValueError(f"Normalized manifest opened outcomes: {month}")
        integrity = manifest["result"]["integrity"]
        for field in (
            "negative_spread_count",
            "conflicting_same_timestamp_count",
            "exact_duplicate_count",
        ):
            if int(integrity[field]) != 0:
                raise ValueError(f"Integrity failure {field}: {month}")
        partition = manifest["result"]["partition"]
        tick_path = replay_root / partition["path"]
        if not tick_path.is_file() or sha256_file(tick_path) != partition["sha256"]:
            raise ValueError(f"Normalized tick hash mismatch: {month}")
        manifests.append(manifest_path)
        if bool(scope["verify_normalized_ticks"]):
            consumed.append(tick_path)
        for basis in scope["consumed_bar_bases"]:
            row = _bar_record(manifest, str(basis), timeframe)
            bar_path = replay_root / row["path"]
            if not bar_path.is_file() or sha256_file(bar_path) != row["sha256"]:
                raise ValueError(f"Consumed bar hash mismatch: {month} {basis}")
            consumed.append(bar_path)
    return status_path, manifests, consumed


def runtime_versions() -> dict[str, str]:
    packages = ("numpy", "pandas", "pyarrow", "scipy", "PyYAML")
    return {
        "python": platform.python_version(),
        **{name: importlib.metadata.version(name) for name in packages},
    }


def build_final_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    if FINAL_LOCK_PATH.exists():
        raise RuntimeError("Out-of-era specialist final contract already exists")
    if OUTCOME_MARKER_PATH.exists() or RESULT_PATH.exists():
        raise RuntimeError("Cannot lock final contract after outcomes")
    definition = validate_definition_lock(config)
    root = storage_root(config)
    months = expected_months(config)
    extension_status = _validate_collection_status(config, root, months)
    normalization_status, manifests, consumed = _validate_normalized_inputs(
        config, root, months
    )
    external_paths = {
        path.resolve()
        for path in (
            extension_status,
            normalization_status,
            *public_input_paths(config),
            *manifests,
            *consumed,
        )
    }
    lock: dict[str, Any] = {
        "schema_version": "xauusd_out_of_era_specialist_final_contract_v2",
        "locked_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": definition["definition_contract_sha256"],
        "expected_months": months,
        "repository_files": definition["repository_files"],
        "external_files": [_record(path, root) for path in sorted(external_paths)],
        "runtime_versions": runtime_versions(),
        "registered_candidates": definition["registered_candidates"],
        "parameter_search_count": 0,
        "outcomes_opened": False,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
        "training_authorized": False,
        "execution_authorized": False,
    }
    lock["final_contract_sha256"] = canonical_hash(lock)
    return lock


def validate_final_lock(
    lock: Mapping[str, Any], config: Mapping[str, Any]
) -> None:
    if lock.get("schema_version") != "xauusd_out_of_era_specialist_final_contract_v2":
        raise ValueError("Unexpected specialist final-contract schema")
    _validate_self_hash(lock, "final_contract_sha256", "Final contract")
    definition = validate_definition_lock(config)
    if lock["definition_contract_sha256"] != definition["definition_contract_sha256"]:
        raise ValueError("Definition contract changed after final lock")
    if lock["expected_months"] != expected_months(config):
        raise ValueError("Final-contract month set changed")
    if lock["registered_candidates"] != definition["registered_candidates"]:
        raise ValueError("Final-contract candidates changed")
    if lock["runtime_versions"] != runtime_versions():
        raise ValueError("Runtime versions changed after final lock")
    _verify_records(lock["repository_files"], REPO, "repository")
    _verify_records(lock["external_files"], storage_root(config), "external")
    for flag in (
        "outcomes_opened",
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
        "training_authorized",
        "execution_authorized",
    ):
        if bool(lock.get(flag)):
            raise ValueError(f"Final contract has prohibited flag: {flag}")

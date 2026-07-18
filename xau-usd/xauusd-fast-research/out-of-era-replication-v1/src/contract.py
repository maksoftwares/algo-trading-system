from __future__ import annotations

import csv
from datetime import UTC, datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
from typing import Any, Iterable, Mapping


PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]


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
    return json.loads(
        (PACKAGE / "config" / "out_of_era_replication_v1.json").read_text(
            encoding="utf-8"
        )
    )


def storage_root(config: Mapping[str, Any]) -> Path:
    source = config["source"]
    return Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()


def expected_months(config: Mapping[str, Any]) -> list[str]:
    source = config["source"]
    start = datetime.fromisoformat(str(source["start_utc"]).replace("Z", "+00:00"))
    end = datetime.fromisoformat(
        str(source["end_exclusive_utc"]).replace("Z", "+00:00")
    )
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise ValueError("Invalid UTC replication boundary")
    year, month = start.year, start.month
    values: list[str] = []
    while (year, month) < (end.year, end.month):
        values.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year += 1
            month = 1
    if len(values) != int(source["expected_months"]):
        raise ValueError("Expected-month count disagrees with date boundary")
    return values


def _assert_authority_disabled(config: Mapping[str, Any]) -> None:
    controls = config["research_controls"]
    prohibited = (
        "paid_data_request_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
    )
    if any(bool(controls[name]) for name in prohibited):
        raise ValueError("A prohibited research authority is enabled")
    if not bool(controls["research_only"]):
        raise ValueError("The out-of-era lane must remain research-only")
    if int(controls["parameter_search_count"]) != 0:
        raise ValueError("Out-of-era replication cannot search parameters")


def _validate_self_hash(
    payload: Mapping[str, Any], hash_key: str, label: str
) -> None:
    claimed = str(payload.get(hash_key, ""))
    body = dict(payload)
    body.pop(hash_key, None)
    if not claimed or canonical_hash(body) != claimed:
        raise ValueError(f"{label} canonical hash mismatch")


def validate_definition_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    path = PACKAGE / "outputs" / "OUT_OF_ERA_DEFINITION_LOCK.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("schema_version") != "xauusd_out_of_era_definition_lock_v1":
        raise ValueError("Unexpected definition-lock schema")
    _validate_self_hash(
        lock, "definition_contract_sha256", "Definition contract"
    )
    config_path = PACKAGE / "config" / "out_of_era_replication_v1.json"
    if lock["config_sha256"] != sha256_file(config_path):
        raise ValueError("Configuration changed after definition lock")
    prereg = PACKAGE / "PREREGISTRATION.md"
    if lock["preregistration_sha256"] != sha256_file(prereg):
        raise ValueError("Preregistration changed after definition lock")
    if lock.get("gates") != config["gates"]:
        raise ValueError("Gates differ from definition lock")
    if lock.get("registered_candidates") != [
        item["candidate_id"] for item in config["candidates"]
    ]:
        raise ValueError("Candidate list differs from definition lock")
    if bool(lock.get("outcomes_opened")):
        raise ValueError("Definition lock says outcomes were already opened")
    for raw_path, expected in lock["file_hashes"].items():
        file_path = Path(raw_path)
        if not file_path.is_file() or sha256_file(file_path) != expected:
            raise ValueError(f"Definition-lock file mismatch: {file_path}")
    return lock


def _repository_paths(config: Mapping[str, Any]) -> list[Path]:
    scope = config["contract_scope"]
    paths: set[Path] = set()
    for relative in scope["repository_code_roots"]:
        root = (REPO / relative).resolve()
        if not root.is_dir():
            raise FileNotFoundError(root)
        paths.update(path.resolve() for path in root.rglob("*.py"))
    for relative in scope["repository_files"]:
        paths.add((REPO / relative).resolve())
    for candidate in config["candidates"]:
        for key, value in candidate.items():
            if key.startswith("source_") and key != "source_policy_id":
                paths.add((PACKAGE / value).resolve())
    definition = PACKAGE / "outputs" / "OUT_OF_ERA_DEFINITION_LOCK.json"
    paths.add(definition.resolve())
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Repository contract files missing: {missing[:3]}")
    for path in paths:
        try:
            path.relative_to(REPO)
        except ValueError as exc:
            raise ValueError(f"Repository file escaped workspace: {path}") from exc
    return sorted(paths)


def _record(path: Path, base: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(base)).replace("\\", "/"),
        "bytes": int(path.stat().st_size),
        "sha256": sha256_file(path),
    }


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


def _validate_public_inputs(
    config: Mapping[str, Any], root: Path
) -> list[Path]:
    public_root = root / config["source"]["public_input_root"]
    manifest_path = public_root / "PUBLIC_INPUT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for flag in (
        "paid_data_request_made",
        "databento_used",
        "broker_action_performed",
        "outcomes_opened",
    ):
        if bool(manifest.get(flag)):
            raise ValueError(f"Public input manifest has prohibited flag: {flag}")
    bls_path = public_root / "bls-nfp-2010-2016.json"
    gld_path = public_root / "gld-daily-2008-2016.csv"
    if sha256_file(bls_path) != manifest["bls"]["output_sha256"]:
        raise ValueError("BLS public input hash mismatch")
    if sha256_file(gld_path) != manifest["gld"]["output_sha256"]:
        raise ValueError("GLD public input hash mismatch")
    bls = json.loads(bls_path.read_text(encoding="utf-8"))
    if len(bls) != int(config["public_sources"]["bls_expected_releases"]):
        raise ValueError("BLS release count mismatch")
    dates = [str(row["date"]) for row in bls]
    if dates != sorted(set(dates)):
        raise ValueError("BLS dates are duplicated or unsorted")
    with gld_path.open("r", encoding="utf-8", newline="") as handle:
        gld_rows = list(csv.DictReader(handle))
    if len(gld_rows) < int(config["public_sources"]["gld_minimum_rows"]):
        raise ValueError("GLD public input is too short")
    paths = [manifest_path, bls_path, gld_path]
    snapshot = manifest["bls"].get("source_snapshot_path")
    if snapshot:
        snapshot_path = Path(snapshot).resolve()
        if not snapshot_path.is_file():
            raise FileNotFoundError(snapshot_path)
        paths.append(snapshot_path)
    return paths


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
    if status.get("normalized_months") != months:
        raise ValueError("Normalization is not exactly complete")
    if status.get("ready_months_seen") != months:
        raise ValueError("Normalization did not see the complete collection")
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
        if bool(manifest.get("outcomes_opened")) or bool(
            manifest.get("strategy_scoring_performed")
        ):
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
    _assert_authority_disabled(config)
    definition = validate_definition_lock(config)
    root = storage_root(config)
    months = expected_months(config)
    extension_status = _validate_collection_status(config, root, months)
    public_paths = _validate_public_inputs(config, root)
    normalization_status, manifests, consumed = _validate_normalized_inputs(
        config, root, months
    )
    repository = [_record(path, REPO) for path in _repository_paths(config)]
    external_paths = {
        path.resolve()
        for path in [
            extension_status,
            normalization_status,
            *public_paths,
            *manifests,
            *consumed,
        ]
    }
    external = [_record(path, root) for path in sorted(external_paths)]
    lock: dict[str, Any] = {
        "schema_version": "xauusd_out_of_era_final_contract_v1",
        "locked_utc": datetime.now(UTC).isoformat(),
        "definition_contract_sha256": definition["definition_contract_sha256"],
        "expected_months": months,
        "repository_files": repository,
        "external_files": external,
        "runtime_versions": runtime_versions(),
        "registered_candidates": [
            item["candidate_id"] for item in config["candidates"]
        ],
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


def validate_final_lock(
    lock: Mapping[str, Any], config: Mapping[str, Any]
) -> None:
    if lock.get("schema_version") != "xauusd_out_of_era_final_contract_v1":
        raise ValueError("Unexpected final-contract schema")
    _validate_self_hash(lock, "final_contract_sha256", "Final contract")
    _assert_authority_disabled(config)
    if lock.get("expected_months") != expected_months(config):
        raise ValueError("Final-contract month list mismatch")
    if lock.get("registered_candidates") != [
        item["candidate_id"] for item in config["candidates"]
    ]:
        raise ValueError("Final-contract candidate list mismatch")
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
    if lock.get("runtime_versions") != runtime_versions():
        raise ValueError("Runtime versions changed after final lock")
    _verify_records(lock["repository_files"], REPO, "repository")
    _verify_records(lock["external_files"], storage_root(config), "external")
    definition = validate_definition_lock(config)
    if lock["definition_contract_sha256"] != definition["definition_contract_sha256"]:
        raise ValueError("Definition contract changed after final lock")

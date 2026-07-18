from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "ppi_event_reaction_v1.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def contract_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    research_root = ROOT.parent
    base_path = (ROOT / config["base_contract"]).resolve()
    base = json.loads(base_path.read_text(encoding="utf-8"))
    source = config["source"]
    storage_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    output = ROOT / config["outputs"]["directory"]
    paths = {
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "PRE_OUTCOME_LOCK_REPLACEMENT.md": ROOT / "PRE_OUTCOME_LOCK_REPLACEMENT.md",
        "requirements.txt": ROOT / "requirements.txt",
        "config/ppi_event_reaction_v1.json": CONFIG_PATH,
        "acquire_calendar.py": ROOT / "acquire_calendar.py",
        "prepare_candidates.py": ROOT / "prepare_candidates.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_stage.py": ROOT / "run_stage.py",
        "tests/test_ppi_event_reaction_v1.py": ROOT
        / "tests"
        / "test_ppi_event_reaction_v1.py",
        "outputs/raw_archive_index": output
        / config["outputs"]["raw_archive_index"],
        "outputs/calendar": output / config["outputs"]["calendar"],
        "outputs/calendar_manifest": output
        / config["outputs"]["calendar_manifest"],
        "outputs/candidates": output / config["outputs"]["candidates"],
        "outputs/candidate_manifest": output
        / config["outputs"]["candidate_manifest"],
        "upstream/event_reaction.py": research_root
        / "macro-event-reaction-replication-v2"
        / "src"
        / "event_reaction.py",
        "upstream/event_reaction_tests.py": research_root
        / "macro-event-reaction-replication-v2"
        / "tests"
        / "test_event_reaction.py",
        "upstream/regimes.py": research_root
        / "balanced-regime-campaign-v3"
        / "src"
        / "regimes.py",
        "upstream/base_config.json": base_path,
        "upstream/metrics_engine.py": research_root
        / "ml-candidate-rankers-v1"
        / "src"
        / "engine.py",
        "upstream/data.py": research_root
        / "independent-specialists-v1"
        / "src"
        / "data.py",
        "upstream/spot_labels.py": research_root
        / "comex-futures-foundation-v1"
        / "src"
        / "spot_labels.py",
        "upstream/foundation.py": research_root
        / "comex-futures-foundation-v1"
        / "src"
        / "foundation.py",
        "upstream/dukascopy_tick_foundation.py": ROOT.parents[2]
        / "multi-asset"
        / "data-foundation"
        / "dukascopy-ticks-v1"
        / "src"
        / "dukascopy_tick_foundation"
        / "foundation.py",
        "external/feature_cache": storage_root / base["source"]["feature_cache"],
        "external/feature_manifest": storage_root
        / base["source"]["feature_manifest"],
    }
    acquisition_manifests = sorted(
        (storage_root / "raw" / source["symbol"]).glob(
            "year=*/month=*/_ACQUISITION_MANIFEST.json"
        )
    )
    for path in acquisition_manifests:
        year = int(path.parents[1].name.removeprefix("year="))
        month = int(path.parent.name.removeprefix("month="))
        if not (201607 <= year * 100 + month < 202607):
            continue
        relative = path.relative_to(storage_root).as_posix()
        paths[f"external/{relative}"] = path
    return paths


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if lock_path.exists() or any(output.glob("*_OUTCOMES_OPENED.json")):
        raise RuntimeError("PPI event V1 was already locked or opened")
    paths = contract_paths(config)
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing PPI contract inputs: {missing}")
    calendar_manifest = json.loads(
        (output / config["outputs"]["calendar_manifest"]).read_text(
            encoding="utf-8"
        )
    )
    candidate_manifest = json.loads(
        (output / config["outputs"]["candidate_manifest"]).read_text(
            encoding="utf-8"
        )
    )
    if _sha256(output / config["outputs"]["calendar"]) != calendar_manifest[
        "calendar_sha256"
    ]:
        raise ValueError("PPI calendar manifest mismatch")
    if _sha256(output / config["outputs"]["candidates"]) != candidate_manifest[
        "candidate_sha256"
    ]:
        raise ValueError("PPI candidate manifest mismatch")
    policies = config["policies"]
    controls = config["research_controls"]
    attempts = [int(policy["attempt_no"]) for policy in policies]
    expected_first = int(controls["campaign_attempts_before_v1"]) + 1
    if attempts != list(range(expected_first, expected_first + len(policies))):
        raise ValueError("PPI attempt sequence changed")
    if len(policies) != int(controls["registered_policy_count"]):
        raise ValueError("PPI registered policy count changed")
    body = {
        "schema_version": "xauusd_ppi_event_contract_lock_v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {name: _sha256(path) for name, path in sorted(paths.items())},
        "attempt_first": min(attempts),
        "attempt_last": max(attempts),
        "policy_ids": [str(policy["policy_id"]) for policy in policies],
        "registered_policy_count": len(policies),
        "parameter_search_count": int(controls["parameter_search_count"]),
        "calendar_rows": int(calendar_manifest["calendar_rows"]),
        "candidate_rows": int(candidate_manifest["candidate_rows"]),
        "outcomes_opened": False,
        "training_authorized": False,
        "execution_authorized": False,
        "paid_data_authorized": False,
        "databento_use_authorized": False,
    }
    body["contract_sha256"] = _canonical_hash(body)
    _write_json(lock_path, body)
    print(json.dumps(body, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

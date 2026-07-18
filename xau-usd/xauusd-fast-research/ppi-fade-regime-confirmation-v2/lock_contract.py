from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config" / "ppi_fade_regime_confirmation_v2.json"


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
    parent = (ROOT / config["parent_package"]).resolve()
    parent_output = parent / "outputs"
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
        "requirements.txt": ROOT / "requirements.txt",
        "config/ppi_fade_regime_confirmation_v2.json": CONFIG_PATH,
        "prepare_candidates.py": ROOT / "prepare_candidates.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_confirmation.py": ROOT / "run_confirmation.py",
        "tests/test_ppi_fade_regime_confirmation_v2.py": ROOT
        / "tests"
        / "test_ppi_fade_regime_confirmation_v2.py",
        "outputs/candidates": output / config["outputs"]["candidates"],
        "outputs/candidate_manifest": output
        / config["outputs"]["candidate_manifest"],
        "parent/PREREGISTRATION.md": parent / "PREREGISTRATION.md",
        "parent/config.json": parent / "config" / "ppi_event_reaction_v1.json",
        "parent/prepare_candidates.py": parent / "prepare_candidates.py",
        "parent/contract_lock": parent_output / "PPI_EVENT_CONTRACT_LOCK.json",
        "parent/calendar": parent_output / "PPI_EVENT_CALENDAR.csv",
        "parent/calendar_manifest": parent_output
        / "PPI_EVENT_CALENDAR_MANIFEST.json",
        "parent/candidates": parent_output / "PPI_EVENT_CANDIDATES.parquet",
        "parent/candidate_manifest": parent_output
        / "PPI_EVENT_CANDIDATE_MANIFEST.json",
        "parent/historical_outcomes": parent_output
        / "PPI_EVENT_HISTORICAL_DISCOVERY_OUTCOMES.parquet",
        "parent/historical_metrics": parent_output
        / "PPI_EVENT_HISTORICAL_DISCOVERY_METRICS.csv",
        "parent/historical_result": parent_output
        / "PPI_EVENT_HISTORICAL_DISCOVERY_RESULT.json",
        "parent/historical_advancement": parent_output
        / "PPI_EVENT_HISTORICAL_DISCOVERY_ADVANCEMENT_LOCK.json",
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
    for path in sorted(
        (storage_root / "raw" / source["symbol"]).glob(
            "year=*/month=*/_ACQUISITION_MANIFEST.json"
        )
    ):
        year = int(path.parents[1].name.removeprefix("year="))
        month = int(path.parent.name.removeprefix("month="))
        if not (202201 <= year * 100 + month < 202607):
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
    parent_output = (ROOT / config["parent_package"]).resolve() / "outputs"
    if lock_path.exists() or any(output.glob("*_OUTCOMES_OPENED.json")):
        raise RuntimeError("PPI fade regime V2 was already locked or opened")
    if (parent_output / "PPI_EVENT_RELATED_CONFIRMATION_OUTCOMES_OPENED.json").exists():
        raise RuntimeError("Parent PPI confirmation was already opened")
    paths = contract_paths(config)
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing V2 contract inputs: {missing}")
    tick_manifests = [
        name for name in paths if name.startswith("external/raw/XAUUSD/year=")
    ]
    if len(tick_manifests) != 54:
        raise ValueError(f"Expected 54 confirmation tick manifests, found {len(tick_manifests)}")

    manifest = json.loads(
        (output / config["outputs"]["candidate_manifest"]).read_text(
            encoding="utf-8"
        )
    )
    if _sha256(output / config["outputs"]["candidates"]) != manifest[
        "candidate_sha256"
    ]:
        raise ValueError("V2 candidate manifest mismatch")
    policy = config["policy"]
    controls = config["research_controls"]
    attempt = int(policy["attempt_no"])
    if attempt != int(controls["campaign_attempts_before_v2"]) + 1:
        raise ValueError("V2 attempt number is not contiguous")
    if int(controls["registered_policy_count"]) != 1:
        raise ValueError("V2 must contain exactly one registered policy")

    body = {
        "schema_version": "xauusd_ppi_fade_regime_confirmation_contract_v2",
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {name: _sha256(path) for name, path in sorted(paths.items())},
        "attempt_first": attempt,
        "attempt_last": attempt,
        "policy_id": str(policy["policy_id"]),
        "registered_policy_count": 1,
        "parameter_search_count": int(controls["parameter_search_count"]),
        "candidate_rows": int(manifest["candidate_rows"]),
        "parent_confirmation_opened": False,
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

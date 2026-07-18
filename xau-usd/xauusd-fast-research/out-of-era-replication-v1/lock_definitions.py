from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def main() -> int:
    config_path = ROOT / "config" / "out_of_era_replication_v1.json"
    preregistration = ROOT / "PREREGISTRATION.md"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    controls = config["research_controls"]
    if controls["registered_candidate_count"] != 3:
        raise ValueError("Exactly three candidate definitions must be registered")
    if controls["parameter_search_count"] != 0:
        raise ValueError("Out-of-era replication cannot contain a parameter search")
    prohibited = (
        "paid_data_request_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
    )
    if any(bool(controls[name]) for name in prohibited):
        raise ValueError("A prohibited authority is enabled")
    source = config["source"]
    storage_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    public_root = storage_root / source["public_input_root"]
    public_files = [
        public_root / "PUBLIC_INPUT_MANIFEST.json",
        public_root / "bls-nfp-2010-2016.json",
        public_root / "gld-daily-2008-2016.csv",
    ]
    if any(not path.is_file() for path in public_files):
        raise FileNotFoundError("The verified public-input set is incomplete")
    source_files: list[Path] = []
    candidate_hashes: dict[str, dict[str, str]] = {}
    for candidate in config["candidates"]:
        paths = {
            key: (ROOT / value).resolve()
            for key, value in candidate.items()
            if key.startswith("source_") and key not in {"source_policy_id"}
        }
        if any(not path.is_file() for path in paths.values()):
            raise FileNotFoundError(f"Candidate source missing: {candidate['candidate_id']}")
        source_files.extend(paths.values())
        candidate_hashes[candidate["candidate_id"]] = {
            str(path.relative_to(ROOT.parents[2])).replace("\\", "/"): sha256_file(path)
            for path in paths.values()
        }
    file_hashes = {
        str(path): sha256_file(path)
        for path in [config_path, preregistration, *public_files, *source_files]
    }
    lock = {
        "schema_version": "xauusd_out_of_era_definition_lock_v1",
        "locked_utc": datetime.now(UTC).isoformat(),
        "config_sha256": sha256_file(config_path),
        "preregistration_sha256": sha256_file(preregistration),
        "candidate_hashes": candidate_hashes,
        "file_hashes": dict(sorted(file_hashes.items())),
        "registered_candidates": [
            candidate["candidate_id"] for candidate in config["candidates"]
        ],
        "gates": config["gates"],
        "normalized_data_ready": False,
        "outcomes_opened": False,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
    }
    lock["definition_contract_sha256"] = canonical_hash(lock)
    output = ROOT / "outputs" / "OUT_OF_ERA_DEFINITION_LOCK.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(lock, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


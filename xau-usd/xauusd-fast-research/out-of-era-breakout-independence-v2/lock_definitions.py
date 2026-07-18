from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "out_of_era_breakout_independence_v2.json"
LOCK_PATH = ROOT / "outputs" / "OUT_OF_ERA_BREAKOUT_DEFINITION_LOCK.json"


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


def _assert_controls(config: Mapping[str, Any]) -> None:
    controls = config["research_controls"]
    if int(controls["registered_candidate_count"]) != 3:
        raise ValueError("Exactly three fixed candidates must be registered")
    if int(controls["parameter_search_count"]) != 0:
        raise ValueError("Out-of-era replication cannot search parameters")
    prohibited = (
        "paid_data_request_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "model_training_authorized",
        "ea_consumption_authorized",
    )
    if any(bool(controls[name]) for name in prohibited):
        raise ValueError("A prohibited authority is enabled")
    if not bool(controls["research_only"]):
        raise ValueError("Replication must remain research-only")


def definition_paths(config: Mapping[str, Any]) -> list[Path]:
    paths = [
        (ROOT / relative).resolve()
        for relative in config["contract_scope"]["repository_files"]
    ]
    for candidate in config["candidates"]:
        paths.extend(
            (ROOT / value).resolve()
            for key, value in candidate.items()
            if key in {"source_config", "source_code"}
        )
    unique = sorted(set(paths))
    missing = [path for path in unique if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Definition files missing: {missing[:3]}")
    for path in unique:
        try:
            path.relative_to(REPO)
        except ValueError as exc:
            raise ValueError(f"Definition file escaped repository: {path}") from exc
    return unique


def main() -> int:
    if LOCK_PATH.exists():
        raise RuntimeError("Out-of-era breakout definitions were already locked")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    _assert_controls(config)
    paths = definition_paths(config)
    lock: dict[str, Any] = {
        "schema_version": "xauusd_out_of_era_breakout_definition_lock_v2",
        "locked_utc": datetime.now(UTC).isoformat(),
        "config_sha256": sha256_file(CONFIG_PATH),
        "preregistration_sha256": sha256_file(ROOT / "PREREGISTRATION.md"),
        "file_hashes": {
            str(path.relative_to(REPO)).replace("\\", "/"): sha256_file(path)
            for path in paths
        },
        "registered_candidates": [
            str(candidate["candidate_id"]) for candidate in config["candidates"]
        ],
        "gates": config["gates"],
        "independence": config["independence"],
        "parameter_search_count": 0,
        "normalized_data_ready": False,
        "outcomes_opened": False,
        "paid_data_request_made": False,
        "databento_used": False,
        "broker_action_performed": False,
    }
    lock["definition_contract_sha256"] = canonical_hash(lock)
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = LOCK_PATH.with_suffix(LOCK_PATH.suffix + ".part")
    temporary.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, LOCK_PATH)
    print(json.dumps(lock, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

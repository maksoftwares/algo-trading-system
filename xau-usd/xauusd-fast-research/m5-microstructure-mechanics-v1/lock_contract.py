from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
LOCK_PATH = OUTPUT / "M5_MICROSTRUCTURE_CONTRACT_LOCK.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def contract_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    source = config["source"]
    storage = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    return {
        "config/m5_microstructure_mechanics_v1.json": ROOT
        / "config"
        / "m5_microstructure_mechanics_v1.json",
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "requirements.txt": ROOT / "requirements.txt",
        "src/campaign.py": ROOT / "src" / "campaign.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_research.py": ROOT / "run_research.py",
        "upstream/data_source": (ROOT / source["data_source"]).resolve(),
        "external/feature_cache": storage / source["feature_cache"],
        "external/feature_manifest": storage / source["feature_manifest"],
    }


def validate_contract(config: Mapping[str, Any], paths: Mapping[str, Path]) -> None:
    controls = config["research_controls"]
    if int(controls["registered_policy_count"]) != 1000:
        raise ValueError("V1 must register exactly 1,000 policies")
    if int(controls["policies_per_mechanic"]) != 200:
        raise ValueError("V1 must register exactly 200 policies per mechanic")
    if bool(controls["same_version_post_outcome_tuning_authorized"]):
        raise ValueError("Same-version post-outcome tuning is prohibited")
    if not bool(controls["research_only"]):
        raise ValueError("Research-only control is disabled")
    prohibited = (
        "paid_data_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "model_training_authorized",
        "ea_consumption_authorized",
    )
    if any(bool(controls[name]) for name in prohibited):
        raise ValueError("Prohibited authority enabled")
    if OUTPUT.exists():
        opened = [
            path
            for path in OUTPUT.iterdir()
            if path.name != LOCK_PATH.name and not path.name.endswith(".part")
        ]
        if opened:
            raise RuntimeError("Microstructure outcomes or stage artifacts already exist")
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Contract file is missing: {name}: {path}")
    source = config["source"]
    if sha256_file(paths["upstream/data_source"]) != source["data_source_sha256"]:
        raise ValueError("Shared data loader hash mismatch")
    if sha256_file(paths["external/feature_cache"]) != source["feature_sha256"]:
        raise ValueError("Feature cache hash mismatch")
    manifest = json.loads(
        paths["external/feature_manifest"].read_text(encoding="utf-8")
    )
    if manifest.get("feature_sha256") != source["feature_sha256"]:
        raise ValueError("Feature manifest cache hash mismatch")
    if manifest.get("source_digest") != source["source_digest"]:
        raise ValueError("Feature manifest source digest mismatch")
    if int(manifest.get("rows", -1)) != int(source["expected_rows"]):
        raise ValueError("Feature manifest row count mismatch")


def build_lock(config: Mapping[str, Any]) -> dict[str, Any]:
    paths = contract_paths(config)
    validate_contract(config, paths)
    lock: dict[str, Any] = {
        "schema_version": "xauusd_m5_microstructure_mechanics_contract_v1",
        "locked_utc": datetime.now(UTC).isoformat(),
        "files": {name: sha256_file(path) for name, path in sorted(paths.items())},
        "attempt_first": int(config["research_controls"]["campaign_attempts_before_v1"]) + 1,
        "attempt_last": int(config["research_controls"]["campaign_attempts_before_v1"])
        + int(config["research_controls"]["registered_policy_count"]),
        "registered_policy_count": int(config["research_controls"]["registered_policy_count"]),
        "mechanics": config["mechanics"],
        "windows": config["windows"],
        "segments": config["segments"],
        "gates": config["gates"],
        "stage_firewall": "discovery_then_confirmation_then_internal_test_then_exam",
        "research_only": True,
        "training_authorized": False,
        "execution_authorized": False,
    }
    lock["contract_sha256"] = canonical_hash(lock)
    return lock


def main() -> int:
    config = json.loads(
        (ROOT / "config" / "m5_microstructure_mechanics_v1.json").read_text(
            encoding="utf-8"
        )
    )
    lock = build_lock(config)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary = LOCK_PATH.with_suffix(LOCK_PATH.suffix + ".part")
    temporary.write_text(
        json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(LOCK_PATH)
    print(lock["contract_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

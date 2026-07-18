from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "trailing_trend_specialists_v1.json"
PREFIX = "TRAILING_TREND_SPECIALISTS"
LOCK_PATH = OUTPUT / f"{PREFIX}_CONTRACT_LOCK.json"
MANIFEST_PATH = OUTPUT / f"{PREFIX}_POLICY_MANIFEST.csv"


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


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def contract_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    source = config["source"]
    source_root = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    return {
        "config/trailing_trend_specialists_v1.json": CONFIG_PATH,
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "requirements.txt": ROOT / "requirements.txt",
        "src/trend.py": ROOT / "src" / "trend.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_research.py": ROOT / "run_research.py",
        "upstream/dukascopy_data_source.py": (
            ROOT / source["data_source"]
        ).resolve(),
        "external/dukascopy_feature_cache": source_root / source["feature_cache"],
        "external/dukascopy_feature_manifest": source_root
        / source["feature_manifest"],
    }


def _verify_inputs(
    config: Mapping[str, Any], paths: Mapping[str, Path]
) -> dict[str, Any]:
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing contract input {name}: {path}")
    source = config["source"]
    actual_feature_hash = _sha256(paths["external/dukascopy_feature_cache"])
    if actual_feature_hash != source["feature_sha256"]:
        raise ValueError("Dukascopy feature cache hash mismatch")
    manifest = json.loads(
        paths["external/dukascopy_feature_manifest"].read_text(encoding="utf-8")
    )
    if manifest["feature_sha256"] != source["feature_sha256"]:
        raise ValueError("Dukascopy manifest feature hash mismatch")
    if manifest["source_digest"] != source["source_digest"]:
        raise ValueError("Dukascopy manifest source digest mismatch")
    if int(manifest["rows"]) != int(source["expected_rows"]):
        raise ValueError("Unexpected Dukascopy source row count")
    return manifest


def _policy_manifest(config: Mapping[str, Any]) -> pd.DataFrame:
    policies = pd.DataFrame(config["policies"]).sort_values(
        "attempt_no", kind="mergesort"
    )
    controls = config["research_controls"]
    expected_count = int(controls["registered_policy_count"])
    first = int(controls["campaign_attempts_before_v1"]) + 1
    expected_attempts = list(range(first, first + expected_count))
    if len(policies) != expected_count:
        raise ValueError("Registered policy count mismatch")
    if policies["attempt_no"].astype(int).tolist() != expected_attempts:
        raise ValueError("Attempt numbers are not the fixed contiguous sequence")
    if policies["policy_id"].astype(str).duplicated().any():
        raise ValueError("Duplicate policy IDs")
    return policies.reset_index(drop=True)


def main() -> int:
    if LOCK_PATH.exists() or MANIFEST_PATH.exists():
        raise RuntimeError("Trailing-trend V1 was already locked")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    paths = contract_paths(config)
    source_manifest = _verify_inputs(config, paths)
    policies = _policy_manifest(config)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary_manifest = MANIFEST_PATH.with_suffix(".csv.part")
    policies.to_csv(temporary_manifest, index=False)
    os.replace(temporary_manifest, MANIFEST_PATH)
    body = {
        "schema_version": "xauusd_trailing_trend_contract_lock_v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {name: _sha256(path) for name, path in sorted(paths.items())},
        "policy_manifest_sha256": _sha256(MANIFEST_PATH),
        "attempt_first": int(policies["attempt_no"].min()),
        "attempt_last": int(policies["attempt_no"].max()),
        "registered_policy_count": int(len(policies)),
        "parameter_search_count": int(
            config["research_controls"]["parameter_search_count"]
        ),
        "dukascopy_source_rows": int(source_manifest["rows"]),
        "outcomes_opened": False,
        "training_authorized": False,
        "execution_authorized": False,
        "paid_data_authorized": False,
        "databento_use_authorized": False,
    }
    body["contract_sha256"] = _canonical_hash(body)
    _write_json(LOCK_PATH, body)
    print(json.dumps(body, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

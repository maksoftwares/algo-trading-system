from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "cftc_options_volatility_routing_v2.json"
LOCK_PATH = OUTPUT / "CFTC_OPTIONS_VOLATILITY_ROUTING_CONTRACT_LOCK.json"
MANIFEST_PATH = OUTPUT / "CFTC_OPTIONS_VOLATILITY_ROUTING_POLICY_MANIFEST.csv"
CENSUS_PATH = OUTPUT / "CFTC_OPTIONS_VOLATILITY_ROUTING_SIGNAL_CENSUS.json"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
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
    cftc = config["cftc_source"]
    cftc_root = Path(
        os.environ.get(
            cftc["storage_environment_variable"], cftc["default_storage_root"]
        )
    ).resolve()
    return {
        "config/cftc_options_volatility_routing_v2.json": CONFIG_PATH,
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "requirements.txt": ROOT / "requirements.txt",
        "src/volatility.py": ROOT / "src" / "volatility.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_research.py": ROOT / "run_research.py",
        "upstream/cftc_positioning_campaign.py": (
            ROOT / config["base_campaign"]["campaign_source"]
        ).resolve(),
        "upstream/dukascopy_data_source.py": (
            ROOT / source["data_source"]
        ).resolve(),
        "upstream/cftc_foundation.py": (
            ROOT / cftc["foundation_source"]
        ).resolve(),
        "external/dukascopy_feature_cache": source_root / source["feature_cache"],
        "external/dukascopy_feature_manifest": source_root
        / source["feature_manifest"],
        "external/cftc_curated": cftc_root / cftc["curated_file"],
        "external/cftc_manifest": cftc_root / cftc["manifest_file"],
    }


def _verify_external(
    config: Mapping[str, Any], paths: Mapping[str, Path]
) -> dict[str, Any]:
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing contract input {name}: {path}")
    source = config["source"]
    if _sha256(paths["external/dukascopy_feature_cache"]) != source["feature_sha256"]:
        raise ValueError("Dukascopy feature cache hash mismatch")
    cftc = config["cftc_source"]
    if _sha256(paths["external/cftc_curated"]) != cftc["curated_sha256"]:
        raise ValueError("CFTC curated data hash mismatch")
    manifest = json.loads(paths["external/cftc_manifest"].read_text(encoding="utf-8"))
    if int(manifest["rows"]) != int(cftc["expected_rows"]):
        raise ValueError("Unexpected CFTC row count")
    if manifest["files"][cftc["curated_file"]] != cftc["curated_sha256"]:
        raise ValueError("CFTC manifest curated hash mismatch")
    forbidden = (
        bool(manifest.get("api_key_used")),
        bool(manifest.get("paid_data_request_made")),
        bool(manifest.get("databento_used")),
        bool(manifest.get("strategy_scoring_performed")),
    )
    if any(forbidden):
        raise ValueError("CFTC foundation violates zero-cost/outcome-blind controls")
    return manifest


def main() -> int:
    if LOCK_PATH.exists() or MANIFEST_PATH.exists() or CENSUS_PATH.exists():
        raise RuntimeError("CFTC options volatility-routing V2 was already locked")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    paths = contract_paths(config)
    cftc_manifest = _verify_external(config, paths)
    volatility = _load_module(
        "cftc_options_volatility_routing_lock", ROOT / "src" / "volatility.py"
    )
    data = _load_module(
        "cftc_options_volatility_data_lock",
        (ROOT / config["source"]["data_source"]).resolve(),
    )
    bundle = data.load_bundle(config)
    cftc_root = paths["external/cftc_curated"].parent.parent
    positioning = pd.read_parquet(cftc_root / config["cftc_source"]["curated_file"])
    frame = volatility.prepare_features(bundle.bars["H1"], positioning, config)
    start, end = map(pd.Timestamp, config["windows"]["discovery"])
    controls = config["research_controls"]
    manifest = volatility.generate_manifest(
        frame,
        start,
        end,
        int(controls["campaign_attempts_before_v2"]),
        int(controls["policies_per_mechanic"]),
        int(controls["minimum_raw_discovery_signals"]),
    )
    if len(manifest) != int(controls["registered_policy_count"]):
        raise ValueError("Locked policy count mismatch")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary_manifest = MANIFEST_PATH.with_suffix(".csv.part")
    manifest.to_csv(temporary_manifest, index=False)
    os.replace(temporary_manifest, MANIFEST_PATH)
    grouped = manifest.groupby("mechanic", sort=True)["raw_discovery_signal_count"]
    census = {
        "schema_version": "xauusd_cftc_options_volatility_signal_census_v2",
        "created_utc": datetime.now(UTC).isoformat(),
        "discovery_start": start.isoformat(),
        "discovery_end": end.isoformat(),
        "policy_count": int(len(manifest)),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "mechanics": {
            mechanic: {
                "policies": int(len(values)),
                "minimum_raw_signals": int(values.min()),
                "median_raw_signals": float(values.median()),
                "maximum_raw_signals": int(values.max()),
            }
            for mechanic, values in grouped
        },
        "coverage_selection_used_trade_outcomes": False,
        "outcomes_opened": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    _write_json(CENSUS_PATH, census)
    body = {
        "schema_version": "xauusd_cftc_options_volatility_contract_lock_v2",
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {name: _sha256(path) for name, path in sorted(paths.items())},
        "policy_manifest_sha256": _sha256(MANIFEST_PATH),
        "signal_census_sha256": _sha256(CENSUS_PATH),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "registered_policy_count": int(len(manifest)),
        "cftc_source_rows": int(cftc_manifest["rows"]),
        "cftc_source_last_report": cftc_manifest["last_report_date"],
        "outcomes_opened": False,
        "training_authorized": False,
        "execution_authorized": False,
        "paid_data_authorized": False,
        "databento_use_authorized": False,
    }
    body["contract_sha256"] = _canonical_hash(body)
    _write_json(LOCK_PATH, body)
    print(json.dumps(_json_ready(body), indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

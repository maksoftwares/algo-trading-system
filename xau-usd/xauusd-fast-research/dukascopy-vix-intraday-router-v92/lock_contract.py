from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "dukascopy_vix_intraday_router_v92.json"
PREFIX = "DUKASCOPY_VIX_INTRADAY_ROUTER_V92"
LOCK_PATH = OUTPUT / f"{PREFIX}_CONTRACT_LOCK.json"
MANIFEST_PATH = OUTPUT / f"{PREFIX}_POLICY_MANIFEST.csv"
CENSUS_PATH = OUTPUT / f"{PREFIX}_SIGNAL_CENSUS.json"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


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


def expected_months(start_utc: str, end_exclusive_utc: str) -> list[str]:
    start = pd.Timestamp(start_utc)
    end = pd.Timestamp(end_exclusive_utc)
    if start.day != 1 or start != start.floor("D"):
        raise ValueError("VIX source start must be a UTC month boundary")
    if end.day != 1 or end != end.floor("D") or end <= start:
        raise ValueError("VIX source end must be a later UTC month boundary")
    return [
        str(month)
        for month in pd.period_range(
            start.tz_localize(None).to_period("M"),
            (end - pd.Timedelta(nanoseconds=1)).tz_localize(None).to_period("M"),
            freq="M",
        )
    ]


def _json_ready(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    return value


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(_json_ready(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def contract_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    source = config["source"]
    xau_storage = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    vix = config["vix_source"]
    vix_storage = Path(
        os.environ.get(vix["storage_environment_variable"], vix["default_storage_root"])
    ).resolve()
    source_package = REPO_ROOT / vix["source_package"]
    return {
        "config/dukascopy_vix_intraday_router_v92.json": CONFIG_PATH,
        "README.md": ROOT / "README.md",
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "SHARED_PORTFOLIO_PRECOMMITMENT.md": ROOT / "SHARED_PORTFOLIO_PRECOMMITMENT.md",
        "requirements.txt": ROOT / "requirements.txt",
        "src/campaign.py": ROOT / "src" / "campaign.py",
        "src/shared_audit.py": ROOT / "src" / "shared_audit.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_research.py": ROOT / "run_research.py",
        "run_shared_audit.py": ROOT / "run_shared_audit.py",
        "upstream/dukascopy_data_source.py": (ROOT / source["data_source"]).resolve(),
        "upstream/base_simulator.py": (
            ROOT / config["base_simulator"]["path"]
        ).resolve(),
        "external/xau_feature_cache": xau_storage / source["feature_cache"],
        "external/xau_feature_manifest": xau_storage / source["feature_manifest"],
        "external/vix_feature_cache": vix_storage / vix["feature_cache"],
        "external/vix_feature_manifest": vix_storage / vix["feature_manifest"],
        "vix_source/SOURCE_CONTRACT.md": source_package / "SOURCE_CONTRACT.md",
        "vix_source/config.json": source_package
        / "config"
        / "dukascopy_vol_index_v1.json",
        "vix_source/acquire.py": source_package / "acquire.py",
        "vix_source/build.py": source_package / "build.py",
        "vix_source/foundation.py": source_package / "src" / "foundation.py",
        **{
            f"shared/{name}": (ROOT / item["path"]).resolve()
            for name, item in config["shared_account"].items()
            if isinstance(item, Mapping) and "path" in item
        },
    }


def verify_sources(
    config: Mapping[str, Any], paths: Mapping[str, Path]
) -> dict[str, Any]:
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing V92 contract input {name}: {path}")
    source = config["source"]
    if sha256_file(paths["external/xau_feature_cache"]) != source["feature_sha256"]:
        raise ValueError("XAU feature cache hash mismatch")
    if (
        sha256_file(paths["upstream/dukascopy_data_source.py"])
        != source["data_source_sha256"]
    ):
        raise ValueError("XAU loader hash mismatch")
    if (
        sha256_file(paths["upstream/base_simulator.py"])
        != config["base_simulator"]["sha256"]
    ):
        raise ValueError("Base simulator hash mismatch")
    for name, item in config["shared_account"].items():
        if isinstance(item, Mapping) and "path" in item:
            if sha256_file(paths[f"shared/{name}"]) != item["sha256"]:
                raise ValueError(f"Shared-account source hash mismatch: {name}")

    vix = config["vix_source"]
    if sha256_file(paths["external/vix_feature_cache"]) != vix["feature_sha256"]:
        raise ValueError("VIX feature cache hash mismatch")
    if sha256_file(paths["external/vix_feature_manifest"]) != vix["manifest_sha256"]:
        raise ValueError("VIX feature manifest hash mismatch")
    manifest = json.loads(
        paths["external/vix_feature_manifest"].read_text(encoding="utf-8")
    )
    source_config = json.loads(
        paths["vix_source/config.json"].read_text(encoding="utf-8")
    )
    if manifest["curated_sha256"] != vix["feature_sha256"]:
        raise ValueError("VIX manifest does not bind the curated cache")
    if bool(manifest["paid_data_used"]):
        raise ValueError("Paid VIX source is forbidden")
    if int(manifest["duplicate_timestamps"]) != 0 or int(manifest["rows"]) <= 0:
        raise ValueError("Invalid VIX curated source cardinality")
    if int(manifest["valid_tick_count"]) + int(manifest["invalid_tick_count"]) != int(
        manifest["source_tick_count"]
    ):
        raise ValueError("VIX source quote accounting does not reconcile")
    maximum_invalid = float(manifest["maximum_invalid_quote_fraction"])
    if maximum_invalid > float(
        source_config["maximum_invalid_quote_fraction_per_hour"]
    ):
        raise ValueError("VIX source invalid-quote fraction exceeds its contract")
    actual_months = [str(item["month"]) for item in manifest["months"]]
    required_months = expected_months(
        str(source_config["start_utc"]), str(source_config["end_exclusive_utc"])
    )
    if actual_months != required_months:
        raise ValueError(
            "VIX source does not contain the exact consecutive month range"
        )
    return {
        "vix_rows": int(manifest["rows"]),
        "vix_months": int(len(manifest["months"])),
        "vix_first_bar_open_timestamp_ms": int(manifest["first_bar_open_timestamp_ms"]),
        "vix_last_bar_open_timestamp_ms": int(manifest["last_bar_open_timestamp_ms"]),
        "vix_source_tick_count": int(manifest["source_tick_count"]),
        "vix_valid_tick_count": int(manifest["valid_tick_count"]),
        "vix_invalid_tick_count": int(manifest["invalid_tick_count"]),
        "vix_maximum_invalid_quote_fraction": maximum_invalid,
        "paid_data_request_made": False,
        "databento_used": False,
        "xau_outcomes_used_for_coverage": False,
    }


def main() -> int:
    if LOCK_PATH.exists() or MANIFEST_PATH.exists() or CENSUS_PATH.exists():
        raise RuntimeError("V92 is already locked")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    paths = contract_paths(config)
    source_evidence = verify_sources(config, paths)
    campaign = _load_module(
        "dukascopy_vix_v92_lock_campaign", ROOT / "src" / "campaign.py"
    )
    data = _load_module(
        "dukascopy_vix_v92_lock_data",
        (ROOT / config["source"]["data_source"]).resolve(),
    )
    bundle = data.load_bundle(config)
    vix_m5 = pd.read_parquet(paths["external/vix_feature_cache"])
    frame = campaign.prepare_features(bundle.bars["H1"], vix_m5, config)
    start, end = map(pd.Timestamp, config["windows"]["discovery"])
    controls = config["research_controls"]
    manifest = campaign.generate_manifest(
        frame,
        start,
        end,
        int(controls["attempt_first"]),
        int(controls["policies_per_mechanic"]),
        int(controls["minimum_raw_discovery_signals"]),
    )
    if len(manifest) != int(controls["registered_policy_count"]):
        raise ValueError("V92 policy count mismatch")
    if int(manifest["attempt_no"].min()) != int(controls["attempt_first"]):
        raise ValueError("V92 first attempt mismatch")
    if int(manifest["attempt_no"].max()) != int(controls["attempt_last"]):
        raise ValueError("V92 last attempt mismatch")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST_PATH.with_suffix(".csv.part")
    manifest.to_csv(temporary, index=False)
    os.replace(temporary, MANIFEST_PATH)
    grouped = manifest.groupby("mechanic", sort=True)["raw_discovery_signal_count"]
    census = {
        "schema_version": "xauusd_dukascopy_vix_v92_signal_census",
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
        "post_entry_quotes_opened": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    write_json(CENSUS_PATH, census)
    body = {
        "schema_version": "xauusd_dukascopy_vix_v92_contract_lock",
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {name: sha256_file(path) for name, path in sorted(paths.items())},
        "policy_manifest_sha256": sha256_file(MANIFEST_PATH),
        "signal_census_sha256": sha256_file(CENSUS_PATH),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "registered_policy_count": int(len(manifest)),
        "source_evidence": source_evidence,
        "outcomes_opened": False,
        "training_authorized": False,
        "execution_authorized": False,
        "paid_data_authorized": False,
        "databento_use_authorized": False,
        "v59_v60_modification_authorized": False,
    }
    body["contract_sha256"] = canonical_hash(body)
    write_json(LOCK_PATH, body)
    print(json.dumps(_json_ready(body), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

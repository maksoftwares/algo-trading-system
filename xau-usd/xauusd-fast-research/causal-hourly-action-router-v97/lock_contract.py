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
CONFIG_PATH = ROOT / "config" / "causal_hourly_action_router_v97.json"
PREFIX = "CAUSAL_HOURLY_ACTION_ROUTER_V97"
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
        raise ValueError("Growth-risk source start must be a UTC month boundary")
    if end.day != 1 or end != end.floor("D") or end <= start:
        raise ValueError("Growth-risk source end must be a later UTC month boundary")
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
    growth_risk = config["growth_risk_source"]
    growth_risk_storage = Path(
        os.environ.get(
            growth_risk["storage_environment_variable"],
            growth_risk["default_storage_root"],
        )
    ).resolve()
    source_package = REPO_ROOT / growth_risk["source_package"]
    return {
        "config/causal_hourly_action_router_v97.json": CONFIG_PATH,
        "README.md": ROOT / "README.md",
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "SHARED_PORTFOLIO_PRECOMMITMENT.md": ROOT / "SHARED_PORTFOLIO_PRECOMMITMENT.md",
        "PROGRAM_CEILING.md": ROOT / "PROGRAM_CEILING.md",
        "requirements.txt": ROOT / "requirements.txt",
        "src/campaign.py": ROOT / "src" / "campaign.py",
        "src/ml_campaign.py": ROOT / "src" / "ml_campaign.py",
        "src/shared_audit.py": ROOT / "src" / "shared_audit.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_research.py": ROOT / "run_research.py",
        "run_shared_audit.py": ROOT / "run_shared_audit.py",
        "tests/test_campaign.py": ROOT / "tests" / "test_campaign.py",
        "tests/test_shared_audit.py": ROOT / "tests" / "test_shared_audit.py",
        "upstream/dukascopy_data_source.py": (ROOT / source["data_source"]).resolve(),
        "upstream/base_simulator.py": (
            ROOT / config["base_simulator"]["path"]
        ).resolve(),
        "external/xau_feature_cache": xau_storage / source["feature_cache"],
        "external/xau_feature_manifest": xau_storage / source["feature_manifest"],
        "external/growth_risk_feature_cache": growth_risk_storage
        / growth_risk["feature_cache"],
        "external/growth_risk_feature_manifest": growth_risk_storage
        / growth_risk["feature_manifest"],
        "growth_risk_source/SOURCE_CONTRACT.md": source_package / "SOURCE_CONTRACT.md",
        "growth_risk_source/README.md": source_package / "README.md",
        "growth_risk_source/config.json": source_package
        / "config"
        / "dukascopy_growth_risk_pulse_v1.json",
        "growth_risk_source/acquire.py": source_package / "acquire.py",
        "growth_risk_source/build.py": source_package / "build.py",
        "growth_risk_source/foundation.py": source_package / "src" / "foundation.py",
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
            raise FileNotFoundError(f"Missing V97 contract input {name}: {path}")
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

    growth_risk = config["growth_risk_source"]
    if "TO_BE_LOCKED" in str(growth_risk["feature_sha256"]) or "TO_BE_LOCKED" in str(
        growth_risk["manifest_sha256"]
    ):
        raise ValueError("Growth-risk source hashes are not populated")
    if (
        sha256_file(paths["external/growth_risk_feature_cache"])
        != growth_risk["feature_sha256"]
    ):
        raise ValueError("Growth-risk feature cache hash mismatch")
    if (
        sha256_file(paths["external/growth_risk_feature_manifest"])
        != growth_risk["manifest_sha256"]
    ):
        raise ValueError("Growth-risk feature manifest hash mismatch")
    manifest = json.loads(
        paths["external/growth_risk_feature_manifest"].read_text(encoding="utf-8")
    )
    source_config = json.loads(
        paths["growth_risk_source/config.json"].read_text(encoding="utf-8")
    )
    if manifest["curated_sha256"] != growth_risk["feature_sha256"]:
        raise ValueError("Growth-risk manifest does not bind the curated cache")
    if bool(manifest["paid_data_used"]) or bool(manifest["databento_used"]):
        raise ValueError("Paid or Databento growth-risk source is forbidden")
    if bool(manifest["xau_outcomes_opened"]):
        raise ValueError("Growth-risk source foundation opened XAU outcomes")
    if int(manifest["duplicate_timestamps"]) != 0 or int(manifest["rows"]) <= 0:
        raise ValueError("Invalid growth-risk curated source cardinality")
    required_months = expected_months(
        str(source_config["start_utc"]), str(source_config["end_exclusive_utc"])
    )
    if source_config["start_utc"] != growth_risk["start_utc"] or source_config[
        "end_exclusive_utc"
    ] != growth_risk["end_exclusive_utc"]:
        raise ValueError("Growth-risk source period differs from V97")
    expected_codes = {"USA500.IDX-USD", "COPPER.CMD-USD", "USD-CNH"}
    configured_codes = {str(item["source_code"]) for item in source_config["instruments"]}
    if configured_codes != expected_codes:
        raise ValueError("Growth-risk source instrument registry changed")
    instruments = manifest.get("instruments")
    if not isinstance(instruments, list) or len(instruments) != 3:
        raise ValueError("Growth-risk source does not contain three instruments")
    for instrument in instruments:
        if str(instrument["source_code"]) not in expected_codes:
            raise ValueError("Unexpected growth-risk source instrument")
        actual_months = [str(item["month"]) for item in instrument["months"]]
        if actual_months != required_months:
            raise ValueError("Growth-risk source month sequence is incomplete")
        if int(instrument["source_tick_count"]) <= 0 or int(instrument["rows"]) <= 0:
            raise ValueError("Growth-risk source instrument is empty")
    return {
        "growth_risk_rows": int(manifest["rows"]),
        "growth_risk_months_per_instrument": int(len(required_months)),
        "growth_risk_first_bar_open_timestamp_ms": int(
            manifest["first_bar_open_timestamp_ms"]
        ),
        "growth_risk_last_bar_open_timestamp_ms": int(
            manifest["last_bar_open_timestamp_ms"]
        ),
        "growth_risk_source_tick_count": int(
            sum(int(item["source_tick_count"]) for item in instruments)
        ),
        "growth_risk_stored_bytes": int(
            sum(int(item["stored_bytes"]) for item in instruments)
        ),
        "paid_data_request_made": False,
        "databento_used": False,
        "xau_outcomes_used_for_coverage": False,
    }


def main() -> int:
    if LOCK_PATH.exists() or MANIFEST_PATH.exists() or CENSUS_PATH.exists():
        raise RuntimeError("V97 is already locked")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    controls = config["research_controls"]
    if not (
        bool(controls["research_only"])
        and bool(controls["model_training_authorized"])
        and bool(controls["model_training_for_research_only"])
    ):
        raise ValueError("V97 research-model fitting controls changed")
    forbidden = (
        "same_version_post_outcome_tuning_authorized",
        "reuse_of_v97_outcomes_for_same_version_changes_authorized",
        "v59_v60_modification_authorized",
        "paid_data_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
    )
    if any(bool(controls[name]) for name in forbidden):
        raise ValueError("V97 contains forbidden authority")
    paths = contract_paths(config)
    source_evidence = verify_sources(config, paths)
    campaign = _load_module(
        "causal_hourly_action_router_v97_lock_campaign", ROOT / "src" / "campaign.py"
    )
    growth_risk_m5 = pd.read_parquet(paths["external/growth_risk_feature_cache"])
    source_h1 = campaign.prepare_source_h1(growth_risk_m5, config)
    start, end = map(pd.Timestamp, config["windows"]["discovery"])
    manifest = campaign.generate_manifest(
        source_h1,
        start,
        end,
        int(controls["attempt_first"]),
        int(controls["policies_per_mechanic"]),
        int(controls["minimum_raw_discovery_source_events"]),
    )
    if len(manifest) != int(controls["registered_policy_count"]):
        raise ValueError("V97 policy count mismatch")
    if int(manifest["attempt_no"].min()) != int(controls["attempt_first"]):
        raise ValueError("V97 first attempt mismatch")
    if int(manifest["attempt_no"].max()) != int(controls["attempt_last"]):
        raise ValueError("V97 last attempt mismatch")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST_PATH.with_suffix(".csv.part")
    manifest.to_csv(temporary, index=False)
    os.replace(temporary, MANIFEST_PATH)
    grouped = manifest.groupby("mechanic", sort=True)["raw_discovery_signal_count"]
    census = {
        "schema_version": "xauusd_causal_hourly_action_router_v97_signal_census",
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
        "schema_version": "xauusd_causal_hourly_action_router_v97_contract_lock",
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {name: sha256_file(path) for name, path in sorted(paths.items())},
        "policy_manifest_sha256": sha256_file(MANIFEST_PATH),
        "signal_census_sha256": sha256_file(CENSUS_PATH),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "registered_policy_count": int(len(manifest)),
        "source_evidence": source_evidence,
        "outcomes_opened": False,
        "research_model_fitting_authorized": True,
        "deployment_model_training_authorized": False,
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

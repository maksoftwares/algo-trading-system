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
OUTPUT = ROOT / "outputs"
CONFIG_PATH = ROOT / "config" / "executable_event_nearmiss_ranker_v99.json"
PREFIX = "EXECUTABLE_EVENT_NEARMISS_RANKER_V99"
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
    storage = Path(
        os.environ.get(
            source["storage_environment_variable"], source["default_storage_root"]
        )
    ).resolve()
    return {
        "config/executable_event_nearmiss_ranker_v99.json": CONFIG_PATH,
        "README.md": ROOT / "README.md",
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "SHARED_PORTFOLIO_PRECOMMITMENT.md": ROOT
        / "SHARED_PORTFOLIO_PRECOMMITMENT.md",
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
        "external/xau_feature_cache": storage / source["feature_cache"],
        "external/xau_feature_manifest": storage / source["feature_manifest"],
        **{
            f"successor/{name}": (ROOT / item["path"]).resolve()
            for name, item in config["successor_correction"].items()
            if isinstance(item, Mapping) and "path" in item
        },
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
            raise FileNotFoundError(f"Missing V99 contract input {name}: {path}")
    source = config["source"]
    if sha256_file(paths["external/xau_feature_cache"]) != source["feature_sha256"]:
        raise ValueError("V99 XAU feature cache hash mismatch")
    if (
        sha256_file(paths["upstream/dukascopy_data_source.py"])
        != source["data_source_sha256"]
    ):
        raise ValueError("V99 XAU loader hash mismatch")
    if (
        sha256_file(paths["upstream/base_simulator.py"])
        != config["base_simulator"]["sha256"]
    ):
        raise ValueError("V99 base simulator hash mismatch")
    for name, item in config["shared_account"].items():
        if isinstance(item, Mapping) and "path" in item:
            if sha256_file(paths[f"shared/{name}"]) != item["sha256"]:
                raise ValueError(f"V99 shared-account source hash mismatch: {name}")
    correction = config["successor_correction"]
    for name in ("v98_result", "v98_artifact_manifest"):
        if sha256_file(paths[f"successor/{name}"]) != correction[name]["sha256"]:
            raise ValueError(f"V99 predecessor evidence changed: {name}")
    v98_result = json.loads(paths["successor/v98_result"].read_text(encoding="utf-8"))
    if v98_result.get("decision") != "V98_ENGINEERING_INVALIDATED_TERMINAL":
        raise ValueError("V99 requires terminally invalidated V98 evidence")
    if bool(v98_result.get("economic_metrics_produced", True)):
        raise ValueError("V99 cannot be an engineering correction after V98 economics")
    manifest = json.loads(
        paths["external/xau_feature_manifest"].read_text(encoding="utf-8")
    )
    if int(manifest["rows"]) != int(source["expected_rows"]):
        raise ValueError("V99 XAU feature row count changed")
    if manifest["feature_sha256"] != source["feature_sha256"]:
        raise ValueError("V99 XAU manifest does not bind the feature cache")
    return {
        "xau_feature_rows": int(manifest["rows"]),
        "xau_feature_sha256": source["feature_sha256"],
        "source_digest": source["source_digest"],
        "paid_data_request_made": False,
        "databento_used": False,
        "xau_post_entry_outcomes_used_for_coverage": False,
    }


def _validate_governance(config: Mapping[str, Any]) -> None:
    controls = config["research_controls"]
    if not (
        bool(controls["research_only"])
        and bool(controls["model_training_authorized"])
        and bool(controls["model_training_for_research_only"])
    ):
        raise ValueError("V99 research-model fitting controls changed")
    forbidden = (
        "same_version_post_outcome_tuning_authorized",
        "reuse_of_v99_outcomes_for_same_version_changes_authorized",
        "v59_v60_modification_authorized",
        "paid_data_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "ea_consumption_authorized",
    )
    if any(bool(controls[name]) for name in forbidden):
        raise ValueError("V99 contains forbidden authority")
    if int(controls["attempt_first"]) != 130001:
        raise ValueError("V99 first attempt changed")
    if int(controls["attempt_last"]) != 131000:
        raise ValueError("V99 last attempt changed")
    if int(controls["registered_policy_count"]) != 1000:
        raise ValueError("V99 policy count changed")
    if float(config["shared_account"]["minimum_combined_trades_per_weekday"]) != 2.0:
        raise ValueError("V99 two-trade target changed")


def main() -> int:
    if LOCK_PATH.exists() or MANIFEST_PATH.exists() or CENSUS_PATH.exists():
        raise RuntimeError("V99 is already locked")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    _validate_governance(config)
    paths = contract_paths(config)
    source_evidence = verify_sources(config, paths)
    campaign = _load_module(
        "executable_event_nearmiss_ranker_v99_lock_campaign",
        ROOT / "src" / "campaign.py",
    )
    data = _load_module(
        "executable_event_nearmiss_ranker_v99_lock_data",
        paths["upstream/dukascopy_data_source.py"],
    )
    bundle = data.load_bundle(config)
    events = campaign.prepare_features(
        bundle.bars["H1"], bundle.bars["M5"], None, config
    )
    start, end = map(pd.Timestamp, config["windows"]["discovery"])
    controls = config["research_controls"]
    manifest = campaign.generate_manifest(
        events,
        start,
        end,
        int(controls["attempt_first"]),
        int(controls["policies_per_mechanic"]),
        int(controls["minimum_raw_discovery_source_events"]),
    )
    if len(manifest) != int(controls["registered_policy_count"]):
        raise ValueError("V99 policy count mismatch")
    attempts = manifest["attempt_no"].astype(int).sort_values().tolist()
    if attempts != list(range(130001, 131001)):
        raise ValueError("V99 attempt registry is not contiguous")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST_PATH.with_suffix(".csv.part")
    manifest.to_csv(temporary, index=False)
    os.replace(temporary, MANIFEST_PATH)
    discovery = events.loc[
        events["bar_end_utc"].ge(start) & events["bar_end_utc"].lt(end)
    ].copy()
    grouped = manifest.groupby("mechanic", sort=True)["raw_discovery_signal_count"]
    census = {
        "schema_version": "xauusd_executable_event_nearmiss_ranker_v99_signal_census",
        "created_utc": datetime.now(UTC).isoformat(),
        "discovery_start": start.isoformat(),
        "discovery_end": end.isoformat(),
        "policy_count": int(len(manifest)),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "unique_candidate_times": int(discovery["bar_end_utc"].nunique()),
        "candidate_rows": int(len(discovery)),
        "long_candidate_times": int(
            discovery.loc[discovery["direction_value"].eq(1), "bar_end_utc"].nunique()
        ),
        "short_candidate_times": int(
            discovery.loc[discovery["direction_value"].eq(-1), "bar_end_utc"].nunique()
        ),
        "candidate_type_rows": discovery["event_type"].value_counts().sort_index().to_dict(),
        "event_pools": [list(pool) for pool in campaign.EVENT_POOLS],
        "locked_execution_profile": config["successor_correction"]["locked_execution_profile"],
        "minimum_observed_v98_calibration_support_per_weekday": config["successor_correction"]["minimum_observed_v98_calibration_support_per_weekday"],
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
        "schema_version": "xauusd_executable_event_nearmiss_ranker_v99_contract_lock",
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

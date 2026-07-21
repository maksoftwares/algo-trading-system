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
CONFIG_PATH = ROOT / "config" / "causal_health_gated_event_sleeves_v100.json"
PREFIX = "CAUSAL_HEALTH_GATED_EVENT_SLEEVES_V100"
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


def _resolve(item: Mapping[str, Any]) -> Path:
    path = Path(str(item["path"]))
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def contract_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    return {
        "config/causal_health_gated_event_sleeves_v100.json": CONFIG_PATH,
        "README.md": ROOT / "README.md",
        "PREREGISTRATION.md": ROOT / "PREREGISTRATION.md",
        "SHARED_PORTFOLIO_PRECOMMITMENT.md": ROOT / "SHARED_PORTFOLIO_PRECOMMITMENT.md",
        "PROGRAM_CEILING.md": ROOT / "PROGRAM_CEILING.md",
        "requirements.txt": ROOT / "requirements.txt",
        "src/campaign.py": ROOT / "src" / "campaign.py",
        "src/shared_audit.py": ROOT / "src" / "shared_audit.py",
        "lock_contract.py": ROOT / "lock_contract.py",
        "run_research.py": ROOT / "run_research.py",
        "run_shared_audit.py": ROOT / "run_shared_audit.py",
        "tests/test_campaign.py": ROOT / "tests" / "test_campaign.py",
        "tests/test_shared_audit.py": ROOT / "tests" / "test_shared_audit.py",
        **{
            f"source/{name}": _resolve(item)
            for name, item in config["source"].items()
        },
        **{
            f"predecessor/{name}": _resolve(item)
            for name, item in config["predecessor"].items()
            if isinstance(item, Mapping) and "path" in item
        },
        **{
            f"shared/{name}": _resolve(item)
            for name, item in config["shared_account"].items()
            if isinstance(item, Mapping) and "path" in item
        },
    }


def verify_sources(
    config: Mapping[str, Any], paths: Mapping[str, Path]
) -> dict[str, Any]:
    for name, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"Missing V100 contract input {name}: {path}")
    for group in ("source", "predecessor", "shared_account"):
        prefix = "shared" if group == "shared_account" else group
        for name, item in config[group].items():
            if isinstance(item, Mapping) and "path" in item:
                if sha256_file(paths[f"{prefix}/{name}"]) != str(item["sha256"]):
                    raise ValueError(f"V100 source hash mismatch: {group}/{name}")
    predecessor = json.loads(
        paths["predecessor/v99_result"].read_text(encoding="utf-8")
    )
    if predecessor.get("decision") != config["predecessor"]["required_decision"]:
        raise ValueError("V100 requires terminal V99 Discovery failure")
    if int(predecessor.get("registered_policy_count", 0)) != 1000:
        raise ValueError("V99 predecessor registry is incomplete")
    artifact = json.loads(
        paths["predecessor/v99_artifact_manifest"].read_text(encoding="utf-8")
    )
    recorded = artifact.get("artifacts", {}).get(paths["predecessor/v99_result"].name)
    if recorded is None or recorded.get("sha256") != sha256_file(
        paths["predecessor/v99_result"]
    ):
        raise ValueError("V99 terminal result is not artifact-bound")
    source = config["source"]
    markout_rows = len(
        pd.read_parquet(paths["source/episode_markouts"], columns=["event_id"])
    )
    market_rows = len(pd.read_parquet(paths["source/market"], columns=["timestamp_ms"]))
    if markout_rows != int(source["episode_markouts"]["expected_rows"]):
        raise ValueError("V100 markout row count changed")
    if market_rows != int(source["market"]["expected_rows"]):
        raise ValueError("V100 market row count changed")
    return {
        "episode_markout_rows": markout_rows,
        "market_rows": market_rows,
        "historical_outcomes_previously_exposed": True,
        "v100_post_entry_values_opened_for_lock": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }


def _validate_governance(config: Mapping[str, Any]) -> None:
    controls = config["research_controls"]
    forbidden = (
        "same_version_post_outcome_tuning_authorized",
        "reuse_of_v100_outcomes_for_same_version_changes_authorized",
        "v59_v60_modification_authorized",
        "paid_data_authorized",
        "databento_use_authorized",
        "broker_action_authorized",
        "python_predictions_authorized",
        "model_training_authorized",
        "ea_consumption_authorized",
    )
    if not bool(controls["research_only"]) or any(bool(controls[name]) for name in forbidden):
        raise ValueError("V100 contains forbidden authority")
    if int(controls["attempt_first"]) != 131001:
        raise ValueError("V100 first attempt changed")
    if int(controls["attempt_last"]) != 132000:
        raise ValueError("V100 last attempt changed")
    if int(controls["registered_policy_count"]) != 1000:
        raise ValueError("V100 policy count changed")
    if int(controls["program_version_ceiling"]) != 100:
        raise ValueError("V100 program ceiling changed")
    if float(config["shared_account"]["minimum_combined_trades_per_weekday"]) != 2.0:
        raise ValueError("V100 two-trade target changed")


def main() -> int:
    if LOCK_PATH.exists() or MANIFEST_PATH.exists() or CENSUS_PATH.exists():
        raise RuntimeError("V100 is already locked")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    _validate_governance(config)
    paths = contract_paths(config)
    source_evidence = verify_sources(config, paths)
    campaign = _load_module(
        "causal_health_gated_event_sleeves_v100_lock_campaign",
        ROOT / "src" / "campaign.py",
    )
    metadata = campaign.load_source(config, outcomes=False)
    start, end = map(pd.Timestamp, config["windows"]["discovery"])
    manifest = campaign.generate_manifest(metadata, config, start, end)
    controls = config["research_controls"]
    if len(manifest) != int(controls["registered_policy_count"]):
        raise ValueError("V100 policy count mismatch")
    attempts = manifest["attempt_no"].astype(int).tolist()
    if attempts != list(range(131001, 132001)):
        raise ValueError("V100 attempt registry is not contiguous")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    temporary = MANIFEST_PATH.with_suffix(".csv.part")
    manifest.to_csv(temporary, index=False)
    os.replace(temporary, MANIFEST_PATH)
    discovery = metadata.loc[
        metadata["entry_time"].ge(start) & metadata["entry_time"].lt(end)
    ]
    grouped = manifest.groupby("mechanic", sort=True)["raw_discovery_signal_count"]
    census = {
        "schema_version": "xauusd_causal_health_gated_event_sleeves_v100_signal_census",
        "created_utc": datetime.now(UTC).isoformat(),
        "discovery_start": start.isoformat(),
        "discovery_end": end.isoformat(),
        "policy_count": int(len(manifest)),
        "attempt_first": int(manifest["attempt_no"].min()),
        "attempt_last": int(manifest["attempt_no"].max()),
        "candidate_rows": int(len(discovery)),
        "unique_episode_ids": int(discovery["episode_id"].nunique()),
        "family_horizon_rows": {
            f"{family}|{int(horizon)}": int(value)
            for (family, horizon), value in discovery.groupby(
                ["family_id", "horizon_minutes"], sort=True
            ).size().items()
        },
        "pools": [dict(item) for item in campaign.POOLS],
        "mechanics": {
            mechanic: {
                "policies": int(len(values)),
                "raw_discovery_signals": int(values.iloc[0]),
            }
            for mechanic, values in grouped
        },
        "coverage_selection_used_trade_outcomes": False,
        "post_entry_values_opened_for_lock": False,
        "strategy_scoring_performed": False,
        "paid_data_request_made": False,
        "databento_used": False,
    }
    write_json(CENSUS_PATH, census)
    body = {
        "schema_version": "xauusd_causal_health_gated_event_sleeves_v100_contract_lock",
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {name: sha256_file(path) for name, path in sorted(paths.items())},
        "policy_manifest_sha256": sha256_file(MANIFEST_PATH),
        "signal_census_sha256": sha256_file(CENSUS_PATH),
        "attempt_first": 131001,
        "attempt_last": 132000,
        "registered_policy_count": int(len(manifest)),
        "source_evidence": source_evidence,
        "outcomes_opened": False,
        "model_training_authorized": False,
        "execution_authorized": False,
        "paid_data_authorized": False,
        "databento_use_authorized": False,
        "v59_v60_modification_authorized": False,
        "program_version_ceiling": 100,
    }
    body["contract_sha256"] = canonical_hash(body)
    write_json(LOCK_PATH, body)
    print(json.dumps(_json_ready(body), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

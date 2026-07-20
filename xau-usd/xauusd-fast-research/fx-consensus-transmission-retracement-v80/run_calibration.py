from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
V78_SRC = ROOT.parent / "fx-consensus-xau-eventtime-v78" / "src"
for source in (ROOT / "src", V72_SRC, V78_SRC):
    sys.path.insert(0, str(source))

from catchup import ManifestTickStore, canonical_hash, load_json, sha256_file  # noqa: E402
from fx_consensus import build_consensus_features, session_quality  # noqa: E402
from retracement import (  # noqa: E402
    build_pattern_rows,
    generate_candidates,
    select_policy,
    select_source_events,
    summarize_candidate_facts,
    timing_policy_grid,
)


CONFIG = ROOT / "config" / "fx_consensus_transmission_retracement_v80.json"


def verified_inheritance(config: Mapping[str, Any]) -> dict[str, Any]:
    v78 = config["inherited_v78"]
    v79 = config["inherited_v79"]
    paths = {
        "v78_contract": REPO_ROOT / str(v78["contract_path"]),
        "v78_source": REPO_ROOT / str(v78["source_audit_path"]),
        "v78_module": REPO_ROOT / str(v78["consensus_module_path"]),
        "v79_contract": REPO_ROOT / str(v79["contract_path"]),
        "v79_development": REPO_ROOT / str(v79["development_audit_path"]),
    }
    expected_hashes = {
        "v78_contract": v78["contract_file_sha256"],
        "v78_source": v78["source_audit_sha256"],
        "v78_module": v78["consensus_module_sha256"],
        "v79_contract": v79["contract_file_sha256"],
        "v79_development": v79["development_audit_sha256"],
    }
    for key, path in paths.items():
        if sha256_file(path) != expected_hashes[key]:
            raise ValueError(f"V80 inherited artifact changed: {path}")
    v78_contract = load_json(paths["v78_contract"])
    v78_source = load_json(paths["v78_source"])
    v79_contract = load_json(paths["v79_contract"])
    v79_development = load_json(paths["v79_development"])
    if canonical_hash(v78_contract, "contract_sha256") != v78_contract.get(
        "contract_sha256"
    ):
        raise ValueError("V80 inherited V78 contract self-hash changed")
    if canonical_hash(v79_contract, "contract_sha256") != v79_contract.get(
        "contract_sha256"
    ):
        raise ValueError("V80 inherited V79 contract self-hash changed")
    if (
        v78_source.get("decision") != "V78_SOURCE_AUDIT_PASS"
        or canonical_hash(v78_source, "audit_sha256")
        != v78_source.get("audit_sha256")
    ):
        raise ValueError("V80 inherited V78 source audit is invalid")
    if (
        v79_development.get("decision") != "V79_DEVELOPMENT_FAIL_TERMINAL"
        or canonical_hash(v79_development, "audit_sha256")
        != v79_development.get("audit_sha256")
    ):
        raise ValueError("V80 inherited V79 development audit is invalid")
    cutoff = pd.to_datetime(v79["exposed_end_exclusive"], utc=True)
    dates = [
        pd.to_datetime(row["date_utc"], utc=True)
        for row in v79_development["session_quality"]
    ]
    if dates and max(dates) >= cutoff:
        raise ValueError("V79 exposed outcomes overlap V80 calibration")
    calibration_start = pd.to_datetime(config["timing_calibration"]["start"], utc=True)
    if calibration_start != cutoff:
        raise ValueError("V80 calibration does not begin at the fresh boundary")
    config_record = next(
        (
            row
            for row in v78_contract["package_files"]
            if row["path"] == "config/fx_consensus_xau_eventtime_v78.json"
        ),
        None,
    )
    if config_record is None:
        raise ValueError("V80 inherited V78 contract has no config record")
    v78_root = paths["v78_contract"].parent.parent
    v78_config_path = v78_root / str(config_record["path"])
    if sha256_file(v78_config_path) != config_record["sha256"]:
        raise ValueError("V80 inherited V78 package config changed")
    v78_config = load_json(v78_config_path)
    source_keys = (
        "storage_environment_variable",
        "default_storage_root",
        "symbols",
        "payment_authorized",
    )
    inherited_source = {key: v78_config["source"][key] for key in source_keys}
    current_source = {key: config["source"][key] for key in source_keys}
    if current_source != inherited_source:
        raise ValueError("V80 source semantics differ from V78")
    if config["spot_source"] != v78_config["spot_source"]:
        raise ValueError("V80 spot-label source differs from V78")
    inherited_rule = dict(v78_config["candidate_rule"])
    inherited_rule["family"] = config["candidate_rule"]["family"]
    if config["candidate_rule"] != inherited_rule:
        raise ValueError("V80 changed a V78 source-event rule")
    return v78_contract


def load_day(
    date: pd.Timestamp,
    *,
    eurusd_store: ManifestTickStore,
    usdjpy_store: ManifestTickStore,
    xau_store: ManifestTickStore,
    rule: Mapping[str, Any],
    source_horizon_ms: int,
    maximum_pattern_seconds: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    start_hour = int(str(rule["session_start_utc"]).split(":")[0])
    end_hour = int(str(rule["session_end_utc"]).split(":")[0])
    start_ms = int(
        (date.normalize() + pd.Timedelta(hours=start_hour)).timestamp() * 1000
    )
    start_ms -= source_horizon_ms + int(rule["maximum_baseline_staleness_ms"])
    end_ms = int(
        (
            date.normalize()
            + pd.Timedelta(hours=end_hour, seconds=maximum_pattern_seconds)
        ).timestamp()
        * 1000
    )
    return (
        eurusd_store.quote_frame(start_ms, end_ms),
        usdjpy_store.quote_frame(start_ms, end_ms),
        xau_store.quote_frame(start_ms, end_ms),
    )


def run_calibration() -> dict[str, Any]:
    config = load_json(CONFIG)
    inherited_contract = verified_inheritance(config)
    output = ROOT / str(config["outputs"]["directory"])
    pattern_path = output / str(config["outputs"]["calibration_patterns"])
    grid_path = output / str(config["outputs"]["calibration_grid"])
    audit_path = output / str(config["outputs"]["calibration_audit"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if any(path.exists() for path in (pattern_path, grid_path, audit_path)):
        raise FileExistsError("V80 calibration outputs already exist")
    if lock_path.exists():
        raise RuntimeError("V80 calibration cannot run after lock")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    eurusd_store = ManifestTickStore(storage, "EURUSD", source["symbols"]["EURUSD"])
    usdjpy_store = ManifestTickStore(storage, "USDJPY", source["symbols"]["USDJPY"])
    xau_store = ManifestTickStore(storage, "XAUUSD", source["symbols"]["XAUUSD"])
    calibration = config["timing_calibration"]
    start, end = pd.Timestamp(calibration["start"]), pd.Timestamp(calibration["end"])
    source_policy = inherited_contract["selected_policy"]
    source_horizon = int(source_policy["horizon_ms"])
    maximum_pattern_seconds = max(
        int(value) for value in calibration["maximum_pattern_seconds_grid"]
    )
    rule = config["candidate_rule"]
    pattern_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    source_event_count = 0
    for date in pd.date_range(start.normalize(), end.normalize(), inclusive="left", freq="D"):
        if date.weekday() >= 5:
            continue
        eurusd, usdjpy, xau = load_day(
            date,
            eurusd_store=eurusd_store,
            usdjpy_store=usdjpy_store,
            xau_store=xau_store,
            rule=rule,
            source_horizon_ms=source_horizon,
            maximum_pattern_seconds=maximum_pattern_seconds,
        )
        quality = session_quality(date, eurusd, usdjpy, xau, rule)
        quality_rows.append(quality)
        if bool(quality["eligible_full_weekday"]):
            source_features = build_consensus_features(
                date,
                eurusd,
                usdjpy,
                xau,
                horizons_ms=[source_horizon],
                rule=rule,
                prefilter=source_policy,
            )
            source_events = select_source_events(source_features, policy=source_policy)
            source_event_count += len(source_events)
            patterns = build_pattern_rows(
                source_events,
                xau,
                transmission_bps_grid=calibration["transmission_bps_grid"],
                retracement_fraction_grid=calibration["retracement_fraction_grid"],
                maximum_pattern_seconds=maximum_pattern_seconds,
            )
            if not patterns.empty:
                pattern_frames.append(patterns)
        print(f"V80 calibrated {date.date()}", flush=True)
    patterns = (
        pd.concat(pattern_frames, ignore_index=True)
        if pattern_frames
        else pd.DataFrame()
    )
    eligible_dates = [
        row["date_utc"] for row in quality_rows if bool(row["eligible_full_weekday"])
    ]
    policies = timing_policy_grid(calibration)
    if len(policies) != 100:
        raise ValueError(f"V80 registered {len(policies)} policies, expected 100")
    rows: list[dict[str, Any]] = []
    for policy in policies:
        candidates = generate_candidates(
            patterns, policy=policy, family=str(rule["family"])
        )
        rows.append(
            summarize_candidate_facts(
                candidates,
                eligible_dates=eligible_dates,
                policy=policy,
                calibration=calibration,
            )
        )
    grid = pd.DataFrame(rows).sort_values("policy_id", kind="stable")
    selected = select_policy(rows, calibration)
    output.mkdir(parents=True, exist_ok=True)
    patterns.to_parquet(pattern_path, index=False)
    grid.to_csv(grid_path, index=False, lineterminator="\n")
    decision = (
        "V80_CALIBRATION_POLICY_SELECTED" if selected else "V80_NO_CALIBRATION_POLICY"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_fx_consensus_v80_calibration_audit",
        "campaign_id": config["campaign_id"],
        "decision": decision,
        "calibration_start": str(start),
        "calibration_end_exclusive": str(end),
        "v78_contract_sha256": inherited_contract["contract_sha256"],
        "source_policy": source_policy,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "source_event_rows": int(source_event_count),
        "pattern_rows": int(len(patterns)),
        "pattern_sha256": sha256_file(pattern_path),
        "registered_policy_count": len(policies),
        "eligible_policy_count": int(grid["selection_eligible"].sum()),
        "grid_sha256": sha256_file(grid_path),
        "selected_policy": selected,
        "post_decision_xau_outcomes_opened": False,
        **config["research_controls"],
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    audit_path.write_bytes((json.dumps(audit, indent=2, sort_keys=True) + "\n").encode())
    print(
        json.dumps(
            {
                "decision": decision,
                "source_events": source_event_count,
                "pattern_rows": len(patterns),
                "eligible_policies": int(grid["selection_eligible"].sum()),
                "selected_policy": selected,
            },
            indent=2,
        )
    )
    return audit


if __name__ == "__main__":
    run_calibration()

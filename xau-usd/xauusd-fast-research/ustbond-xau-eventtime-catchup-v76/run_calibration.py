from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
for source in (ROOT / "src", V72_SRC):
    sys.path.insert(0, str(source))

from catchup import ManifestTickStore, canonical_hash, load_json, sha256_file  # noqa: E402
from same_direction_lead import (  # noqa: E402
    build_same_direction_features,
    calibration_prefilter,
    generate_candidates,
    policy_grid,
    select_policy,
    session_quality,
    summarize_candidate_facts,
)


CONFIG = ROOT / "config" / "ustbond_xau_eventtime_catchup_v76.json"


def load_day(
    date: pd.Timestamp,
    *,
    source_store: ManifestTickStore,
    xau_store: ManifestTickStore,
    rule: Mapping[str, Any],
    maximum_horizon_ms: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    start_hour = int(str(rule["session_start_utc"]).split(":")[0])
    end_hour = int(str(rule["session_end_utc"]).split(":")[0])
    start_ms = int((date.normalize() + pd.Timedelta(hours=start_hour)).timestamp() * 1000)
    start_ms -= maximum_horizon_ms + int(rule["maximum_baseline_staleness_ms"])
    end_ms = int((date.normalize() + pd.Timedelta(hours=end_hour)).timestamp() * 1000) - 1
    return source_store.quote_frame(start_ms, end_ms), xau_store.quote_frame(
        start_ms, end_ms
    )


def run_calibration() -> dict[str, Any]:
    config = load_json(CONFIG)
    output = ROOT / str(config["outputs"]["directory"])
    feature_path = output / str(config["outputs"]["calibration_features"])
    grid_path = output / str(config["outputs"]["calibration_grid"])
    audit_path = output / str(config["outputs"]["calibration_audit"])
    if any(path.exists() for path in (feature_path, grid_path, audit_path)):
        raise FileExistsError("V76 calibration outputs already exist")
    if (output / str(config["outputs"]["contract_lock"])).exists():
        raise RuntimeError("V76 calibration cannot run after lock")
    source_path = output / str(config["outputs"]["source_audit"])
    source_audit = load_json(source_path)
    if (
        source_audit.get("decision") != "V76_SOURCE_AUDIT_PASS"
        or canonical_hash(source_audit, "audit_sha256") != source_audit.get("audit_sha256")
    ):
        raise ValueError("V76 source audit is invalid")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    source_store = ManifestTickStore(
        storage, "USTBONDTRUSD", source["symbols"]["USTBONDTRUSD"]
    )
    xau_store = ManifestTickStore(storage, "XAUUSD", source["symbols"]["XAUUSD"])
    calibration = config["calibration"]
    start, end = pd.Timestamp(calibration["start"]), pd.Timestamp(calibration["end"])
    horizons = [int(value) for value in calibration["horizon_ms_grid"]]
    rule = config["candidate_rule"]
    features_list: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    for date in pd.date_range(start.normalize(), end.normalize(), inclusive="left", freq="D"):
        if date.weekday() >= 5:
            continue
        bond, xau = load_day(
            date,
            source_store=source_store,
            xau_store=xau_store,
            rule=rule,
            maximum_horizon_ms=max(horizons),
        )
        quality = session_quality(date, bond, xau, rule)
        quality_rows.append(quality)
        if bool(quality["eligible_full_weekday"]):
            features_list.append(
                build_same_direction_features(
                    date,
                    bond,
                    xau,
                    horizons_ms=horizons,
                    rule=rule,
                    prefilter=calibration_prefilter(calibration),
                )
            )
        print(f"V76 calibrated {date.date()}", flush=True)
    features = pd.concat(features_list, ignore_index=True) if features_list else pd.DataFrame()
    eligible_dates = [
        row["date_utc"] for row in quality_rows if bool(row["eligible_full_weekday"])
    ]
    policies = policy_grid(calibration)
    if len(policies) != 1000:
        raise ValueError(f"V76 registered {len(policies)} policies, expected 1000")
    rows: list[dict[str, Any]] = []
    for policy in policies:
        candidates = generate_candidates(features, policy=policy, family=str(rule["family"]))
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
    features.to_parquet(feature_path, index=False)
    grid.to_csv(grid_path, index=False, lineterminator="\n")
    decision = "V76_CALIBRATION_POLICY_SELECTED" if selected else "V76_NO_CALIBRATION_POLICY"
    audit: dict[str, Any] = {
        "schema_version": "xauusd_ustbond_xau_v76_calibration_audit",
        "campaign_id": config["campaign_id"],
        "decision": decision,
        "calibration_start": str(start),
        "calibration_end_exclusive": str(end),
        "source_audit_sha256": sha256_file(source_path),
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "feature_rows": int(len(features)),
        "feature_sha256": sha256_file(feature_path),
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
                "feature_rows": len(features),
                "eligible_policies": int(grid["selection_eligible"].sum()),
                "selected_policy": selected,
            },
            indent=2,
        )
    )
    return audit


if __name__ == "__main__":
    run_calibration()

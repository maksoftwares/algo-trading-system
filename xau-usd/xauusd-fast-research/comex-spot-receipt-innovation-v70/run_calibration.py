from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
FOUNDATION_SRC = ROOT.parent / "comex-futures-foundation-v1" / "src"
for source in (ROOT / "src", BASE_SRC, FOUNDATION_SRC):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from innovation import (  # noqa: E402
    build_innovation_features,
    bucket_received_trades,
    canonical_hash,
    generate_candidates,
    load_json,
    policy_grid,
    publisher_clock_lead_rows,
    received_session,
    select_policy,
    sha256_file,
    spot_quote_frame,
    summarize_candidate_facts,
    timestamp_milliseconds,
)
import size_segment_flow as base  # noqa: E402
from spot_labels import (  # noqa: E402
    VerifiedSpotTickStore,
    load_dukascopy_foundation,
    resolve_spot_storage,
)


CONFIG = ROOT / "config" / "comex_spot_receipt_innovation_v70.json"


def output_paths(config: Mapping[str, Any]) -> tuple[Path, Path, Path]:
    output = ROOT / str(config["outputs"]["directory"])
    return (
        output / str(config["outputs"]["calibration_features"]),
        output / str(config["outputs"]["calibration_grid"]),
        output / str(config["outputs"]["calibration_audit"]),
    )


def run_calibration() -> dict[str, Any]:
    config = load_json(CONFIG)
    feature_path, grid_path, audit_path = output_paths(config)
    output = feature_path.parent
    if any(path.exists() for path in (feature_path, grid_path, audit_path)):
        raise FileExistsError("V70 calibration outputs already exist")
    if (output / str(config["outputs"]["contract_lock"])).exists():
        raise RuntimeError("V70 calibration cannot run after contract lock")
    calibration = config["calibration"]
    start = pd.Timestamp(calibration["start"])
    end = pd.Timestamp(calibration["end"])
    files = base.discover_source_files(
        Path(str(config["source"]["job_directory"])), start=start, end=end
    )
    storage = resolve_spot_storage(config)
    tick_store = VerifiedSpotTickStore(
        storage_root=storage,
        symbol=str(config["spot_source"]["symbol"]),
        foundation=load_dukascopy_foundation(),
    )
    rule = config["candidate_rule"]
    horizons = [int(value) for value in calibration["horizon_ms_grid"]]
    maximum_horizon = max(horizons)
    feature_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    publisher_clock_lead_count = 0
    for number, path in enumerate(files, start=1):
        raw = base.load_dbn_trades(path)
        publisher_clock_lead_count += publisher_clock_lead_rows(raw)
        quality = base.session_quality(base.session_trades(raw, rule), rule)
        quality["source_file"] = path.name
        quality_rows.append(quality)
        source_files.append(
            {
                "path": str(path),
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
        if not bool(quality["eligible_full_weekday"]):
            continue
        session = received_session(raw, rule)
        buckets = bucket_received_trades(
            session, bucket_ms=int(rule["receipt_bucket_ms"])
        )
        if buckets.empty:
            continue
        decision_ms = timestamp_milliseconds(buckets["feature_time_utc"])
        quotes = spot_quote_frame(
            tick_store,
            start_timestamp_ms=int(decision_ms.min())
            - maximum_horizon
            - int(rule["maximum_spot_quote_staleness_ms"]),
            end_timestamp_ms=int(decision_ms.max()),
        )
        for horizon in horizons:
            feature_frames.append(
                build_innovation_features(
                    buckets,
                    quotes,
                    horizon_ms=horizon,
                    maximum_spot_quote_staleness_ms=int(
                        rule["maximum_spot_quote_staleness_ms"]
                    ),
                    maximum_comex_baseline_staleness_ms=int(
                        rule["maximum_comex_baseline_staleness_ms"]
                    ),
                )
            )
        print(f"calibrated {number}/{len(files)} source days", flush=True)
    features = (
        pd.concat(feature_frames, ignore_index=True)
        if feature_frames
        else pd.DataFrame()
    )
    eligible_dates = [
        str(row["date_utc"])
        for row in quality_rows
        if bool(row["eligible_full_weekday"])
    ]
    policies = policy_grid(calibration)
    if len(policies) != 1000:
        raise ValueError(f"V70 registered {len(policies)} policies, expected 1000")
    rows = []
    for policy in policies:
        candidates = generate_candidates(
            features, policy=policy, family=str(rule["family"])
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
    features.to_parquet(feature_path, index=False)
    grid.to_csv(grid_path, index=False, lineterminator="\n")
    decision = (
        "V70_CALIBRATION_POLICY_SELECTED" if selected else "V70_NO_CALIBRATION_POLICY"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_comex_spot_receipt_v70_calibration_audit",
        "campaign_id": str(config["campaign_id"]),
        "decision": decision,
        "calibration_start": str(start),
        "calibration_end_exclusive": str(end),
        "source_files": source_files,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "feature_rows": int(len(features)),
        "publisher_clock_lead_rows": int(publisher_clock_lead_count),
        "feature_sha256": sha256_file(feature_path),
        "registered_policy_count": len(policies),
        "eligible_policy_count": int(grid["selection_eligible"].sum()),
        "grid_sha256": sha256_file(grid_path),
        "selected_policy": selected,
        "post_decision_spot_outcomes_opened": False,
        **config["research_controls"],
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    audit_path.write_bytes(
        (json.dumps(audit, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
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

from __future__ import annotations

import argparse
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
    publisher_clock_lead_rows,
    received_session,
    sha256_file,
    spot_quote_frame,
    timestamp_milliseconds,
)
from lock_contract import verify_lock  # noqa: E402
import size_segment_flow as base  # noqa: E402
from spot_labels import (  # noqa: E402
    VerifiedSpotTickStore,
    label_candidates,
    load_completed_atr,
    load_dukascopy_foundation,
    resolve_spot_storage,
)


CONFIG = ROOT / "config" / "comex_spot_receipt_innovation_v70.json"
STAGES = ("development", "validation", "exam")


def output_paths(config: Mapping[str, Any], stage: str) -> tuple[Path, Path, Path]:
    output = ROOT / str(config["outputs"]["directory"])
    prefix = f"COMEX_SPOT_RECEIPT_V70_{stage.upper()}"
    return (
        output / f"{prefix}_CANDIDATES.parquet",
        output / f"{prefix}_LABELS.parquet",
        output / f"{prefix}_AUDIT.json",
    )


def require_firewall(config: Mapping[str, Any], stage: str) -> None:
    for prior in STAGES[: STAGES.index(stage)]:
        audit_path = output_paths(config, prior)[2]
        if not audit_path.is_file():
            raise RuntimeError(f"V70 {stage} sealed because {prior} has not run")
        audit = load_json(audit_path)
        if canonical_hash(audit, "audit_sha256") != str(audit.get("audit_sha256")):
            raise RuntimeError(f"V70 {prior} audit self-hash changed")
        if not bool(audit.get("gate_passed")):
            raise RuntimeError(f"V70 {stage} sealed because {prior} failed")


def run_stage(stage: str) -> dict[str, Any]:
    config = load_json(CONFIG)
    contract = verify_lock(config)
    require_firewall(config, stage)
    candidate_path, label_path, audit_path = output_paths(config, stage)
    if any(path.exists() for path in (candidate_path, label_path, audit_path)):
        raise FileExistsError(f"V70 {stage} outputs already exist")
    start, end = (pd.Timestamp(value) for value in config["splits"][stage])
    files = base.discover_source_files(
        Path(str(config["source"]["job_directory"])), start=start, end=end
    )
    storage = resolve_spot_storage(config)
    feature_cache = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(feature_cache) != str(config["spot_source"]["m5_feature_sha256"]):
        raise ValueError("V70 completed-M5 feature cache changed")
    tick_store = VerifiedSpotTickStore(
        storage_root=storage,
        symbol=str(config["spot_source"]["symbol"]),
        foundation=load_dukascopy_foundation(),
    )
    atr_source = load_completed_atr(config, storage)
    rule = config["candidate_rule"]
    policy = contract["selected_policy"]
    horizon = int(policy["horizon_ms"])
    candidate_frames: list[pd.DataFrame] = []
    label_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    feature_rows = 0
    raw_trade_rows = 0
    publisher_clock_lead_count = 0
    for number, path in enumerate(files, start=1):
        raw = base.load_dbn_trades(path)
        raw_trade_rows += len(raw)
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
        if bool(quality["eligible_full_weekday"]):
            session = received_session(raw, rule)
            buckets = bucket_received_trades(
                session, bucket_ms=int(rule["receipt_bucket_ms"])
            )
            if not buckets.empty:
                decision_ms = timestamp_milliseconds(buckets["feature_time_utc"])
                quotes = spot_quote_frame(
                    tick_store,
                    start_timestamp_ms=int(decision_ms.min())
                    - horizon
                    - int(rule["maximum_spot_quote_staleness_ms"]),
                    end_timestamp_ms=int(decision_ms.max()),
                )
                features = build_innovation_features(
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
                feature_rows += len(features)
                candidates = generate_candidates(
                    features, policy=policy, family=str(rule["family"])
                )
                if not candidates.empty:
                    candidate_frames.append(candidates)
                    label_frames.append(
                        label_candidates(
                            candidates,
                            atr_source=atr_source,
                            tick_store=tick_store,
                            config=config,
                        )
                    )
        if number % 25 == 0:
            print(f"processed {number}/{len(files)} COMEX files", flush=True)
    candidates = (
        pd.concat(candidate_frames, ignore_index=True)
        if candidate_frames
        else pd.DataFrame(
            columns=["candidate_id", "feature_time_utc", "family", "direction"]
        )
    )
    labels = (
        pd.concat(label_frames, ignore_index=True)
        if label_frames
        else pd.DataFrame(columns=["candidate_id", "status", "direction"])
    )
    eligible_dates = [
        str(row["date_utc"])
        for row in quality_rows
        if bool(row["eligible_full_weekday"])
    ]
    result = base.summarize_stage(
        labels, stage=stage, eligible_dates=eligible_dates, config=config
    )
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_parquet(candidate_path, index=False)
    labels.to_parquet(label_path, index=False)
    decision = (
        f"V70_{stage.upper()}_PASS"
        if bool(result["gate_passed"])
        else f"V70_{stage.upper()}_FAIL_TERMINAL"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_comex_spot_receipt_v70_stage_audit",
        "campaign_id": str(config["campaign_id"]),
        "stage": stage,
        "decision": decision,
        "contract_sha256": str(contract["contract_sha256"]),
        "selected_policy": policy,
        "raw_trade_rows": int(raw_trade_rows),
        "publisher_clock_lead_rows": int(publisher_clock_lead_count),
        "innovation_feature_rows": int(feature_rows),
        "source_files": source_files,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "candidate_rows": int(len(candidates)),
        "candidate_sha256": sha256_file(candidate_path),
        "label_rows": int(len(labels)),
        "label_status_counts": {
            str(key): int(value)
            for key, value in labels["status"].value_counts().items()
        },
        "labels_sha256": sha256_file(label_path),
        **result,
        **config["research_controls"],
    }
    audit["audit_sha256"] = canonical_hash(audit, "audit_sha256")
    audit_path.write_bytes(
        (json.dumps(audit, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )
    print(json.dumps({"decision": decision, **result["metrics"]}, indent=2))
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one sealed V70 stage")
    parser.add_argument("--stage", required=True, choices=STAGES)
    args = parser.parse_args()
    run_stage(str(args.stage))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

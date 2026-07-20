from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
V72_SRC = ROOT.parent / "xag-xau-eventtime-catchup-v72" / "src"
V78_SRC = ROOT.parent / "fx-consensus-xau-eventtime-v78" / "src"
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
LABEL_SRC = ROOT.parent / "comex-futures-foundation-v1" / "src"
for source in (ROOT / "src", V72_SRC, V78_SRC, BASE_SRC, LABEL_SRC):
    sys.path.insert(0, str(source))

from catchup import (  # noqa: E402
    ManifestTickStore,
    canonical_hash,
    load_json,
    sha256_file,
)
from fx_consensus import build_consensus_features, session_quality  # noqa: E402
from lock_contract import verify_lock  # noqa: E402
from retracement import (  # noqa: E402
    build_pattern_rows,
    generate_candidates,
    select_source_events,
)
from run_calibration import load_day  # noqa: E402
import size_segment_flow as base  # noqa: E402
from spot_labels import label_candidates, load_completed_atr  # noqa: E402


CONFIG = ROOT / "config" / "fx_consensus_transmission_retracement_v80.json"
STAGES = ("development", "validation")


def output_paths(config: Mapping[str, Any], stage: str) -> tuple[Path, Path, Path]:
    output = ROOT / str(config["outputs"]["directory"])
    prefix = f"FX_CONSENSUS_XAU_V80_{stage.upper()}"
    return (
        output / f"{prefix}_CANDIDATES.parquet",
        output / f"{prefix}_LABELS.parquet",
        output / f"{prefix}_AUDIT.json",
    )


def require_firewall(config: Mapping[str, Any], stage: str) -> None:
    for prior in STAGES[: STAGES.index(stage)]:
        audit_path = output_paths(config, prior)[2]
        if not audit_path.is_file():
            raise RuntimeError(f"V80 {stage} sealed because {prior} has not run")
        audit = load_json(audit_path)
        if (
            canonical_hash(audit, "audit_sha256") != audit.get("audit_sha256")
            or not bool(audit.get("gate_passed"))
        ):
            raise RuntimeError(f"V80 {stage} sealed because {prior} failed")


def run_stage(stage: str) -> dict[str, Any]:
    config = load_json(CONFIG)
    contract = verify_lock(config)
    require_firewall(config, stage)
    candidate_path, label_path, audit_path = output_paths(config, stage)
    if any(path.exists() for path in (candidate_path, label_path, audit_path)):
        raise FileExistsError(f"V80 {stage} outputs already exist")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    atr_path = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(atr_path) != config["spot_source"]["m5_feature_sha256"]:
        raise ValueError("V80 completed-M5 ATR cache changed")
    atr_source = load_completed_atr(config, storage)
    eurusd_store = ManifestTickStore(storage, "EURUSD", source["symbols"]["EURUSD"])
    usdjpy_store = ManifestTickStore(storage, "USDJPY", source["symbols"]["USDJPY"])
    xau_store = ManifestTickStore(storage, "XAUUSD", source["symbols"]["XAUUSD"])
    source_policy = contract["source_policy"]
    timing_policy = contract["selected_timing_policy"]
    source_horizon = int(source_policy["horizon_ms"])
    maximum_pattern_seconds = int(timing_policy["maximum_pattern_seconds"])
    rule = config["candidate_rule"]
    start, end = (pd.Timestamp(value) for value in config["splits"][stage])
    candidate_frames: list[pd.DataFrame] = []
    label_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    source_event_rows = 0
    pattern_rows = 0
    for number, date in enumerate(
        pd.date_range(start.normalize(), end.normalize(), inclusive="left", freq="D"),
        start=1,
    ):
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
            source_event_rows += len(source_events)
            patterns = build_pattern_rows(
                source_events,
                xau,
                transmission_bps_grid=[timing_policy["transmission_bps"]],
                retracement_fraction_grid=[timing_policy["retracement_fraction"]],
                maximum_pattern_seconds=maximum_pattern_seconds,
            )
            pattern_rows += len(patterns)
            candidates = generate_candidates(
                patterns, policy=timing_policy, family=str(rule["family"])
            )
            if not candidates.empty:
                candidate_frames.append(candidates)
                label_frames.append(
                    label_candidates(
                        candidates,
                        atr_source=atr_source,
                        tick_store=xau_store,
                        config=config,
                    )
                )
        if number % 25 == 0:
            print(f"V80 {stage}: processed through {date.date()}", flush=True)
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
        row["date_utc"] for row in quality_rows if bool(row["eligible_full_weekday"])
    ]
    result = base.summarize_stage(
        labels, stage=stage, eligible_dates=eligible_dates, config=config
    )
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidates.to_parquet(candidate_path, index=False)
    labels.to_parquet(label_path, index=False)
    decision = (
        f"V80_{stage.upper()}_PASS"
        if bool(result["gate_passed"])
        else f"V80_{stage.upper()}_FAIL_TERMINAL"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_fx_consensus_v80_stage_audit",
        "campaign_id": config["campaign_id"],
        "stage": stage,
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "source_policy": source_policy,
        "selected_timing_policy": timing_policy,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "source_event_rows": int(source_event_rows),
        "pattern_rows": int(pattern_rows),
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
    audit_path.write_bytes((json.dumps(audit, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"decision": decision, **result["metrics"]}, indent=2))
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one sealed V80 stage")
    parser.add_argument("--stage", required=True, choices=STAGES)
    args = parser.parse_args()
    run_stage(str(args.stage))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
LABEL_SRC = ROOT.parent / "comex-futures-foundation-v1" / "src"
for source in (ROOT / "src", BASE_SRC, LABEL_SRC):
    sys.path.insert(0, str(source))

from catchup import (  # noqa: E402
    ManifestTickStore,
    build_event_features,
    canonical_hash,
    generate_candidates,
    load_json,
    session_quality,
    sha256_file,
)
from lock_contract import verify_lock  # noqa: E402
from run_calibration import load_day  # noqa: E402
import size_segment_flow as base  # noqa: E402
from spot_labels import label_candidates, load_completed_atr  # noqa: E402


CONFIG = ROOT / "config" / "xag_xau_eventtime_catchup_v72.json"
STAGES = ("development", "confirmation", "validation", "exam")


def output_paths(config: Mapping[str, Any], stage: str) -> tuple[Path, Path, Path]:
    output = ROOT / str(config["outputs"]["directory"])
    prefix = f"XAG_XAU_V72_{stage.upper()}"
    return (
        output / f"{prefix}_CANDIDATES.parquet",
        output / f"{prefix}_LABELS.parquet",
        output / f"{prefix}_AUDIT.json",
    )


def require_firewall(config: Mapping[str, Any], stage: str) -> None:
    for prior in STAGES[: STAGES.index(stage)]:
        audit_path = output_paths(config, prior)[2]
        if not audit_path.is_file():
            raise RuntimeError(f"V72 {stage} sealed because {prior} has not run")
        audit = load_json(audit_path)
        if canonical_hash(audit, "audit_sha256") != audit.get("audit_sha256"):
            raise RuntimeError(f"V72 {prior} audit self-hash changed")
        if not bool(audit.get("gate_passed")):
            raise RuntimeError(f"V72 {stage} sealed because {prior} failed")
    if stage == "exam":
        source_path = ROOT / str(config["outputs"]["directory"]) / str(
            config["outputs"]["exam_source_audit"]
        )
        if not source_path.is_file():
            raise RuntimeError("V72 exam sealed because its source audit is missing")
        source_audit = load_json(source_path)
        if (
            source_audit.get("decision") != "V72_EXAM_SOURCE_AUDIT_PASS"
            or canonical_hash(source_audit, "audit_sha256")
            != source_audit.get("audit_sha256")
            or bool(source_audit.get("economic_outcomes_opened"))
        ):
            raise RuntimeError("V72 exam source audit is invalid")


def run_stage(stage: str) -> dict[str, Any]:
    config = load_json(CONFIG)
    contract = verify_lock(config)
    require_firewall(config, stage)
    candidate_path, label_path, audit_path = output_paths(config, stage)
    if any(path.exists() for path in (candidate_path, label_path, audit_path)):
        raise FileExistsError(f"V72 {stage} outputs already exist")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    atr_path = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(atr_path) != config["spot_source"]["m5_feature_sha256"]:
        raise ValueError("V72 completed-M5 ATR cache changed")
    atr_source = load_completed_atr(config, storage)
    xag_store = ManifestTickStore(storage, "XAGUSD", source["symbols"]["XAGUSD"])
    xau_store = ManifestTickStore(storage, "XAUUSD", source["symbols"]["XAUUSD"])
    policy = contract["selected_policy"]
    horizon = int(policy["horizon_ms"])
    rule = config["candidate_rule"]
    start, end = (pd.Timestamp(value) for value in config["splits"][stage])
    candidates_list: list[pd.DataFrame] = []
    labels_list: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    feature_rows = 0
    for number, date in enumerate(
        pd.date_range(start.normalize(), end.normalize(), inclusive="left", freq="D"),
        start=1,
    ):
        if date.weekday() >= 5:
            continue
        xag, xau = load_day(
            date,
            xag_store=xag_store,
            xau_store=xau_store,
            rule=rule,
            maximum_horizon_ms=horizon,
        )
        quality = session_quality(date, xag, xau, rule)
        quality_rows.append(quality)
        if bool(quality["eligible_full_weekday"]):
            features = build_event_features(
                date,
                xag,
                xau,
                horizons_ms=[horizon],
                rule=rule,
                prefilter=policy,
            )
            feature_rows += len(features)
            candidates = generate_candidates(
                features, policy=policy, family=str(rule["family"])
            )
            if not candidates.empty:
                candidates_list.append(candidates)
                labels_list.append(
                    label_candidates(
                        candidates,
                        atr_source=atr_source,
                        tick_store=xau_store,
                        config=config,
                    )
                )
        if number % 25 == 0:
            print(f"V72 {stage}: processed through {date.date()}", flush=True)
    candidates = (
        pd.concat(candidates_list, ignore_index=True)
        if candidates_list
        else pd.DataFrame(columns=["candidate_id", "feature_time_utc", "family", "direction"])
    )
    labels = (
        pd.concat(labels_list, ignore_index=True)
        if labels_list
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
        f"V72_{stage.upper()}_PASS"
        if bool(result["gate_passed"])
        else f"V72_{stage.upper()}_FAIL_TERMINAL"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_xag_xau_v72_stage_audit",
        "campaign_id": str(config["campaign_id"]),
        "stage": stage,
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "selected_policy": policy,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "event_feature_rows": int(feature_rows),
        "candidate_rows": int(len(candidates)),
        "candidate_sha256": sha256_file(candidate_path),
        "label_rows": int(len(labels)),
        "label_status_counts": {
            str(key): int(value) for key, value in labels["status"].value_counts().items()
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
    parser = argparse.ArgumentParser(description="Run one sealed V72 stage")
    parser.add_argument("--stage", required=True, choices=STAGES)
    args = parser.parse_args()
    run_stage(str(args.stage))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

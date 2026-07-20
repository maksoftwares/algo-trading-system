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
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
LABEL_SRC = ROOT.parent / "comex-futures-foundation-v1" / "src"
for source in (ROOT / "src", V72_SRC, BASE_SRC, LABEL_SRC):
    sys.path.insert(0, str(source))

from catchup import (  # noqa: E402
    ManifestTickStore,
    canonical_hash,
    load_json,
    sha256_file,
)
from fx_breadth import (  # noqa: E402
    build_breadth_features,
    generate_candidates,
    session_quality,
)
from lock_contract import verify_lock  # noqa: E402
from run_calibration import load_day  # noqa: E402
from run_source_audit import (  # noqa: E402
    audit_month_bounds,
    source_audit_decision,
    source_audit_output_path,
)
import size_segment_flow as base  # noqa: E402
from spot_labels import label_candidates, load_completed_atr  # noqa: E402


CONFIG = ROOT / "config" / "fx_breadth_overreaction_fade_v81.json"
STAGES = (
    "development",
    "confirmation",
    "validation",
    "exam",
    "forward_confirmation",
    "forward_final",
)


def output_paths(config: Mapping[str, Any], stage: str) -> tuple[Path, Path, Path]:
    output = ROOT / str(config["outputs"]["directory"])
    prefix = f"FX_BREADTH_XAU_V81_{stage.upper()}"
    return (
        output / f"{prefix}_CANDIDATES.parquet",
        output / f"{prefix}_LABELS.parquet",
        output / f"{prefix}_AUDIT.json",
    )


def require_firewall(config: Mapping[str, Any], stage: str) -> None:
    for prior in STAGES[: STAGES.index(stage)]:
        path = output_paths(config, prior)[2]
        if not path.is_file():
            raise RuntimeError(f"V81 {stage} sealed because {prior} has not run")
        audit = load_json(path)
        if (
            canonical_hash(audit, "audit_sha256") != audit.get("audit_sha256")
            or not bool(audit.get("gate_passed"))
        ):
            raise RuntimeError(f"V81 {stage} sealed because {prior} failed")


def verify_stage_source_audit(
    config: Mapping[str, Any], stage: str, contract: Mapping[str, Any]
) -> tuple[dict[str, Any], Path]:
    values = dict(config)
    path = source_audit_output_path(values, stage)
    audit = load_json(path)
    first_month, last_month = audit_month_bounds(values, stage)
    if (
        audit.get("decision") != source_audit_decision(stage)
        or canonical_hash(audit, "audit_sha256") != audit.get("audit_sha256")
        or audit.get("symbols") != config["source"]["symbols"]
        or audit.get("first_month") != first_month
        or audit.get("last_month") != last_month
        or bool(audit.get("paid_data_used"))
        or bool(audit.get("economic_outcomes_opened"))
    ):
        raise ValueError(f"V81 {stage} source audit is invalid")
    if stage == "development" and sha256_file(path) != contract[
        "development_source_audit"
    ]["sha256"]:
        raise ValueError("V81 locked development source audit changed")
    return audit, path


def run_stage(stage: str) -> dict[str, Any]:
    config = load_json(CONFIG)
    contract = verify_lock(config)
    require_firewall(config, stage)
    stage_source_audit, stage_source_path = verify_stage_source_audit(
        config, stage, contract
    )
    candidate_path, label_path, audit_path = output_paths(config, stage)
    if any(path.exists() for path in (candidate_path, label_path, audit_path)):
        raise FileExistsError(f"V81 {stage} outputs already exist")
    source = config["source"]
    storage = Path(
        os.environ.get(
            str(source["storage_environment_variable"]),
            str(source["default_storage_root"]),
        )
    ).resolve()
    atr_path = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(atr_path) != config["spot_source"]["m5_feature_sha256"]:
        raise ValueError("V81 completed-M5 ATR cache changed")
    atr_source = load_completed_atr(config, storage)
    stores = {
        symbol: ManifestTickStore(storage, symbol, spec)
        for symbol, spec in source["symbols"].items()
    }
    policy = contract["selected_policy"]
    horizon = int(policy["horizon_ms"])
    rule = config["candidate_rule"]
    start, end = (pd.Timestamp(value) for value in config["splits"][stage])
    candidate_frames: list[pd.DataFrame] = []
    label_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    feature_rows = 0
    for number, date in enumerate(
        pd.date_range(start.normalize(), end.normalize(), inclusive="left", freq="D"),
        start=1,
    ):
        if date.weekday() >= 5:
            continue
        eurusd, gbpusd, usdjpy, xau = load_day(
            date,
            eurusd_store=stores["EURUSD"],
            gbpusd_store=stores["GBPUSD"],
            usdjpy_store=stores["USDJPY"],
            xau_store=stores["XAUUSD"],
            rule=rule,
            maximum_horizon_ms=horizon,
        )
        quality = session_quality(date, eurusd, gbpusd, usdjpy, xau, rule)
        quality_rows.append(quality)
        if bool(quality["eligible_full_weekday"]):
            features = build_breadth_features(
                date,
                eurusd,
                gbpusd,
                usdjpy,
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
                candidate_frames.append(candidates)
                label_frames.append(
                    label_candidates(
                        candidates,
                        atr_source=atr_source,
                        tick_store=stores["XAUUSD"],
                        config=config,
                    )
                )
        if number % 25 == 0:
            print(f"V81 {stage}: processed through {date.date()}", flush=True)
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
        f"V81_{stage.upper()}_PASS"
        if bool(result["gate_passed"])
        else f"V81_{stage.upper()}_FAIL_TERMINAL"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_fx_breadth_overreaction_v81_stage_audit",
        "campaign_id": config["campaign_id"],
        "stage": stage,
        "decision": decision,
        "contract_sha256": contract["contract_sha256"],
        "selected_policy": policy,
        "stage_source_audit_sha256": sha256_file(stage_source_path),
        "stage_source_audit_hash": stage_source_audit["audit_sha256"],
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "event_feature_rows": int(feature_rows),
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
    parser = argparse.ArgumentParser(description="Run one sealed V81 stage")
    parser.add_argument("--stage", required=True, choices=STAGES)
    args = parser.parse_args()
    run_stage(str(args.stage))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

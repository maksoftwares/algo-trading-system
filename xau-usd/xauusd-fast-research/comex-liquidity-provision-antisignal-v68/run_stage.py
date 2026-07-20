from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

import pandas as pd


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
FLOW_SRC = ROOT.parent / "comex-flow-transition-v44" / "src"
SEQUENCE_SRC = ROOT.parent / "comex-sequence-ignition-v45" / "src"
FOUNDATION_SRC = ROOT.parent / "comex-futures-foundation-v1" / "src"
for source in (ROOT / "src", FLOW_SRC, SEQUENCE_SRC, FOUNDATION_SRC):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

from antisignal import (  # noqa: E402
    canonical_hash,
    load_json,
    prepare_source_candidates,
    route_one_per_day,
    sha256_file,
)
import flow_transition  # noqa: E402
from lock_contract import verify_lock  # noqa: E402
import sequence_ignition  # noqa: E402
from spot_labels import (  # noqa: E402
    VerifiedSpotTickStore,
    label_candidates,
    load_completed_atr,
    load_dukascopy_foundation,
    resolve_spot_storage,
)


CONFIG = ROOT / "config" / "comex_liquidity_provision_antisignal_v68.json"
STAGES = ("development", "validation", "exam")


def output_paths(config: Mapping[str, Any], stage: str) -> tuple[Path, Path, Path]:
    output = ROOT / str(config["outputs"]["directory"])
    prefix = f"COMEX_LIQUIDITY_PROVISION_V68_{stage.upper()}"
    return (
        output / f"{prefix}_CANDIDATES.parquet",
        output / f"{prefix}_LABELS.parquet",
        output / f"{prefix}_AUDIT.json",
    )


def require_firewall(config: Mapping[str, Any], stage: str) -> None:
    for prior in STAGES[: STAGES.index(stage)]:
        audit_path = output_paths(config, prior)[2]
        if not audit_path.is_file():
            raise RuntimeError(f"V68 {stage} sealed because {prior} has not run")
        audit = load_json(audit_path)
        if canonical_hash(audit, "audit_sha256") != str(audit.get("audit_sha256")):
            raise RuntimeError(f"V68 {prior} audit self-hash changed")
        if not bool(audit.get("gate_passed")):
            raise RuntimeError(f"V68 {stage} sealed because {prior} failed")


def source_candidates(
    session: pd.DataFrame, config: Mapping[str, Any]
) -> list[pd.DataFrame]:
    sources = config["source_hypotheses"]
    v44 = sources["V44"]
    v44_features = flow_transition.build_transition_features(
        session, rule=v44["candidate_rule"]
    )
    v44_candidates = flow_transition.generate_candidates(
        v44_features,
        policy=v44["selected_policy"],
        rule=v44["candidate_rule"],
    )
    v45 = sources["V45"]
    v45_features = sequence_ignition.build_sequence_features(
        session, rule=v45["candidate_rule"]
    )
    v45_candidates = sequence_ignition.generate_candidates(
        v45_features,
        policy=v45["selected_policy"],
        rule=v45["candidate_rule"],
    )
    return [
        prepare_source_candidates(
            v44_candidates,
            source="V44",
            antisignal_family=str(v44["antisignal_family"]),
        ),
        prepare_source_candidates(
            v45_candidates,
            source="V45",
            antisignal_family=str(v45["antisignal_family"]),
        ),
    ]


def run_stage(stage: str) -> dict[str, Any]:
    config = load_json(CONFIG)
    contract = verify_lock(config)
    require_firewall(config, stage)
    candidate_path, label_path, audit_path = output_paths(config, stage)
    if any(path.exists() for path in (candidate_path, label_path, audit_path)):
        raise FileExistsError(f"V68 {stage} outputs already exist")
    start, end = (pd.Timestamp(value) for value in config["splits"][stage])
    files = flow_transition.discover_source_files(
        Path(str(config["source"]["job_directory"])), start=start, end=end
    )
    common_rule = config["source_hypotheses"]["V44"]["candidate_rule"]
    candidate_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    raw_trade_rows = 0
    for number, path in enumerate(files, start=1):
        raw = flow_transition.load_dbn_trades(path)
        session = flow_transition.session_trades(raw, common_rule)
        quality = flow_transition.session_quality(session, common_rule)
        quality["source_file"] = path.name
        quality_rows.append(quality)
        source_files.append(
            {
                "path": str(path),
                "bytes": int(path.stat().st_size),
                "sha256": sha256_file(path),
            }
        )
        raw_trade_rows += len(raw)
        if bool(quality["eligible_full_weekday"]):
            candidate_frames.extend(source_candidates(session, config))
        if number % 25 == 0:
            print(f"processed {number}/{len(files)} COMEX files", flush=True)
    combined = (
        pd.concat(candidate_frames, ignore_index=True)
        if candidate_frames
        else pd.DataFrame(
            columns=[
                "candidate_id",
                "source_family",
                "family",
                "direction",
                "feature_time_utc",
            ]
        )
    )
    selected, route_audit = route_one_per_day(
        combined,
        source_priority=[str(value) for value in config["router"]["source_priority"]],
    )
    eligible_dates = [
        str(row["date_utc"])
        for row in quality_rows
        if bool(row["eligible_full_weekday"])
    ]
    storage = resolve_spot_storage(config)
    feature_cache = storage / str(config["spot_source"]["m5_feature_cache"])
    if sha256_file(feature_cache) != str(config["spot_source"]["m5_feature_sha256"]):
        raise ValueError("V68 spot feature cache changed before labeling")
    labels = label_candidates(
        selected,
        atr_source=load_completed_atr(config, storage),
        tick_store=VerifiedSpotTickStore(
            storage_root=storage,
            symbol=str(config["spot_source"]["symbol"]),
            foundation=load_dukascopy_foundation(),
        ),
        config=config,
    )
    if labels.empty:
        labels = pd.DataFrame(columns=["candidate_id", "status", "direction"])
    result = flow_transition.summarize_stage(
        labels, stage=stage, eligible_dates=eligible_dates, config=config
    )
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    selected.to_parquet(candidate_path, index=False)
    labels.to_parquet(label_path, index=False)
    decision = (
        f"V68_{stage.upper()}_PASS"
        if bool(result["gate_passed"])
        else f"V68_{stage.upper()}_FAIL_TERMINAL"
    )
    audit: dict[str, Any] = {
        "schema_version": "xauusd_comex_liquidity_provision_v68_stage_audit",
        "campaign_id": str(config["campaign_id"]),
        "stage": stage,
        "decision": decision,
        "contract_sha256": str(contract["contract_sha256"]),
        "development_is_hypothesis_generation_only": stage == "development",
        "raw_trade_rows": int(raw_trade_rows),
        "source_files": source_files,
        "session_quality": quality_rows,
        "eligible_full_weekdays": len(eligible_dates),
        "route_audit": route_audit,
        "candidate_rows": int(len(selected)),
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
    parser = argparse.ArgumentParser(description="Run one sealed V68 stage")
    parser.add_argument("--stage", required=True, choices=STAGES)
    args = parser.parse_args()
    run_stage(str(args.stage))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

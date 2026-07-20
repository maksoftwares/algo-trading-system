from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
V45_ROOT = ROOT.parent / "comex-sequence-ignition-v45"
V45_SRC = V45_ROOT / "src"
FOUNDATION = ROOT.parent / "comex-futures-foundation-v1" / "src"
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
for source in (SRC, V45_SRC, FOUNDATION, BASE_SRC):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

import size_segment_flow as base  # noqa: E402
from model_lock import MODEL, OUTPUTS, verify_lock  # noqa: E402
from ranker import load_config, prepare_matrix, rank_auc, sha256_file  # noqa: E402
from sequence_ignition import (  # noqa: E402
    build_sequence_features,
    discover_source_files,
    generate_candidates,
    load_dbn_trades,
    session_quality,
    session_trades,
)
from spot_labels import (  # noqa: E402
    VerifiedSpotTickStore,
    label_candidates,
    load_completed_atr,
    load_dukascopy_foundation,
    resolve_spot_storage,
)


CONFIG = ROOT / "config" / "comex_sequence_ml_ranker_v46.json"
INTERNAL_AUDIT = OUTPUTS / "COMEX_SEQUENCE_ML_V46_INTERNAL_EXAM_AUDIT.json"
STAGES = ("validation", "exam")


def _paths(stage: str) -> tuple[Path, Path, Path, Path]:
    prefix = f"COMEX_SEQUENCE_ML_V46_{stage.upper()}"
    return (
        OUTPUTS / f"{prefix}_CANDIDATES.parquet",
        OUTPUTS / f"{prefix}_LABELS.parquet",
        OUTPUTS / f"{prefix}_SCORES.parquet",
        OUTPUTS / f"{prefix}_AUDIT.json",
    )


def _digest(payload: dict[str, Any]) -> str:
    clean = {key: value for key, value in payload.items() if key != "audit_sha256"}
    return hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _require_firewall(stage: str) -> None:
    if not INTERNAL_AUDIT.is_file():
        raise RuntimeError("Historical stages are sealed until V46 internal exam runs.")
    internal = json.loads(INTERNAL_AUDIT.read_text(encoding="utf-8"))
    if internal.get("gate_passed") is not True:
        raise RuntimeError(
            "Historical stages are sealed because V46 internal exam failed."
        )
    for prior in STAGES[: STAGES.index(stage)]:
        audit = json.loads(_paths(prior)[3].read_text(encoding="utf-8"))
        if audit.get("gate_passed") is not True:
            raise RuntimeError(f"{stage} is sealed because {prior} failed.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=STAGES)
    stage = str(parser.parse_args().stage)
    _require_firewall(stage)
    lock = verify_lock()
    paths = _paths(stage)
    if any(path.exists() for path in paths):
        raise RuntimeError(f"V46 {stage} outputs already exist; rerun is prohibited.")
    config = load_config(CONFIG)
    v45_config = load_config(V45_ROOT / "config" / "comex_sequence_ignition_v45.json")
    v45_lock = json.loads(
        (
            V45_ROOT / "outputs" / "COMEX_SEQUENCE_IGNITION_V45_CONTRACT_LOCK.json"
        ).read_text(encoding="utf-8")
    )
    start, end = (pd.Timestamp(value) for value in config["evaluation_splits"][stage])
    files = discover_source_files(
        Path(v45_config["source"]["job_directory"]), start=start, end=end
    )
    rule = v45_config["candidate_rule"]
    policy = v45_lock["selected_policy"]
    candidate_frames: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    for number, path in enumerate(files, start=1):
        raw = load_dbn_trades(path)
        session = session_trades(raw, rule)
        quality = session_quality(session, rule)
        quality["source_file"] = path.name
        quality_rows.append(quality)
        if quality["eligible_full_weekday"]:
            candidate_frames.append(
                generate_candidates(
                    build_sequence_features(session, rule=rule),
                    policy=policy,
                    rule=rule,
                )
            )
        if number % 25 == 0:
            print(f"processed {number}/{len(files)} COMEX files", flush=True)
    candidates = (
        pd.concat(candidate_frames, ignore_index=True)
        if candidate_frames
        else pd.DataFrame()
    )
    model = joblib.load(MODEL)
    scores = model.predict_proba(prepare_matrix(candidates))[:, 1]
    candidates["model_probability"] = scores
    candidates["accepted"] = scores >= float(lock["threshold"])
    label_config = dict(v45_config)
    label_config["splits"] = config["evaluation_splits"]
    foundation = load_dukascopy_foundation()
    storage = resolve_spot_storage(label_config)
    labels = label_candidates(
        candidates,
        atr_source=load_completed_atr(label_config, storage),
        tick_store=VerifiedSpotTickStore(
            storage_root=storage,
            symbol=str(label_config["spot_source"]["symbol"]),
            foundation=foundation,
        ),
        config=label_config,
    )
    merged = candidates.merge(labels, on="candidate_id", validate="one_to_one")
    resolved = merged.loc[merged["status"] == "RESOLVED"].copy()
    auc = rank_auc(
        resolved["profitable_after_stress"], resolved["model_probability"].to_numpy()
    )
    accepted = resolved.loc[resolved["accepted"]].copy()
    eligible_dates = [
        str(row["date_utc"]) for row in quality_rows if row["eligible_full_weekday"]
    ]
    result = base.summarize_stage(
        accepted, stage=stage, eligible_dates=eligible_dates, config=config
    )
    auc_pass = auc is not None and auc >= float(config["gates"]["minimum_rank_auc"])
    gate_passed = bool(result["gate_passed"] and auc_pass)
    candidates.to_parquet(paths[0], index=False)
    labels.to_parquet(paths[1], index=False)
    resolved[["candidate_id", "model_probability", "accepted"]].to_parquet(
        paths[2], index=False
    )
    payload: dict[str, Any] = {
        "schema_version": "xauusd_comex_sequence_ml_v46_stage_audit",
        "campaign_id": config["campaign_id"],
        "stage": stage,
        "decision": f"V46_{stage.upper()}_PASS"
        if gate_passed
        else f"V46_{stage.upper()}_FAIL_TERMINAL",
        "model_contract_sha256": lock["contract_sha256"],
        "raw_resolved_candidates": len(resolved),
        "rank_auc": auc,
        "rank_auc_gate_passed": auc_pass,
        "candidate_sha256": sha256_file(paths[0]),
        "labels_sha256": sha256_file(paths[1]),
        "scores_sha256": sha256_file(paths[2]),
        **result,
        "gate_passed": gate_passed,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }
    payload["audit_sha256"] = _digest(payload)
    paths[3].write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"decision": payload["decision"], "rank_auc": auc, **result["metrics"]},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

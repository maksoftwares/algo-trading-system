from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
for source in (SRC, BASE_SRC):
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))

import size_segment_flow as base  # noqa: E402
from model_lock import MODEL, OUTPUTS, verify_lock  # noqa: E402
from ranker import (  # noqa: E402
    eligible_dates_from_audit,
    load_config,
    merge_resolved,
    prepare_matrix,
    rank_auc,
    sha256_file,
)


CONFIG = ROOT / "config" / "comex_sequence_ml_ranker_v46.json"
SCORES = OUTPUTS / "COMEX_SEQUENCE_ML_V46_INTERNAL_EXAM_SCORES.parquet"
AUDIT = OUTPUTS / "COMEX_SEQUENCE_ML_V46_INTERNAL_EXAM_AUDIT.json"


def _digest(payload: dict[str, Any]) -> str:
    clean = {key: value for key, value in payload.items() if key != "audit_sha256"}
    return hashlib.sha256(
        json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def main() -> None:
    if SCORES.exists() or AUDIT.exists():
        raise RuntimeError(
            "V46 internal-exam outputs already exist; rerun is prohibited."
        )
    lock = verify_lock()
    config = load_config(CONFIG)
    v45_root = (ROOT / config["v45"]["root"]).resolve()
    candidate_path = (
        v45_root
        / "outputs"
        / "COMEX_SEQUENCE_IGNITION_V45_DEVELOPMENT_CANDIDATES.parquet"
    )
    label_path = (
        v45_root / "outputs" / "COMEX_SEQUENCE_IGNITION_V45_DEVELOPMENT_LABELS.parquet"
    )
    audit_path = (
        v45_root / "outputs" / "COMEX_SEQUENCE_IGNITION_V45_DEVELOPMENT_AUDIT.json"
    )
    start, end = (
        pd.Timestamp(value) for value in config["partitions"]["internal_exam"]
    )
    candidates = pd.read_parquet(
        candidate_path,
        filters=[("feature_time_utc", ">=", start), ("feature_time_utc", "<", end)],
    )
    labels = pd.read_parquet(
        label_path,
        filters=[
            ("decision_time_utc", ">=", start.isoformat()),
            ("decision_time_utc", "<", end.isoformat()),
        ],
    )
    rows = merge_resolved(candidates, labels)
    model = joblib.load(MODEL)
    scores = model.predict_proba(prepare_matrix(rows))[:, 1]
    rows["model_probability"] = scores
    rows["accepted"] = scores >= float(lock["threshold"])
    auc = rank_auc(rows["profitable_after_stress"], scores)
    accepted = rows.loc[rows["accepted"]].copy()
    v45_audit = json.loads(audit_path.read_text(encoding="utf-8"))
    eligible_dates = eligible_dates_from_audit(v45_audit, start=start, end=end)
    result = base.summarize_stage(
        accepted,
        stage="internal_exam",
        eligible_dates=eligible_dates,
        config=config,
    )
    auc_pass = auc is not None and auc >= float(config["gates"]["minimum_rank_auc"])
    gate_passed = bool(result["gate_passed"] and auc_pass)
    score_frame = rows[
        [
            "candidate_id",
            "feature_time_utc",
            "direction",
            "model_probability",
            "accepted",
            "profitable_after_stress",
            "stress_net_pnl_usd",
        ]
    ].copy()
    score_frame.to_parquet(SCORES, index=False)
    payload: dict[str, Any] = {
        "schema_version": "xauusd_comex_sequence_ml_v46_internal_exam_audit",
        "campaign_id": config["campaign_id"],
        "decision": "V46_INTERNAL_EXAM_PASS"
        if gate_passed
        else "V46_INTERNAL_EXAM_FAIL_TERMINAL",
        "model_contract_sha256": lock["contract_sha256"],
        "start": start.isoformat(),
        "end": end.isoformat(),
        "raw_resolved_candidates": len(rows),
        "rank_auc": auc,
        "rank_auc_gate_passed": auc_pass,
        "scores_sha256": sha256_file(SCORES),
        **result,
        "gate_passed": gate_passed,
        "same_version_retraining_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }
    payload["audit_sha256"] = _digest(payload)
    AUDIT.write_text(
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

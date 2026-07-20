from __future__ import annotations

import json
import sys
from importlib.metadata import version
from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from model_lock import (  # noqa: E402
    CALIBRATION_SCORES,
    LOCK,
    MODEL,
    OUTPUTS,
    TRACKED,
    payload_digest,
    verify_lock,
)
from ranker import (  # noqa: E402
    MODEL_FEATURES,
    build_model,
    eligible_dates_from_audit,
    load_config,
    merge_resolved,
    prepare_matrix,
    select_threshold,
    sha256_file,
)


CONFIG = ROOT / "config" / "comex_sequence_ml_ranker_v46.json"


def _verify_source(path: Path, expected: str) -> None:
    if sha256_file(path).lower() != expected.lower():
        raise RuntimeError(f"V46 source hash mismatch: {path}")


def main() -> None:
    if LOCK.exists():
        payload = verify_lock()
        print(f"verified {payload['contract_sha256']}")
        return
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
    contract_path = (
        v45_root / "outputs" / "COMEX_SEQUENCE_IGNITION_V45_CONTRACT_LOCK.json"
    )
    for path, key in (
        (candidate_path, "development_candidates_sha256"),
        (label_path, "development_labels_sha256"),
        (audit_path, "development_audit_sha256"),
        (contract_path, "contract_lock_sha256"),
    ):
        _verify_source(path, str(config["v45"][key]))
    v45_lock = json.loads(contract_path.read_text(encoding="utf-8"))
    if v45_lock.get("contract_sha256") != config["v45"]["contract_sha256"]:
        raise RuntimeError(
            "V45 contract identity differs from the V46 preregistration."
        )

    candidates = pd.read_parquet(candidate_path)
    fit_start, fit_end = (pd.Timestamp(value) for value in config["partitions"]["fit"])
    calibration_start, calibration_end = (
        pd.Timestamp(value) for value in config["partitions"]["threshold_calibration"]
    )
    candidate_time = pd.to_datetime(candidates["feature_time_utc"], utc=True)
    fit_candidates = candidates.loc[
        (candidate_time >= fit_start) & (candidate_time < fit_end)
    ].copy()
    calibration_candidates = candidates.loc[
        (candidate_time >= calibration_start) & (candidate_time < calibration_end)
    ].copy()
    # Parquet filtering prevents calibration and internal-exam outcomes from entering training memory.
    fit_labels = pd.read_parquet(
        label_path,
        filters=[
            ("decision_time_utc", ">=", fit_start.isoformat()),
            ("decision_time_utc", "<", fit_end.isoformat()),
        ],
    )
    fit_rows = merge_resolved(fit_candidates, fit_labels)
    exit_time = pd.to_datetime(fit_rows["exit_time_utc"], utc=True)
    fit_rows = fit_rows.loc[exit_time < fit_end].copy()
    target = fit_rows["profitable_after_stress"].astype(int)
    if target.nunique() != 2:
        raise RuntimeError("V46 fit labels do not contain both classes.")
    model = build_model(config)
    model.fit(prepare_matrix(fit_rows), target)

    calibration_scores = model.predict_proba(prepare_matrix(calibration_candidates))[
        :, 1
    ]
    v45_audit = json.loads(audit_path.read_text(encoding="utf-8"))
    calibration_dates = eligible_dates_from_audit(
        v45_audit, start=calibration_start, end=calibration_end
    )
    selected = select_threshold(
        calibration_candidates,
        calibration_scores,
        eligible_dates=calibration_dates,
        selection=config["threshold_selection"],
    )
    if selected is None:
        raise RuntimeError(
            "V46 score distribution cannot preserve the locked density target."
        )
    threshold, facts = selected
    score_frame = calibration_candidates[
        ["candidate_id", "feature_time_utc", "direction"]
    ].copy()
    score_frame["model_probability"] = calibration_scores
    score_frame["accepted"] = calibration_scores >= threshold

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL, compress=3)
    score_frame.to_parquet(CALIBRATION_SCORES, index=False)
    payload = {
        "schema_version": "xauusd_comex_sequence_ml_v46_model_lock",
        "campaign_id": config["campaign_id"],
        "v45_contract_sha256": v45_lock["contract_sha256"],
        "source_sha256": {
            "development_candidates": sha256_file(candidate_path),
            "development_labels": sha256_file(label_path),
            "development_audit": sha256_file(audit_path),
            "v45_contract_lock": sha256_file(contract_path),
        },
        "model_class": type(model).__name__,
        "model_parameters": config["model"],
        "model_features": MODEL_FEATURES,
        "fit_start": fit_start.isoformat(),
        "fit_end": fit_end.isoformat(),
        "fit_rows": len(fit_rows),
        "fit_positive_labels": int(target.sum()),
        "fit_negative_labels": int((target == 0).sum()),
        "threshold_calibration_start": calibration_start.isoformat(),
        "threshold_calibration_end": calibration_end.isoformat(),
        "threshold_calibration_candidates": len(calibration_candidates),
        "threshold": threshold,
        "threshold_candidate_facts": facts,
        "threshold_labels_read": False,
        "internal_exam_labels_read_before_lock": False,
        "model_sha256": sha256_file(MODEL),
        "calibration_scores_sha256": sha256_file(CALIBRATION_SCORES),
        "tracked_file_sha256": {name: sha256_file(ROOT / name) for name in TRACKED},
        "runtime_versions": {
            "joblib": version("joblib"),
            "numpy": version("numpy"),
            "pandas": version("pandas"),
            "scikit_learn": version("scikit-learn"),
        },
        "same_version_retraining_authorized": False,
        "python_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }
    payload["contract_sha256"] = payload_digest(payload)
    LOCK.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "contract_sha256": payload["contract_sha256"],
                "threshold": threshold,
                **facts,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

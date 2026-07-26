from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
sys.path.insert(0, str(PACKAGE / "src"))
sys.path.insert(0, str(PACKAGE.parent / "causal-candidate-quality-ml-v1" / "src"))

from regime_model import predict  # noqa: E402
from regime_runner import (  # noqa: E402
    _acceptance,
    _family_pooled,
    _fold_weekdays,
    availability_table,
)
from step_3_common import (  # noqa: E402
    canonical_json_sha256,
    sha256_file,
    verify_bound_file,
)
from step_4_bootstrap import primary_block_bootstrap  # noqa: E402
from step_4_metrics import choose_threshold  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    config_path = PACKAGE / "config" / "regime_models_v2.json"
    contract = load_json(config_path)
    output_dir = PACKAGE / str(contract["outputs"]["directory"])
    outputs = contract["outputs"]
    lock_path = output_dir / str(outputs["contract_lock"])
    lock = load_json(lock_path)
    if lock["definition"]["config_sha256"] != sha256_file(config_path):
        raise ValueError("Regime V2 config differs from lock")
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        if sha256_file((PACKAGE / relative).resolve()) != expected:
            raise ValueError(f"Locked implementation differs: {relative}")
    bound = {
        name: verify_bound_file(REPO, spec, name)
        for name, spec in contract["bound_inputs"].items()
    }

    manifest_path = output_dir / str(outputs["artifact_manifest"])
    manifest = load_json(manifest_path)
    for name, artifact in manifest["artifacts"].items():
        path = REPO / str(artifact["path"])
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != int(artifact["bytes"]):
            raise ValueError(f"Artifact size mismatch: {name}")
        if sha256_file(path) != artifact["sha256"]:
            raise ValueError(f"Artifact hash mismatch: {name}")

    result = load_json(output_dir / str(outputs["result_json"]))
    if result["decision"] != "REGIME_V2_FAMILY_GATES_PASSED_DEVELOPMENT_ONLY":
        raise ValueError("Unexpected Regime V2 decision")
    required_false = (
        "comex_used",
        "databento_api_accessed",
        "demo_outcomes_used",
        "runtime_changed",
        "ml_shadow_or_execution_activated",
    )
    if any(bool(result[name]) for name in required_false):
        raise ValueError("Regime V2 crossed an offline control boundary")
    if result["journey_rows_used"] != 0 or not result["development_only"]:
        raise ValueError("Regime V2 population or evidence boundary is invalid")

    step2b = load_json(bound["step_2b_contract"])
    dataset = pd.read_parquet(bound["step_3_dataset"])
    splits = pd.read_parquet(bound["step_3_splits"])
    frame = splits[
        ["fold_id", "candidate_id", "assignment", "resolved_label", "dataset_eligible"]
    ].merge(dataset, on="candidate_id", validate="many_to_one")
    frame = frame.loc[
        frame["resolved_label"]
        & frame["dataset_eligible"]
        & frame["xau_feature_status"].eq("PASS")
    ].copy()
    expected_availability = availability_table(frame, contract).sort_values(
        ["family_id", "fold_id"], kind="stable"
    ).reset_index(drop=True)
    observed_availability = pd.read_parquet(
        output_dir / str(outputs["availability"])
    ).sort_values(["family_id", "fold_id"], kind="stable").reset_index(drop=True)
    pd.testing.assert_frame_equal(observed_availability, expected_availability)

    predictions = pd.read_parquet(output_dir / str(outputs["predictions"]))
    if predictions.duplicated(["family_id", "candidate_id"]).any():
        raise ValueError("Regime V2 test prediction identity is duplicated")
    features = list(contract["features"])
    model_dir = output_dir / str(outputs["model_directory"])
    model_count = 0
    for family_id, fold_ids in contract["availability"][
        "expected_trainable_folds"
    ].items():
        for fold_id in fold_ids:
            model_count += 1
            artifact = joblib.load(model_dir / f"{family_id}_{fold_id}.joblib")
            if artifact["family_id"] != family_id or artifact["fold_id"] != fold_id:
                raise ValueError("Serialized family/fold identity mismatch")
            if artifact["features"] != features or artifact["runtime_authorized"]:
                raise ValueError("Serialized model feature or authorization mismatch")
            local = frame.loc[
                frame["family_id"].eq(family_id)
                & frame["fold_id"].eq(fold_id)
            ].copy()
            calibration = local.loc[local["assignment"].eq("CALIBRATION")].copy()
            calibration["probability"] = predict(
                artifact["model"], calibration, features
            )
            threshold, _ = choose_threshold(
                calibration, contract["threshold_policy"]
            )
            if not np.isclose(threshold, float(artifact["threshold"])):
                raise ValueError(f"Threshold does not reproduce: {family_id} {fold_id}")
            test = local.loc[local["assignment"].eq("TEST")].sort_values(
                "candidate_id", kind="stable"
            )
            observed = predictions.loc[
                predictions["family_id"].eq(family_id)
                & predictions["fold_id"].eq(fold_id)
            ].sort_values("candidate_id", kind="stable")
            if test["candidate_id"].tolist() != observed["candidate_id"].tolist():
                raise ValueError(f"Test population mismatch: {family_id} {fold_id}")
            probability = predict(artifact["model"], test, features)
            if not np.allclose(
                probability,
                observed["probability"].to_numpy(float),
                rtol=1e-12,
                atol=1e-12,
            ):
                raise ValueError(f"Prediction mismatch: {family_id} {fold_id}")
            if observed["selected"].tolist() != (probability >= threshold).tolist():
                raise ValueError(f"Selection mismatch: {family_id} {fold_id}")

    weekdays = _fold_weekdays(step2b)
    stored_metrics = load_json(output_dir / str(outputs["family_metrics"]))
    stored_bootstraps = load_json(output_dir / str(outputs["bootstrap"]))
    stored_acceptance = load_json(output_dir / str(outputs["acceptance"]))
    recomputed_metrics: dict[str, dict] = {}
    recomputed_bootstraps: dict[str, dict] = {}
    recomputed_acceptance: dict[str, dict] = {}
    for family_id in contract["population"]["families"]:
        local = predictions.loc[predictions["family_id"].eq(family_id)].copy()
        fold_ids = contract["availability"]["expected_trainable_folds"][family_id]
        if local.empty:
            recomputed_acceptance[family_id] = _acceptance(
                family_id,
                eligible_folds=fold_ids,
                pooled=None,
                bootstrap=None,
                contract=contract,
            )
            continue
        pooled = _family_pooled(
            local, weekdays=sum(weekdays[fold_id] for fold_id in fold_ids)
        )
        bootstrap = primary_block_bootstrap(local, contract)
        recomputed_metrics[family_id] = pooled
        recomputed_bootstraps[family_id] = bootstrap
        recomputed_acceptance[family_id] = _acceptance(
            family_id,
            eligible_folds=fold_ids,
            pooled=pooled,
            bootstrap=bootstrap,
            contract=contract,
        )
    for expected, observed, label in (
        (recomputed_metrics, stored_metrics, "family metrics"),
        (recomputed_bootstraps, stored_bootstraps, "bootstraps"),
        (recomputed_acceptance, stored_acceptance, "acceptance"),
    ):
        if canonical_json_sha256(expected) != canonical_json_sha256(observed):
            raise ValueError(f"Regime V2 {label} do not reproduce")

    v8 = stored_metrics["V8_RETEST_HEALTH"]
    v8_bootstrap = stored_bootstraps["V8_RETEST_HEALTH"]
    print(
        json.dumps(
            {
                "decision": "REGIME_V2_VERIFIED",
                "evidence_decision": result["decision"],
                "artifact_manifest_sha256": sha256_file(manifest_path),
                "artifacts_verified": len(manifest["artifacts"]),
                "models_replayed": model_count,
                "trained_families": len(stored_metrics),
                "insufficient_families": result["insufficient_families"],
                "passed_families": result["passed_families"],
                "v8_test_rows": v8["baseline"]["rows"],
                "v8_selected_rows": v8["selected"]["rows"],
                "v8_weighted_auc": v8["probability"]["weighted_roc_auc"],
                "v8_auc_ci_lower": v8_bootstrap["weighted_roc_auc"]["lower"],
                "v8_delta_ev_r": v8[
                    "selected_minus_baseline_weighted_mean_stress_r"
                ],
                "v8_delta_ev_ci_lower": v8_bootstrap[
                    "selected_minus_baseline_weighted_mean_stress_r"
                ]["lower"],
                "runtime_changed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

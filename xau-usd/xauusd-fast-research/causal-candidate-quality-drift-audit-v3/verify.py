from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from run_audit import load_policies, model_record, verify_lock
from src.drift import (
    build_findings,
    categorical_drift_rows,
    decomposition_table,
    feature_drift_table,
    label_metrics_table,
    monthly_metrics_table,
    prepare_actions,
    replay_policy,
    resolve_inputs,
    score_bin_table,
    score_metrics_table,
    sha256_file,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "drift_audit_v3.json"


def compare_frames(actual: pd.DataFrame, stored: pd.DataFrame, name: str) -> None:
    try:
        pd.testing.assert_frame_equal(
            actual.reset_index(drop=True),
            stored.reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            rtol=1e-12,
            atol=1e-12,
        )
    except AssertionError as error:
        raise ValueError(f"Drift artifact replay mismatch: {name}") from error


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock = json.loads(
        (output / config["outputs"]["contract_lock"]).read_text(encoding="utf-8")
    )
    verify_lock(config, lock)
    manifest_path = output / config["outputs"]["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in manifest["inputs"].values():
        if sha256_file(REPO_ROOT / record["path"]) != record["sha256"]:
            raise ValueError(f"Drift manifest input changed: {record['path']}")
    for record in manifest["artifacts"].values():
        if sha256_file(REPO_ROOT / record["path"]) != record["sha256"]:
            raise ValueError(f"Drift artifact hash mismatch: {record['path']}")
    inputs = resolve_inputs(REPO_ROOT, config)
    v3_config = json.loads(inputs["v3_dataset_config"].read_text(encoding="utf-8"))
    action_config = json.loads(inputs["action_v3_config"].read_text(encoding="utf-8"))
    action_manifest = json.loads(
        inputs["action_v3_manifest"].read_text(encoding="utf-8")
    )
    features = list(v3_config["model_features"])
    actions = prepare_actions(
        pd.read_parquet(inputs["v3_action_dataset"]),
        pd.read_parquet(inputs["v3_split_assignments"]),
        v3_config,
        action_config,
        config,
    )
    policies = load_policies(pd.read_parquet(inputs["action_v3_policies"]), config)
    stored_predictions = pd.read_parquet(inputs["action_v3_predictions"])
    chosen_frames: list[pd.DataFrame] = []
    for lane in config["expected"]["lanes"]:
        policy = policies[lane]
        record = model_record(action_manifest, lane, policy)
        model_path = REPO_ROOT / record["path"]
        if sha256_file(model_path) != record["sha256"]:
            raise ValueError(f"Action V3 model hash changed: {model_path.name}")
        model = joblib.load(model_path)
        scored, chosen = replay_policy(
            model,
            actions.loc[actions["model_lane"].eq(lane)].copy(),
            features,
            float(policy["score_threshold"]),
        )
        current = scored.loc[scored["period"].eq("CURRENT")].sort_values(
            "candidate_id", kind="mergesort"
        )
        stored = stored_predictions.loc[
            stored_predictions["fold_id"].eq(config["target_fold"])
            & stored_predictions["model_lane"].eq(lane)
        ].sort_values("candidate_id", kind="mergesort")
        if current["candidate_id"].tolist() != stored["candidate_id"].tolist():
            raise ValueError(f"Independent replay candidates changed for {lane}")
        if not np.allclose(
            current["model_score"], stored["model_score"], rtol=1e-12, atol=1e-12
        ):
            raise ValueError(f"Independent replay scores changed for {lane}")
        chosen["chosen_model_id"] = policy["model_id"]
        chosen["score_threshold"] = policy["score_threshold"]
        chosen_frames.append(chosen)
    chosen_all = pd.concat(chosen_frames, ignore_index=True)

    tables: dict[str, pd.DataFrame] = {
        "feature_metrics": feature_drift_table(actions, features, config),
        "categorical_metrics": categorical_drift_rows(chosen_all, config),
        "score_metrics": score_metrics_table(chosen_all, policies, config),
        "score_bins": score_bin_table(chosen_all, config),
        "monthly_metrics": monthly_metrics_table(chosen_all),
        "label_metrics": label_metrics_table(actions, chosen_all, config),
        "decomposition": decomposition_table(chosen_all, config),
    }
    for name, frame in tables.items():
        stored = pd.read_parquet(output / config["outputs"][name])
        compare_frames(frame, stored, name)

    replayed = pd.read_parquet(output / config["outputs"]["replayed_events"])
    expected_ids = chosen_all.sort_values(
        ["model_lane", "period", "candidate_id"], kind="mergesort"
    )["candidate_id"].tolist()
    if replayed["candidate_id"].tolist() != expected_ids:
        raise ValueError("Replayed event ledger identities changed")
    if replayed.duplicated(["period", "model_lane", "event_id"]).any():
        raise ValueError("Replayed event ledger contains duplicates")

    findings = build_findings(
        tables["feature_metrics"],
        tables["categorical_metrics"],
        tables["score_metrics"],
        tables["decomposition"],
        config,
    )
    stored_findings = json.loads(
        (output / config["outputs"]["findings"]).read_text(encoding="utf-8")
    )
    if findings["decision"] != stored_findings["decision"]:
        raise ValueError("Drift findings decision changed")
    if findings["lanes"] != stored_findings["lanes"]:
        raise ValueError("Drift lane findings changed")
    if any(
        config["authorization"].get(key)
        for key in config["authorization"]
        if key != "research_only"
    ):
        raise ValueError("A runtime authorization is unexpectedly enabled")
    result: dict[str, Any] = {
        "decision": "DRIFT_V3_VERIFICATION_PASS",
        "evidence_decision": stored_findings["decision"],
        "manifest_sha256": sha256_file(manifest_path),
        "models_replayed": len(config["expected"]["lanes"]),
        "replayed_events": len(replayed),
        "feature_metrics": len(tables["feature_metrics"]),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

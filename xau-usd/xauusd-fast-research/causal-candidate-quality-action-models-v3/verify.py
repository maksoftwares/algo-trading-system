from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from run_evaluation import acceptance_checks, fold_windows
from src.action_models import (
    bootstrap_comparison,
    canonical_json_sha256,
    economic_metrics,
    predict_model,
    prepare_dataset,
    sha256_file,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "action_models_v3.json"


def close(left: object, right: object, name: str) -> None:
    if left is None or right is None:
        if left is not right:
            raise ValueError(f"Verification mismatch for {name}: {left} != {right}")
        return
    if not np.isclose(float(left), float(right), rtol=1e-10, atol=1e-10):
        raise ValueError(f"Verification mismatch for {name}: {left} != {right}")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    manifest_path = output / config["outputs"]["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, spec in manifest["inputs"].items():
        path = REPO_ROOT / spec["path"]
        if sha256_file(path) != spec["sha256"]:
            raise ValueError(f"Input artifact hash mismatch: {name}")
    for name, spec in manifest["artifacts"].items():
        if name == "models":
            for model_spec in spec:
                path = REPO_ROOT / model_spec["path"]
                if sha256_file(path) != model_spec["sha256"]:
                    raise ValueError(f"Model artifact hash mismatch: {path.name}")
            continue
        path = REPO_ROOT / spec["path"]
        if sha256_file(path) != spec["sha256"]:
            raise ValueError(f"Output artifact hash mismatch: {name}")

    input_paths = {
        name: REPO_ROOT / spec["path"] for name, spec in manifest["inputs"].items()
    }
    v3_config = json.loads(input_paths["v3_dataset_config"].read_text(encoding="utf-8"))
    features = list(v3_config["model_features"])
    if canonical_json_sha256(features) != str(
        config["expected"]["model_feature_sha256"]
    ):
        raise ValueError("Verified feature surface changed")
    source = prepare_dataset(
        pd.read_parquet(input_paths["v3_action_dataset"]), config, features
    ).set_index("candidate_id", drop=False)
    policies = pd.read_parquet(output / config["outputs"]["calibration_policies"])
    predictions = pd.read_parquet(output / config["outputs"]["predictions"])
    selected = pd.read_parquet(output / config["outputs"]["selected_events"])
    baseline = pd.read_parquet(output / config["outputs"]["baseline_events"])
    comparison = pd.read_parquet(output / config["outputs"]["event_comparison"])
    fold_metrics = pd.read_parquet(output / config["outputs"]["fold_metrics"])
    family_metrics = json.loads(
        (output / config["outputs"]["family_metrics"]).read_text(encoding="utf-8")
    )
    bootstrap_result = json.loads(
        (output / config["outputs"]["bootstrap_result"]).read_text(encoding="utf-8")
    )
    acceptance = json.loads(
        (output / config["outputs"]["acceptance"]).read_text(encoding="utf-8")
    )
    result = json.loads(
        (output / config["outputs"]["result_json"]).read_text(encoding="utf-8")
    )
    lanes = list(config["lane_ownership"]["priority"])
    folds = list(config["expected"]["folds"])
    chosen = policies.loc[policies["chosen"]]
    if len(chosen) != len(lanes) * len(folds):
        raise ValueError("Expected one chosen policy per lane/fold")
    if predictions["candidate_id"].duplicated().any():
        raise ValueError("Out-of-time action predictions are duplicated")
    if selected.duplicated(["fold_id", "model_lane", "event_id"]).any():
        raise ValueError("Selected events are duplicated")
    if baseline.duplicated(["fold_id", "model_lane", "event_id"]).any():
        raise ValueError("Baseline events are duplicated")
    predicted_selected = set(predictions.loc[predictions["selected"], "candidate_id"])
    if predicted_selected != set(selected["candidate_id"]):
        raise ValueError("Selected-event ledger does not match predictions")

    model_records = manifest["artifacts"]["models"]
    model_lookup = {Path(record["path"]).name: record for record in model_records}
    for policy in chosen.itertuples(index=False):
        name = f"{policy.model_lane}_{policy.fold_id}_{policy.model_id}.joblib"
        record = model_lookup.get(name)
        if record is None:
            raise ValueError(f"Missing serialized chosen model: {name}")
        model = joblib.load(REPO_ROOT / record["path"])
        stored = predictions.loc[
            predictions["model_lane"].eq(policy.model_lane)
            & predictions["fold_id"].eq(policy.fold_id)
        ].sort_values("candidate_id", kind="mergesort")
        replay_source = source.loc[stored["candidate_id"]].reset_index(drop=True)
        if replay_source["candidate_id"].tolist() != stored["candidate_id"].tolist():
            raise ValueError(f"Replay candidate order mismatch: {name}")
        replay = predict_model(model, replay_source, features)
        if not np.allclose(
            replay, stored["model_score"].to_numpy(), rtol=1e-12, atol=1e-12
        ):
            raise ValueError(f"Serialized model replay mismatch: {name}")

    windows = fold_windows(v3_config)
    all_start = min(windows[fold]["TEST"][0] for fold in folds)
    all_end = max(windows[fold]["TEST"][1] for fold in folds)
    top_removed = int(config["acceptance_gates"]["top_winners_removed"])
    for lane_index, lane in enumerate(lanes):
        selected_lane = selected.loc[selected["model_lane"].eq(lane)]
        baseline_lane = baseline.loc[baseline["model_lane"].eq(lane)]
        comparison_lane = comparison.loc[comparison["model_lane"].eq(lane)]
        selected_metrics = economic_metrics(
            selected_lane, start=all_start, end=all_end, top_winners_removed=top_removed
        )
        baseline_metrics = economic_metrics(
            baseline_lane, start=all_start, end=all_end, top_winners_removed=top_removed
        )
        for key, value in selected_metrics.items():
            close(
                value, family_metrics[lane]["selected"][key], f"{lane}.selected.{key}"
            )
        for key, value in baseline_metrics.items():
            close(
                value, family_metrics[lane]["baseline"][key], f"{lane}.baseline.{key}"
            )
        replay_bootstrap = bootstrap_comparison(
            comparison_lane,
            resamples=int(config["bootstrap"]["resamples"]),
            confidence=float(config["bootstrap"]["confidence"]),
            seed=int(config["bootstrap"]["seed"]) + lane_index,
        )
        for metric in (
            "selected_mean_stress_r",
            "common_event_action_uplift_r",
            "total_policy_delta_r_per_episode",
        ):
            for bound in ("lower", "median", "upper"):
                close(
                    replay_bootstrap[metric][bound],
                    bootstrap_result[lane][metric][bound],
                    f"{lane}.bootstrap.{metric}.{bound}",
                )
        checks = acceptance_checks(
            family_metrics[lane], bootstrap_result[lane], config["acceptance_gates"]
        )
        if checks != acceptance[lane]["checks"]:
            raise ValueError(f"Acceptance replay mismatch for {lane}")

    runtime_keys = (
        "portfolio_simulation_authorized",
        "python_serving_authorized",
        "ml_shadow_authorized",
        "ea_consumption_authorized",
        "demo_authorized",
        "live_authorized",
        "broker_action_authorized",
    )
    if any(config["authorization"][key] for key in runtime_keys):
        raise ValueError("A runtime authorization is unexpectedly enabled")
    if result["runtime_changed"] or result["ml_shadow_or_execution_activated"]:
        raise ValueError("Result claims a forbidden runtime change")
    if len(fold_metrics) != len(lanes) * len(folds):
        raise ValueError("Fold metric count changed")
    print(
        json.dumps(
            {
                "decision": "ACTION_V3_VERIFICATION_PASS",
                "evidence_decision": result["decision"],
                "models_replayed": len(model_records),
                "prediction_rows": len(predictions),
                "selected_events": len(selected),
                "manifest_sha256": sha256_file(manifest_path),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

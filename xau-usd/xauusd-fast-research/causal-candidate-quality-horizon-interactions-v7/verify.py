from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from run_evaluation import (
    acceptance_checks,
    fold_windows,
    incremental_checks,
    partition_for,
    policy_rank,
    verify_lock,
)
from src.action_models import (
    apply_fixed_action_cascade,
    bootstrap_comparison,
    calibration_checks,
    canonical_json_sha256,
    choose_best_action,
    economic_metrics,
    fixed_action_ranking,
    prepare_dataset,
    sha256_file,
)
from src.adaptive_models import (
    assert_adaptive_v5_parity,
    build_result_comparison,
    fit_adaptive_model,
    predict_adaptive_model,
)
from src.interaction_features import (
    add_action_interactions,
    event_feature_columns,
    interaction_feature_columns,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "horizon_interactions_v7.json"


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
    lock = json.loads(
        (output / config["outputs"]["contract_lock"]).read_text(encoding="utf-8")
    )
    verify_lock(config, lock)
    manifest_path = output / config["outputs"]["manifest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["definition_contract_sha256"] != lock["definition_contract_sha256"]:
        raise ValueError("Horizon V7 manifest references a different contract")
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
    v4_config = json.loads(input_paths["v4_dataset_config"].read_text(encoding="utf-8"))
    reference_config = json.loads(
        input_paths["reference_adaptive_v5_config"].read_text(encoding="utf-8")
    )
    reference_result = json.loads(
        input_paths["reference_adaptive_v5_result"].read_text(encoding="utf-8")
    )
    base_method_hash = assert_adaptive_v5_parity(config, reference_config)
    if base_method_hash != lock["base_method_contract_sha256"]:
        raise ValueError("Verified Horizon V7 base method contract changed")
    base_features = list(v4_config["model_features"])
    interactions = interaction_feature_columns(base_features)
    features = [*base_features, *interactions]
    if canonical_json_sha256(features) != str(
        config["expected"]["model_feature_sha256"]
    ):
        raise ValueError("Verified feature surface changed")
    source = prepare_dataset(
        pd.read_parquet(input_paths["v4_action_dataset"]), config, base_features
    )
    source, generated_interactions = add_action_interactions(source, base_features)
    if generated_interactions != interactions:
        raise ValueError("Verified Horizon V7 interaction order changed")
    inventory = json.loads(
        (output / config["outputs"]["interaction_inventory"]).read_text(
            encoding="utf-8"
        )
    )
    if inventory != {
        "base_features": base_features,
        "event_features": event_feature_columns(base_features),
        "interaction_features": interactions,
        "model_features": features,
    }:
        raise ValueError("Horizon V7 interaction inventory changed")
    source_lookup = source.set_index("candidate_id", drop=False)
    splits = pd.read_parquet(input_paths["v4_split_assignments"])
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
    comparison_v5 = json.loads(
        (output / config["outputs"]["comparison_v5"]).read_text(encoding="utf-8")
    )
    if comparison_v5 != build_result_comparison(result, reference_result):
        raise ValueError("Horizon V7 versus Adaptive V5 comparison replay mismatch")
    lanes = list(config["lane_ownership"]["priority"])
    folds = list(config["expected"]["folds"])
    chosen = policies.loc[policies["chosen"]]
    if len(policies) != int(config["expected"]["calibration_policy_rows"]):
        raise ValueError("Horizon V7 calibration policy count changed")
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

    top_removed = int(config["acceptance_gates"]["top_winners_removed"])
    variant_order = {
        str(spec["variant_id"]): index
        for index, spec in enumerate(config["training_variants"])
    }
    variants = {str(spec["variant_id"]): spec for spec in config["training_variants"]}
    windows = fold_windows(v4_config)
    refitted_models: dict[tuple[str, str, str], Any] = {}
    for lane in lanes:
        for fold_id in folds:
            fit = partition_for(
                source, splits, fold_id=fold_id, lane=lane, partition="FIT"
            )
            calibration = partition_for(
                source,
                splits,
                fold_id=fold_id,
                lane=lane,
                partition="CALIBRATION",
            )
            action_ranking, _ = fixed_action_ranking(
                calibration, config["action_tie_order"]
            )
            baseline_cal = apply_fixed_action_cascade(calibration, action_ranking)
            cal_start, cal_end = windows[fold_id]["CALIBRATION"]
            baseline_metrics = economic_metrics(
                baseline_cal,
                start=cal_start,
                end=cal_end,
                top_winners_removed=top_removed,
            )
            replay_rows: list[dict[str, Any]] = []
            for variant_id, variant in variants.items():
                model = fit_adaptive_model(
                    fit,
                    features=features,
                    config=config,
                    variant=variant,
                    fit_boundary=cal_start,
                )
                refitted_models[(lane, fold_id, variant_id)] = model
                scored = calibration.copy()
                scored["model_score"] = predict_adaptive_model(model, scored, features)
                best = choose_best_action(scored)
                for quantile in config["retention_quantiles"]:
                    threshold = float(best["model_score"].quantile(float(quantile)))
                    selected_cal = best.loc[best["model_score"].ge(threshold)]
                    fraction = float(
                        selected_cal["event_id"].nunique()
                        / baseline_cal["event_id"].nunique()
                    )
                    metrics = economic_metrics(
                        selected_cal,
                        start=cal_start,
                        end=cal_end,
                        top_winners_removed=top_removed,
                    )
                    checks = calibration_checks(
                        metrics,
                        baseline_metrics,
                        fraction,
                        config["calibration_gates"],
                    )
                    objective = float(
                        metrics["weighted_r_sum"]
                        - float(
                            config["calibration_gates"]["selection_drawdown_penalty"]
                        )
                        * metrics["weighted_max_drawdown_r"]
                    )
                    replay_row = {
                        "variant_id": variant_id,
                        "retention_quantile": float(quantile),
                        "score_threshold": threshold,
                        "selected_fraction": fraction,
                        "selection_objective": objective,
                        "calibration_gate_pass": bool(all(checks.values())),
                    }
                    replay_rows.append(replay_row)
                    stored_policy = policies.loc[
                        policies["model_lane"].eq(lane)
                        & policies["fold_id"].eq(fold_id)
                        & policies["variant_id"].eq(variant_id)
                        & policies["retention_quantile"].eq(float(quantile))
                    ]
                    if len(stored_policy) != 1:
                        raise ValueError("Horizon V7 calibration policy key mismatch")
                    stored_row = stored_policy.iloc[0]
                    close(
                        threshold,
                        stored_row["score_threshold"],
                        f"{lane}.{fold_id}.{variant_id}.threshold",
                    )
                    close(
                        fraction,
                        stored_row["selected_fraction"],
                        f"{lane}.{fold_id}.{variant_id}.fraction",
                    )
                    close(
                        objective,
                        stored_row["selection_objective"],
                        f"{lane}.{fold_id}.{variant_id}.objective",
                    )
                    if bool(stored_row["calibration_gate_pass"]) != bool(
                        all(checks.values())
                    ):
                        raise ValueError("Horizon V7 calibration gate replay mismatch")
                    if (
                        json.loads(stored_row["fit_metadata_json"])
                        != model.fit_metadata
                    ):
                        raise ValueError("Horizon V7 fit metadata replay mismatch")
            eligible = [row for row in replay_rows if row["calibration_gate_pass"]]
            replay_chosen = sorted(
                eligible if eligible else replay_rows,
                key=lambda row: policy_rank(row, variant_order),
            )[0]
            stored_chosen = chosen.loc[
                chosen["model_lane"].eq(lane) & chosen["fold_id"].eq(fold_id)
            ]
            if len(stored_chosen) != 1:
                raise ValueError("Horizon V7 chosen policy key mismatch")
            chosen_row = stored_chosen.iloc[0]
            if (
                chosen_row["variant_id"] != replay_chosen["variant_id"]
                or float(chosen_row["retention_quantile"])
                != replay_chosen["retention_quantile"]
                or bool(chosen_row["diagnostic_fallback"]) != (not bool(eligible))
            ):
                raise ValueError("Horizon V7 chosen policy replay mismatch")

    model_records = manifest["artifacts"]["models"]
    model_lookup = {Path(record["path"]).name: record for record in model_records}
    for policy in chosen.itertuples(index=False):
        name = f"{policy.model_lane}_{policy.fold_id}_{policy.variant_id}.joblib"
        record = model_lookup.get(name)
        if record is None:
            raise ValueError(f"Missing serialized chosen model: {name}")
        model = joblib.load(REPO_ROOT / record["path"])
        stored = predictions.loc[
            predictions["model_lane"].eq(policy.model_lane)
            & predictions["fold_id"].eq(policy.fold_id)
        ].sort_values("candidate_id", kind="mergesort")
        replay_source = source_lookup.loc[stored["candidate_id"]].reset_index(drop=True)
        if replay_source["candidate_id"].tolist() != stored["candidate_id"].tolist():
            raise ValueError(f"Replay candidate order mismatch: {name}")
        replay = predict_adaptive_model(model, replay_source, features)
        if not np.allclose(
            replay, stored["model_score"].to_numpy(), rtol=1e-12, atol=1e-12
        ):
            raise ValueError(f"Serialized model replay mismatch: {name}")
        refitted = refitted_models[
            (policy.model_lane, policy.fold_id, policy.variant_id)
        ]
        refitted_scores = predict_adaptive_model(refitted, replay_source, features)
        if not np.allclose(
            refitted_scores,
            stored["model_score"].to_numpy(),
            rtol=1e-12,
            atol=1e-12,
        ):
            raise ValueError(f"Independent model refit mismatch: {name}")
        scored = replay_source.copy()
        scored["model_score"] = refitted_scores
        best = choose_best_action(scored)
        expected_chosen = set(best["candidate_id"])
        stored_chosen = set(stored.loc[stored["chosen_action"], "candidate_id"])
        if expected_chosen != stored_chosen:
            raise ValueError(f"Chosen-action replay mismatch: {name}")
        expected_selected = set(
            best.loc[
                best["model_score"].ge(float(policy.score_threshold)), "candidate_id"
            ]
        )
        stored_selected = set(stored.loc[stored["selected"], "candidate_id"])
        if expected_selected != stored_selected:
            raise ValueError(f"Threshold-selection replay mismatch: {name}")

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
        checks.update(
            incremental_checks(
                family_metrics[lane],
                reference_result["families"][lane]["metrics"],
                config["incremental_gates_vs_v5"],
            )
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
                "decision": "HORIZON_V7_VERIFICATION_PASS",
                "evidence_decision": result["decision"],
                "models_replayed": len(model_records),
                "calibration_models_independently_refit": len(refitted_models),
                "calibration_policies_replayed": len(policies),
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

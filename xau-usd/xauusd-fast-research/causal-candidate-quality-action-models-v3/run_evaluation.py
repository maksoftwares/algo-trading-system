from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from src.action_models import (
    apply_fixed_action_cascade,
    bootstrap_comparison,
    build_event_comparison,
    calibration_checks,
    choose_best_action,
    comparison_metrics,
    economic_metrics,
    fit_model,
    fixed_action_ranking,
    predict_model,
    prepare_dataset,
    resolve_inputs,
    sha256_file,
    weighted_auc,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "action_models_v3.json"


def verify_lock(config: dict[str, Any], lock: dict[str, Any]) -> None:
    if sha256_file(CONFIG_PATH) != lock["config_sha256"]:
        raise ValueError("Action V3 configuration changed after lock")
    if sha256_file(ROOT / "PREREGISTRATION.md") != lock["preregistration_sha256"]:
        raise ValueError("Action V3 preregistration changed after lock")
    for name, spec in lock["implementation"].items():
        path = REPO_ROOT / str(spec["path"])
        if sha256_file(path) != str(spec["sha256"]):
            raise ValueError(f"Action V3 implementation changed after lock: {name}")


def flatten(prefix: str, value: dict[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": item for key, item in value.items()}


def fold_windows(
    v3_config: dict[str, Any],
) -> dict[str, dict[str, tuple[pd.Timestamp, pd.Timestamp]]]:
    result: dict[str, dict[str, tuple[pd.Timestamp, pd.Timestamp]]] = {}
    for fold in v3_config["folds"]:
        result[str(fold["fold_id"])] = {
            "FIT": tuple(pd.Timestamp(value) for value in fold["fit"]),
            "CALIBRATION": tuple(pd.Timestamp(value) for value in fold["calibration"]),
            "TEST": tuple(pd.Timestamp(value) for value in fold["test"]),
        }
    return result


def build_availability(
    dataset: pd.DataFrame, splits: pd.DataFrame, fold_ids: list[str]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for fold_id in fold_ids:
        assignment = splits.loc[splits["fold_id"].eq(fold_id) & splits["eligible"]][
            ["structural_episode_id", "partition"]
        ]
        joined = dataset.merge(
            assignment, on="structural_episode_id", how="inner", validate="many_to_one"
        )
        for (lane, partition, action), group in joined.groupby(
            ["model_lane", "partition", "action_id"], sort=True
        ):
            rows.append(
                {
                    "fold_id": fold_id,
                    "model_lane": lane,
                    "partition": partition,
                    "action_id": action,
                    "action_rows": int(len(group)),
                    "events": int(group["event_id"].nunique()),
                    "episodes": int(group["structural_episode_id"].nunique()),
                    "stressed_winners": int(group["stress_net_r_positive"].sum()),
                    "excluded_shock_rows": int(
                        group["regime"].eq("UNSAFE_SHOCK").sum()
                    ),
                }
            )
    return pd.DataFrame(rows)


def partition_for(
    dataset: pd.DataFrame,
    splits: pd.DataFrame,
    *,
    fold_id: str,
    lane: str,
    partition: str,
) -> pd.DataFrame:
    episodes = splits.loc[
        splits["fold_id"].eq(fold_id)
        & splits["partition"].eq(partition)
        & splits["eligible"],
        "structural_episode_id",
    ]
    return dataset.loc[
        dataset["structural_episode_id"].isin(episodes)
        & dataset["model_lane"].eq(lane)
        & dataset["model_eligible"]
    ].copy()


def policy_rank(row: dict[str, Any], model_order: dict[str, int]) -> tuple[Any, ...]:
    return (
        -float(row["selection_objective"]),
        -float(row["selected_fraction"]),
        model_order[str(row["model_id"])],
        float(row["retention_quantile"]),
    )


def acceptance_checks(
    metrics: dict[str, Any],
    bootstrap: dict[str, Any],
    gates: dict[str, Any],
) -> dict[str, bool]:
    selected_pf = metrics["selected"]["weighted_profit_factor"]
    latest_pf = metrics["latest_fold"]["selected_weighted_profit_factor"]
    retention = metrics["comparison"]["baseline_r_retention"]
    drawdown_ratio = metrics["drawdown_ratio_to_baseline"]
    return {
        "minimum_evaluated_folds": metrics["evaluated_folds"]
        >= int(gates["minimum_evaluated_folds"]),
        "minimum_calibration_passed_folds": metrics["calibration_passed_folds"]
        >= int(gates["minimum_calibration_passed_folds"]),
        "minimum_test_events": metrics["baseline"]["events"]
        >= int(gates["minimum_test_events"]),
        "minimum_selected_events": metrics["selected"]["events"]
        >= int(gates["minimum_selected_events"]),
        "minimum_selected_fraction": metrics["selected_fraction"]
        >= float(gates["minimum_selected_fraction"]),
        "maximum_selected_fraction": metrics["selected_fraction"]
        <= float(gates["maximum_selected_fraction"]),
        "minimum_selected_events_per_weekday": metrics["selected"]["events_per_weekday"]
        >= float(gates["minimum_selected_events_per_weekday"]),
        "minimum_selected_mean_stress_r": metrics["selected"]["weighted_mean_stress_r"]
        >= float(gates["minimum_selected_mean_stress_r"]),
        "minimum_selected_profit_factor": selected_pf is not None
        and float(selected_pf) >= float(gates["minimum_selected_profit_factor"]),
        "minimum_selected_mean_ci_lower_r": bootstrap["selected_mean_stress_r"]["lower"]
        > float(gates["minimum_selected_mean_ci_lower_r"]),
        "minimum_common_event_action_uplift_ci_lower_r": bootstrap[
            "common_event_action_uplift_r"
        ]["lower"]
        > float(gates["minimum_common_event_action_uplift_ci_lower_r"]),
        "minimum_total_policy_delta_ci_lower_r_per_episode": bootstrap[
            "total_policy_delta_r_per_episode"
        ]["lower"]
        >= float(gates["minimum_total_policy_delta_ci_lower_r_per_episode"]),
        "minimum_baseline_r_retention": retention is not None
        and float(retention) >= float(gates["minimum_baseline_r_retention"]),
        "maximum_drawdown_ratio_to_baseline": drawdown_ratio is not None
        and float(drawdown_ratio) <= float(gates["maximum_drawdown_ratio_to_baseline"]),
        "minimum_positive_folds": metrics["positive_folds"]
        >= int(gates["minimum_positive_folds"]),
        "minimum_weighted_test_auc": metrics["weighted_test_auc"] is not None
        and float(metrics["weighted_test_auc"])
        >= float(gates["minimum_weighted_test_auc"]),
        "minimum_latest_fold_mean_stress_r": metrics["latest_fold"][
            "selected_weighted_mean_stress_r"
        ]
        >= float(gates["minimum_latest_fold_mean_stress_r"]),
        "minimum_latest_fold_profit_factor": latest_pf is not None
        and float(latest_pf) >= float(gates["minimum_latest_fold_profit_factor"]),
        "minimum_latest_fold_common_event_uplift_r": metrics["latest_fold"][
            "common_event_action_uplift_r"
        ]
        >= float(gates["minimum_latest_fold_common_event_uplift_r"]),
        "top_winners_removed_positive": metrics["selected"][
            "top_winners_removed_weighted_r_sum"
        ]
        > 0.0,
    }


def write_result_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Action Models V3 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Lane | Decision | Test events | Selected | Coverage | PF | Mean R | AUC | Quality uplift R |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for lane, value in result["families"].items():
        metrics = value["metrics"]
        pf = metrics["selected"]["weighted_profit_factor"]
        auc = metrics["weighted_test_auc"]
        lines.append(
            f"| {lane} | {value['decision']} | {metrics['baseline']['events']} | "
            f"{metrics['selected']['events']} | {metrics['selected_fraction']:.3f} | "
            f"{('n/a' if pf is None else f'{pf:.3f}')} | "
            f"{metrics['selected']['weighted_mean_stress_r']:.4f} | "
            f"{('n/a' if auc is None else f'{auc:.4f}')} | "
            f"{metrics['comparison']['common_event_action_uplift_r']:.4f} |"
        )
    lines.extend(
        [
            "",
            "All results are offline and development-only on previously exposed history.",
            "No model has MT5, shadow, demo, live, sizing, or broker authority.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    output = ROOT / config["outputs"]["directory"]
    lock_path = output / config["outputs"]["contract_lock"]
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before Action V3 evaluation")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    verify_lock(config, lock)
    inputs = resolve_inputs(REPO_ROOT, config)
    v3_config = json.loads(inputs["v3_dataset_config"].read_text(encoding="utf-8"))
    features = list(v3_config["model_features"])
    if lock["model_feature_sha256"] != lock["expected_model_feature_sha256"]:
        raise ValueError("Locked Action V3 feature hash is inconsistent")
    dataset = prepare_dataset(
        pd.read_parquet(inputs["v3_action_dataset"]), config, features
    )
    splits = pd.read_parquet(inputs["v3_split_assignments"])
    fold_ids = list(config["expected"]["folds"])
    if sorted(splits["fold_id"].unique()) != sorted(fold_ids):
        raise ValueError("V3 split fold IDs changed")
    windows = fold_windows(v3_config)
    lanes = list(config["lane_ownership"]["priority"])
    model_order = {
        str(spec["model_id"]): index for index, spec in enumerate(config["models"])
    }
    gates = config["calibration_gates"]
    top_removed = int(config["acceptance_gates"]["top_winners_removed"])

    output.mkdir(parents=True, exist_ok=True)
    models_dir = output / config["outputs"]["models_directory"]
    models_dir.mkdir(parents=True, exist_ok=True)
    availability = build_availability(dataset, splits, fold_ids)

    policy_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []
    selected_frames: list[pd.DataFrame] = []
    baseline_frames: list[pd.DataFrame] = []
    comparison_frames: list[pd.DataFrame] = []
    fold_metric_rows: list[dict[str, Any]] = []
    model_paths: list[Path] = []

    for lane in lanes:
        for fold_id in fold_ids:
            fit = partition_for(
                dataset, splits, fold_id=fold_id, lane=lane, partition="FIT"
            )
            calibration = partition_for(
                dataset,
                splits,
                fold_id=fold_id,
                lane=lane,
                partition="CALIBRATION",
            )
            test = partition_for(
                dataset, splits, fold_id=fold_id, lane=lane, partition="TEST"
            )
            if len(fit) < int(gates["minimum_fit_action_rows"]):
                raise ValueError(f"Insufficient fit rows for {lane} {fold_id}")
            if calibration["event_id"].nunique() < int(
                gates["minimum_calibration_events"]
            ):
                raise ValueError(
                    f"Insufficient calibration events for {lane} {fold_id}"
                )
            action_ranking, action_ranking_rows = fixed_action_ranking(
                calibration, config["action_tie_order"]
            )
            baseline_cal = apply_fixed_action_cascade(calibration, action_ranking)
            cal_start, cal_end = windows[fold_id]["CALIBRATION"]
            baseline_cal_metrics = economic_metrics(
                baseline_cal,
                start=cal_start,
                end=cal_end,
                top_winners_removed=top_removed,
            )
            fitted_models: dict[str, Any] = {}
            fold_policies: list[dict[str, Any]] = []
            for spec in config["models"]:
                model_id = str(spec["model_id"])
                model = fit_model(fit, features=features, spec=spec)
                fitted_models[model_id] = model
                scored_cal = calibration.copy()
                scored_cal["model_score"] = predict_model(model, scored_cal, features)
                best_cal = choose_best_action(scored_cal)
                for quantile in config["retention_quantiles"]:
                    threshold = float(best_cal["model_score"].quantile(float(quantile)))
                    selected_cal = best_cal.loc[
                        best_cal["model_score"].ge(threshold)
                    ].copy()
                    selected_fraction = float(
                        selected_cal["event_id"].nunique()
                        / baseline_cal["event_id"].nunique()
                    )
                    selected_metrics = economic_metrics(
                        selected_cal,
                        start=cal_start,
                        end=cal_end,
                        top_winners_removed=top_removed,
                    )
                    checks = calibration_checks(
                        selected_metrics,
                        baseline_cal_metrics,
                        selected_fraction,
                        gates,
                    )
                    row = {
                        "fold_id": fold_id,
                        "model_lane": lane,
                        "model_id": model_id,
                        "retention_quantile": float(quantile),
                        "score_threshold": threshold,
                        "selected_fraction": selected_fraction,
                        "selection_objective": float(
                            selected_metrics["weighted_r_sum"]
                            - float(gates["selection_drawdown_penalty"])
                            * selected_metrics["weighted_max_drawdown_r"]
                        ),
                        "calibration_gate_pass": bool(all(checks.values())),
                        "calibration_checks_json": json.dumps(
                            checks, sort_keys=True, separators=(",", ":")
                        ),
                        "baseline_action_ranking_json": json.dumps(action_ranking),
                        "baseline_action_statistics_json": json.dumps(
                            action_ranking_rows, sort_keys=True, separators=(",", ":")
                        ),
                        **flatten("selected", selected_metrics),
                        **flatten("baseline", baseline_cal_metrics),
                    }
                    fold_policies.append(row)
            eligible = [row for row in fold_policies if row["calibration_gate_pass"]]
            chosen = sorted(
                eligible if eligible else fold_policies,
                key=lambda row: policy_rank(row, model_order),
            )[0]
            chosen["chosen"] = True
            chosen["diagnostic_fallback"] = not bool(eligible)
            for row in fold_policies:
                if row is not chosen:
                    row["chosen"] = False
                    row["diagnostic_fallback"] = False
            policy_rows.extend(fold_policies)

            model_id = str(chosen["model_id"])
            model = fitted_models[model_id]
            model_path = models_dir / f"{lane}_{fold_id}_{model_id}.joblib"
            joblib.dump(model, model_path)
            model_paths.append(model_path)
            scored_test = test.copy()
            scored_test["model_score"] = predict_model(model, scored_test, features)
            best_test = choose_best_action(scored_test)
            selected_test = best_test.loc[
                best_test["model_score"].ge(float(chosen["score_threshold"]))
            ].copy()
            baseline_test = apply_fixed_action_cascade(test, action_ranking)
            test_start, test_end = windows[fold_id]["TEST"]
            selected_metrics = economic_metrics(
                selected_test,
                start=test_start,
                end=test_end,
                top_winners_removed=top_removed,
            )
            baseline_metrics = economic_metrics(
                baseline_test,
                start=test_start,
                end=test_end,
                top_winners_removed=top_removed,
            )
            selected_fraction = float(
                selected_test["event_id"].nunique()
                / baseline_test["event_id"].nunique()
            )
            comparison = build_event_comparison(
                selected_test, baseline_test, lane=lane, fold_id=fold_id
            )
            comparison_value = comparison_metrics(comparison)
            fold_auc = weighted_auc(scored_test)
            fold_metric_rows.append(
                {
                    "fold_id": fold_id,
                    "model_lane": lane,
                    "model_id": model_id,
                    "calibration_gate_pass": bool(chosen["calibration_gate_pass"]),
                    "diagnostic_fallback": bool(chosen["diagnostic_fallback"]),
                    "score_threshold": float(chosen["score_threshold"]),
                    "retention_quantile": float(chosen["retention_quantile"]),
                    "fit_action_rows": int(len(fit)),
                    "calibration_action_rows": int(len(calibration)),
                    "test_action_rows": int(len(test)),
                    "test_action_weight_sum": float(test["structural_weight"].sum()),
                    "weighted_test_auc": fold_auc,
                    "selected_fraction": selected_fraction,
                    **flatten("selected", selected_metrics),
                    **flatten("baseline", baseline_metrics),
                    **comparison_value,
                }
            )
            chosen_ids = set(selected_test["candidate_id"])
            scored_test["fold_id"] = fold_id
            scored_test["selected"] = scored_test["candidate_id"].isin(chosen_ids)
            scored_test["chosen_action"] = scored_test["candidate_id"].isin(
                set(best_test["candidate_id"])
            )
            scored_test["chosen_model_id"] = model_id
            scored_test["score_threshold"] = float(chosen["score_threshold"])
            prediction_frames.append(
                scored_test[
                    [
                        "fold_id",
                        "model_lane",
                        "candidate_id",
                        "event_id",
                        "structural_episode_id",
                        "signal_time",
                        "action_id",
                        "stress_net_r",
                        "stress_net_r_positive",
                        "structural_weight",
                        "event_eval_weight",
                        "model_score",
                        "chosen_action",
                        "selected",
                        "chosen_model_id",
                        "score_threshold",
                    ]
                ].copy()
            )
            selected_test["fold_id"] = fold_id
            selected_test["chosen_model_id"] = model_id
            selected_test["score_threshold"] = float(chosen["score_threshold"])
            baseline_test["fold_id"] = fold_id
            baseline_test["baseline_action_ranking_json"] = json.dumps(action_ranking)
            selected_frames.append(selected_test)
            baseline_frames.append(baseline_test)
            comparison_frames.append(comparison)

    policies = pd.DataFrame(policy_rows).sort_values(
        ["model_lane", "fold_id", "model_id", "retention_quantile"],
        kind="mergesort",
    )
    predictions = pd.concat(prediction_frames, ignore_index=True)
    selected_all = pd.concat(selected_frames, ignore_index=True)
    baseline_all = pd.concat(baseline_frames, ignore_index=True)
    comparisons = pd.concat(comparison_frames, ignore_index=True)
    fold_metrics = pd.DataFrame(fold_metric_rows).sort_values(
        ["model_lane", "fold_id"], kind="mergesort"
    )

    family_results: dict[str, Any] = {}
    bootstrap_results: dict[str, Any] = {}
    acceptance: dict[str, Any] = {}
    all_test_start = min(windows[fold_id]["TEST"][0] for fold_id in fold_ids)
    all_test_end = max(windows[fold_id]["TEST"][1] for fold_id in fold_ids)
    latest_fold = fold_ids[-1]
    for lane_index, lane in enumerate(lanes):
        selected_lane = selected_all.loc[selected_all["model_lane"].eq(lane)]
        baseline_lane = baseline_all.loc[baseline_all["model_lane"].eq(lane)]
        comparison_lane = comparisons.loc[comparisons["model_lane"].eq(lane)]
        folds_lane = fold_metrics.loc[fold_metrics["model_lane"].eq(lane)]
        selected_metrics = economic_metrics(
            selected_lane,
            start=all_test_start,
            end=all_test_end,
            top_winners_removed=top_removed,
        )
        baseline_metrics = economic_metrics(
            baseline_lane,
            start=all_test_start,
            end=all_test_end,
            top_winners_removed=top_removed,
        )
        comparison_value = comparison_metrics(comparison_lane)
        bootstrap = bootstrap_comparison(
            comparison_lane,
            resamples=int(config["bootstrap"]["resamples"]),
            confidence=float(config["bootstrap"]["confidence"]),
            seed=int(config["bootstrap"]["seed"]) + lane_index,
        )
        bootstrap_results[lane] = bootstrap
        auc_valid = folds_lane["weighted_test_auc"].notna()
        weighted_test_auc = (
            float(
                np.average(
                    folds_lane.loc[auc_valid, "weighted_test_auc"],
                    weights=folds_lane.loc[auc_valid, "test_action_weight_sum"],
                )
            )
            if auc_valid.any()
            else None
        )
        latest = folds_lane.loc[folds_lane["fold_id"].eq(latest_fold)].iloc[0]
        drawdown_ratio = (
            float(
                selected_metrics["weighted_max_drawdown_r"]
                / baseline_metrics["weighted_max_drawdown_r"]
            )
            if baseline_metrics["weighted_max_drawdown_r"] > 0
            else None
        )
        metrics = {
            "evaluated_folds": int(len(folds_lane)),
            "calibration_passed_folds": int(folds_lane["calibration_gate_pass"].sum()),
            "selected_fraction": float(
                selected_metrics["events"] / baseline_metrics["events"]
            ),
            "weighted_test_auc": weighted_test_auc,
            "positive_folds": int(
                folds_lane["selected_weighted_mean_stress_r"].gt(0.0).sum()
            ),
            "drawdown_ratio_to_baseline": drawdown_ratio,
            "selected": selected_metrics,
            "baseline": baseline_metrics,
            "comparison": comparison_value,
            "latest_fold": {
                "fold_id": latest_fold,
                "selected_weighted_mean_stress_r": float(
                    latest["selected_weighted_mean_stress_r"]
                ),
                "selected_weighted_profit_factor": latest[
                    "selected_weighted_profit_factor"
                ],
                "common_event_action_uplift_r": float(
                    latest["common_event_action_uplift_r"]
                ),
                "selected_fraction": float(latest["selected_fraction"]),
            },
        }
        checks = acceptance_checks(metrics, bootstrap, config["acceptance_gates"])
        decision = (
            "ACTION_MODEL_V3_LANE_GATE_PASS_DEVELOPMENT_ONLY"
            if all(checks.values())
            else "ACTION_MODEL_V3_LANE_GATE_FAIL"
        )
        acceptance[lane] = {
            "decision": decision,
            "checks": checks,
            "passed_checks": int(sum(checks.values())),
            "required_checks": len(checks),
            "runtime_authorized": False,
        }
        family_results[lane] = metrics

    passed = [
        lane
        for lane, value in acceptance.items()
        if value["decision"] == "ACTION_MODEL_V3_LANE_GATE_PASS_DEVELOPMENT_ONLY"
    ]
    decision = (
        "ACTION_MODEL_V3_FAMILY_GATES_PASS_DEVELOPMENT_ONLY"
        if passed
        else "ACTION_MODEL_V3_MODEL_EVIDENCE_GATE_FAIL"
    )
    result = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "passed_lanes": passed,
        "failed_lanes": [lane for lane in lanes if lane not in passed],
        "families": {
            lane: {
                "decision": acceptance[lane]["decision"],
                "metrics": family_results[lane],
                "checks": acceptance[lane]["checks"],
            }
            for lane in lanes
        },
        "historical_outcomes_already_exposed": True,
        "runtime_changed": False,
        "ml_shadow_or_execution_activated": False,
        "authorization": config["authorization"],
    }

    paths = {
        "contract_lock": lock_path,
        "availability": output / config["outputs"]["availability"],
        "calibration_policies": output / config["outputs"]["calibration_policies"],
        "predictions": output / config["outputs"]["predictions"],
        "selected_events": output / config["outputs"]["selected_events"],
        "baseline_events": output / config["outputs"]["baseline_events"],
        "event_comparison": output / config["outputs"]["event_comparison"],
        "fold_metrics": output / config["outputs"]["fold_metrics"],
        "family_metrics": output / config["outputs"]["family_metrics"],
        "bootstrap_result": output / config["outputs"]["bootstrap_result"],
        "acceptance": output / config["outputs"]["acceptance"],
        "result_json": output / config["outputs"]["result_json"],
        "result_md": output / config["outputs"]["result_md"],
    }
    availability.to_parquet(paths["availability"], index=False)
    policies.to_parquet(paths["calibration_policies"], index=False)
    predictions.to_parquet(paths["predictions"], index=False)
    selected_all.to_parquet(paths["selected_events"], index=False)
    baseline_all.to_parquet(paths["baseline_events"], index=False)
    comparisons.to_parquet(paths["event_comparison"], index=False)
    fold_metrics.to_parquet(paths["fold_metrics"], index=False)
    write_json(paths["family_metrics"], family_results)
    write_json(paths["bootstrap_result"], bootstrap_results)
    write_json(paths["acceptance"], acceptance)
    write_json(paths["result_json"], result)
    write_result_markdown(paths["result_md"], result)

    artifacts = {
        name: {
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": sha256_file(path),
        }
        for name, path in paths.items()
    }
    artifacts["models"] = [
        {
            "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": sha256_file(path),
        }
        for path in sorted(model_paths)
    ]
    manifest = {
        "schema_version": config["schema_version"],
        "decision": decision,
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "inputs": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for name, path in inputs.items()
        },
        "artifacts": artifacts,
        "counts": {
            "calibration_policies": len(policies),
            "test_action_predictions": len(predictions),
            "selected_events": len(selected_all),
            "baseline_events": len(baseline_all),
            "models": len(model_paths),
        },
        "authorization": config["authorization"],
    }
    manifest_path = output / config["outputs"]["manifest"]
    write_json(manifest_path, manifest)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

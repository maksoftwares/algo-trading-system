from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd
import sklearn

from step_3_common import sha256_file, stable_parquet, verify_bound_file, write_json
from step_4_bootstrap import primary_block_bootstrap
from step_4_metrics import (
    choose_threshold,
    economic_metrics,
    pooled_attribution,
    probability_metrics,
)
from step_4_model import (
    eligibility_mask,
    feature_names_for_blocks,
    fit_probability_model,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _weekdays_by_fold(step2b: Mapping[str, Any]) -> dict[str, int]:
    result: dict[str, int] = {}
    for fold in step2b["split_contract"]["outer_eras"]:
        start = np.datetime64(pd.Timestamp(fold["test_start"]).date(), "D")
        end = np.datetime64(pd.Timestamp(fold["test_end_exclusive"]).date(), "D")
        result[str(fold["fold_id"])] = int(np.busday_count(start, end))
    return result


def _flatten_metrics(
    *,
    fold_id: str,
    spec: Mapping[str, Any],
    feature_count: int,
    fit_rows: int,
    calibration_rows: int,
    test: pd.DataFrame,
    threshold: float,
    fit_prior: float,
    weekdays: int,
    inner_base_rows: int,
    inner_calibrator_rows: int,
    inner_purged_rows: int,
) -> dict[str, Any]:
    probability = probability_metrics(test)
    selected = economic_metrics(test, test["selected"], weekdays=weekdays)
    baseline = economic_metrics(test, np.ones(len(test), dtype=bool), weekdays=weekdays)
    constant = test.copy()
    constant["probability"] = fit_prior
    constant_metrics = probability_metrics(constant)
    row: dict[str, Any] = {
        "fold_id": fold_id,
        "model_id": str(spec["model_id"]),
        "role": str(spec["role"]),
        "feature_count": feature_count,
        "fit_rows": fit_rows,
        "calibration_rows": calibration_rows,
        "test_rows": len(test),
        "threshold": threshold,
        "fit_weighted_positive_prior": fit_prior,
        "inner_base_rows": inner_base_rows,
        "inner_calibrator_rows": inner_calibrator_rows,
        "inner_purged_rows": inner_purged_rows,
        **probability,
        "constant_prior_weighted_brier": constant_metrics["weighted_brier"],
        "constant_prior_weighted_log_loss": constant_metrics["weighted_log_loss"],
    }
    row.update({f"selected_{key}": value for key, value in selected.items()})
    row.update({f"baseline_{key}": value for key, value in baseline.items()})
    row["selected_minus_baseline_weighted_mean_stress_r"] = float(
        selected["weighted_mean_stress_r"]
    ) - float(baseline["weighted_mean_stress_r"])
    return row


def _pooled_metrics(
    predictions: pd.DataFrame,
    *,
    weekdays: int,
) -> dict[str, Any]:
    probability = probability_metrics(predictions)
    selected = economic_metrics(predictions, predictions["selected"], weekdays=weekdays)
    baseline = economic_metrics(
        predictions, np.ones(len(predictions), dtype=bool), weekdays=weekdays
    )
    constant = predictions.copy()
    constant["probability"] = constant["fit_weighted_positive_prior"]
    return {
        "probability": probability,
        "constant_fit_prior": probability_metrics(constant),
        "selected": selected,
        "baseline": baseline,
        "selected_minus_baseline_weighted_mean_stress_r": float(
            selected["weighted_mean_stress_r"]
        )
        - float(baseline["weighted_mean_stress_r"]),
        "attribution": pooled_attribution(predictions, ["family_id", "direction"]),
    }


def _journey_diagnostic(frame: pd.DataFrame) -> dict[str, Any]:
    resolved = frame["label_status"].str.startswith("RESOLVED_")
    local = frame.loc[resolved].copy()
    weights = local["candidate_action_weight"].to_numpy(dtype=float)
    target = local["stress_net_r_positive"].astype(float).to_numpy()
    weighted_win_rate = float(np.dot(weights, target) / weights.sum())
    groups: list[dict[str, Any]] = []
    for dimension in ("source_id", "regime", "action_id"):
        for value, group in local.groupby(dimension, dropna=False, sort=True):
            group_weights = group["candidate_action_weight"].to_numpy(dtype=float)
            group_target = group["stress_net_r_positive"].astype(float).to_numpy()
            groups.append(
                {
                    "dimension": dimension,
                    "value": str(value),
                    "rows": len(group),
                    "weighted_rows": float(group_weights.sum()),
                    "weighted_win_rate": float(
                        np.dot(group_weights, group_target) / group_weights.sum()
                    ),
                }
            )
    return {
        "schema_version": "xauusd_step_4_journey_label_diagnostic_v1",
        "action_rows": len(frame),
        "resolved_rows": int(resolved.sum()),
        "unresolved_rows": int((~resolved).sum()),
        "weighted_win_rate": weighted_win_rate,
        "groups": groups,
        "entered_primary_fit": False,
        "features_built_for_journey": False,
    }


def _acceptance(
    primary: pd.DataFrame,
    fold_metrics: pd.DataFrame,
    pooled: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    gates = contract["acceptance_gates"]
    selected = pooled["selected"]
    baseline = pooled["baseline"]
    probability = pooled["probability"]
    attribution = [
        row for row in pooled["attribution"] if row["dimension"] == "family_id"
    ]
    checks = {
        "pooled_weighted_roc_auc": probability["weighted_roc_auc"]
        >= float(gates["pooled_weighted_roc_auc_minimum"]),
        "pooled_weighted_roc_auc_ci": bootstrap["weighted_roc_auc"]["lower"]
        > float(gates["pooled_weighted_roc_auc_ci_lower_strictly_above"]),
        "selected_ev_ci": bootstrap["selected_weighted_mean_stress_r"]["lower"]
        > float(gates["selected_weighted_mean_stress_r_ci_lower_strictly_above"]),
        "delta_ev_ci": bootstrap["selected_minus_baseline_weighted_mean_stress_r"][
            "lower"
        ]
        > float(gates["selected_minus_baseline_mean_stress_r_ci_lower_strictly_above"]),
        "selected_profit_factor": float(selected["weighted_profit_factor"] or 0.0)
        >= float(gates["selected_weighted_profit_factor_minimum"]),
        "pooled_selected_fraction": float(selected["selected_fraction"])
        >= float(gates["pooled_selected_fraction_minimum"]),
        "minimum_fold_selected_fraction": float(
            fold_metrics["selected_selected_fraction"].min()
        )
        >= float(gates["minimum_fold_selected_fraction"]),
        "positive_selected_ev_folds": int(
            fold_metrics["selected_weighted_mean_stress_r"].gt(0.0).sum()
        )
        >= int(gates["minimum_positive_selected_ev_folds"]),
        "selected_drawdown": float(selected["weighted_max_drawdown_r"])
        <= float(baseline["weighted_max_drawdown_r"]),
        "weighted_ece": float(probability["weighted_ece"])
        <= float(gates["weighted_ece_maximum"]),
        "minimum_selected_rows": int(selected["rows"])
        >= int(gates["minimum_selected_rows"]),
        "family_concentration": max(
            (float(row["weight_fraction"]) for row in attribution), default=0.0
        )
        <= float(gates["maximum_single_family_selected_weight_fraction"]),
    }
    passed = all(checks.values())
    return {
        "schema_version": "xauusd_step_4_acceptance_gates_v1",
        "primary_model_id": contract["models"]["primary_model_id"],
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "required_checks": len(checks),
        "all_required": True,
        "decision": contract["decision_policy"]["pass"]
        if passed
        else contract["decision_policy"]["fail"],
        "runtime_authorized": False,
        "primary_test_rows": len(primary),
    }


def _artifact_manifest(
    output_dir: Path,
    repo_root: Path,
    *,
    decision: str,
    lock_sha256: str,
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "STEP_4_ARTIFACT_MANIFEST.json":
            continue
        artifacts[path.relative_to(output_dir).as_posix()] = {
            "path": path.relative_to(repo_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return {
        "schema_version": "xauusd_step_4_artifact_manifest_v1",
        "decision": decision,
        "contract_lock_sha256": lock_sha256,
        "scikit_learn_version": sklearn.__version__,
        "runtime_changed": False,
        "artifacts": artifacts,
    }


def run_step_4(
    repo_root: Path, package_root: Path, config_path: Path
) -> dict[str, Any]:
    contract = load_json(config_path)
    bound = {
        name: verify_bound_file(repo_root, spec, name)
        for name, spec in contract["bound_inputs"].items()
    }
    output_dir = package_root / str(contract["outputs"]["directory"])
    lock_path = output_dir / str(contract["outputs"]["contract_lock"])
    if not lock_path.is_file():
        raise ValueError("Step 4 contract must be locked before model fitting")
    lock = load_json(lock_path)
    if lock["definition"]["config_sha256"] != sha256_file(config_path):
        raise ValueError("Step 4 configuration changed after lock")
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        path = package_root / relative
        if sha256_file(path) != expected:
            raise ValueError(f"Step 4 implementation changed after lock: {path}")
    lock_sha = sha256_file(lock_path)
    step2b = load_json(bound["step_2b_contract"])
    dataset = pd.read_parquet(bound["step_3_dataset"])
    splits = pd.read_parquet(bound["step_3_splits"])
    journey = pd.read_parquet(bound["step_3_journey_labels"])
    if any(name.startswith("family_id_") for name in dataset.columns):
        raise ValueError("Step 3 dataset contains suffixed family IDs")
    if dataset["candidate_id"].duplicated().any():
        raise ValueError("Step 3 dataset candidate IDs are duplicated")

    assignment = splits.loc[
        splits["fold_id"].isin(contract["outer_evaluation"]["fold_ids"]),
        [
            "fold_id",
            "candidate_id",
            "assignment",
            "resolved_label",
            "dataset_eligible",
        ],
    ]
    frame = assignment.merge(dataset, on="candidate_id", validate="many_to_one")
    weekdays = _weekdays_by_fold(step2b)
    categorical = contract["preprocessing"]["categorical_features"]
    clip = float(contract["probability_calibration"]["clip_probability"])
    primary_id = str(contract["models"]["primary_model_id"])
    model_dir = output_dir / str(contract["outputs"]["model_directory"])
    model_dir.mkdir(parents=True, exist_ok=True)

    predictions: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    for spec in contract["models"]["specifications"]:
        model_id = str(spec["model_id"])
        feature_names = feature_names_for_blocks(step2b, spec["feature_blocks"])
        if any(name.startswith("gc_") for name in feature_names):
            raise ValueError(f"COMEX feature reached estimator {model_id}")
        for fold_id in contract["outer_evaluation"]["fold_ids"]:
            local = frame.loc[frame["fold_id"].eq(fold_id)].copy()
            local = local.loc[eligibility_mask(local, str(spec["eligibility"]))]
            fit = local.loc[
                local["assignment"].eq("FIT") & local["dataset_eligible"]
            ].copy()
            calibration = local.loc[
                local["assignment"].eq("CALIBRATION") & local["dataset_eligible"]
            ].copy()
            test = local.loc[
                local["assignment"].eq("TEST") & local["dataset_eligible"]
            ].copy()
            fitted = fit_probability_model(
                fit,
                spec=spec,
                feature_names=feature_names,
                categorical=categorical,
                calibration=contract["probability_calibration"],
            )
            fit_weights = fit["structural_weight"].to_numpy(dtype=float)
            fit_prior = float(
                np.dot(
                    fit_weights,
                    fit["stress_net_r_positive"].astype(float).to_numpy(),
                )
                / fit_weights.sum()
            )
            calibration["probability"] = fitted.predict_proba(calibration, clip)
            threshold, audit = choose_threshold(
                calibration, contract["threshold_policy"]
            )
            for row in audit:
                threshold_rows.append({"fold_id": fold_id, "model_id": model_id, **row})
            test["probability"] = fitted.predict_proba(test, clip)
            test["target"] = test["stress_net_r_positive"].astype(int)
            test["selected"] = test["probability"].ge(threshold)
            test["model_id"] = model_id
            test["model_role"] = str(spec["role"])
            test["threshold"] = threshold
            test["fit_weighted_positive_prior"] = fit_prior
            predictions.append(
                test[
                    [
                        "fold_id",
                        "model_id",
                        "model_role",
                        "candidate_id",
                        "structural_episode_id",
                        "decision_time",
                        "family_id",
                        "direction",
                        "structural_weight",
                        "target",
                        "stress_net_r",
                        "probability",
                        "threshold",
                        "selected",
                        "fit_weighted_positive_prior",
                    ]
                ]
            )
            metric_rows.append(
                _flatten_metrics(
                    fold_id=fold_id,
                    spec=spec,
                    feature_count=len(feature_names),
                    fit_rows=len(fit),
                    calibration_rows=len(calibration),
                    test=test,
                    threshold=threshold,
                    fit_prior=fit_prior,
                    weekdays=weekdays[fold_id],
                    inner_base_rows=fitted.inner_base_rows,
                    inner_calibrator_rows=fitted.inner_calibrator_rows,
                    inner_purged_rows=fitted.inner_purged_rows,
                )
            )
            if model_id == primary_id:
                joblib.dump(
                    {
                        "model": fitted,
                        "threshold": threshold,
                        "feature_names": feature_names,
                        "fold_id": fold_id,
                        "contract_lock_sha256": lock_sha,
                        "runtime_authorized": False,
                    },
                    model_dir / f"{model_id}_{fold_id}.joblib",
                    compress=3,
                )

    prediction_frame = pd.concat(predictions, ignore_index=True).sort_values(
        ["model_id", "decision_time", "candidate_id"], kind="stable"
    )
    metric_frame = pd.DataFrame(metric_rows).sort_values(
        ["model_id", "fold_id"], kind="stable"
    )
    threshold_frame = pd.DataFrame(threshold_rows).sort_values(
        ["model_id", "fold_id", "threshold"], kind="stable"
    )
    outputs = contract["outputs"]
    stable_parquet(prediction_frame, output_dir / str(outputs["fold_predictions"]))
    stable_parquet(metric_frame, output_dir / str(outputs["fold_metrics"]))
    stable_parquet(threshold_frame, output_dir / str(outputs["thresholds"]))

    total_weekdays = sum(weekdays.values())
    pooled = {
        model_id: _pooled_metrics(group.reset_index(drop=True), weekdays=total_weekdays)
        for model_id, group in prediction_frame.groupby("model_id", sort=True)
    }
    write_json(output_dir / str(outputs["pooled_metrics"]), pooled)
    primary = prediction_frame.loc[prediction_frame["model_id"].eq(primary_id)].copy()
    bootstrap = primary_block_bootstrap(primary, contract)
    write_json(output_dir / str(outputs["bootstrap"]), bootstrap)
    journey_diagnostic = _journey_diagnostic(journey)
    write_json(output_dir / str(outputs["journey_diagnostic"]), journey_diagnostic)
    primary_folds = metric_frame.loc[metric_frame["model_id"].eq(primary_id)]
    acceptance = _acceptance(
        primary, primary_folds, pooled[primary_id], bootstrap, contract
    )
    write_json(output_dir / str(outputs["acceptance"]), acceptance)

    result = {
        "schema_version": "xauusd_step_4_result_v1",
        "decision": acceptance["decision"],
        "contract_lock_sha256": lock_sha,
        "primary_model_id": primary_id,
        "models_evaluated": sorted(prediction_frame["model_id"].unique()),
        "outer_folds": sorted(prediction_frame["fold_id"].unique()),
        "primary_out_of_time_rows": len(primary),
        "primary_selected_rows": int(primary["selected"].sum()),
        "primary_pooled_metrics": pooled[primary_id],
        "primary_bootstrap": bootstrap,
        "acceptance_checks": acceptance["checks"],
        "journey_rows_used_for_fit": 0,
        "comex_features_used": False,
        "databento_api_accessed": False,
        "portfolio_simulated": False,
        "runtime_changed": False,
        "shadow_or_demo_activated": False,
    }
    write_json(output_dir / str(outputs["result_json"]), result)
    selected = pooled[primary_id]["selected"]
    baseline = pooled[primary_id]["baseline"]
    markdown = "\n".join(
        [
            "# Step 4 Locked Walk-Forward Evaluation",
            "",
            f"Decision: `{result['decision']}`",
            "",
            f"- Primary model: `{primary_id}`.",
            f"- Out-of-time candidates: `{len(primary)}`; selected: "
            f"`{int(primary['selected'].sum())}` "
            f"(`{float(selected['selected_fraction']):.1%}`).",
            f"- Weighted ROC AUC: "
            f"`{pooled[primary_id]['probability']['weighted_roc_auc']:.4f}`.",
            f"- Selected weighted mean stressed R: "
            f"`{float(selected['weighted_mean_stress_r']):.4f}` versus baseline "
            f"`{float(baseline['weighted_mean_stress_r']):.4f}`.",
            f"- Selected weighted profit factor: "
            f"`{float(selected['weighted_profit_factor'] or 0.0):.4f}`.",
            f"- Acceptance checks: `{acceptance['passed_checks']}` / "
            f"`{acceptance['required_checks']}` passed.",
            "- COMEX features and Databento API access were not used.",
            "- No portfolio, MT5, shadow, demo, live, or runtime action was performed.",
            "",
        ]
    )
    (output_dir / str(outputs["result_markdown"])).write_text(
        markdown, encoding="utf-8"
    )
    manifest = _artifact_manifest(
        output_dir,
        repo_root,
        decision=result["decision"],
        lock_sha256=lock_sha,
    )
    write_json(output_dir / str(outputs["artifact_manifest"]), manifest)
    result["artifact_manifest_sha256"] = sha256_file(
        output_dir / str(outputs["artifact_manifest"])
    )
    return result

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd

from regime_model import (
    fit_model,
    fold_metric_row,
    predict,
    safe_probability_metrics,
    weighted_prior,
)
from step_3_common import sha256_file, stable_parquet, verify_bound_file, write_json
from step_4_bootstrap import primary_block_bootstrap
from step_4_metrics import choose_threshold, economic_metrics


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _weekdays(start: pd.Timestamp, end: pd.Timestamp) -> int:
    return int(
        np.busday_count(
            np.datetime64(start.date(), "D"), np.datetime64(end.date(), "D")
        )
    )


def _fold_weekdays(step2b: Mapping[str, Any]) -> dict[str, int]:
    return {
        str(row["fold_id"]): _weekdays(
            pd.Timestamp(row["test_start"]),
            pd.Timestamp(row["test_end_exclusive"]),
        )
        for row in step2b["split_contract"]["outer_eras"]
    }


def availability_table(
    frame: pd.DataFrame, contract: Mapping[str, Any]
) -> pd.DataFrame:
    minimum = contract["availability"]
    rows: list[dict[str, Any]] = []
    fold_ids = sorted(frame["fold_id"].unique())
    for family_id in contract["population"]["families"]:
        for fold_id in fold_ids:
            local = frame.loc[
                frame["family_id"].eq(family_id) & frame["fold_id"].eq(fold_id)
            ]
            counts = local["assignment"].value_counts()
            fit_rows = int(counts.get("FIT", 0))
            calibration_rows = int(counts.get("CALIBRATION", 0))
            test_rows = int(counts.get("TEST", 0))
            trainable = (
                fit_rows >= int(minimum["minimum_fit_rows"])
                and calibration_rows >= int(minimum["minimum_calibration_rows"])
                and test_rows >= int(minimum["minimum_test_rows"])
            )
            rows.append(
                {
                    "family_id": family_id,
                    "fold_id": fold_id,
                    "fit_rows": fit_rows,
                    "calibration_rows": calibration_rows,
                    "test_rows": test_rows,
                    "trainable": trainable,
                }
            )
    return pd.DataFrame(rows)


def _family_pooled(
    predictions: pd.DataFrame, *, weekdays: int
) -> dict[str, Any]:
    probability = safe_probability_metrics(predictions)
    selected = economic_metrics(
        predictions, predictions["selected"], weekdays=weekdays
    )
    baseline = economic_metrics(
        predictions, np.ones(len(predictions), dtype=bool), weekdays=weekdays
    )
    constant = predictions.copy()
    constant["probability"] = constant["fit_weighted_positive_prior"]
    constant_probability = safe_probability_metrics(constant)
    return {
        "probability": probability,
        "constant_fit_prior": constant_probability,
        "selected": selected,
        "baseline": baseline,
        "selected_minus_baseline_weighted_mean_stress_r": (
            float(selected["weighted_mean_stress_r"])
            - float(baseline["weighted_mean_stress_r"])
        ),
    }


def _acceptance(
    family_id: str,
    *,
    eligible_folds: list[str],
    pooled: Mapping[str, Any] | None,
    bootstrap: Mapping[str, Any] | None,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    decisions = contract["decisions"]
    if not eligible_folds or pooled is None or bootstrap is None:
        return {
            "family_id": family_id,
            "decision": decisions["insufficient"],
            "eligible_folds": eligible_folds,
            "checks": {},
            "passed_checks": 0,
            "required_checks": 0,
            "runtime_authorized": False,
        }
    gates = contract["acceptance_gates"]
    probability = pooled["probability"]
    selected = pooled["selected"]
    baseline = pooled["baseline"]
    prior = pooled["constant_fit_prior"]
    auc = probability["weighted_roc_auc"]
    brier = probability["weighted_brier"]
    prior_brier = prior["weighted_brier"]
    checks = {
        "minimum_evaluated_folds": len(eligible_folds)
        >= int(gates["minimum_evaluated_folds"]),
        "minimum_test_rows": int(baseline["rows"])
        >= int(gates["minimum_test_rows"]),
        "weighted_roc_auc": auc is not None
        and float(auc) >= float(gates["weighted_roc_auc_minimum"]),
        "weighted_roc_auc_ci": float(bootstrap["weighted_roc_auc"]["lower"])
        > float(gates["weighted_roc_auc_ci_lower_strictly_above"]),
        "selected_ev_ci": float(
            bootstrap["selected_weighted_mean_stress_r"]["lower"]
        )
        > float(gates["selected_weighted_mean_stress_r_ci_lower_strictly_above"]),
        "delta_ev_ci": float(
            bootstrap["selected_minus_baseline_weighted_mean_stress_r"]["lower"]
        )
        > float(
            gates["selected_minus_baseline_mean_stress_r_ci_lower_strictly_above"]
        ),
        "selected_profit_factor": float(
            selected["weighted_profit_factor"] or 0.0
        )
        >= float(gates["selected_weighted_profit_factor_minimum"]),
        "selected_fraction": float(selected["selected_fraction"])
        >= float(gates["selected_fraction_minimum"]),
        "minimum_selected_rows": int(selected["rows"])
        >= int(gates["minimum_selected_rows"]),
        "weighted_brier_vs_prior": brier is not None
        and prior_brier is not None
        and float(brier) <= float(prior_brier),
        "selected_drawdown": float(selected["weighted_max_drawdown_r"])
        <= float(baseline["weighted_max_drawdown_r"]),
    }
    passed = all(checks.values())
    return {
        "family_id": family_id,
        "decision": decisions["pass"] if passed else decisions["fail"],
        "eligible_folds": eligible_folds,
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "required_checks": len(checks),
        "runtime_authorized": False,
    }


def _artifact_manifest(
    output_dir: Path, repo_root: Path, *, decision: str, lock_sha256: str
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    for path in sorted(output_dir.rglob("*")):
        if not path.is_file() or path.name == "REGIME_V2_ARTIFACT_MANIFEST.json":
            continue
        artifacts[path.relative_to(output_dir).as_posix()] = {
            "path": path.relative_to(repo_root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    return {
        "schema_version": "xauusd_regime_v2_artifact_manifest_v1",
        "decision": decision,
        "contract_lock_sha256": lock_sha256,
        "runtime_changed": False,
        "artifacts": artifacts,
    }


def _markdown(result: Mapping[str, Any], metrics: Mapping[str, Any]) -> str:
    lines = [
        "# Regime-Specific Candidate Quality Models V2",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Family | Decision | Folds | Test rows | AUC | Selected | Delta EV R |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    acceptance = result["family_acceptance"]
    for family_id in result["families"]:
        gate = acceptance[family_id]
        if family_id not in metrics:
            lines.append(
                f"| {family_id} | {gate['decision']} | 0 | 0 | n/a | 0 | n/a |"
            )
            continue
        local = metrics[family_id]
        auc = local["probability"]["weighted_roc_auc"]
        lines.append(
            f"| {family_id} | {gate['decision']} | {len(gate['eligible_folds'])} | "
            f"{int(local['baseline']['rows'])} | {float(auc):.4f} | "
            f"{int(local['selected']['rows'])} | "
            f"{float(local['selected_minus_baseline_weighted_mean_stress_r']):.4f} |"
        )
    lines.extend(
        [
            "",
            "All results are development-only on exposed history. No model was "
            "connected to MT5, shadow, demo, or live execution.",
            "",
        ]
    )
    return "\n".join(lines)


def run_regime_v2(
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
        raise ValueError("Regime V2 contract must be locked before fitting")
    lock = load_json(lock_path)
    if lock["definition"]["config_sha256"] != sha256_file(config_path):
        raise ValueError("Regime V2 config changed after lock")
    for relative, expected in lock["definition"]["implementation_sha256"].items():
        if sha256_file((package_root / relative).resolve()) != expected:
            raise ValueError(f"Regime V2 implementation changed: {relative}")
    lock_sha = sha256_file(lock_path)
    step2b = load_json(bound["step_2b_contract"])
    step4 = load_json(bound["step_4_result"])
    if step4["decision"] != "MODEL_EVIDENCE_GATE_FAIL":
        raise ValueError("V2 requires the recorded V1 pooled-model failure")

    dataset = pd.read_parquet(bound["step_3_dataset"])
    splits = pd.read_parquet(bound["step_3_splits"])
    assignment = splits[
        ["fold_id", "candidate_id", "assignment", "resolved_label", "dataset_eligible"]
    ]
    frame = assignment.merge(dataset, on="candidate_id", validate="many_to_one")
    frame = frame.loc[
        frame["resolved_label"]
        & frame["dataset_eligible"]
        & frame["xau_feature_status"].eq("PASS")
    ].copy()
    availability = availability_table(frame, contract)
    observed = {
        family_id: sorted(
            availability.loc[
                availability["family_id"].eq(family_id)
                & availability["trainable"],
                "fold_id",
            ].tolist()
        )
        for family_id in contract["population"]["families"]
    }
    expected = {
        family: sorted(folds)
        for family, folds in contract["availability"][
            "expected_trainable_folds"
        ].items()
    }
    if observed != expected:
        raise ValueError(f"Regime V2 trainable fold set changed: {observed}")

    features = list(contract["features"])
    if len(features) != len(set(features)) or any(
        name not in frame.columns for name in features
    ):
        raise ValueError("Regime V2 feature contract is invalid")
    prohibited = {
        "family_id",
        "candidate_id",
        "decision_time",
        "stress_net_r",
        "stress_net_r_positive",
        "historical_portfolio_accepted",
    }
    if prohibited.intersection(features) or any(name.startswith("gc_") for name in features):
        raise ValueError("Prohibited identity, outcome, policy, or COMEX feature")

    weekdays = _fold_weekdays(step2b)
    prediction_frames: list[pd.DataFrame] = []
    fold_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    model_dir = output_dir / str(contract["outputs"]["model_directory"])
    model_dir.mkdir(parents=True, exist_ok=True)
    for family_id, fold_ids in observed.items():
        for fold_id in fold_ids:
            local = frame.loc[
                frame["family_id"].eq(family_id)
                & frame["fold_id"].eq(fold_id)
            ].copy()
            fit = local.loc[local["assignment"].eq("FIT")].copy()
            calibration = local.loc[local["assignment"].eq("CALIBRATION")].copy()
            test = local.loc[local["assignment"].eq("TEST")].copy()
            model = fit_model(
                fit,
                features=features,
                parameters=contract["model"]["parameters"],
            )
            prior = weighted_prior(fit)
            calibration["probability"] = predict(model, calibration, features)
            threshold, audit = choose_threshold(
                calibration, contract["threshold_policy"]
            )
            for row in audit:
                threshold_rows.append(
                    {"family_id": family_id, "fold_id": fold_id, **row}
                )
            test["probability"] = predict(model, test, features)
            test["target"] = test["stress_net_r_positive"].astype(int)
            test["selected"] = test["probability"].ge(threshold)
            test["threshold"] = threshold
            test["fit_weighted_positive_prior"] = prior
            prediction_frames.append(
                test[
                    [
                        "family_id",
                        "fold_id",
                        "candidate_id",
                        "structural_episode_id",
                        "decision_time",
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
            fold_rows.append(
                fold_metric_row(
                    test,
                    family_id=family_id,
                    fold_id=fold_id,
                    fit_rows=len(fit),
                    calibration_rows=len(calibration),
                    threshold=threshold,
                    fit_prior=prior,
                    weekdays=weekdays[fold_id],
                )
            )
            joblib.dump(
                {
                    "family_id": family_id,
                    "fold_id": fold_id,
                    "model": model,
                    "threshold": threshold,
                    "features": features,
                    "contract_lock_sha256": lock_sha,
                    "runtime_authorized": False,
                },
                model_dir / f"{family_id}_{fold_id}.joblib",
                compress=3,
            )

    predictions = pd.concat(prediction_frames, ignore_index=True).sort_values(
        ["family_id", "decision_time", "candidate_id"], kind="stable"
    )
    fold_metrics = pd.DataFrame(fold_rows).sort_values(
        ["family_id", "fold_id"], kind="stable"
    )
    thresholds = pd.DataFrame(threshold_rows).sort_values(
        ["family_id", "fold_id", "threshold"], kind="stable"
    )
    family_metrics: dict[str, Any] = {}
    bootstraps: dict[str, Any] = {}
    family_acceptance: dict[str, Any] = {}
    for family_id in contract["population"]["families"]:
        family_predictions = predictions.loc[
            predictions["family_id"].eq(family_id)
        ].copy()
        fold_ids = observed[family_id]
        if family_predictions.empty:
            family_acceptance[family_id] = _acceptance(
                family_id,
                eligible_folds=fold_ids,
                pooled=None,
                bootstrap=None,
                contract=contract,
            )
            continue
        pooled = _family_pooled(
            family_predictions,
            weekdays=sum(weekdays[fold_id] for fold_id in fold_ids),
        )
        bootstrap = primary_block_bootstrap(family_predictions, contract)
        family_metrics[family_id] = pooled
        bootstraps[family_id] = bootstrap
        family_acceptance[family_id] = _acceptance(
            family_id,
            eligible_folds=fold_ids,
            pooled=pooled,
            bootstrap=bootstrap,
            contract=contract,
        )

    passed = sorted(
        family
        for family, gate in family_acceptance.items()
        if gate["decision"] == contract["decisions"]["pass"]
    )
    decision = (
        "REGIME_V2_FAMILY_GATES_PASSED_DEVELOPMENT_ONLY"
        if passed
        else "REGIME_V2_NO_FAMILY_GATE_PASS"
    )
    outputs = contract["outputs"]
    stable_parquet(availability, output_dir / str(outputs["availability"]))
    stable_parquet(predictions, output_dir / str(outputs["predictions"]))
    stable_parquet(fold_metrics, output_dir / str(outputs["fold_metrics"]))
    stable_parquet(thresholds, output_dir / str(outputs["thresholds"]))
    write_json(output_dir / str(outputs["family_metrics"]), family_metrics)
    write_json(output_dir / str(outputs["bootstrap"]), bootstraps)
    write_json(output_dir / str(outputs["acceptance"]), family_acceptance)
    result = {
        "schema_version": "xauusd_regime_models_v2_result_v1",
        "decision": decision,
        "contract_lock_sha256": lock_sha,
        "families": list(contract["population"]["families"]),
        "trained_families": sorted(family_metrics),
        "insufficient_families": sorted(set(observed) - set(family_metrics)),
        "passed_families": passed,
        "family_acceptance": family_acceptance,
        "family_metrics": family_metrics,
        "canonical_rows_available": int(dataset.shape[0]),
        "eligible_family_fold_rows": int(frame.shape[0]),
        "journey_rows_used": 0,
        "comex_used": False,
        "databento_api_accessed": False,
        "demo_outcomes_used": False,
        "historical_outcomes_already_exposed": True,
        "development_only": True,
        "runtime_changed": False,
        "ml_shadow_or_execution_activated": False,
    }
    write_json(output_dir / str(outputs["result_json"]), result)
    (output_dir / str(outputs["result_markdown"])).write_text(
        _markdown(result, family_metrics), encoding="utf-8"
    )
    manifest = _artifact_manifest(
        output_dir, repo_root, decision=decision, lock_sha256=lock_sha
    )
    write_json(output_dir / str(outputs["artifact_manifest"]), manifest)
    result["artifact_manifest_sha256"] = sha256_file(
        output_dir / str(outputs["artifact_manifest"])
    )
    return result

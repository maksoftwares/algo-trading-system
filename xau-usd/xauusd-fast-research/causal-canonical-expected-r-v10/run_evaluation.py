from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd

from src.expected_r import (
    PartialPoolingExpectedR,
    apply_thresholds,
    calibration_thresholds,
    canonical_json_sha256,
    comparison_metrics,
    feature_surface,
    prepare_dataset,
    prepare_population,
    resolve_inputs,
    sha256_file,
    weekly_block_bootstrap,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "canonical_expected_r_v10.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_lock(
    config: Mapping[str, Any],
    lock: Mapping[str, Any],
) -> None:
    if sha256_file(CONFIG_PATH) != str(lock["config_sha256"]):
        raise ValueError("Configuration changed after contract lock")
    for name, spec in lock["implementation"].items():
        path = REPO_ROOT / str(spec["path"])
        if sha256_file(path) != str(spec["sha256"]):
            raise ValueError(f"Implementation changed after lock: {name}")
    if canonical_json_sha256(config["model"]) != str(lock["model_sha256"]):
        raise ValueError("Model contract changed after lock")
    if canonical_json_sha256(config["threshold"]) != str(lock["threshold_sha256"]):
        raise ValueError("Threshold contract changed after lock")
    if canonical_json_sha256(config["acceptance_gates"]) != str(
        lock["acceptance_sha256"]
    ):
        raise ValueError("Acceptance contract changed after lock")


def flatten_metrics(prefix: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": value for key, value in metrics.items()}


def acceptance_checks(
    pooled: Mapping[str, Any],
    fold_metrics: pd.DataFrame,
    family_metrics: pd.DataFrame,
    bootstrap: Mapping[str, Any],
    gates: Mapping[str, Any],
) -> dict[str, bool]:
    latest = fold_metrics.loc[fold_metrics["fold_id"].eq("F2025")].iloc[0]
    intervals = bootstrap["intervals"]
    selected_family_weights = family_metrics["selected_weight"].to_numpy(dtype=float)
    single_family_fraction = float(
        selected_family_weights.max() / selected_family_weights.sum()
    )
    return {
        "minimum_weighted_score_auc": float(pooled["weighted_score_auc"])
        >= float(gates["minimum_weighted_score_auc"]),
        "minimum_selected_weighted_mean_r": float(pooled["selected"]["weighted_mean_r"])
        >= float(gates["minimum_selected_weighted_mean_r"]),
        "minimum_selected_mean_bootstrap_lower_r": float(
            intervals["selected_weighted_mean_r"]["lower"]
        )
        > float(gates["minimum_selected_mean_bootstrap_lower_r"]),
        "minimum_ev_lift_r": float(pooled["selected_mean_lift_r"])
        >= float(gates["minimum_ev_lift_r"]),
        "minimum_ev_lift_bootstrap_lower_r": float(
            intervals["selected_mean_lift_r"]["lower"]
        )
        > float(gates["minimum_ev_lift_bootstrap_lower_r"]),
        "minimum_selected_profit_factor": float(
            pooled["selected"]["weighted_profit_factor"]
        )
        >= float(gates["minimum_selected_profit_factor"]),
        "minimum_profit_factor_bootstrap_lower": float(
            intervals["selected_profit_factor"]["lower"]
        )
        >= float(gates["minimum_profit_factor_bootstrap_lower"]),
        "minimum_selected_weight_coverage": float(pooled["selected_weight_coverage"])
        >= float(gates["minimum_selected_weight_coverage"]),
        "maximum_selected_weight_coverage": float(pooled["selected_weight_coverage"])
        <= float(gates["maximum_selected_weight_coverage"]),
        "minimum_selected_candidates_per_weekday": float(
            pooled["selected"]["candidates_per_weekday"]
        )
        >= float(gates["minimum_selected_candidates_per_weekday"]),
        "minimum_positive_folds": int(
            (fold_metrics["selected_weighted_mean_r"] > 0.0).sum()
        )
        >= int(gates["minimum_positive_folds"]),
        "minimum_latest_fold_mean_r": float(latest["selected_weighted_mean_r"])
        >= float(gates["minimum_latest_fold_mean_r"]),
        "minimum_latest_fold_profit_factor": float(
            latest["selected_weighted_profit_factor"]
        )
        >= float(gates["minimum_latest_fold_profit_factor"]),
        "minimum_latest_fold_weight_coverage": float(latest["selected_weight_coverage"])
        >= float(gates["minimum_latest_fold_weight_coverage"]),
        "maximum_drawdown_ratio_to_baseline": float(
            pooled["drawdown_ratio_to_baseline"]
        )
        <= float(gates["maximum_drawdown_ratio_to_baseline"]),
        "minimum_family_selected_mean_r": bool(
            (
                family_metrics["selected_weighted_mean_r"]
                >= float(gates["minimum_family_selected_mean_r"])
            ).all()
        ),
        "maximum_single_family_selected_weight_fraction": single_family_fraction
        <= float(gates["maximum_single_family_selected_weight_fraction"]),
        "minimum_selected_rows": int(pooled["selected"]["rows"])
        >= int(gates["minimum_selected_rows"]),
    }


def model_from_config(
    fit: pd.DataFrame,
    numeric_features: list[str],
    config: Mapping[str, Any],
) -> PartialPoolingExpectedR:
    return PartialPoolingExpectedR.fit(
        fit,
        numeric_features=numeric_features,
        families=config["population"]["families"],
        alpha=float(config["model"]["alpha"]),
        interaction_scale=float(config["features"]["family_interaction_scale"]),
        target_clip=(
            float(config["model"]["target_clip_min_r"]),
            float(config["model"]["target_clip_max_r"]),
        ),
    )


def fit_final_model(
    population: pd.DataFrame,
    numeric_features: list[str],
    config: Mapping[str, Any],
    lock: Mapping[str, Any],
    output: Path,
) -> dict[str, Any]:
    spec = config["final_research_model"]
    fit_cutoff = pd.Timestamp(spec["fit_decision_before_utc"])
    label_cutoff = pd.Timestamp(spec["fit_label_end_before_utc"])
    calibration_start = pd.Timestamp(spec["calibration_start_utc"])
    calibration_end = pd.Timestamp(spec["calibration_end_exclusive_utc"])
    fit = population.loc[
        population["decision_time"].lt(fit_cutoff)
        & population["label_end_time"].lt(label_cutoff)
    ].copy()
    calibration = population.loc[
        population["decision_time"].ge(calibration_start)
        & population["decision_time"].lt(calibration_end)
    ].copy()
    overlap = set(fit["structural_episode_id"]) & set(
        calibration["structural_episode_id"]
    )
    if overlap:
        raise ValueError("Final fit and calibration share structural episodes")
    model = model_from_config(fit, numeric_features, config)
    calibration["model_score"] = model.predict(calibration)
    pooled, thresholds, rows = calibration_thresholds(
        calibration,
        families=config["population"]["families"],
        quantile=float(config["threshold"]["weighted_veto_quantile"]),
        minimum_family_rows=int(config["threshold"]["minimum_family_calibration_rows"]),
    )
    payload = {
        "schema_version": "xauusd_expected_r_v10_final_research_model",
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "model": model,
        "numeric_features": numeric_features,
        "families": list(config["population"]["families"]),
        "pooled_threshold": pooled,
        "family_thresholds": thresholds,
        "threshold_rows": rows,
        "fit_rows": int(len(fit)),
        "fit_winners": int(fit["stress_net_r_positive"].astype(bool).sum()),
        "fit_losers": int((~fit["stress_net_r_positive"].astype(bool)).sum()),
        "calibration_rows": int(len(calibration)),
        "fit_decision_before_utc": fit_cutoff.isoformat(),
        "fit_label_end_before_utc": label_cutoff.isoformat(),
        "calibration_start_utc": calibration_start.isoformat(),
        "calibration_end_exclusive_utc": calibration_end.isoformat(),
        "research_only": True,
        "runtime_authorized": False,
    }
    final_path = output / str(config["outputs"]["final_model"])
    joblib.dump(payload, final_path, compress=3)
    return {
        key: value
        for key, value in payload.items()
        if key not in {"model", "family_thresholds", "threshold_rows"}
    } | {
        "path": str(final_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "sha256": sha256_file(final_path),
    }


def artifact_manifest(
    output: Path,
    inputs: Mapping[str, Path],
    lock: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    manifest_name = str(config["outputs"]["manifest"])
    files = sorted(
        path
        for path in output.rglob("*")
        if path.is_file() and path.name != manifest_name
    )
    return {
        "schema_version": "xauusd_expected_r_v10_artifact_manifest",
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "inputs": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for name, path in inputs.items()
        },
        "artifacts": {
            str(path.relative_to(output)).replace("\\", "/"): {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in files
        },
    }


def main() -> int:
    config = load_json(CONFIG_PATH)
    output = ROOT / str(config["outputs"]["directory"])
    output.mkdir(parents=True, exist_ok=True)
    models_directory = output / str(config["outputs"]["models_directory"])
    models_directory.mkdir(parents=True, exist_ok=True)
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    verify_lock(config, lock)
    inputs = resolve_inputs(REPO_ROOT, config)
    step_2b = load_json(inputs["step_2b_contract"])
    raw_features, numeric_features = feature_surface(step_2b, config)
    if canonical_json_sha256({"raw": raw_features, "numeric": numeric_features}) != str(
        lock["feature_sha256"]
    ):
        raise ValueError("Feature surface changed after lock")
    raw_dataset = pd.read_parquet(inputs["step_3_dataset"])
    splits = pd.read_parquet(inputs["step_3_splits"])
    population = prepare_population(raw_dataset, config, numeric_features)
    source = prepare_dataset(raw_dataset, splits, config, numeric_features)

    predictions: list[pd.DataFrame] = []
    fold_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    for fold_id in config["outer_evaluation"]["folds"]:
        fit = source.loc[
            source["fold_id"].eq(fold_id)
            & source["assignment"].eq(str(config["outer_evaluation"]["fit_assignment"]))
        ].copy()
        calibration = source.loc[
            source["fold_id"].eq(fold_id)
            & source["assignment"].eq(
                str(config["outer_evaluation"]["calibration_assignment"])
            )
        ].copy()
        test = source.loc[
            source["fold_id"].eq(fold_id)
            & source["assignment"].eq(
                str(config["outer_evaluation"]["test_assignment"])
            )
        ].copy()
        if (
            set(fit["structural_episode_id"])
            & set(calibration["structural_episode_id"])
            or set(fit["structural_episode_id"]) & set(test["structural_episode_id"])
            or set(calibration["structural_episode_id"])
            & set(test["structural_episode_id"])
        ):
            raise ValueError(f"Structural episode crossed partitions in {fold_id}")
        model = model_from_config(fit, numeric_features, config)
        calibration["model_score"] = model.predict(calibration)
        test["model_score"] = model.predict(test)
        pooled_threshold, thresholds, rows = calibration_thresholds(
            calibration,
            families=config["population"]["families"],
            quantile=float(config["threshold"]["weighted_veto_quantile"]),
            minimum_family_rows=int(
                config["threshold"]["minimum_family_calibration_rows"]
            ),
        )
        for row in rows:
            threshold_rows.append(
                {"fold_id": fold_id, "pooled_threshold": pooled_threshold, **row}
            )
        scored = apply_thresholds(test, thresholds, pooled_threshold)
        scored["fold_id"] = fold_id
        model_path = models_directory / f"EXPECTED_R_V10_{fold_id}.joblib"
        joblib.dump(
            {
                "schema_version": "xauusd_expected_r_v10_outer_model",
                "fold_id": fold_id,
                "model": model,
                "pooled_threshold": pooled_threshold,
                "family_thresholds": thresholds,
                "fit_rows": int(len(fit)),
                "fit_winners": int(fit["stress_net_r_positive"].astype(bool).sum()),
                "fit_losers": int((~fit["stress_net_r_positive"].astype(bool)).sum()),
                "calibration_rows": int(len(calibration)),
                "definition_contract_sha256": lock["definition_contract_sha256"],
            },
            model_path,
            compress=3,
        )
        keep = [
            "candidate_id",
            "family_id",
            "decision_time",
            "label_end_time",
            "structural_episode_id",
            "structural_weight",
            "stress_net_r",
            "stress_net_r_positive",
            "model_score",
            "threshold",
            "selected",
            "fold_id",
        ]
        predictions.append(scored[keep])
        metrics = comparison_metrics(scored)
        fold_rows.append(
            {
                "fold_id": fold_id,
                "fit_rows": int(len(fit)),
                "fit_winners": int(fit["stress_net_r_positive"].astype(bool).sum()),
                "fit_losers": int((~fit["stress_net_r_positive"].astype(bool)).sum()),
                "calibration_rows": int(len(calibration)),
                "test_rows": int(len(test)),
                **flatten_metrics("baseline", metrics["baseline"]),
                **flatten_metrics("selected", metrics["selected"]),
                "weighted_score_auc": metrics["weighted_score_auc"],
                "selected_weight_coverage": metrics["selected_weight_coverage"],
                "selected_mean_lift_r": metrics["selected_mean_lift_r"],
                "drawdown_ratio_to_baseline": metrics["drawdown_ratio_to_baseline"],
            }
        )

    prediction_frame = (
        pd.concat(predictions, ignore_index=True)
        .sort_values(["decision_time", "candidate_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    if prediction_frame["candidate_id"].duplicated().any():
        raise ValueError("Out-of-time predictions contain duplicate candidates")
    fold_frame = pd.DataFrame(fold_rows)
    threshold_frame = pd.DataFrame(threshold_rows)
    pooled = comparison_metrics(prediction_frame)
    family_rows: list[dict[str, Any]] = []
    for family, group in prediction_frame.groupby("family_id", sort=True):
        metrics = comparison_metrics(group)
        family_rows.append(
            {
                "family_id": family,
                **flatten_metrics("baseline", metrics["baseline"]),
                **flatten_metrics("selected", metrics["selected"]),
                "weighted_score_auc": metrics["weighted_score_auc"],
                "selected_weight_coverage": metrics["selected_weight_coverage"],
                "selected_mean_lift_r": metrics["selected_mean_lift_r"],
                "drawdown_ratio_to_baseline": metrics["drawdown_ratio_to_baseline"],
            }
        )
    family_frame = pd.DataFrame(family_rows)
    bootstrap = weekly_block_bootstrap(
        prediction_frame,
        resamples=int(config["bootstrap"]["resamples"]),
        confidence=float(config["bootstrap"]["confidence"]),
        seed=int(config["bootstrap"]["seed"]),
    )
    checks = acceptance_checks(
        pooled,
        fold_frame,
        family_frame,
        bootstrap,
        config["acceptance_gates"],
    )
    passed = all(checks.values())
    acceptance = {
        "schema_version": "xauusd_expected_r_v10_acceptance",
        "all_required": True,
        "checks": checks,
        "passed_checks": int(sum(checks.values())),
        "required_checks": int(len(checks)),
        "passed": bool(passed),
        "decision": (
            "EXPECTED_R_V10_HISTORICAL_GATE_PASS_FORWARD_CONFIRMATION_REQUIRED"
            if passed
            else "EXPECTED_R_V10_HISTORICAL_GATE_FAIL"
        ),
        "runtime_authorized": False,
    }
    final_model = fit_final_model(population, numeric_features, config, lock, output)
    result = {
        "schema_version": "xauusd_expected_r_v10_result",
        "decision": acceptance["decision"],
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "historical_outcomes_already_exposed": True,
        "development_selection_disclosed": True,
        "canonical_rows": int(len(raw_dataset)),
        "xau_feature_pass_rows": int(len(population)),
        "out_of_time_rows": int(len(prediction_frame)),
        "numeric_feature_count": int(len(numeric_features)),
        "design_feature_count": int(
            len(numeric_features)
            + len(config["population"]["families"])
            + len(numeric_features) * len(config["population"]["families"])
        ),
        "fit_includes_winners_and_losers": True,
        "folds": list(config["outer_evaluation"]["folds"]),
        "pooled": pooled,
        "bootstrap": bootstrap,
        "acceptance": acceptance,
        "final_research_model": final_model,
        "runtime_changed": False,
        "ml_shadow_or_execution_activated": False,
        "authorization": config["authorization"],
    }

    prediction_frame.to_parquet(
        output / str(config["outputs"]["predictions"]), index=False
    )
    fold_frame.to_parquet(output / str(config["outputs"]["fold_metrics"]), index=False)
    family_frame.to_parquet(
        output / str(config["outputs"]["family_metrics"]), index=False
    )
    threshold_frame.to_parquet(
        output / str(config["outputs"]["thresholds"]), index=False
    )
    write_json(output / str(config["outputs"]["bootstrap"]), bootstrap)
    write_json(output / str(config["outputs"]["acceptance"]), acceptance)
    write_json(output / str(config["outputs"]["result_json"]), result)
    markdown = (
        "# Expected-R V10 Result\n\n"
        f"- Decision: `{acceptance['decision']}`\n"
        f"- Out-of-time rows: {len(prediction_frame):,}\n"
        f"- Selected rows: {pooled['selected']['rows']:,}\n"
        f"- Selected candidates/weekday: "
        f"{pooled['selected']['candidates_per_weekday']:.6f}\n"
        f"- Baseline weighted mean: "
        f"{pooled['baseline']['weighted_mean_r']:.6f}R\n"
        f"- Selected weighted mean: "
        f"{pooled['selected']['weighted_mean_r']:.6f}R\n"
        f"- Expected-R lift: {pooled['selected_mean_lift_r']:.6f}R\n"
        f"- Selected PF: {pooled['selected']['weighted_profit_factor']:.6f}\n"
        f"- Selected coverage: {pooled['selected_weight_coverage']:.6%}\n"
        f"- Weighted score AUC: {pooled['weighted_score_auc']:.6f}\n"
        f"- Runtime authorized: false\n"
    )
    (output / str(config["outputs"]["result_markdown"])).write_text(
        markdown, encoding="utf-8"
    )
    manifest = artifact_manifest(output, inputs, lock, config)
    write_json(output / str(config["outputs"]["manifest"]), manifest)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from run_evaluation import (
    acceptance_checks,
    model_from_config,
    verify_lock,
)
from src.expected_r import (
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
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "canonical_expected_r_v10.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def close(left: object, right: object, name: str) -> None:
    if left is None or right is None:
        if left is not right:
            raise ValueError(f"Verification mismatch for {name}")
        return
    if not np.isclose(float(left), float(right), rtol=1e-11, atol=1e-11):
        raise ValueError(f"Verification mismatch for {name}: {left} != {right}")


def compare_metrics(
    actual: dict[str, Any],
    stored: pd.Series,
    prefix: str,
) -> None:
    for key, value in actual.items():
        close(value, stored[f"{prefix}_{key}"], f"{prefix}.{key}")


def main() -> int:
    config = load_json(CONFIG_PATH)
    output = ROOT / str(config["outputs"]["directory"])
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    verify_lock(config, lock)
    manifest = load_json(output / str(config["outputs"]["manifest"]))
    if manifest["definition_contract_sha256"] != lock["definition_contract_sha256"]:
        raise ValueError("Manifest references another definition contract")
    for spec in manifest["inputs"].values():
        if sha256_file(REPO_ROOT / spec["path"]) != spec["sha256"]:
            raise ValueError(f"Input changed: {spec['path']}")
    for spec in manifest["artifacts"].values():
        if sha256_file(REPO_ROOT / spec["path"]) != spec["sha256"]:
            raise ValueError(f"Artifact changed: {spec['path']}")

    inputs = resolve_inputs(REPO_ROOT, config)
    step_2b = load_json(inputs["step_2b_contract"])
    raw_features, numeric_features = feature_surface(step_2b, config)
    if (
        canonical_json_sha256({"raw": raw_features, "numeric": numeric_features})
        != lock["feature_sha256"]
    ):
        raise ValueError("Verified feature surface changed")
    raw_dataset = pd.read_parquet(inputs["step_3_dataset"])
    splits = pd.read_parquet(inputs["step_3_splits"])
    population = prepare_population(raw_dataset, config, numeric_features)
    source = prepare_dataset(raw_dataset, splits, config, numeric_features)
    predictions = (
        pd.read_parquet(output / str(config["outputs"]["predictions"]))
        .sort_values(["fold_id", "candidate_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    fold_metrics = pd.read_parquet(output / str(config["outputs"]["fold_metrics"]))
    family_metrics = pd.read_parquet(output / str(config["outputs"]["family_metrics"]))
    stored_thresholds = pd.read_parquet(output / str(config["outputs"]["thresholds"]))
    result = load_json(output / str(config["outputs"]["result_json"]))
    bootstrap = load_json(output / str(config["outputs"]["bootstrap"]))
    acceptance = load_json(output / str(config["outputs"]["acceptance"]))
    if predictions["candidate_id"].duplicated().any():
        raise ValueError("Stored predictions duplicate candidates")

    replay_parts: list[pd.DataFrame] = []
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
        stored = predictions.loc[predictions["fold_id"].eq(fold_id)].sort_values(
            "candidate_id", kind="mergesort"
        )
        test = test.sort_values("candidate_id", kind="mergesort")
        model_path = (
            output
            / str(config["outputs"]["models_directory"])
            / f"EXPECTED_R_V10_{fold_id}.joblib"
        )
        payload = joblib.load(model_path)
        if payload["fit_winners"] <= 0 or payload["fit_losers"] <= 0:
            raise ValueError("Outer model did not fit both outcome classes")
        serialized_scores = payload["model"].predict(test)
        if not np.allclose(
            serialized_scores,
            stored["model_score"].to_numpy(dtype=float),
            rtol=1e-12,
            atol=1e-12,
        ):
            raise ValueError(f"Serialized score replay failed for {fold_id}")

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
        refit_scores = test["model_score"].to_numpy(dtype=float)
        if not np.allclose(
            refit_scores,
            stored["model_score"].to_numpy(dtype=float),
            rtol=1e-12,
            atol=1e-12,
        ):
            raise ValueError(f"Independent expected-R refit failed for {fold_id}")
        threshold_frame = stored_thresholds.loc[
            stored_thresholds["fold_id"].eq(fold_id)
        ].sort_values("family_id", kind="mergesort")
        replay_threshold_frame = pd.DataFrame(
            [
                {"fold_id": fold_id, "pooled_threshold": pooled_threshold, **row}
                for row in rows
            ]
        ).sort_values("family_id", kind="mergesort")
        for column in ("threshold", "pooled_threshold"):
            if not np.allclose(
                threshold_frame[column].to_numpy(dtype=float),
                replay_threshold_frame[column].to_numpy(dtype=float),
                rtol=1e-12,
                atol=1e-12,
            ):
                raise ValueError(f"Threshold replay failed for {fold_id}")
        scored = apply_thresholds(test, thresholds, pooled_threshold)
        if not np.array_equal(
            scored["selected"].to_numpy(dtype=bool),
            stored["selected"].to_numpy(dtype=bool),
        ):
            raise ValueError(f"Selection replay failed for {fold_id}")
        scored["fold_id"] = fold_id
        replay_parts.append(scored)
        metrics = comparison_metrics(scored)
        stored_fold = fold_metrics.loc[fold_metrics["fold_id"].eq(fold_id)].iloc[0]
        compare_metrics(metrics["baseline"], stored_fold, "baseline")
        compare_metrics(metrics["selected"], stored_fold, "selected")
        for key in (
            "weighted_score_auc",
            "selected_weight_coverage",
            "selected_mean_lift_r",
            "drawdown_ratio_to_baseline",
        ):
            close(metrics[key], stored_fold[key], f"{fold_id}.{key}")

    replay = (
        pd.concat(replay_parts, ignore_index=True)
        .sort_values(["decision_time", "candidate_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    pooled = comparison_metrics(replay)
    for section in ("baseline", "selected"):
        for key, value in pooled[section].items():
            close(value, result["pooled"][section][key], f"pooled.{section}.{key}")
    for key in (
        "weighted_score_auc",
        "selected_weight_coverage",
        "selected_mean_lift_r",
        "drawdown_ratio_to_baseline",
    ):
        close(pooled[key], result["pooled"][key], f"pooled.{key}")

    replay_bootstrap = weekly_block_bootstrap(
        replay,
        resamples=int(config["bootstrap"]["resamples"]),
        confidence=float(config["bootstrap"]["confidence"]),
        seed=int(config["bootstrap"]["seed"]),
    )
    if canonical_json_sha256(replay_bootstrap) != canonical_json_sha256(bootstrap):
        raise ValueError("Bootstrap replay mismatch")
    checks = acceptance_checks(
        pooled,
        fold_metrics,
        family_metrics,
        replay_bootstrap,
        config["acceptance_gates"],
    )
    if checks != acceptance["checks"]:
        raise ValueError("Acceptance checks failed replay")

    final_payload = joblib.load(output / str(config["outputs"]["final_model"]))
    final_spec = config["final_research_model"]
    fit = population.loc[
        population["decision_time"].lt(
            pd.Timestamp(final_spec["fit_decision_before_utc"])
        )
        & population["label_end_time"].lt(
            pd.Timestamp(final_spec["fit_label_end_before_utc"])
        )
    ].copy()
    calibration = population.loc[
        population["decision_time"].ge(
            pd.Timestamp(final_spec["calibration_start_utc"])
        )
        & population["decision_time"].lt(
            pd.Timestamp(final_spec["calibration_end_exclusive_utc"])
        )
    ].copy()
    final_refit = model_from_config(fit, numeric_features, config)
    if not np.allclose(
        final_refit.estimator.coef_,
        final_payload["model"].estimator.coef_,
        rtol=1e-12,
        atol=1e-12,
    ):
        raise ValueError("Final model coefficient replay failed")
    close(
        final_refit.estimator.intercept_,
        final_payload["model"].estimator.intercept_,
        "final.intercept",
    )
    calibration["model_score"] = final_refit.predict(calibration)
    pooled_threshold, thresholds, _ = calibration_thresholds(
        calibration,
        families=config["population"]["families"],
        quantile=float(config["threshold"]["weighted_veto_quantile"]),
        minimum_family_rows=int(config["threshold"]["minimum_family_calibration_rows"]),
    )
    close(
        pooled_threshold,
        final_payload["pooled_threshold"],
        "final.pooled_threshold",
    )
    for family, threshold in thresholds.items():
        close(
            threshold,
            final_payload["family_thresholds"][family],
            f"final.{family}.threshold",
        )
    if final_payload["runtime_authorized"]:
        raise ValueError("Final research model claims runtime authority")
    if result["runtime_changed"] or result["ml_shadow_or_execution_activated"]:
        raise ValueError("Result claims a forbidden runtime change")
    print("EXPECTED_R_V10_VERIFICATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

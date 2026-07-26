from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd

from policy import (
    apply_profit_threshold,
    canonical_json_sha256,
    choose_profit_threshold,
    comparison,
    resolve_inputs,
    sha256_file,
    weekly_profit_bootstrap,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "profit_policy_v12.json"
V10_ROOT = (
    REPO_ROOT
    / "xau-usd"
    / "xauusd-fast-research"
    / "causal-canonical-expected-r-v10"
)
sys.path.insert(0, str(V10_ROOT / "src"))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_metrics(prefix: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": value for key, value in metrics.items()}


def verify_lock(config: Mapping[str, Any], lock: Mapping[str, Any]) -> None:
    if sha256_file(CONFIG_PATH) != str(lock["config_sha256"]):
        raise ValueError("Configuration changed after contract lock")
    for name, spec in lock["implementation"].items():
        path = REPO_ROOT / str(spec["path"])
        if sha256_file(path) != str(spec["sha256"]):
            raise ValueError(f"Implementation changed after lock: {name}")
    checks = {
        "policy_sha256": config["policy"],
        "recent_windows_sha256": config["recent_windows"],
        "acceptance_sha256": config["acceptance_gates"],
        "bootstrap_sha256": config["bootstrap"],
    }
    for key, value in checks.items():
        if canonical_json_sha256(value) != str(lock[key]):
            raise ValueError(f"Locked contract section changed: {key}")


def verify_v10_artifact(
    manifest: Mapping[str, Any],
    relative_name: str,
) -> Path:
    spec = manifest["artifacts"].get(relative_name)
    if spec is None:
        raise ValueError(f"V10 manifest is missing {relative_name}")
    path = REPO_ROOT / str(spec["path"])
    if sha256_file(path) != str(spec["sha256"]):
        raise ValueError(f"V10 artifact hash mismatch: {relative_name}")
    return path


def prepare_source(
    dataset: pd.DataFrame,
    splits: pd.DataFrame,
    v10_config: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(dataset) != int(v10_config["population"]["expected_canonical_rows"]):
        raise ValueError("Canonical row count changed")
    if dataset["candidate_id"].duplicated().any():
        raise ValueError("Canonical candidate IDs are duplicated")
    population = dataset.loc[
        dataset[str(v10_config["population"]["eligibility_column"])].eq(
            str(v10_config["population"]["eligibility_value"])
        )
    ].copy()
    if len(population) != int(
        v10_config["population"]["expected_xau_feature_pass_rows"]
    ):
        raise ValueError("Feature-pass population changed")
    for column in ("decision_time", "label_end_time"):
        population[column] = pd.to_datetime(population[column], utc=True)
    if (
        population["initial_risk_usd_0p01"].isna().any()
        or population["initial_risk_usd_0p01"].le(0.0).any()
    ):
        raise ValueError("Normalized 0.01-lot risk must be positive")
    source = population.merge(
        splits[
            [
                "fold_id",
                "candidate_id",
                "structural_episode_id",
                "assignment",
                "dataset_eligible",
            ]
        ],
        on=["candidate_id", "structural_episode_id"],
        how="inner",
        validate="one_to_many",
    )
    source = source.loc[source["dataset_eligible"].astype(bool)].copy()
    return population, source


def attach_risk(
    predictions: pd.DataFrame,
    population: pd.DataFrame,
) -> pd.DataFrame:
    result = predictions.drop(columns=["initial_risk_usd_0p01"], errors="ignore").merge(
        population[["candidate_id", "initial_risk_usd_0p01"]],
        on="candidate_id",
        how="left",
        validate="one_to_one",
    )
    if result["initial_risk_usd_0p01"].isna().any():
        raise ValueError("Predictions could not be joined to normalized risk")
    for column in ("decision_time", "label_end_time"):
        result[column] = pd.to_datetime(result[column], utc=True)
    return result


def score_calibration(
    source: pd.DataFrame,
    fold_id: str,
    model: Any,
    assignment: str,
) -> pd.DataFrame:
    calibration = source.loc[
        source["fold_id"].eq(fold_id) & source["assignment"].eq(assignment)
    ].copy()
    calibration["model_score"] = model.predict(calibration)
    return calibration


def fold_row(
    fold_id: str,
    action: str,
    fit_rows: int,
    quantile: float,
    threshold: float,
    v12: Mapping[str, Any],
    v11: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "fold_id": fold_id,
        "action": action,
        "fit_rows": int(fit_rows),
        "chosen_quantile": float(quantile),
        "chosen_threshold": float(threshold),
        **flatten_metrics("baseline", v12["baseline"]),
        **flatten_metrics("v12", v12["selected"]),
        "v12_selected_weight_coverage": v12["selected_weight_coverage"],
        "v12_profit_delta_r": v12["selected_profit_delta_r"],
        "v12_profit_delta_usd": v12["selected_profit_delta_usd"],
        "v12_drawdown_ratio_to_baseline": v12["drawdown_ratio_to_baseline"],
        **flatten_metrics("v11", v11["selected"]),
        "v11_selected_weight_coverage": v11["selected_weight_coverage"],
        "v11_profit_delta_r": v11["selected_profit_delta_r"],
        "v11_profit_delta_usd": v11["selected_profit_delta_usd"],
    }


def window_row(
    months: int,
    start: pd.Timestamp,
    end: pd.Timestamp,
    v12_predictions: pd.DataFrame,
    v11_predictions: pd.DataFrame,
) -> dict[str, Any]:
    mask_v12 = v12_predictions["decision_time"].ge(start) & v12_predictions[
        "decision_time"
    ].lt(end)
    mask_v11 = v11_predictions["decision_time"].ge(start) & v11_predictions[
        "decision_time"
    ].lt(end)
    v12 = comparison(v12_predictions.loc[mask_v12])
    v11 = comparison(v11_predictions.loc[mask_v11])
    return {
        "months": int(months),
        "start_utc": start,
        "end_exclusive_utc": end,
        **flatten_metrics("baseline", v12["baseline"]),
        **flatten_metrics("v12", v12["selected"]),
        **flatten_metrics("v11", v11["selected"]),
        "v12_profit_delta_vs_baseline_usd": v12["selected_profit_delta_usd"],
        "v12_profit_delta_vs_v11_usd": float(
            v12["selected"]["normalized_weighted_usd_sum"]
            - v11["selected"]["normalized_weighted_usd_sum"]
        ),
    }


def acceptance_checks(
    pooled: Mapping[str, Any],
    v11_pooled: Mapping[str, Any],
    folds: pd.DataFrame,
    recent: pd.DataFrame,
    bootstrap: Mapping[str, Any],
    gates: Mapping[str, Any],
) -> dict[str, bool]:
    latest = folds.loc[folds["fold_id"].eq("F2025")].iloc[0]
    selected = pooled["selected"]
    baseline = pooled["baseline"]
    return {
        "minimum_total_normalized_usd_vs_baseline": float(
            selected["normalized_weighted_usd_sum"]
            - baseline["normalized_weighted_usd_sum"]
        )
        > float(gates["minimum_total_normalized_usd_vs_baseline"]),
        "minimum_total_normalized_usd_vs_v11": float(
            selected["normalized_weighted_usd_sum"]
            - v11_pooled["selected"]["normalized_weighted_usd_sum"]
        )
        > float(gates["minimum_total_normalized_usd_vs_v11"]),
        "minimum_profit_delta_bootstrap_lower_usd": float(
            bootstrap["intervals"]["selected_profit_delta_usd"]["lower"]
        )
        > float(gates["minimum_profit_delta_bootstrap_lower_usd"]),
        "minimum_selected_weighted_mean_r": float(selected["weighted_mean_r"])
        >= float(gates["minimum_selected_weighted_mean_r"]),
        "minimum_selected_profit_factor": float(
            selected["weighted_profit_factor"]
        )
        >= float(gates["minimum_selected_profit_factor"]),
        "maximum_drawdown_ratio_to_baseline": float(
            pooled["drawdown_ratio_to_baseline"]
        )
        <= float(gates["maximum_drawdown_ratio_to_baseline"]),
        "minimum_selected_rows": int(selected["rows"])
        >= int(gates["minimum_selected_rows"]),
        "minimum_latest_fold_normalized_usd_vs_baseline": float(
            latest["v12_normalized_weighted_usd_sum"]
            - latest["baseline_normalized_weighted_usd_sum"]
        )
        > float(gates["minimum_latest_fold_normalized_usd_vs_baseline"]),
        "minimum_latest_fold_normalized_usd_vs_v11": float(
            latest["v12_normalized_weighted_usd_sum"]
            - latest["v11_normalized_weighted_usd_sum"]
        )
        > float(gates["minimum_latest_fold_normalized_usd_vs_v11"]),
        "minimum_recent_window_profit_wins_vs_v11": int(
            recent["v12_profit_delta_vs_v11_usd"].gt(0.0).sum()
        )
        >= int(gates["minimum_recent_window_profit_wins_vs_v11"]),
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
        "schema_version": "xauusd_profit_policy_v12_artifact_manifest",
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
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    verify_lock(config, lock)
    inputs = resolve_inputs(REPO_ROOT, config)
    v10_config = load_json(inputs["v10_config"])
    v10_manifest = load_json(inputs["v10_manifest"])
    dataset = pd.read_parquet(inputs["canonical_dataset"])
    splits = pd.read_parquet(inputs["split_assignments"])
    population, source = prepare_source(dataset, splits, v10_config)
    v10_predictions = attach_risk(
        pd.read_parquet(inputs["v10_predictions"]), population
    )
    v11_predictions = attach_risk(
        pd.read_parquet(inputs["v11_predictions"]), population
    )
    if set(v10_predictions["candidate_id"]) != set(v11_predictions["candidate_id"]):
        raise ValueError("V10 and V11 prediction populations differ")

    predictions: list[pd.DataFrame] = []
    fold_rows: list[dict[str, Any]] = []
    threshold_rows: list[pd.DataFrame] = []
    policy = config["policy"]
    calibration_assignment = str(
        v10_config["outer_evaluation"]["calibration_assignment"]
    )
    for fold_id in v10_config["outer_evaluation"]["folds"]:
        model_name = f"models/EXPECTED_R_V10_{fold_id}.joblib"
        payload = joblib.load(verify_v10_artifact(v10_manifest, model_name))
        fit_rows = int(payload["fit_rows"])
        test = v10_predictions.loc[v10_predictions["fold_id"].eq(fold_id)].copy()
        if fit_rows < int(policy["minimum_fit_rows"]):
            chosen = {
                "quantile": float(policy["fallback_quantile"]),
                "threshold": float(test["model_score"].min()),
                "selection_reason": str(policy["unavailable_action"]),
            }
            test["selected"] = True
            action = str(policy["unavailable_action"])
        else:
            calibration = score_calibration(
                source,
                fold_id,
                payload["model"],
                calibration_assignment,
            )
            chosen, grid = choose_profit_threshold(calibration, policy)
            grid.insert(0, "fold_id", fold_id)
            grid["chosen"] = grid["quantile"].eq(float(chosen["quantile"]))
            threshold_rows.append(grid)
            test = apply_profit_threshold(
                test,
                chosen,
                float(policy["fallback_quantile"]),
            )
            action = str(chosen["selection_reason"])
        test["v12_threshold"] = float(chosen["threshold"])
        test["v12_quantile"] = float(chosen["quantile"])
        test["v12_action"] = action
        predictions.append(test)

        v12_metrics = comparison(test)
        v11_test = v11_predictions.loc[
            v11_predictions["fold_id"].eq(fold_id)
        ].copy()
        v11_metrics = comparison(v11_test)
        fold_rows.append(
            fold_row(
                fold_id,
                action,
                fit_rows,
                float(chosen["quantile"]),
                float(chosen["threshold"]),
                v12_metrics,
                v11_metrics,
            )
        )

    prediction_frame = (
        pd.concat(predictions, ignore_index=True)
        .sort_values(["decision_time", "candidate_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    if prediction_frame["candidate_id"].duplicated().any():
        raise ValueError("V12 out-of-time predictions contain duplicate candidates")
    fold_frame = pd.DataFrame(fold_rows)
    threshold_frame = pd.concat(threshold_rows, ignore_index=True)
    pooled = comparison(prediction_frame)
    v11_pooled = comparison(v11_predictions)

    end = pd.Timestamp(config["recent_windows"]["end_exclusive_utc"])
    recent_frame = pd.DataFrame(
        [
            window_row(
                int(months),
                end - pd.DateOffset(months=int(months)),
                end,
                prediction_frame,
                v11_predictions,
            )
            for months in config["recent_windows"]["months"]
        ]
    )
    bootstrap = weekly_profit_bootstrap(
        prediction_frame,
        resamples=int(config["bootstrap"]["resamples"]),
        confidence=float(config["bootstrap"]["confidence"]),
        seed=int(config["bootstrap"]["seed"]),
    )
    checks = acceptance_checks(
        pooled,
        v11_pooled,
        fold_frame,
        recent_frame,
        bootstrap,
        config["acceptance_gates"],
    )
    passed = all(checks.values())
    decision = (
        "PROFIT_POLICY_V12_HISTORICAL_GATE_PASS_FORWARD_CONFIRMATION_REQUIRED"
        if passed
        else "PROFIT_POLICY_V12_HISTORICAL_GATE_FAIL"
    )
    acceptance = {
        "schema_version": "xauusd_profit_policy_v12_acceptance",
        "all_required": True,
        "checks": checks,
        "passed_checks": int(sum(checks.values())),
        "required_checks": int(len(checks)),
        "passed": bool(passed),
        "decision": decision,
        "runtime_authorized": False,
    }

    final_model_path = verify_v10_artifact(
        v10_manifest, "EXPECTED_R_V10_FINAL_RESEARCH_MODEL.joblib"
    )
    final_payload = joblib.load(final_model_path)
    final_spec = v10_config["final_research_model"]
    calibration = population.loc[
        population["decision_time"].ge(
            pd.Timestamp(final_spec["calibration_start_utc"])
        )
        & population["decision_time"].lt(
            pd.Timestamp(final_spec["calibration_end_exclusive_utc"])
        )
    ].copy()
    calibration["model_score"] = final_payload["model"].predict(calibration)
    final_choice, _ = choose_profit_threshold(calibration, policy)
    final_policy = {
        "schema_version": "xauusd_profit_policy_v12_final_research_policy",
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "v10_final_model_path": str(final_model_path.relative_to(REPO_ROOT)).replace(
            "\\", "/"
        ),
        "v10_final_model_sha256": sha256_file(final_model_path),
        "calibration_rows": int(len(calibration)),
        "chosen_quantile": float(final_choice["quantile"]),
        "chosen_threshold": float(final_choice["threshold"]),
        "selection_reason": str(final_choice["selection_reason"]),
        "research_only": True,
        "runtime_authorized": False,
    }

    result = {
        "schema_version": "xauusd_profit_policy_v12_result",
        "decision": decision,
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "historical_outcomes_already_exposed": True,
        "development_selection_disclosed": True,
        "out_of_time_rows": int(len(prediction_frame)),
        "pooled": pooled,
        "v11_pooled": v11_pooled,
        "profit_delta_vs_v11_usd": float(
            pooled["selected"]["normalized_weighted_usd_sum"]
            - v11_pooled["selected"]["normalized_weighted_usd_sum"]
        ),
        "bootstrap": bootstrap,
        "acceptance": acceptance,
        "final_research_policy": final_policy,
        "runtime_changed": False,
        "ml_shadow_or_execution_activated": False,
        "authorization": config["authorization"],
    }

    prediction_frame.to_parquet(
        output / str(config["outputs"]["predictions"]), index=False
    )
    fold_frame.to_parquet(output / str(config["outputs"]["fold_metrics"]), index=False)
    threshold_frame.to_parquet(
        output / str(config["outputs"]["threshold_decisions"]), index=False
    )
    recent_frame.to_parquet(
        output / str(config["outputs"]["recent_windows"]), index=False
    )
    write_json(output / str(config["outputs"]["bootstrap"]), bootstrap)
    write_json(output / str(config["outputs"]["acceptance"]), acceptance)
    write_json(output / str(config["outputs"]["final_policy"]), final_policy)
    write_json(output / str(config["outputs"]["result_json"]), result)
    markdown = (
        "# Profit Policy V12 Result\n\n"
        f"- Decision: `{decision}`\n"
        f"- Out-of-time rows: {len(prediction_frame):,}\n"
        f"- Selected rows: {pooled['selected']['rows']:,}\n"
        f"- Selected candidates/weekday: "
        f"{pooled['selected']['candidates_per_weekday']:.6f}\n"
        f"- Baseline normalized USD: "
        f"${pooled['baseline']['normalized_weighted_usd_sum']:,.2f}\n"
        f"- V11 normalized USD: "
        f"${v11_pooled['selected']['normalized_weighted_usd_sum']:,.2f}\n"
        f"- V12 normalized USD: "
        f"${pooled['selected']['normalized_weighted_usd_sum']:,.2f}\n"
        f"- V12 minus baseline: ${pooled['selected_profit_delta_usd']:,.2f}\n"
        f"- V12 minus V11: ${result['profit_delta_vs_v11_usd']:,.2f}\n"
        f"- Selected weighted mean: "
        f"{pooled['selected']['weighted_mean_r']:.6f}R\n"
        f"- Selected PF: {pooled['selected']['weighted_profit_factor']:.6f}\n"
        f"- Selected max DD: "
        f"{pooled['selected']['normalized_weighted_max_drawdown_usd']:,.2f} USD\n"
        "- Runtime authorized: false\n"
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

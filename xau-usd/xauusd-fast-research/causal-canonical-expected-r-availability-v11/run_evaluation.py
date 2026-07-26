from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from policy import (
    apply_availability,
    canonical_json_sha256,
    comparison,
    resolve_inputs,
    sha256_file,
    weekly_bootstrap,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "availability_v11.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_lock(config: Mapping[str, Any], lock: Mapping[str, Any]) -> None:
    if sha256_file(CONFIG_PATH) != lock["config_sha256"]:
        raise ValueError("Configuration changed after lock")
    for name, spec in lock["implementation"].items():
        if sha256_file(REPO_ROOT / spec["path"]) != spec["sha256"]:
            raise ValueError(f"Implementation changed after lock: {name}")
    if canonical_json_sha256(config["availability"]) != lock["policy_sha256"]:
        raise ValueError("Availability policy changed after lock")
    if canonical_json_sha256(config["acceptance_gates"]) != lock["acceptance_sha256"]:
        raise ValueError("Acceptance gates changed after lock")


def flatten(prefix: str, metrics: Mapping[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": value for key, value in metrics.items()}


def build_metrics(
    predictions: pd.DataFrame,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    pooled = comparison(predictions)
    fold_rows = []
    for fold_id, group in predictions.groupby("fold_id", sort=True):
        metrics = comparison(group)
        fold_rows.append(
            {
                "fold_id": fold_id,
                "model_available": bool(group["model_available"].iloc[0]),
                **flatten("baseline", metrics["baseline"]),
                **flatten("selected", metrics["selected"]),
                "weighted_score_auc": metrics["weighted_score_auc"],
                "selected_weight_coverage": metrics["selected_weight_coverage"],
                "selected_mean_lift_r": metrics["selected_mean_lift_r"],
                "drawdown_ratio_to_baseline": metrics["drawdown_ratio_to_baseline"],
            }
        )
    family_rows = []
    for family_id, group in predictions.groupby("family_id", sort=True):
        metrics = comparison(group)
        family_rows.append(
            {
                "family_id": family_id,
                **flatten("baseline", metrics["baseline"]),
                **flatten("selected", metrics["selected"]),
                "weighted_score_auc": metrics["weighted_score_auc"],
                "selected_weight_coverage": metrics["selected_weight_coverage"],
                "selected_mean_lift_r": metrics["selected_mean_lift_r"],
                "drawdown_ratio_to_baseline": metrics["drawdown_ratio_to_baseline"],
            }
        )
    return pooled, pd.DataFrame(fold_rows), pd.DataFrame(family_rows)


def acceptance_checks(
    pooled: Mapping[str, Any],
    folds: pd.DataFrame,
    families: pd.DataFrame,
    bootstrap: Mapping[str, Any],
    gates: Mapping[str, Any],
) -> dict[str, bool]:
    latest = folds.loc[folds["fold_id"].eq("F2025")].iloc[0]
    active = folds.loc[folds["model_available"]]
    inactive = folds.loc[~folds["model_available"]]
    intervals = bootstrap["intervals"]
    family_weights = families["selected_weight"].to_numpy(dtype=float)
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
        "minimum_active_folds": int(len(active)) >= int(gates["minimum_active_folds"]),
        "minimum_active_fold_lift_r": bool(
            (
                active["selected_mean_lift_r"]
                > float(gates["minimum_active_fold_lift_r"])
            ).all()
        ),
        "minimum_all_fold_lift_r": bool(
            (
                folds["selected_mean_lift_r"] >= float(gates["minimum_all_fold_lift_r"])
            ).all()
        ),
        "inactive_folds_are_full_abstention": bool(
            np.allclose(inactive["selected_weight_coverage"], 1.0)
            and np.allclose(inactive["selected_mean_lift_r"], 0.0)
        ),
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
                families["selected_weighted_mean_r"]
                >= float(gates["minimum_family_selected_mean_r"])
            ).all()
        ),
        "maximum_single_family_selected_weight_fraction": float(
            family_weights.max() / family_weights.sum()
        )
        <= float(gates["maximum_single_family_selected_weight_fraction"]),
        "minimum_selected_rows": int(pooled["selected"]["rows"])
        >= int(gates["minimum_selected_rows"]),
    }


def manifest(
    output: Path,
    inputs: Mapping[str, Path],
    lock: Mapping[str, Any],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    name = str(config["outputs"]["manifest"])
    artifacts = [
        path for path in output.rglob("*") if path.is_file() and path.name != name
    ]
    return {
        "schema_version": "xauusd_expected_r_availability_v11_manifest",
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "inputs": {
            key: {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for key, path in inputs.items()
        },
        "artifacts": {
            str(path.relative_to(output)).replace("\\", "/"): {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for path in sorted(artifacts)
        },
    }


def main() -> int:
    config = load_json(CONFIG_PATH)
    output = ROOT / str(config["outputs"]["directory"])
    output.mkdir(parents=True, exist_ok=True)
    lock = load_json(output / str(config["outputs"]["contract_lock"]))
    verify_lock(config, lock)
    inputs = resolve_inputs(REPO_ROOT, config)
    predictions = pd.read_parquet(inputs["v10_predictions"])
    predictions["decision_time"] = pd.to_datetime(
        predictions["decision_time"], utc=True
    )
    folds_v10 = pd.read_parquet(inputs["v10_fold_metrics"])
    scored = (
        apply_availability(
            predictions,
            folds_v10,
            int(config["availability"]["minimum_fit_rows"]),
        )
        .sort_values(["decision_time", "candidate_id"], kind="mergesort")
        .reset_index(drop=True)
    )
    pooled, folds, families = build_metrics(scored)
    fit_rows = folds_v10.set_index("fold_id")["fit_rows"].astype(int).to_dict()
    folds["fit_rows"] = folds["fold_id"].map(fit_rows).astype(int)
    bootstrap = weekly_bootstrap(
        scored,
        resamples=int(config["bootstrap"]["resamples"]),
        confidence=float(config["bootstrap"]["confidence"]),
        seed=int(config["bootstrap"]["seed"]),
    )
    checks = acceptance_checks(
        pooled, folds, families, bootstrap, config["acceptance_gates"]
    )
    passed = all(checks.values())
    acceptance = {
        "schema_version": "xauusd_expected_r_availability_v11_acceptance",
        "all_required": True,
        "checks": checks,
        "passed_checks": int(sum(checks.values())),
        "required_checks": int(len(checks)),
        "passed": bool(passed),
        "decision": (
            "EXPECTED_R_V11_WORKING_OFFLINE_MODEL_FORWARD_CONFIRMATION_REQUIRED"
            if passed
            else "EXPECTED_R_V11_AVAILABILITY_GATE_FAIL"
        ),
        "runtime_authorized": False,
    }
    v10_result = load_json(inputs["v10_result"])
    final_fit_rows = int(v10_result["final_research_model"]["fit_rows"])
    final_policy = {
        "schema_version": "xauusd_expected_r_availability_v11_final_policy",
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "v10_model_path": str(inputs["v10_final_model"].relative_to(REPO_ROOT)).replace(
            "\\", "/"
        ),
        "v10_model_sha256": sha256_file(inputs["v10_final_model"]),
        "minimum_fit_rows": int(config["availability"]["minimum_fit_rows"]),
        "actual_final_fit_rows": final_fit_rows,
        "model_available": final_fit_rows
        >= int(config["availability"]["minimum_fit_rows"]),
        "unavailable_action": config["availability"]["unavailable_action"],
        "runtime_authorized": False,
        "research_only": True,
    }
    result = {
        "schema_version": "xauusd_expected_r_availability_v11_result",
        "decision": acceptance["decision"],
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "post_outcome_development_rule": True,
        "v10_predictions_changed": False,
        "inactive_folds": sorted(
            folds.loc[~folds["model_available"], "fold_id"].tolist()
        ),
        "active_folds": sorted(folds.loc[folds["model_available"], "fold_id"].tolist()),
        "out_of_time_rows": int(len(scored)),
        "pooled": pooled,
        "bootstrap": bootstrap,
        "acceptance": acceptance,
        "final_policy": final_policy,
        "runtime_changed": False,
        "ml_shadow_or_execution_activated": False,
        "authorization": config["authorization"],
    }
    scored.to_parquet(output / str(config["outputs"]["predictions"]), index=False)
    folds.to_parquet(output / str(config["outputs"]["fold_metrics"]), index=False)
    families.to_parquet(output / str(config["outputs"]["family_metrics"]), index=False)
    write_json(output / str(config["outputs"]["bootstrap"]), bootstrap)
    write_json(output / str(config["outputs"]["acceptance"]), acceptance)
    write_json(output / str(config["outputs"]["final_policy"]), final_policy)
    write_json(output / str(config["outputs"]["result_json"]), result)
    markdown = (
        "# Expected-R Availability V11 Result\n\n"
        f"- Decision: `{acceptance['decision']}`\n"
        f"- Active folds: {', '.join(result['active_folds'])}\n"
        f"- ML-abstain folds: {', '.join(result['inactive_folds'])}\n"
        f"- Selected candidates/weekday: "
        f"{pooled['selected']['candidates_per_weekday']:.6f}\n"
        f"- Selected weighted mean: "
        f"{pooled['selected']['weighted_mean_r']:.6f}R\n"
        f"- Expected-R lift: {pooled['selected_mean_lift_r']:.6f}R\n"
        f"- Selected PF: {pooled['selected']['weighted_profit_factor']:.6f}\n"
        f"- Selected coverage: {pooled['selected_weight_coverage']:.6%}\n"
        "- Runtime authorized: false\n"
    )
    (output / str(config["outputs"]["result_markdown"])).write_text(
        markdown, encoding="utf-8"
    )
    write_json(
        output / str(config["outputs"]["manifest"]),
        manifest(output, inputs, lock, config),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

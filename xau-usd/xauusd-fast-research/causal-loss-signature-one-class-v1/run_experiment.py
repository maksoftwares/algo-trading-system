from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd

from src.loss_only import (
    canonical_json_sha256,
    fit_loss_model,
    json_ready,
    loss_similarity,
    loss_veto_metrics,
    partition_for,
    prepare_dataset,
    resolve_inputs,
    sha256_file,
    weekly_block_bootstrap,
    weighted_quantile,
    write_json,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "loss_signature_one_class_v1.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_lock(config: Mapping[str, Any], lock: Mapping[str, Any]) -> None:
    if sha256_file(CONFIG_PATH) != str(lock["config_sha256"]):
        raise ValueError("Loss-only config changed after contract lock")
    if sha256_file(ROOT / "PREREGISTRATION.md") != str(lock["preregistration_sha256"]):
        raise ValueError("Loss-only preregistration changed after contract lock")
    for name, spec in lock["implementation"].items():
        if sha256_file(REPO_ROOT / str(spec["path"])) != str(spec["sha256"]):
            raise ValueError(f"Implementation changed after lock: {name}")
    if any(
        bool(value)
        for key, value in config["authorization"].items()
        if key != "research_only"
    ):
        raise ValueError("Loss-only experiment has forbidden runtime authorization")


def acceptance_checks(
    pooled: Mapping[str, Any],
    folds: pd.DataFrame,
    bootstrap: Mapping[str, Any],
    gates: Mapping[str, Any],
) -> dict[str, bool]:
    latest = folds.loc[
        folds["fold_id"].eq("F2026") & folds["primary"].astype(bool)
    ].iloc[0]
    primary = folds.loc[folds["primary"].astype(bool)]
    baseline_pf = pooled["baseline"]["weighted_profit_factor"]
    retained_pf = pooled["retained"]["weighted_profit_factor"]
    return {
        "pooled_weighted_loss_auc": float(pooled["weighted_loss_auc"])
        >= float(gates["pooled_weighted_loss_auc_minimum"]),
        "pooled_loss_precision_lift": float(pooled["loss_precision_lift"])
        >= float(gates["pooled_loss_precision_lift_minimum"]),
        "precision_lift_bootstrap_lower": float(
            bootstrap["loss_precision_lift"]["lower"]
        )
        > float(gates["loss_precision_lift_bootstrap_lower_strictly_above"]),
        "pooled_loss_recall": float(pooled["loss_recall"])
        >= float(gates["pooled_loss_recall_minimum"]),
        "pooled_retained_coverage": float(pooled["retained_coverage"])
        >= float(gates["pooled_retained_coverage_minimum"]),
        "pooled_retained_ev_lift": float(pooled["retained_ev_lift_r"])
        >= float(gates["pooled_retained_ev_lift_minimum_r"]),
        "retained_ev_lift_bootstrap_lower": float(
            bootstrap["retained_ev_lift_r"]["lower"]
        )
        > float(gates["retained_ev_lift_bootstrap_lower_strictly_above"]),
        "retained_profit_factor": retained_pf is not None
        and baseline_pf is not None
        and float(retained_pf) > float(baseline_pf),
        "positive_precision_lift_folds": int(
            primary["loss_precision_lift"].gt(0.0).sum()
        )
        >= int(gates["minimum_positive_precision_lift_folds"]),
        "positive_retained_ev_lift_folds": int(
            primary["retained_ev_lift_r"].gt(0.0).sum()
        )
        >= int(gates["minimum_positive_retained_ev_lift_folds"]),
        "latest_fold_precision_lift": (
            float(latest["loss_precision_lift"]) > 0.0
            if gates["latest_fold_requires_positive_precision_lift"]
            else True
        ),
        "latest_fold_retained_ev_lift": (
            float(latest["retained_ev_lift_r"]) > 0.0
            if gates["latest_fold_requires_positive_retained_ev_lift"]
            else True
        ),
    }


def flatten_fold_metrics(
    *,
    fold_id: str,
    quantile: float,
    primary: bool,
    threshold: float,
    fit_rows: int,
    fit_loss_rows: int,
    test: pd.DataFrame,
    metrics: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "fold_id": fold_id,
        "quantile": quantile,
        "primary": primary,
        "threshold": threshold,
        "fit_rows": fit_rows,
        "fit_loss_rows": fit_loss_rows,
        "fit_winner_rows": 0,
        "test_rows": len(test),
        "weighted_loss_auc": metrics["weighted_loss_auc"],
        "weighted_loss_average_precision": metrics["weighted_loss_average_precision"],
        "baseline_loss_rate": metrics["baseline_loss_rate"],
        "flagged_loss_precision": metrics["flagged_loss_precision"],
        "loss_precision_lift": metrics["loss_precision_lift"],
        "loss_recall": metrics["loss_recall"],
        "winner_collateral_rate": metrics["winner_collateral_rate"],
        "flagged_coverage": metrics["flagged_coverage"],
        "retained_coverage": metrics["retained_coverage"],
        "retained_ev_lift_r": metrics["retained_ev_lift_r"],
        "baseline_weighted_mean_stress_r": metrics["baseline"][
            "weighted_mean_stress_r"
        ],
        "baseline_weighted_profit_factor": metrics["baseline"][
            "weighted_profit_factor"
        ],
        "baseline_weighted_max_drawdown_r": metrics["baseline"][
            "weighted_max_drawdown_r"
        ],
        "vetoed_weighted_mean_stress_r": metrics["vetoed"]["weighted_mean_stress_r"],
        "retained_weighted_mean_stress_r": metrics["retained"][
            "weighted_mean_stress_r"
        ],
        "retained_weighted_profit_factor": metrics["retained"][
            "weighted_profit_factor"
        ],
        "retained_weighted_max_drawdown_r": metrics["retained"][
            "weighted_max_drawdown_r"
        ],
    }


def artifact_manifest(
    config: Mapping[str, Any],
    inputs: Mapping[str, Path],
    output: Path,
    *,
    decision: str,
    lock_sha256: str,
) -> dict[str, Any]:
    artifacts: dict[str, Any] = {}
    manifest_name = str(config["outputs"]["manifest"])
    for path in sorted(output.rglob("*")):
        if not path.is_file() or path.name == manifest_name:
            continue
        relative = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        artifacts[relative] = {"path": relative, "sha256": sha256_file(path)}
    return {
        "schema_version": "xauusd_loss_only_v1_artifact_manifest",
        "definition_contract_sha256": lock_sha256,
        "decision": decision,
        "inputs": {
            name: {
                "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for name, path in inputs.items()
        },
        "artifacts": artifacts,
        "authorization": config["authorization"],
    }


def main() -> int:
    config = load_json(CONFIG_PATH)
    output = ROOT / str(config["outputs"]["directory"])
    lock_path = output / str(config["outputs"]["contract_lock"])
    if not lock_path.is_file():
        raise FileNotFoundError("Run lock_contract.py before the experiment")
    lock = load_json(lock_path)
    verify_lock(config, lock)
    inputs = resolve_inputs(REPO_ROOT, config)
    v4_config = load_json(inputs["v4_dataset_config"])
    features = list(v4_config["model_features"])
    if canonical_json_sha256(features) != str(config["population"]["feature_sha256"]):
        raise ValueError("V4 feature surface does not match the frozen experiment")
    source = prepare_dataset(
        pd.read_parquet(inputs["v4_action_dataset"]), config, features
    )
    splits = pd.read_parquet(inputs["v4_split_assignments"])
    output.mkdir(parents=True, exist_ok=True)
    model_dir = output / str(config["outputs"]["model_directory"])
    model_dir.mkdir(parents=True, exist_ok=True)

    primary_quantile = float(config["training"]["primary_weighted_loss_quantile"])
    quantiles = [
        primary_quantile,
        *[
            float(value)
            for value in config["training"]["diagnostic_weighted_loss_quantiles"]
        ],
    ]
    predictions: list[pd.DataFrame] = []
    fold_rows: list[dict[str, Any]] = []
    for fold_index, fold_id in enumerate(config["folds"]):
        fit = partition_for(source, splits, fold_id=fold_id, partition="FIT")
        test = partition_for(source, splits, fold_id=fold_id, partition="TEST")
        losses = fit.loc[~fit["stress_net_r_positive"].astype(bool)].copy()
        model_spec = dict(config["training"]["model"])
        model_spec["random_state"] = int(model_spec["random_state"]) + fold_index
        model = fit_loss_model(losses, features=features, model_config=model_spec)
        loss_fit_scores = loss_similarity(model, losses, features)
        test = test.copy()
        test["loss_similarity"] = loss_similarity(model, test, features)
        test["fold_id"] = fold_id
        for quantile in quantiles:
            threshold = weighted_quantile(
                loss_fit_scores,
                losses["structural_weight"].to_numpy(dtype=float),
                quantile,
            )
            flagged = test["loss_similarity"].ge(threshold).to_numpy()
            metrics = loss_veto_metrics(test, flagged)
            fold_rows.append(
                flatten_fold_metrics(
                    fold_id=fold_id,
                    quantile=quantile,
                    primary=quantile == primary_quantile,
                    threshold=threshold,
                    fit_rows=len(fit),
                    fit_loss_rows=len(losses),
                    test=test,
                    metrics=metrics,
                )
            )
            if quantile == primary_quantile:
                test["threshold"] = threshold
                test["flagged"] = flagged
                predictions.append(
                    test[
                        [
                            "fold_id",
                            "candidate_id",
                            "event_id",
                            "structural_episode_id",
                            "signal_time",
                            "mechanism_signature",
                            "direction",
                            "regime",
                            "action_id",
                            "current_account_feasible",
                            "structural_weight",
                            "stress_net_r",
                            "stress_net_r_positive",
                            "loss_similarity",
                            "threshold",
                            "flagged",
                        ]
                    ]
                )
                joblib.dump(
                    {
                        "estimator": model,
                        "features": features,
                        "fold_id": fold_id,
                        "threshold": threshold,
                        "weighted_loss_quantile": primary_quantile,
                        "fit_rows": len(fit),
                        "fit_loss_rows": len(losses),
                        "fit_winner_rows": 0,
                        "definition_contract_sha256": lock[
                            "definition_contract_sha256"
                        ],
                        "runtime_authorized": False,
                    },
                    model_dir / f"LOSS_ONLY_ISOLATION_FOREST_{fold_id}.joblib",
                    compress=3,
                )

    prediction_frame = pd.concat(predictions, ignore_index=True).sort_values(
        ["signal_time", "candidate_id"], kind="mergesort"
    )
    fold_frame = pd.DataFrame(fold_rows).sort_values(
        ["fold_id", "quantile"], kind="mergesort"
    )
    pooled = loss_veto_metrics(prediction_frame, prediction_frame["flagged"].to_numpy())
    feasible = prediction_frame.loc[prediction_frame["current_account_feasible"]]
    feasible_metrics = loss_veto_metrics(feasible, feasible["flagged"].to_numpy())
    bootstrap = weekly_block_bootstrap(
        prediction_frame,
        resamples=int(config["bootstrap"]["resamples"]),
        confidence=float(config["bootstrap"]["confidence"]),
        seed=int(config["bootstrap"]["seed"]),
    )
    checks = acceptance_checks(
        pooled, fold_frame, bootstrap, config["acceptance_gates"]
    )
    passed = all(checks.values())
    decision = (
        "LOSS_ONLY_SIGNATURE_PROGRESS_RESEARCH_ONLY"
        if passed
        else "LOSS_ONLY_SIGNATURE_NO_RELIABLE_PROGRESS"
    )
    acceptance = {
        "schema_version": "xauusd_loss_only_v1_acceptance",
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "required_checks": len(checks),
        "all_required": True,
        "passed": passed,
        "decision": decision,
        "runtime_authorized": False,
    }
    result = {
        "schema_version": "xauusd_loss_only_v1_result",
        "decision": decision,
        "definition_contract_sha256": lock["definition_contract_sha256"],
        "dataset_rows": len(source),
        "dataset_failures": int((~source["stress_net_r_positive"].astype(bool)).sum()),
        "dataset_winners": int(source["stress_net_r_positive"].astype(bool).sum()),
        "feature_count": len(features),
        "folds": list(config["folds"]),
        "out_of_time_rows": len(prediction_frame),
        "fit_winner_rows": 0,
        "primary_weighted_loss_quantile": primary_quantile,
        "pooled": pooled,
        "current_account_feasible": feasible_metrics,
        "bootstrap": bootstrap,
        "acceptance": acceptance,
        "runtime_changed": False,
        "ml_shadow_or_execution_activated": False,
    }
    prediction_frame.to_parquet(
        output / str(config["outputs"]["predictions"]), index=False
    )
    fold_frame.to_parquet(output / str(config["outputs"]["fold_metrics"]), index=False)
    write_json(output / str(config["outputs"]["bootstrap"]), bootstrap)
    write_json(output / str(config["outputs"]["acceptance"]), acceptance)
    write_json(output / str(config["outputs"]["result_json"]), result)
    markdown = [
        "# Loss-Only One-Class V1 Result",
        "",
        f"Decision: `{decision}`",
        "",
        f"- Dataset failures used by fold training: `{result['dataset_failures']}` available; winners fitted: `0`.",
        f"- Out-of-time rows: `{len(prediction_frame)}`.",
        f"- Weighted loss AUC: `{pooled['weighted_loss_auc']:.6f}`.",
        f"- Loss precision: `{pooled['flagged_loss_precision']:.6f}` versus baseline `{pooled['baseline_loss_rate']:.6f}`.",
        f"- Precision lift: `{pooled['loss_precision_lift']:.6f}`.",
        f"- Loss recall: `{pooled['loss_recall']:.6f}`; winner collateral: `{pooled['winner_collateral_rate']:.6f}`.",
        f"- Retained coverage: `{pooled['retained_coverage']:.6f}`.",
        f"- Retained EV lift: `{pooled['retained_ev_lift_r']:.6f}R`.",
        f"- Gates passed: `{acceptance['passed_checks']}/{acceptance['required_checks']}`.",
        "",
        "This is exposed-history research only and has no runtime authorization.",
        "",
    ]
    (output / str(config["outputs"]["result_markdown"])).write_text(
        "\n".join(markdown), encoding="utf-8"
    )
    manifest = artifact_manifest(
        config,
        inputs,
        output,
        decision=decision,
        lock_sha256=str(lock["definition_contract_sha256"]),
    )
    write_json(output / str(config["outputs"]["manifest"]), manifest)
    print(json.dumps(json_ready(result), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

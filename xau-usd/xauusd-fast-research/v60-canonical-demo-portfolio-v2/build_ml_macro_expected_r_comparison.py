from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from build_ml_profit_policy_comparison import (
    CONFIG_PATH,
    LEDGER_PATH,
    REPO_ROOT,
    REPORTS,
    load_cooldowns,
    load_joined_trades,
    relative_path,
    sha256_file,
    window_rows,
)

ROOT = Path(__file__).resolve().parent
ML_ROOT = REPO_ROOT / "xau-usd/xauusd-fast-research/causal-candidate-quality-ml-v1"
V10_ROOT = REPO_ROOT / "xau-usd/xauusd-fast-research/causal-canonical-expected-r-v10"
V12_ROOT = REPO_ROOT / "xau-usd/xauusd-fast-research/causal-canonical-profit-policy-v12"
CANONICAL_PATH = ML_ROOT / "outputs/step_3/STEP_3_CANONICAL_DATASET.parquet"
SPLITS_PATH = ML_ROOT / "outputs/step_3/STEP_3_SPLIT_ASSIGNMENTS.parquet"
FEATURE_CONTRACT_PATH = ML_ROOT / "config/step_2b_dataset_feature_contract_v1.json"
V10_CONFIG_PATH = V10_ROOT / "config/canonical_expected_r_v10.json"
EXPECTED_R_PATH = V10_ROOT / "src/expected_r.py"
V12_CONFIG_PATH = V12_ROOT / "config/profit_policy_v12.json"
POLICY_PATH = V12_ROOT / "policy.py"

EXPECTED_SHA256 = {
    CANONICAL_PATH: "fc4771063013cf3633192715d2124c374cf37b44b1be9c1fddde7f67741fbc45",
    SPLITS_PATH: "0ba856a55666af55243d104ada4195b0850f522cfd608a4c623e07630137d3fc",
    FEATURE_CONTRACT_PATH: "f1cafa6375db1597e9721397bb6c2f7e54b25ead9016df6fdc670a94584317de",
    V10_CONFIG_PATH: "3af418d65876277711b5a480c015275c8df70bfcd84dea467c7499bb2684ae97",
    EXPECTED_R_PATH: "2ea01130ab139fc6795909724ae375ad03cf69e3e17b09bd66b8905446a66f0a",
    V12_CONFIG_PATH: "8ad9446682f6996b17f07feccc574e13f18237be1c0abb435e87831484a3362e",
    POLICY_PATH: "f8400eba4fa06c06a9bee7c29a7e7817ec78316bc6059ed33f612a871c122a00",
    LEDGER_PATH: "ba9044e0f5ef73292b3b243c39c6b9aa8d7f9921da33633b3354281f378b5bbf",
    CONFIG_PATH: "37e6fbae77af5c615977cd0341ef0053349c70f96829db4a63d78c168e3f840f",
}

SOURCE_BLOCKS = [
    "B1_DETERMINISTIC_CANDIDATE_AND_REGIME",
    "B2_PLUS_XAU_MICROSTRUCTURE_AND_COST",
    "B3_PLUS_COMPLETED_CROSS_ASSET_STATE",
]
MODEL_SETTINGS = {
    "kind": "RIDGE_PARTIAL_POOLING_EXPECTED_R",
    "alpha": 300.0,
    "family_interaction_scale": 0.25,
    "target_clip_min_r": -3.0,
    "target_clip_max_r": 3.0,
    "minimum_fit_rows": 1000,
}
PROFIT_POLICY_OVERRIDES = {
    "weighted_quantile_grid": [0.0, 0.025, 0.05, 0.075, 0.1, 0.15],
    "minimum_selected_weight_coverage": 0.85,
    "minimum_profit_improvement_usd": 10.0,
}

SUMMARY_PATH = REPORTS / "V60_ML_B123_EXPECTED_R_COMPARISON.json"
WINDOWS_PATH = REPORTS / "V60_ML_B123_EXPECTED_R_WINDOWS.csv"
FOLDS_PATH = REPORTS / "V60_ML_B123_EXPECTED_R_FOLDS.csv"
PREDICTIONS_PATH = REPORTS / "V60_ML_B123_EXPECTED_R_PREDICTIONS.parquet"
AUDIT_PATH = REPORTS / "V60_ML_B123_EXPECTED_R_TRADE_AUDIT.csv"


def _load_implementations() -> tuple[Any, Any]:
    sys.path.insert(0, str(V10_ROOT))
    sys.path.insert(0, str(V12_ROOT))
    import policy

    from src import expected_r

    return expected_r, policy


def verify_inputs() -> dict[str, str]:
    observed: dict[str, str] = {}
    for path, expected in EXPECTED_SHA256.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = sha256_file(path)
        if digest != expected:
            raise ValueError(f"B123 diagnostic input changed for {relative_path(path)}")
        observed[relative_path(path)] = digest
    return observed


def build_predictions() -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    expected_r, policy_module = _load_implementations()
    config = json.loads(V10_CONFIG_PATH.read_text(encoding="utf-8"))
    config["features"]["source_blocks"] = SOURCE_BLOCKS
    policy = json.loads(V12_CONFIG_PATH.read_text(encoding="utf-8"))["policy"]
    policy.update(PROFIT_POLICY_OVERRIDES)
    contract = json.loads(FEATURE_CONTRACT_PATH.read_text(encoding="utf-8"))
    _, numeric_features = expected_r.feature_surface(contract, config)
    dataset = pd.read_parquet(CANONICAL_PATH)
    splits = pd.read_parquet(SPLITS_PATH)
    source = expected_r.prepare_dataset(dataset, splits, config, numeric_features)

    predictions: list[pd.DataFrame] = []
    fold_rows: list[dict[str, Any]] = []
    for fold_id in config["outer_evaluation"]["folds"]:
        fold = source["fold_id"].eq(fold_id)
        fit = source.loc[fold & source["assignment"].eq("FIT")].copy()
        calibration = source.loc[fold & source["assignment"].eq("CALIBRATION")].copy()
        test = source.loc[fold & source["assignment"].eq("TEST")].copy()
        if len(fit) < int(MODEL_SETTINGS["minimum_fit_rows"]):
            test["model_score"] = None
            test["selected"] = True
            chosen = {
                "quantile": 0.0,
                "threshold": None,
                "selection_reason": "ML_ABSTAIN_RETAIN_ALL_INSUFFICIENT_FIT",
            }
        else:
            model = expected_r.PartialPoolingExpectedR.fit(
                fit,
                numeric_features=numeric_features,
                families=config["population"]["families"],
                alpha=float(MODEL_SETTINGS["alpha"]),
                interaction_scale=float(MODEL_SETTINGS["family_interaction_scale"]),
                target_clip=(
                    float(MODEL_SETTINGS["target_clip_min_r"]),
                    float(MODEL_SETTINGS["target_clip_max_r"]),
                ),
            )
            calibration["model_score"] = model.predict(calibration)
            test["model_score"] = model.predict(test)
            chosen, _ = policy_module.choose_profit_threshold(calibration, policy)
            test = policy_module.apply_profit_threshold(
                test, chosen, float(policy["fallback_quantile"])
            )
        test["b123_quantile"] = float(chosen["quantile"])
        test["b123_threshold"] = chosen["threshold"]
        test["b123_action"] = str(chosen["selection_reason"])
        test["fold_id"] = fold_id
        broad = policy_module.comparison(test)
        fold_rows.append(
            {
                "fold_id": fold_id,
                "fit_rows": len(fit),
                "calibration_rows": len(calibration),
                "test_rows": len(test),
                "chosen_quantile": float(chosen["quantile"]),
                "chosen_threshold": chosen["threshold"],
                "selection_reason": str(chosen["selection_reason"]),
                "selected_rows": int(test["selected"].sum()),
                "selected_weight_coverage": broad["selected_weight_coverage"],
                "broad_candidate_delta_usd": broad["selected_profit_delta_usd"],
                "broad_candidate_delta_r": broad["selected_profit_delta_r"],
            }
        )
        predictions.append(
            test[
                [
                    "candidate_id",
                    "fold_id",
                    "decision_time",
                    "family_id",
                    "model_score",
                    "selected",
                    "b123_quantile",
                    "b123_threshold",
                    "b123_action",
                ]
            ]
        )
    result = pd.concat(predictions, ignore_index=True)
    if result["candidate_id"].duplicated().any():
        raise ValueError("B123 out-of-time predictions contain duplicates")
    return result, pd.DataFrame(fold_rows), numeric_features


def build_outputs() -> tuple[
    dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    hashes = verify_inputs()
    predictions, broad_folds, numeric_features = build_predictions()
    trades, join_checks = load_joined_trades()
    replace_columns = [
        "fold_id",
        "model_score",
        "threshold",
        "v12_threshold",
        "v12_quantile",
        "v12_action",
        "selected",
        "v12_prediction_available",
        "v12_retained",
    ]
    trades = trades.drop(
        columns=[column for column in replace_columns if column in trades]
    )
    trades = trades.merge(
        predictions[
            [
                "candidate_id",
                "fold_id",
                "model_score",
                "selected",
                "b123_quantile",
                "b123_threshold",
                "b123_action",
            ]
        ],
        on="candidate_id",
        how="left",
        validate="one_to_one",
    )
    trades["v12_prediction_available"] = trades["model_score"].notna()
    trades["v12_retained"] = trades["selected"].fillna(True).astype(bool)
    trades["v12_action"] = trades["b123_action"].fillna("MODEL_ABSTAIN_RETAIN_ALL")
    windows, audits = window_rows(trades, load_cooldowns())
    window_index = windows.set_index("period")
    diagnostics = {
        "six_month_net_pnl_improved": bool(
            window_index.at["6M", "delta_net_pnl_usd"] > 0.0
        ),
        "twelve_month_net_pnl_improved": bool(
            window_index.at["1Y", "delta_net_pnl_usd"] > 0.0
        ),
        "all_history_net_pnl_improved": bool(
            window_index.at["ALL", "delta_net_pnl_usd"] > 0.0
        ),
        "all_history_profit_factor_improved": bool(
            window_index.at["ALL", "delta_profit_factor"] > 0.0
        ),
        "all_history_drawdown_not_worse": bool(
            window_index.at["ALL", "delta_closed_trade_drawdown_usd"] <= 0.0
        ),
        "latest_three_month_net_pnl_improved": bool(
            window_index.at["3M", "delta_net_pnl_usd"] > 0.0
        ),
        "prospective_confirmation_available": False,
    }
    report = {
        "schema_version": "xauusd_v60_ml_b123_expected_r_comparison_v1",
        "status": "HISTORICAL_DIAGNOSTIC_POSITIVE_LATEST_WINDOW_FAIL",
        "deployment_eligible": False,
        "historical_outcomes_already_exposed": True,
        "post_outcome_parameter_selection_disclosed": True,
        "input_sha256": hashes,
        "data_checks": join_checks,
        "model": {
            **MODEL_SETTINGS,
            "source_blocks": SOURCE_BLOCKS,
            "numeric_feature_count": len(numeric_features),
            "profit_policy_overrides": PROFIT_POLICY_OVERRIDES,
            "missing_prediction_action": "MODEL_ABSTAIN_RETAIN_ALL",
        },
        "diagnostic_checks": diagnostics,
        "authorization": {
            "offline_research_authorized": True,
            "python_serving_authorized": False,
            "ml_shadow_authorized": False,
            "ea_consumption_authorized": False,
            "demo_authorized": False,
            "live_authorized": False,
            "broker_action_authorized": False,
            "runtime_change_authorized": False,
        },
        "artifact_paths": {
            "windows_csv": relative_path(WINDOWS_PATH),
            "folds_csv": relative_path(FOLDS_PATH),
            "predictions_parquet": relative_path(PREDICTIONS_PATH),
            "trade_audit_csv": relative_path(AUDIT_PATH),
        },
        "limitations": [
            "This B3 design was formalized after its historical portfolio result was observed.",
            "The latest three-month portfolio remains worse than non-ML.",
            "The model has no prospective Capital dollar/bond feature confirmation.",
            "The exact comparison can veto routed trades but cannot re-admit historically rejected candidates.",
            "No historical result authorizes ML use in demo or live trading.",
        ],
    }
    audit_columns = [
        "trade_id",
        "candidate_id",
        "family_id",
        "fold_id",
        "signal_time",
        "entry_time",
        "exit_time",
        "direction",
        "fee_stress_pnl_usd",
        "model_score",
        "b123_quantile",
        "b123_threshold",
        "v12_action",
        "v12_retained",
        "raw_cooldown_accepted",
        "raw_cooldown_reason",
        "ml_cooldown_accepted",
        "ml_cooldown_reason",
    ]
    return (
        report,
        windows,
        broad_folds,
        predictions,
        audits["ALL"][audit_columns],
    )


def main() -> int:
    report, windows, folds, predictions, audit = build_outputs()
    REPORTS.mkdir(parents=True, exist_ok=True)
    windows.to_csv(WINDOWS_PATH, index=False)
    folds.to_csv(FOLDS_PATH, index=False)
    predictions.to_parquet(PREDICTIONS_PATH, index=False)
    audit.to_csv(AUDIT_PATH, index=False)
    SUMMARY_PATH.write_text(
        json.dumps(report, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

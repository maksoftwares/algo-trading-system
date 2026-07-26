from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.consensus import (
    AUXILIARY_SCORES,
    apply_consensus,
    calibration_thresholds,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "auxiliary_consensus_v16.json"
OUTPUT = ROOT / "outputs"
CONTRACT_PATH = OUTPUT / "AUX_CONSENSUS_V16_CONTRACT_LOCK.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("contract_sha256", None)
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def verify_contract(config: Mapping[str, Any]) -> dict[str, Any]:
    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError("Run lock_contract.py before V16 evaluation")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract["contract_sha256"] != canonical_hash(contract):
        raise ValueError("V16 contract self-hash changed")
    for base, records in (
        (ROOT, contract["package_files"]),
        (REPO_ROOT, contract["inputs"]),
    ):
        for item in records:
            path = base / item["path"]
            if (
                not path.is_file()
                or path.stat().st_size != int(item["bytes"])
                or sha256_file(path) != item["sha256"]
            ):
                raise ValueError(f"Locked V16 dependency changed: {path}")
    if contract["authorization"] != config["authorization"]:
        raise ValueError("V16 authority changed after lock")
    return contract


def input_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    return {
        name: REPO_ROOT / str(relative)
        for name, relative in config["inputs"].items()
    }


def weighted_auc(frame: pd.DataFrame, score: str) -> float | None:
    target = frame["stress_net_r_positive"].astype(int)
    if target.nunique() < 2:
        return None
    return float(
        roc_auc_score(
            target,
            frame[score],
            sample_weight=frame["structural_weight"],
        )
    )


def assert_float_parity(
    observed: pd.Series,
    expected: pd.Series,
    name: str,
) -> None:
    left = observed.to_numpy(dtype=float)
    right = expected.to_numpy(dtype=float)
    if not np.array_equal(np.isnan(left), np.isnan(right)):
        raise ValueError(f"{name} missing-value parity failed")
    finite = ~np.isnan(left)
    if not np.allclose(left[finite], right[finite], atol=1e-10, rtol=1e-10):
        difference = float(np.max(np.abs(left[finite] - right[finite])))
        raise ValueError(f"{name} parity failed: maximum difference {difference}")


def sorted_locked(
    locked: pd.DataFrame,
    fold_id: str,
    candidate_ids: pd.Series,
) -> pd.DataFrame:
    expected = locked.loc[locked["fold_id"].eq(fold_id)].copy()
    expected = expected.set_index("candidate_id").loc[candidate_ids].reset_index()
    if expected["candidate_id"].tolist() != candidate_ids.tolist():
        raise ValueError(f"{fold_id} locked candidate order changed")
    return expected


def b123_fold_scores(
    fit: pd.DataFrame,
    calibration: pd.DataFrame,
    test: pd.DataFrame,
    *,
    expected_r: ModuleType,
    policy: ModuleType,
    numeric_features: list[str],
    canonical_config: Mapping[str, Any],
    settings: Mapping[str, Any],
    policy_settings: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    calibration = calibration.copy()
    test = test.copy()
    if len(fit) < int(settings["minimum_fit_rows"]):
        calibration["b123_model_score"] = np.nan
        calibration["b123_selected"] = True
        test["b123_model_score"] = np.nan
        test["b123_selected"] = True
        chosen = {
            "quantile": 0.0,
            "threshold": None,
            "selection_reason": "ML_ABSTAIN_RETAIN_ALL_INSUFFICIENT_FIT",
        }
        return calibration, test, chosen

    model = expected_r.PartialPoolingExpectedR.fit(
        fit,
        numeric_features=numeric_features,
        families=canonical_config["population"]["families"],
        alpha=float(settings["alpha"]),
        interaction_scale=float(settings["family_interaction_scale"]),
        target_clip=tuple(float(value) for value in settings["target_clip_r"]),
    )
    calibration["model_score"] = model.predict(calibration)
    test["model_score"] = model.predict(test)
    chosen, _ = policy.choose_profit_threshold(calibration, policy_settings)
    calibration = policy.apply_profit_threshold(
        calibration,
        chosen,
        float(policy_settings["fallback_quantile"]),
    )
    test = policy.apply_profit_threshold(
        test,
        chosen,
        float(policy_settings["fallback_quantile"]),
    )
    calibration = calibration.rename(
        columns={"model_score": "b123_model_score", "selected": "b123_selected"}
    )
    test = test.rename(
        columns={"model_score": "b123_model_score", "selected": "b123_selected"}
    )
    return calibration, test, chosen


def consensus_policy_choice(
    calibration: pd.DataFrame,
    *,
    policy: ModuleType,
    settings: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], pd.DataFrame]:
    baseline_frame = calibration.copy()
    baseline_frame["selected"] = True
    baseline = policy.comparison(baseline_frame)["baseline"]
    b123_frame = calibration.copy()
    b123_frame["selected"] = b123_frame["b123_selected"].astype(bool)
    b123 = policy.comparison(b123_frame)["selected"]

    rows: list[dict[str, Any]] = []
    candidates: dict[float, tuple[pd.DataFrame, dict[str, float]]] = {}
    for quantile in settings["bottom_tail_quantile_grid"]:
        quantile_value = float(quantile)
        thresholds = calibration_thresholds(calibration, quantile_value)
        candidate = apply_consensus(
            calibration,
            thresholds,
            minimum_low_votes=int(settings["minimum_low_votes"]),
        )
        metrics = policy.comparison(candidate)
        selected = metrics["selected"]
        constraints = {
            "coverage": metrics["selected_weight_coverage"]
            >= float(settings["minimum_selected_weight_coverage"]),
            "profit": metrics["selected_profit_delta_usd"]
            > float(settings["minimum_profit_improvement_usd"]),
            "mean": (
                not bool(settings["require_mean_not_worse"])
                or selected["weighted_mean_r"] >= baseline["weighted_mean_r"]
            ),
            "profit_factor": (
                not bool(settings["require_profit_factor_not_worse"])
                or policy.profit_factor_not_worse(
                    selected["weighted_profit_factor"],
                    baseline["weighted_profit_factor"],
                )
            ),
            "drawdown": (
                not bool(settings["require_drawdown_not_worse"])
                or selected["weighted_max_drawdown_r"]
                <= baseline["weighted_max_drawdown_r"]
            ),
        }
        rows.append(
            {
                "quantile": quantile_value,
                **{f"{score}_threshold": thresholds[score] for score in AUXILIARY_SCORES},
                "eligible": bool(all(constraints.values())),
                **{f"constraint_{key}": value for key, value in constraints.items()},
                "v16_vetoed_rows": int(candidate["v16_veto"].sum()),
                "b123_vetoed_rows": int((~candidate["b123_selected"]).sum()),
                "b123_re_admitted_rows": int(
                    ((~candidate["b123_selected"]) & candidate["selected"]).sum()
                ),
                "selected_rows": selected["rows"],
                "selected_weight_coverage": metrics["selected_weight_coverage"],
                "selected_weighted_mean_r": selected["weighted_mean_r"],
                "selected_weighted_r_sum": selected["weighted_r_sum"],
                "selected_weighted_profit_factor": selected[
                    "weighted_profit_factor"
                ],
                "selected_weighted_max_drawdown_r": selected[
                    "weighted_max_drawdown_r"
                ],
                "selected_normalized_weighted_usd_sum": selected[
                    "normalized_weighted_usd_sum"
                ],
                "profit_improvement_usd_vs_raw": metrics[
                    "selected_profit_delta_usd"
                ],
                "profit_delta_usd_vs_b123": (
                    selected["normalized_weighted_usd_sum"]
                    - b123["normalized_weighted_usd_sum"]
                ),
            }
        )
        candidates[quantile_value] = (candidate, thresholds)

    grid = pd.DataFrame(rows)
    eligible = grid.loc[grid["eligible"]].sort_values(
        ["selected_normalized_weighted_usd_sum", "quantile"],
        ascending=[False, True],
        kind="mergesort",
    )
    if eligible.empty:
        result = calibration.copy()
        result["auxiliary_low_votes"] = 0
        result["auxiliary_consensus_low"] = False
        result["v16_veto"] = False
        result["selected"] = True
        chosen = {
            "quantile": 0.0,
            "thresholds": {score: None for score in AUXILIARY_SCORES},
            "selection_reason": str(settings["fallback_action"]),
        }
        return result, chosen, grid

    selected_row = eligible.iloc[0]
    selected_quantile = float(selected_row["quantile"])
    result, thresholds = candidates[selected_quantile]
    chosen = {
        "quantile": selected_quantile,
        "thresholds": thresholds,
        "selection_reason": "MAXIMUM_ELIGIBLE_CALIBRATION_NORMALIZED_USD",
    }
    return result, chosen, grid


def observed_population(
    canonical_raw: pd.DataFrame,
    auxiliary_raw: pd.DataFrame,
    expanded_manifest: Mapping[str, Any],
    overlap_audit: Mapping[str, int],
    locked_b123: pd.DataFrame,
) -> dict[str, int]:
    return {
        "canonical_rows": int(len(canonical_raw)),
        "canonical_feature_pass_rows": int(
            canonical_raw["xau_feature_status"].eq("PASS").sum()
        ),
        "expanded_action_rows": int(len(auxiliary_raw)),
        "expanded_source_event_rows": int(expanded_manifest["counts"]["events"]),
        "expanded_resolved_event_rows": int(auxiliary_raw["event_id"].nunique()),
        "expanded_structural_episodes": int(
            auxiliary_raw["structural_episode_id"].nunique()
        ),
        "post_overlap_action_rows": int(overlap_audit["kept_actions"]),
        "post_overlap_event_rows": int(overlap_audit["kept_events"]),
        "post_overlap_structural_episodes": int(
            overlap_audit["kept_structural_episodes"]
        ),
        "post_overlap_winners": int(overlap_audit["kept_winners"]),
        "post_overlap_failures": int(overlap_audit["kept_failures"]),
        "locked_prediction_rows": int(len(locked_b123)),
    }


def build_predictions(
    config: dict[str, Any],
    paths: Mapping[str, Path],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    expected_r = load_module("v16_expected_r", paths["expected_r_module"])
    policy = load_module("v16_profit_policy", paths["profit_policy_module"])
    transfer = load_module("v16_transfer", paths["v15_transfer_module"])
    canonical_config = json.loads(paths["v10_config"].read_text(encoding="utf-8"))
    canonical_config["features"]["source_blocks"] = list(
        config["canonical_source_blocks"]
    )
    feature_contract = json.loads(
        paths["canonical_feature_contract"].read_text(encoding="utf-8")
    )
    _, numeric_features = expected_r.feature_surface(
        feature_contract, canonical_config
    )
    canonical_raw = pd.read_parquet(paths["canonical_dataset"])
    canonical_splits = pd.read_parquet(paths["canonical_splits"])
    canonical = expected_r.prepare_dataset(
        canonical_raw,
        canonical_splits,
        canonical_config,
        numeric_features,
    )
    auxiliary_raw = pd.read_parquet(paths["expanded_actions"])
    expanded_manifest = json.loads(
        paths["expanded_manifest"].read_text(encoding="utf-8")
    )
    auxiliary, overlap_audit = transfer.exclude_overlapping_episodes(
        auxiliary_raw, canonical_raw
    )
    for column in ("signal_time", "label_end_time"):
        auxiliary[column] = pd.to_datetime(auxiliary[column], utc=True)

    locked_b123 = pd.read_parquet(paths["locked_b123_predictions"])
    locked_v15 = pd.read_parquet(paths["v15_predictions"])
    observed = observed_population(
        canonical_raw,
        auxiliary_raw,
        expanded_manifest,
        overlap_audit,
        locked_b123,
    )
    if observed != config["expected"]:
        raise ValueError(f"V16 population changed: {observed}")
    if locked_b123["candidate_id"].duplicated().any():
        raise ValueError("Locked B123 predictions are duplicated")
    if locked_v15["candidate_id"].duplicated().any():
        raise ValueError("Locked V15 predictions are duplicated")

    b123_policy = dict(config["b123_profit_policy"])
    predictions: list[pd.DataFrame] = []
    fold_rows: list[dict[str, Any]] = []
    threshold_rows: list[pd.DataFrame] = []
    fold_definitions = {row["fold_id"]: row for row in config["folds"]}
    for fold_id in canonical_config["outer_evaluation"]["folds"]:
        fold_mask = canonical["fold_id"].eq(fold_id)
        fit = canonical.loc[
            fold_mask & canonical["assignment"].eq("FIT")
        ].copy()
        calibration = canonical.loc[
            fold_mask & canonical["assignment"].eq("CALIBRATION")
        ].copy()
        test = canonical.loc[
            fold_mask & canonical["assignment"].eq("TEST")
        ].copy()
        calibration, test, b123_chosen = b123_fold_scores(
            fit,
            calibration,
            test,
            expected_r=expected_r,
            policy=policy,
            numeric_features=numeric_features,
            canonical_config=canonical_config,
            settings=config["b123_model"],
            policy_settings=b123_policy,
        )

        locked_fold = sorted_locked(
            locked_b123, fold_id, test["candidate_id"]
        )
        assert_float_parity(
            test["b123_model_score"],
            locked_fold["model_score"],
            f"{fold_id} B123 score",
        )
        if (
            test["b123_selected"].astype(bool).tolist()
            != locked_fold["selected"].astype(bool).tolist()
        ):
            raise ValueError(f"{fold_id} B123 selection parity failed")
        if not np.allclose(
            float(b123_chosen["quantile"]),
            locked_fold["b123_quantile"].to_numpy(dtype=float),
            atol=1e-12,
            rtol=0.0,
        ):
            raise ValueError(f"{fold_id} B123 quantile parity failed")

        cutoff = pd.Timestamp(fold_definitions[fold_id]["calibration_start_utc"])
        aux_fit = auxiliary.loc[
            auxiliary["signal_time"].lt(cutoff)
            & auxiliary["label_end_time"].lt(cutoff)
        ].copy()
        if len(aux_fit) < int(config["transfer"]["minimum_auxiliary_actions"]):
            raise ValueError(f"{fold_id} has too few auxiliary actions")
        if aux_fit["structural_episode_id"].nunique() < int(
            config["transfer"]["minimum_auxiliary_episodes"]
        ):
            raise ValueError(f"{fold_id} has too few auxiliary episodes")
        bundle = transfer.AuxiliaryTransferBundle.fit(
            aux_fit, fit, config["transfer"]
        )
        calibration = transfer.add_transfer_scores(calibration, bundle)
        test = transfer.add_transfer_scores(test, bundle)

        locked_v15_fold = sorted_locked(
            locked_v15, fold_id, test["candidate_id"]
        )
        for score in AUXILIARY_SCORES:
            assert_float_parity(
                test[score],
                locked_v15_fold[score],
                f"{fold_id} {score}",
            )

        selected_calibration, chosen, grid = consensus_policy_choice(
            calibration,
            policy=policy,
            settings=config["consensus_policy"],
        )
        grid.insert(0, "fold_id", fold_id)
        grid["selected_policy"] = grid["quantile"].eq(
            float(chosen["quantile"])
        ) & grid["eligible"]
        threshold_rows.append(grid)
        if chosen["selection_reason"] == config["consensus_policy"]["fallback_action"]:
            selected_test = test.copy()
            selected_test["auxiliary_low_votes"] = 0
            selected_test["auxiliary_consensus_low"] = False
            selected_test["v16_veto"] = False
            selected_test["selected"] = True
        else:
            selected_test = apply_consensus(
                test,
                chosen["thresholds"],
                minimum_low_votes=int(
                    config["consensus_policy"]["minimum_low_votes"]
                ),
            )

        selected_test["v16_quantile"] = float(chosen["quantile"])
        selected_test["v16_action"] = str(chosen["selection_reason"])
        for score in AUXILIARY_SCORES:
            selected_test[f"{score}_threshold"] = chosen["thresholds"][score]
        broad = policy.comparison(selected_test)
        b123_test = test.copy()
        b123_test["selected"] = b123_test["b123_selected"].astype(bool)
        b123_broad = policy.comparison(b123_test)
        fold_rows.append(
            {
                "fold_id": fold_id,
                "calibration_start_utc": cutoff.isoformat(),
                "auxiliary_fit_actions": int(len(aux_fit)),
                "auxiliary_fit_events": int(aux_fit["event_id"].nunique()),
                "auxiliary_fit_episodes": int(
                    aux_fit["structural_episode_id"].nunique()
                ),
                "canonical_fit_rows": int(len(fit)),
                "canonical_calibration_rows": int(len(calibration)),
                "canonical_test_rows": int(len(test)),
                "b123_quantile": float(b123_chosen["quantile"]),
                "b123_test_vetoes": int((~test["b123_selected"]).sum()),
                "chosen_consensus_quantile": float(chosen["quantile"]),
                "selection_reason": str(chosen["selection_reason"]),
                "v16_test_vetoes": int(selected_test["v16_veto"].sum()),
                "b123_test_re_admitted": int(
                    (
                        (~selected_test["b123_selected"])
                        & selected_test["selected"]
                    ).sum()
                ),
                "selected_rows": int(selected_test["selected"].sum()),
                "selected_weight_coverage": broad[
                    "selected_weight_coverage"
                ],
                "broad_candidate_delta_usd_vs_raw": broad[
                    "selected_profit_delta_usd"
                ],
                "broad_candidate_delta_usd_vs_b123": (
                    broad["selected"]["normalized_weighted_usd_sum"]
                    - b123_broad["selected"]["normalized_weighted_usd_sum"]
                ),
                "aux_linear_test_auc": weighted_auc(
                    selected_test, AUXILIARY_SCORES[0]
                ),
                "aux_nonlinear_test_auc": weighted_auc(
                    selected_test, AUXILIARY_SCORES[1]
                ),
                "aux_win_test_auc": weighted_auc(
                    selected_test, AUXILIARY_SCORES[2]
                ),
            }
        )
        predictions.append(
            selected_test[
                [
                    "candidate_id",
                    "fold_id",
                    "decision_time",
                    "family_id",
                    *AUXILIARY_SCORES,
                    "b123_model_score",
                    "b123_selected",
                    "auxiliary_low_votes",
                    "auxiliary_consensus_low",
                    "v16_veto",
                    "selected",
                    "v16_quantile",
                    *(f"{score}_threshold" for score in AUXILIARY_SCORES),
                    "v16_action",
                ]
            ].rename(columns={"selected": "v16_selected"})
        )

    prediction_frame = pd.concat(predictions, ignore_index=True)
    if prediction_frame["candidate_id"].duplicated().any():
        raise ValueError("V16 out-of-time predictions are duplicated")
    dataset_audit = {
        "schema_version": "xauusd_auxiliary_consensus_v16_dataset_audit",
        **observed,
        **overlap_audit,
        "journey_rows_used": 0,
        "outcome_or_identity_features_used": False,
        "structural_weight_sum": float(auxiliary["structural_weight"].sum()),
        "first_auxiliary_decision_time": auxiliary[
            "signal_time"
        ].min().isoformat(),
        "last_auxiliary_decision_time": auxiliary[
            "signal_time"
        ].max().isoformat(),
        "locked_b123_parity_passed": True,
        "locked_v15_auxiliary_score_parity_passed": True,
    }
    return (
        prediction_frame,
        pd.DataFrame(fold_rows),
        pd.concat(threshold_rows, ignore_index=True),
        dataset_audit,
    )


def exact_v60_replay(
    predictions: pd.DataFrame,
    paths: Mapping[str, Path],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, bool]]:
    v60_root = paths["v60_replay_module"].parent
    sys.path.insert(0, str(v60_root))
    helper = load_module("v16_v60_replay", paths["v60_replay_module"])
    trades, checks = helper.load_joined_trades()
    replacement = (
        "fold_id",
        "model_score",
        "threshold",
        "v12_threshold",
        "v12_quantile",
        "v12_action",
        "selected",
        "v12_prediction_available",
        "v12_retained",
    )
    trades = trades.drop(
        columns=[column for column in replacement if column in trades]
    )
    trades = trades.merge(
        predictions,
        on=["candidate_id", "family_id"],
        how="left",
        validate="one_to_one",
    )
    trades["model_score"] = trades["b123_model_score"]
    trades["v12_prediction_available"] = trades["fold_id"].notna()
    trades["v12_retained"] = trades["v16_selected"].fillna(True).astype(bool)
    trades["v12_action"] = trades["v16_action"].fillna(
        "MODEL_ABSTAIN_RETAIN_ALL"
    )
    windows, audits = helper.window_rows(trades, helper.load_cooldowns())
    return windows, audits["ALL"].copy(), checks


def combined_windows(
    v16: pd.DataFrame,
    locked_path: Path,
) -> pd.DataFrame:
    locked = pd.read_csv(locked_path).set_index("period")
    current = v16.set_index("period")
    if list(current.index) != list(locked.index):
        raise ValueError("Locked B123 and V16 windows differ")
    for column in (
        "raw_trades",
        "raw_net_pnl_usd",
        "raw_profit_factor",
        "raw_closed_trade_drawdown_usd",
    ):
        if not np.allclose(
            current[column].to_numpy(float),
            locked[column].to_numpy(float),
            atol=1e-9,
            rtol=0.0,
        ):
            raise ValueError(f"Raw V60 replay changed: {column}")
    result = current[
        [
            "start_inclusive_utc",
            "end_exclusive_utc",
            "raw_trades",
            "raw_net_pnl_usd",
            "raw_win_rate_pct",
            "raw_profit_factor",
            "raw_closed_trade_drawdown_usd",
            "ml_trades",
            "ml_net_pnl_usd",
            "ml_win_rate_pct",
            "ml_profit_factor",
            "ml_closed_trade_drawdown_usd",
        ]
    ].rename(
        columns={
            "ml_trades": "v16_trades",
            "ml_net_pnl_usd": "v16_net_pnl_usd",
            "ml_win_rate_pct": "v16_win_rate_pct",
            "ml_profit_factor": "v16_profit_factor",
            "ml_closed_trade_drawdown_usd": "v16_closed_trade_drawdown_usd",
        }
    )
    result["locked_b123_trades"] = locked["ml_trades"]
    result["locked_b123_net_pnl_usd"] = locked["ml_net_pnl_usd"]
    result["locked_b123_win_rate_pct"] = locked["ml_win_rate_pct"]
    result["locked_b123_profit_factor"] = locked["ml_profit_factor"]
    result["locked_b123_closed_trade_drawdown_usd"] = locked[
        "ml_closed_trade_drawdown_usd"
    ]
    result["v16_delta_vs_raw_usd"] = (
        result["v16_net_pnl_usd"] - result["raw_net_pnl_usd"]
    )
    result["v16_delta_vs_locked_b123_usd"] = (
        result["v16_net_pnl_usd"] - result["locked_b123_net_pnl_usd"]
    )
    result["v16_trade_retention"] = result["v16_trades"] / result["raw_trades"]
    return result.reset_index()


def build_result(
    config: Mapping[str, Any],
    contract: Mapping[str, Any],
    windows: pd.DataFrame,
    folds: pd.DataFrame,
    dataset_audit: Mapping[str, Any],
) -> dict[str, Any]:
    indexed = windows.set_index("period")
    all_row = indexed.loc["ALL"]
    gates = config["acceptance"]
    checks = {
        "all_history_delta_vs_raw": float(all_row["v16_delta_vs_raw_usd"])
        > float(gates["minimum_all_history_delta_vs_raw_usd"]),
        "all_history_delta_vs_locked_b123": float(
            all_row["v16_delta_vs_locked_b123_usd"]
        )
        > float(gates["minimum_all_history_delta_vs_locked_b123_usd"]),
        "latest_3m_delta_vs_raw": float(
            indexed.loc["3M", "v16_delta_vs_raw_usd"]
        )
        >= float(gates["minimum_latest_3m_delta_vs_raw_usd"]),
        "six_month_delta_vs_raw": float(
            indexed.loc["6M", "v16_delta_vs_raw_usd"]
        )
        > float(gates["minimum_6m_delta_vs_raw_usd"]),
        "twelve_month_delta_vs_raw": float(
            indexed.loc["1Y", "v16_delta_vs_raw_usd"]
        )
        > float(gates["minimum_12m_delta_vs_raw_usd"]),
        "all_history_trade_retention": float(all_row["v16_trade_retention"])
        >= float(gates["minimum_all_history_trade_retention"]),
        "all_history_profit_factor_not_worse": float(
            all_row["v16_profit_factor"]
        )
        >= float(all_row["raw_profit_factor"]),
        "all_history_drawdown_not_worse": float(
            all_row["v16_closed_trade_drawdown_usd"]
        )
        <= float(all_row["raw_closed_trade_drawdown_usd"]),
    }
    passed = all(checks.values())
    return {
        "schema_version": "xauusd_auxiliary_consensus_v16_result",
        "decision": (
            "V16_HISTORICAL_ADVANCE_PROSPECTIVE_CHALLENGER_ONLY"
            if passed
            else "V16_HISTORICAL_GATE_FAIL"
        ),
        "passed": passed,
        "checks": checks,
        "definition_contract_sha256": contract["contract_sha256"],
        "population": dict(dataset_audit),
        "out_of_time": {
            "prediction_rows": int(folds["canonical_test_rows"].sum()),
            "selected_rows": int(folds["selected_rows"].sum()),
            "b123_vetoes": int(folds["b123_test_vetoes"].sum()),
            "v16_consensus_vetoes": int(folds["v16_test_vetoes"].sum()),
            "b123_re_admitted": int(folds["b123_test_re_admitted"].sum()),
            "positive_broad_candidate_delta_folds_vs_raw": int(
                folds["broad_candidate_delta_usd_vs_raw"].gt(0.0).sum()
            ),
            "positive_broad_candidate_delta_folds_vs_b123": int(
                folds["broad_candidate_delta_usd_vs_b123"].gt(0.0).sum()
            ),
            "mean_auxiliary_linear_test_auc": float(
                folds["aux_linear_test_auc"].mean()
            ),
            "mean_auxiliary_nonlinear_test_auc": float(
                folds["aux_nonlinear_test_auc"].mean()
            ),
            "mean_auxiliary_win_test_auc": float(
                folds["aux_win_test_auc"].mean()
            ),
        },
        "exact_v60": {
            period: {
                key: (
                    None
                    if pd.isna(value)
                    else value.item()
                    if hasattr(value, "item")
                    else value
                )
                for key, value in row.items()
                if key not in ("start_inclusive_utc", "end_exclusive_utc")
            }
            for period, row in windows.set_index("period").iterrows()
        },
        "historical_outcomes_already_exposed": True,
        "v14_changed": False,
        "v15_changed": False,
        "deployment_eligible": False,
        "authorization": config["authorization"],
        "limitations": [
            "Historical outcomes were exposed before V16 was designed.",
            "V16 selects among three fixed consensus tails using historical calibration outcomes.",
            "The auxiliary mechanics are related to, but not identical to, canonical V60 specialists.",
            "The same XAUUSD history underlies both domains after overlapping episodes are excluded.",
            "Only untouched prospective evidence could support any later runtime role.",
            "V14 remains the locked prospective lane; V14 and V15 were not modified.",
        ],
    }


def write_markdown(result: Mapping[str, Any], windows: pd.DataFrame) -> str:
    rows = windows.set_index("period")
    lines = [
        "# Auxiliary Consensus V16 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Period | Raw P&L | Locked B123 P&L | V16 P&L | V16 vs raw | V16 vs B123 | Trades | PF | DD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for period in ("3M", "6M", "1Y", "2Y", "5Y", "10Y", "ALL"):
        row = rows.loc[period]
        lines.append(
            f"| {period} | ${row['raw_net_pnl_usd']:.2f} | "
            f"${row['locked_b123_net_pnl_usd']:.2f} | "
            f"${row['v16_net_pnl_usd']:.2f} | "
            f"${row['v16_delta_vs_raw_usd']:.2f} | "
            f"${row['v16_delta_vs_locked_b123_usd']:.2f} | "
            f"{int(row['v16_trades'])} | {row['v16_profit_factor']:.3f} | "
            f"${row['v16_closed_trade_drawdown_usd']:.2f} |"
        )
    lines.extend(
        [
            "",
            f"B123 vetoes: {result['out_of_time']['b123_vetoes']}. "
            f"Consensus-confirmed vetoes: {result['out_of_time']['v16_consensus_vetoes']}. "
            f"Re-admitted: {result['out_of_time']['b123_re_admitted']}.",
            "",
            "V16 is historical research only. V14, V15, MT5, and demo execution were not changed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    contract = verify_contract(config)
    paths = input_paths(config)
    predictions, folds, thresholds, dataset_audit = build_predictions(
        config, paths
    )
    v16_windows, trade_audit, replay_checks = exact_v60_replay(
        predictions, paths
    )
    windows = combined_windows(v16_windows, paths["locked_b123_windows"])
    result = build_result(config, contract, windows, folds, dataset_audit)
    result["exact_v60_replay_checks"] = replay_checks
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "contract_lock": CONTRACT_PATH,
        "dataset_audit": OUTPUT / config["outputs"]["dataset_audit"],
        "predictions": OUTPUT / config["outputs"]["predictions"],
        "fold_metrics": OUTPUT / config["outputs"]["fold_metrics"],
        "threshold_decisions": OUTPUT / config["outputs"]["threshold_decisions"],
        "windows": OUTPUT / config["outputs"]["windows"],
        "trade_audit": OUTPUT / config["outputs"]["trade_audit"],
        "result_json": OUTPUT / config["outputs"]["result_json"],
        "result_markdown": OUTPUT / config["outputs"]["result_markdown"],
    }
    output_paths["dataset_audit"].write_text(
        json.dumps(dataset_audit, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    predictions.to_parquet(output_paths["predictions"], index=False)
    folds.to_csv(output_paths["fold_metrics"], index=False)
    thresholds.to_csv(output_paths["threshold_decisions"], index=False)
    windows.to_csv(output_paths["windows"], index=False)
    trade_audit.to_parquet(output_paths["trade_audit"], index=False)
    output_paths["result_json"].write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    output_paths["result_markdown"].write_text(
        write_markdown(result, windows),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "xauusd_auxiliary_consensus_v16_artifact_manifest",
        "definition_contract_sha256": contract["contract_sha256"],
        "decision": result["decision"],
        "inputs": {
            name: {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": sha256_file(path),
            }
            for name, path in paths.items()
        },
        "artifacts": {
            name: {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "sha256": sha256_file(path),
            }
            for name, path in output_paths.items()
        },
        "authorization": config["authorization"],
    }
    manifest_path = OUTPUT / config["outputs"]["manifest"]
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

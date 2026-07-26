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

from src.veto import (
    AUXILIARY_SCORES,
    apply_v8_veto,
    weighted_quantile,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
CONFIG_PATH = ROOT / "config" / "v8_auxiliary_veto_v18.json"
OUTPUT = ROOT / "outputs"
CONTRACT_PATH = OUTPUT / "V8_AUX_V18_CONTRACT_LOCK.json"


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
        raise FileNotFoundError("Run lock_contract.py before V18 evaluation")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract["contract_sha256"] != canonical_hash(contract):
        raise ValueError("V18 contract self-hash changed")
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
                raise ValueError(f"Locked V18 dependency changed: {path}")
    if contract["authorization"] != config["authorization"]:
        raise ValueError("V18 authority changed after lock")
    return contract


def input_paths(config: Mapping[str, Any]) -> dict[str, Path]:
    return {
        name: REPO_ROOT / str(relative)
        for name, relative in config["inputs"].items()
    }


def weighted_auc(frame: pd.DataFrame, score: str) -> float | None:
    if frame.empty:
        return None
    target = frame["stress_net_r_positive"].astype(int)
    values = frame[score]
    available = values.notna()
    if available.sum() == 0 or target.loc[available].nunique() < 2:
        return None
    return float(
        roc_auc_score(
            target.loc[available],
            values.loc[available],
            sample_weight=frame.loc[available, "structural_weight"],
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
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    fit = fit.copy()
    calibration = calibration.copy()
    test = test.copy()
    if len(fit) < int(settings["minimum_fit_rows"]):
        for frame in (fit, calibration, test):
            frame["b123_model_score"] = np.nan
            frame["b123_selected"] = True
        chosen = {
            "quantile": 0.0,
            "threshold": None,
            "selection_reason": "ML_ABSTAIN_RETAIN_ALL_INSUFFICIENT_FIT",
        }
        return fit, calibration, test, chosen

    model = expected_r.PartialPoolingExpectedR.fit(
        fit,
        numeric_features=numeric_features,
        families=canonical_config["population"]["families"],
        alpha=float(settings["alpha"]),
        interaction_scale=float(settings["family_interaction_scale"]),
        target_clip=tuple(float(value) for value in settings["target_clip_r"]),
    )
    for frame in (fit, calibration, test):
        frame["model_score"] = model.predict(frame)
    chosen, _ = policy.choose_profit_threshold(calibration, policy_settings)
    fit = policy.apply_profit_threshold(
        fit,
        chosen,
        float(policy_settings["fallback_quantile"]),
    )
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
    renamed = {"model_score": "b123_model_score", "selected": "b123_selected"}
    return (
        fit.rename(columns=renamed),
        calibration.rename(columns=renamed),
        test.rename(columns=renamed),
        chosen,
    )


def choose_specialist_threshold(
    calibration: pd.DataFrame,
    *,
    policy: ModuleType,
    specialist_id: str,
    settings: Mapping[str, Any],
) -> tuple[float | None, str, pd.DataFrame]:
    specialist = calibration.loc[
        calibration["family_id"].eq(specialist_id)
    ].copy()
    baseline_selected = specialist.loc[
        specialist["b123_selected"].astype(bool)
    ].copy()
    start = specialist["decision_time"].min()
    end = specialist["decision_time"].max()
    baseline_metrics = policy.economics(
        baseline_selected,
        start=start,
        end=end,
    )
    rows: list[dict[str, Any]] = []
    for quantile in settings["weighted_quantile_grid"]:
        quantile_value = float(quantile)
        threshold = weighted_quantile(
            specialist["v8_model_score"],
            specialist["structural_weight"],
            quantile_value,
        )
        candidate = apply_v8_veto(
            specialist,
            specialist_id=specialist_id,
            threshold=threshold,
        ).rename(columns={"v18_selected": "selected"})
        selected_rows = candidate.loc[candidate["selected"].astype(bool)]
        selected = policy.economics(selected_rows, start=start, end=end)
        selected_weight_coverage = float(
            selected["weight"] / baseline_metrics["weight"]
        )
        profit_improvement = float(
            selected["normalized_weighted_usd_sum"]
            - baseline_metrics["normalized_weighted_usd_sum"]
        )
        constraints = {
            "coverage": selected_weight_coverage
            >= float(settings["minimum_selected_weight_coverage"]),
            "profit": profit_improvement
            > float(settings["minimum_profit_improvement_usd"]),
            "mean": (
                not bool(settings["require_mean_not_worse"])
                or selected["weighted_mean_r"]
                >= baseline_metrics["weighted_mean_r"]
            ),
            "profit_factor": (
                not bool(settings["require_profit_factor_not_worse"])
                or policy.profit_factor_not_worse(
                    selected["weighted_profit_factor"],
                    baseline_metrics["weighted_profit_factor"],
                )
            ),
            "drawdown": (
                not bool(settings["require_drawdown_not_worse"])
                or selected["weighted_max_drawdown_r"]
                <= baseline_metrics["weighted_max_drawdown_r"]
            ),
        }
        rows.append(
            {
                "quantile": quantile_value,
                "threshold": threshold,
                "eligible": bool(all(constraints.values())),
                **{f"constraint_{key}": value for key, value in constraints.items()},
                "b123_vetoed_rows": int((~specialist["b123_selected"]).sum()),
                "v18_additional_veto_rows": int(
                    candidate["v8_additional_veto"].sum()
                ),
                "selected_rows": selected["rows"],
                "selected_weight_coverage": selected_weight_coverage,
                "selected_weighted_mean_r": selected["weighted_mean_r"],
                "selected_weighted_profit_factor": selected[
                    "weighted_profit_factor"
                ],
                "selected_weighted_max_drawdown_r": selected[
                    "weighted_max_drawdown_r"
                ],
                "selected_normalized_weighted_usd_sum": selected[
                    "normalized_weighted_usd_sum"
                ],
                "profit_improvement_usd_vs_b123_v8": profit_improvement,
            }
        )
    grid = pd.DataFrame(rows)
    eligible = grid.loc[grid["eligible"]].sort_values(
        ["selected_normalized_weighted_usd_sum", "quantile"],
        ascending=[False, True],
        kind="mergesort",
    )
    if eligible.empty:
        return (
            None,
            str(settings["fallback_action"]),
            grid.assign(selected_policy=False),
        )
    chosen = eligible.iloc[0]
    chosen_quantile = float(chosen["quantile"])
    grid["selected_policy"] = grid["quantile"].eq(chosen_quantile)
    return (
        float(chosen["threshold"]),
        "MAXIMUM_ELIGIBLE_V8_VETO_CALIBRATION_NORMALIZED_USD",
        grid,
    )


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
    expected_r = load_module("v18_expected_r", paths["expected_r_module"])
    policy = load_module("v18_profit_policy", paths["profit_policy_module"])
    transfer = load_module("v18_transfer", paths["v15_transfer_module"])
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
        raise ValueError(f"V18 population changed: {observed}")
    if locked_b123["candidate_id"].duplicated().any():
        raise ValueError("Locked B123 predictions are duplicated")
    if locked_v15["candidate_id"].duplicated().any():
        raise ValueError("Locked V15 predictions are duplicated")

    specialist_id = str(config["specialist"]["family_id"])
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
        fit, calibration, test, b123_chosen = b123_fold_scores(
            fit,
            calibration,
            test,
            expected_r=expected_r,
            policy=policy,
            numeric_features=numeric_features,
            canonical_config=canonical_config,
            settings=config["b123_model"],
            policy_settings=config["b123_profit_policy"],
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
        fit = transfer.add_transfer_scores(fit, bundle)
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

        v8_fit = fit.loc[fit["family_id"].eq(specialist_id)].copy()
        v8_calibration = calibration.loc[
            calibration["family_id"].eq(specialist_id)
        ].copy()
        v8_test_mask = test["family_id"].eq(specialist_id)
        supported = len(v8_calibration) >= int(
            config["specialist"]["minimum_calibration_rows"]
        )
        for frame in (fit, calibration, test):
            frame["v8_model_score"] = frame[str(config["specialist"]["score"])]
        if supported:
            threshold, action, grid = choose_specialist_threshold(
                calibration,
                policy=policy,
                specialist_id=specialist_id,
                settings=config["specialist_policy"],
            )
        else:
            threshold = None
            action = "V8_PRESERVE_B123_INSUFFICIENT_CALIBRATION_SUPPORT"
            grid = pd.DataFrame(
                [
                    {
                        "quantile": np.nan,
                        "threshold": np.nan,
                        "eligible": False,
                        "selected_policy": False,
                    }
                ]
            )
        grid.insert(0, "fold_id", fold_id)
        grid["specialist_fit_rows"] = len(v8_fit)
        grid["specialist_calibration_rows"] = len(v8_calibration)
        grid["selection_reason"] = action
        threshold_rows.append(grid)

        selected_test = apply_v8_veto(
            test,
            specialist_id=specialist_id,
            threshold=threshold,
        )
        selected_test["v18_threshold"] = threshold
        selected_test["v18_action"] = action
        selected_for_policy = selected_test.rename(
            columns={"v18_selected": "selected"}
        )
        broad = policy.comparison(selected_for_policy)
        b123_test = test.copy()
        b123_test["selected"] = b123_test["b123_selected"].astype(bool)
        b123_broad = policy.comparison(b123_test)
        v8_selected_test = selected_test.loc[v8_test_mask]
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
                "v8_fit_rows": int(len(v8_fit)),
                "v8_calibration_rows": int(len(v8_calibration)),
                "v8_test_rows": int(v8_test_mask.sum()),
                "specialist_supported": bool(supported),
                "b123_quantile": float(b123_chosen["quantile"]),
                "b123_total_test_vetoes": int((~test["b123_selected"]).sum()),
                "b123_v8_test_vetoes": int(
                    (~v8_selected_test["b123_selected"]).sum()
                ),
                "v18_total_test_vetoes": int(selected_test["v18_veto"].sum()),
                "v18_v8_test_vetoes": int(
                    v8_selected_test["v18_veto"].sum()
                ),
                "v8_test_additional_vetoes": int(
                    v8_selected_test["v8_additional_veto"].sum()
                ),
                "chosen_threshold": threshold,
                "selection_reason": action,
                "selected_rows": int(selected_test["v18_selected"].sum()),
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
                "v8_auxiliary_nonlinear_test_auc": weighted_auc(
                    v8_selected_test, "v8_model_score"
                ),
                "aux_linear_v8_test_auc": weighted_auc(
                    v8_selected_test, AUXILIARY_SCORES[0]
                ),
                "aux_nonlinear_v8_test_auc": weighted_auc(
                    v8_selected_test, AUXILIARY_SCORES[1]
                ),
                "aux_win_v8_test_auc": weighted_auc(
                    v8_selected_test, AUXILIARY_SCORES[2]
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
                    "v8_model_score",
                    "v18_threshold",
                    "v18_veto",
                    "v18_selected",
                    "v8_additional_veto",
                    "v18_action",
                ]
            ]
        )

    prediction_frame = pd.concat(predictions, ignore_index=True)
    if prediction_frame["candidate_id"].duplicated().any():
        raise ValueError("V18 out-of-time predictions are duplicated")
    dataset_audit = {
        "schema_version": "xauusd_v8_auxiliary_veto_v18_dataset_audit",
        **observed,
        **overlap_audit,
        "specialist_family_id": specialist_id,
        "journey_rows_used": 0,
        "outcome_or_identity_features_used": False,
        "specialist_model_feature_count": 1,
        "specialist_model_features": [str(config["specialist"]["score"])],
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
    helper = load_module("v18_v60_replay", paths["v60_replay_module"])
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
    trades["model_score"] = trades["v8_model_score"]
    trades["v12_prediction_available"] = trades["fold_id"].notna()
    trades["v12_retained"] = trades["v18_selected"].fillna(True).astype(bool)
    trades["v12_action"] = trades["v18_action"].fillna(
        "MODEL_ABSTAIN_RETAIN_ALL"
    )
    windows, audits = helper.window_rows(trades, helper.load_cooldowns())
    return windows, audits["ALL"].copy(), checks


def combined_windows(
    v18: pd.DataFrame,
    locked_path: Path,
) -> pd.DataFrame:
    locked = pd.read_csv(locked_path).set_index("period")
    current = v18.set_index("period")
    if list(current.index) != list(locked.index):
        raise ValueError("Locked B123 and V18 windows differ")
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
            "ml_trades": "v18_trades",
            "ml_net_pnl_usd": "v18_net_pnl_usd",
            "ml_win_rate_pct": "v18_win_rate_pct",
            "ml_profit_factor": "v18_profit_factor",
            "ml_closed_trade_drawdown_usd": "v18_closed_trade_drawdown_usd",
        }
    )
    result["locked_b123_trades"] = locked["ml_trades"]
    result["locked_b123_net_pnl_usd"] = locked["ml_net_pnl_usd"]
    result["locked_b123_win_rate_pct"] = locked["ml_win_rate_pct"]
    result["locked_b123_profit_factor"] = locked["ml_profit_factor"]
    result["locked_b123_closed_trade_drawdown_usd"] = locked[
        "ml_closed_trade_drawdown_usd"
    ]
    result["v18_delta_vs_raw_usd"] = (
        result["v18_net_pnl_usd"] - result["raw_net_pnl_usd"]
    )
    result["v18_delta_vs_locked_b123_usd"] = (
        result["v18_net_pnl_usd"] - result["locked_b123_net_pnl_usd"]
    )
    result["v18_trade_retention"] = result["v18_trades"] / result["raw_trades"]
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
        "all_history_delta_vs_raw": float(all_row["v18_delta_vs_raw_usd"])
        > float(gates["minimum_all_history_delta_vs_raw_usd"]),
        "all_history_delta_vs_locked_b123": float(
            all_row["v18_delta_vs_locked_b123_usd"]
        )
        > float(gates["minimum_all_history_delta_vs_locked_b123_usd"]),
        "latest_3m_delta_vs_raw": float(
            indexed.loc["3M", "v18_delta_vs_raw_usd"]
        )
        >= float(gates["minimum_latest_3m_delta_vs_raw_usd"]),
        "six_month_delta_vs_raw": float(
            indexed.loc["6M", "v18_delta_vs_raw_usd"]
        )
        > float(gates["minimum_6m_delta_vs_raw_usd"]),
        "twelve_month_delta_vs_raw": float(
            indexed.loc["1Y", "v18_delta_vs_raw_usd"]
        )
        > float(gates["minimum_12m_delta_vs_raw_usd"]),
        "all_history_trade_retention": float(all_row["v18_trade_retention"])
        >= float(gates["minimum_all_history_trade_retention"]),
        "all_history_profit_factor_not_worse": float(
            all_row["v18_profit_factor"]
        )
        >= float(all_row["raw_profit_factor"]),
        "all_history_drawdown_not_worse": float(
            all_row["v18_closed_trade_drawdown_usd"]
        )
        <= float(all_row["raw_closed_trade_drawdown_usd"]),
    }
    passed = all(checks.values())
    return {
        "schema_version": "xauusd_v8_auxiliary_veto_v18_result",
        "decision": (
            "V18_HISTORICAL_ADVANCE_PROSPECTIVE_CHALLENGER_ONLY"
            if passed
            else "V18_HISTORICAL_GATE_FAIL"
        ),
        "passed": passed,
        "checks": checks,
        "definition_contract_sha256": contract["contract_sha256"],
        "population": dict(dataset_audit),
        "out_of_time": {
            "prediction_rows": int(folds["canonical_test_rows"].sum()),
            "selected_rows": int(folds["selected_rows"].sum()),
            "supported_specialist_folds": int(
                folds["specialist_supported"].sum()
            ),
            "b123_total_vetoes": int(folds["b123_total_test_vetoes"].sum()),
            "b123_v8_vetoes": int(folds["b123_v8_test_vetoes"].sum()),
            "v18_total_vetoes": int(folds["v18_total_test_vetoes"].sum()),
            "v18_v8_vetoes": int(folds["v18_v8_test_vetoes"].sum()),
            "v8_additional_vetoes": int(
                folds["v8_test_additional_vetoes"].sum()
            ),
            "positive_broad_candidate_delta_folds_vs_raw": int(
                folds["broad_candidate_delta_usd_vs_raw"].gt(0.0).sum()
            ),
            "positive_broad_candidate_delta_folds_vs_b123": int(
                folds["broad_candidate_delta_usd_vs_b123"].gt(0.0).sum()
            ),
            "mean_v8_auxiliary_nonlinear_test_auc": float(
                folds["v8_auxiliary_nonlinear_test_auc"].mean()
            ),
            "mean_auxiliary_linear_v8_test_auc": float(
                folds["aux_linear_v8_test_auc"].mean()
            ),
            "mean_auxiliary_nonlinear_v8_test_auc": float(
                folds["aux_nonlinear_v8_test_auc"].mean()
            ),
            "mean_auxiliary_win_v8_test_auc": float(
                folds["aux_win_v8_test_auc"].mean()
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
        "experiment_registry": [
            {
                "experiment": "V14",
                "role": "LOCKED_PROSPECTIVE_LANE",
                "exact_historical_replay_distinct": False,
            },
            {
                "experiment": "B123",
                "role": "LOCKED_HISTORICAL_DIAGNOSTIC",
                "exact_historical_replay_distinct": True,
            },
            {
                "experiment": "V15",
                "role": "AUXILIARY_SCORE_STACKING",
                "exact_historical_replay_distinct": True,
            },
            {
                "experiment": "V16",
                "role": "GLOBAL_AUXILIARY_CONSENSUS",
                "exact_historical_replay_distinct": True,
            },
            {
                "experiment": "V17",
                "role": "V57_SPECIALIST_AUXILIARY_CALIBRATOR",
                "exact_historical_replay_distinct": True,
            },
            {
                "experiment": "V18",
                "role": "V8_AUXILIARY_NONLINEAR_BOTTOM_TAIL_VETO",
                "exact_historical_replay_distinct": True,
            },
        ],
        "historical_outcomes_already_exposed": True,
        "v14_changed": False,
        "v15_changed": False,
        "v16_changed": False,
        "v17_changed": False,
        "deployment_eligible": False,
        "authorization": config["authorization"],
        "limitations": [
            "Historical outcomes were exposed before V18 was designed.",
            "The V8 score was chosen after the V15-V17 family AUC audit.",
            "Only the frozen nonlinear auxiliary score enters the V8 veto.",
            "Only untouched prospective evidence could support any later runtime role.",
            "V14 remains the locked prospective lane; V14-V17 were not modified.",
        ],
    }


def experiment_comparison(
    windows: pd.DataFrame,
    paths: Mapping[str, Path],
    v18_decision: str,
) -> pd.DataFrame:
    v15 = pd.read_csv(paths["v15_windows"]).set_index("period")
    v16 = pd.read_csv(paths["v16_windows"]).set_index("period")
    v17 = pd.read_csv(paths["v17_windows"]).set_index("period")
    current = windows.set_index("period")
    b123_status = json.loads(
        paths["locked_b123_report"].read_text(encoding="utf-8")
    )["status"]
    v15_status = json.loads(
        paths["v15_result"].read_text(encoding="utf-8")
    )["decision"]
    v16_status = json.loads(
        paths["v16_result"].read_text(encoding="utf-8")
    )["decision"]
    v17_status = json.loads(
        paths["v17_result"].read_text(encoding="utf-8")
    )["decision"]
    rows: list[dict[str, Any]] = []
    periods = ("3M", "6M", "1Y", "2Y", "5Y", "10Y", "ALL")
    for period in periods:
        current_row = current.loc[period]
        sources = (
            (
                "RAW",
                "BENCHMARK",
                "raw",
                current_row,
            ),
            (
                "B123",
                b123_status,
                "locked_b123",
                current_row,
            ),
            (
                "V15",
                v15_status,
                "v15",
                v15.loc[period],
            ),
            (
                "V16",
                v16_status,
                "v16",
                v16.loc[period],
            ),
            (
                "V17",
                v17_status,
                "v17",
                v17.loc[period],
            ),
            (
                "V18",
                v18_decision,
                "v18",
                current_row,
            ),
        )
        raw_pnl = float(current_row["raw_net_pnl_usd"])
        for approach, decision, prefix, source in sources:
            rows.append(
                {
                    "period": period,
                    "approach": approach,
                    "decision": decision,
                    "trades": int(source[f"{prefix}_trades"]),
                    "net_pnl_usd": float(source[f"{prefix}_net_pnl_usd"]),
                    "delta_vs_raw_usd": float(
                        source[f"{prefix}_net_pnl_usd"] - raw_pnl
                    ),
                    "win_rate_pct": float(source[f"{prefix}_win_rate_pct"]),
                    "profit_factor": float(source[f"{prefix}_profit_factor"]),
                    "closed_trade_drawdown_usd": float(
                        source[f"{prefix}_closed_trade_drawdown_usd"]
                    ),
                }
            )
    return pd.DataFrame(rows)


def comparison_markdown(comparison: pd.DataFrame) -> str:
    lines = [
        "# ML Experiment Comparison Through V18",
        "",
        "V14 is the locked prospective lane and has no distinct exact historical "
        "replay, so it is listed in the registry but not duplicated in these tables.",
        "",
    ]
    for period in ("3M", "6M", "1Y", "2Y", "5Y", "10Y", "ALL"):
        lines.extend(
            [
                f"## {period}",
                "",
                "| Approach | Trades | P&L | Delta vs raw | Win rate | PF | DD | Decision |",
                "|---|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for _, row in comparison.loc[comparison["period"].eq(period)].iterrows():
            lines.append(
                f"| {row['approach']} | {int(row['trades'])} | "
                f"${row['net_pnl_usd']:.2f} | ${row['delta_vs_raw_usd']:.2f} | "
                f"{row['win_rate_pct']:.2f}% | {row['profit_factor']:.3f} | "
                f"${row['closed_trade_drawdown_usd']:.2f} | "
                f"`{row['decision']}` |"
            )
        lines.append("")
    return "\n".join(lines)


def result_markdown(result: Mapping[str, Any], windows: pd.DataFrame) -> str:
    rows = windows.set_index("period")
    lines = [
        "# V8 Auxiliary Veto V18 Result",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "| Period | Raw P&L | B123 P&L | V18 P&L | V18 vs raw | V18 vs B123 | Trades | Win rate | PF | DD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for period in ("3M", "6M", "1Y", "2Y", "5Y", "10Y", "ALL"):
        row = rows.loc[period]
        lines.append(
            f"| {period} | ${row['raw_net_pnl_usd']:.2f} | "
            f"${row['locked_b123_net_pnl_usd']:.2f} | "
            f"${row['v18_net_pnl_usd']:.2f} | "
            f"${row['v18_delta_vs_raw_usd']:.2f} | "
            f"${row['v18_delta_vs_locked_b123_usd']:.2f} | "
            f"{int(row['v18_trades'])} | {row['v18_win_rate_pct']:.2f}% | "
            f"{row['v18_profit_factor']:.3f} | "
            f"${row['v18_closed_trade_drawdown_usd']:.2f} |"
        )
    lines.extend(
        [
            "",
            f"B123 V8 vetoes: {result['out_of_time']['b123_v8_vetoes']}. "
            f"V18 V8 vetoes: {result['out_of_time']['v18_v8_vetoes']}. "
            f"V8 additional vetoes: "
            f"{result['out_of_time']['v8_additional_vetoes']}.",
            "",
            "V18 is historical research only. V14-V17, MT5, and demo execution were not changed.",
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
    v18_windows, trade_audit, replay_checks = exact_v60_replay(
        predictions, paths
    )
    windows = combined_windows(v18_windows, paths["locked_b123_windows"])
    result = build_result(config, contract, windows, folds, dataset_audit)
    result["exact_v60_replay_checks"] = replay_checks
    comparison = experiment_comparison(windows, paths, result["decision"])

    OUTPUT.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "contract_lock": CONTRACT_PATH,
        "dataset_audit": OUTPUT / config["outputs"]["dataset_audit"],
        "predictions": OUTPUT / config["outputs"]["predictions"],
        "fold_metrics": OUTPUT / config["outputs"]["fold_metrics"],
        "threshold_decisions": OUTPUT / config["outputs"]["threshold_decisions"],
        "windows": OUTPUT / config["outputs"]["windows"],
        "trade_audit": OUTPUT / config["outputs"]["trade_audit"],
        "experiment_comparison_csv": (
            OUTPUT / config["outputs"]["experiment_comparison_csv"]
        ),
        "experiment_comparison_markdown": (
            OUTPUT / config["outputs"]["experiment_comparison_markdown"]
        ),
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
    comparison.to_csv(output_paths["experiment_comparison_csv"], index=False)
    output_paths["experiment_comparison_markdown"].write_text(
        comparison_markdown(comparison),
        encoding="utf-8",
    )
    output_paths["result_json"].write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    output_paths["result_markdown"].write_text(
        result_markdown(result, windows),
        encoding="utf-8",
    )
    manifest = {
        "schema_version": "xauusd_v8_auxiliary_veto_v18_artifact_manifest",
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

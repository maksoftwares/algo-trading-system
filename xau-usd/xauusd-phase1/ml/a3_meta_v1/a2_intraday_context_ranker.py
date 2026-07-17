from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import roc_auc_score


DEFAULT_CONTRACT = Path("config/ml/a3_ml_a2_intraday_context_ranker_v1.json")
EXPECTED_MODEL = {
    "family": "HIST_GRADIENT_BOOSTING_REGRESSOR_V1",
    "loss": "squared_error",
    "learning_rate": 0.05,
    "max_iter": 150,
    "max_leaf_nodes": 7,
    "max_depth": 3,
    "min_samples_leaf": 75,
    "l2_regularization": 2.0,
    "early_stopping": False,
    "random_state": 20260717,
    "hyperparameter_search_authorized": False,
}
OUTCOME_TOKENS = ("profit", "stress_net", "exit_", "mfe", "mae", "target")


class A2IntradayContextRankerError(RuntimeError):
    pass


def run_a2_intraday_context_ranker(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = Path(
        os.environ.get(
            str(contract["storage_environment_variable"]),
            str(contract["default_storage_root"]),
        )
    ).resolve()
    outputs = {
        key: (root / value).resolve() for key, value in contract["outputs"].items()
    }
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    for key, path in outputs.items():
        if key not in {"report_json", "report_markdown"} and path.exists():
            path.unlink()

    source_rows, source_audit = _load_and_validate_a2_source(storage_root, contract)
    microstructure, source_locks = _load_feature_sources(root, storage_root, contract)
    dataset, join_audit = _build_dataset(source_rows, microstructure, contract)
    dataset.to_parquet(outputs["dataset_parquet"], index=False)

    windows = contract["windows"]
    train = _segment(
        dataset,
        windows["train_start_utc"],
        windows["train_end_exclusive_utc"],
    )
    oof, fold_audit = _purged_oof_predictions(train, contract)
    if oof["position_id"].duplicated().any():
        raise A2IntradayContextRankerError("OOF position identifiers are not unique")
    oof.to_csv(outputs["oof_predictions_csv"], index=False, lineterminator="\n")

    predictive = _predictive_metrics(oof)
    evaluations: list[dict[str, Any]] = []
    selections: dict[float, pd.DataFrame] = {}
    for fraction in contract["selection"]["oof_score_top_fractions"]:
        fraction = float(fraction)
        cutoff = _top_fraction_cutoff(oof["model_score"].to_numpy(), fraction)
        selected = _select_daily(oof, cutoff, contract["selection"])
        economic = _economic_metrics(
            selected,
            _active_source_days(oof),
            contract["selection"],
        )
        gates = _segment_gates(
            predictive,
            economic,
            contract["oof_gates"],
            require_bootstrap=True,
        )
        evaluations.append(
            {
                "stage": "OOF",
                "policy_id": f"OOF_TOP_{int(fraction * 100)}",
                "retention_fraction": fraction,
                "score_cutoff": cutoff,
                "predictive_metrics": predictive,
                "economic_metrics": economic,
                "gates": gates,
                "passes": all(gates.values()),
            }
        )
        selections[fraction] = selected

    passing = [row for row in evaluations if row["passes"]]
    passing.sort(key=_policy_sort_key)
    selected_policy = passing[0] if passing else None
    selected_frames: list[pd.DataFrame] = []
    model_payload: dict[str, Any] | None = None
    opened = {"validation": False, "internal_test": False, "exam": False}
    classification = "A2_INTRADAY_CONTEXT_RANKER_NO_OOF_SURVIVOR"

    if selected_policy:
        fraction = float(selected_policy["retention_fraction"])
        selected_oof = selections[fraction].copy()
        selected_oof["stage"] = "OOF"
        selected_frames.append(selected_oof)
        cutoff = float(selected_policy["score_cutoff"])
        features = list(contract["features"])
        model = _fit_model(train, features, contract["model"])
        validation, validation_result = _score_segment(
            dataset,
            model,
            cutoff,
            windows["train_end_exclusive_utc"],
            windows["validation_end_exclusive_utc"],
            "VALIDATION",
            contract["validation_gates"],
            contract,
        )
        opened["validation"] = True
        evaluations.append(validation_result)
        if not validation.empty:
            selected_frames.append(validation)
        classification = "A2_INTRADAY_CONTEXT_RANKER_VALIDATION_REJECTED"
        model_payload = _model_payload(model, features, selected_policy, contract_file)

        if validation_result["passes"]:
            fit_through_validation = _segment(
                dataset,
                windows["train_start_utc"],
                windows["validation_end_exclusive_utc"],
            )
            model = _fit_model(fit_through_validation, features, contract["model"])
            internal, internal_result = _score_segment(
                dataset,
                model,
                cutoff,
                windows["validation_end_exclusive_utc"],
                windows["internal_test_end_exclusive_utc"],
                "INTERNAL_TEST",
                contract["internal_test_gates"],
                contract,
            )
            opened["internal_test"] = True
            evaluations.append(internal_result)
            if not internal.empty:
                selected_frames.append(internal)
            classification = "A2_INTRADAY_CONTEXT_RANKER_INTERNAL_TEST_REJECTED"
            model_payload = _model_payload(
                model, features, selected_policy, contract_file
            )

            if internal_result["passes"]:
                fit_through_internal = _segment(
                    dataset,
                    windows["train_start_utc"],
                    windows["internal_test_end_exclusive_utc"],
                )
                model = _fit_model(fit_through_internal, features, contract["model"])
                exam, exam_result = _score_segment(
                    dataset,
                    model,
                    cutoff,
                    windows["internal_test_end_exclusive_utc"],
                    windows["exam_end_exclusive_utc"],
                    "EXAM",
                    contract["exam_gates"],
                    contract,
                )
                opened["exam"] = True
                evaluations.append(exam_result)
                if not exam.empty:
                    selected_frames.append(exam)
                classification = (
                    "A2_INTRADAY_CONTEXT_RANKER_RESEARCH_SURVIVOR"
                    if exam_result["passes"]
                    else "A2_INTRADAY_CONTEXT_RANKER_EXAM_REJECTED"
                )
                model_payload = _model_payload(
                    model, features, selected_policy, contract_file
                )

    selected = (
        pd.concat(selected_frames, ignore_index=True)
        if selected_frames
        else pd.DataFrame(
            columns=["stage", "position_id", "model_score", "stress_net_r"]
        )
    )
    selected.to_csv(
        outputs["selected_predictions_csv"], index=False, lineterminator="\n"
    )
    _write_evaluations(outputs["evaluations_csv"], evaluations)
    if model_payload is not None:
        joblib.dump(model_payload, outputs["model_joblib"], compress=3)

    payload = {
        "schema_version": contract["schema_version"],
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "storage_root": str(storage_root),
        "source_audit": source_audit,
        "source_locks": source_locks,
        "join_audit": join_audit,
        "dataset_rows": len(dataset),
        "train_rows": len(train),
        "oof_rows": len(oof),
        "oof_fold_audit": fold_audit,
        "oof_predictive_metrics": predictive,
        "evaluations": evaluations,
        "selected_policy": selected_policy,
        "chronological_stages_opened": opened,
        "artifacts": _artifact_manifest(outputs),
        "research_controls": contract["research_controls"],
        "authorization": {
            **contract["authorization"],
            "model_execution_authorized": False,
            "demo_or_live_authorized": False,
        },
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_a2_intraday_context_ranker_v1":
        raise A2IntradayContextRankerError("unexpected ranker contract")
    if contract.get("model") != EXPECTED_MODEL:
        raise A2IntradayContextRankerError("preregistered model configuration changed")
    causal = contract.get("causal_join", {})
    if causal.get("feature_cutoff_minutes_before_entry") != 5:
        raise A2IntradayContextRankerError("feature cutoff must remain five minutes")
    if not causal.get("require_exact_completed_m5_feature_timestamp"):
        raise A2IntradayContextRankerError("exact completed M5 join is required")
    if (
        causal.get("forward_fill_authorized")
        or causal.get("maximum_clock_difference_seconds") != 0
    ):
        raise A2IntradayContextRankerError(
            "forward or approximate feature joins are forbidden"
        )
    macro = contract.get("intraday_macro_features", {})
    if macro.get("forward_fill_authorized") or macro.get(
        "allow_returns_across_timestamp_gaps"
    ):
        raise A2IntradayContextRankerError(
            "macro forward fill or gap returns are forbidden"
        )
    features = list(contract.get("features", []))
    if len(features) != len(set(features)) or not features:
        raise A2IntradayContextRankerError(
            "model feature list must be unique and nonempty"
        )
    forbidden = [
        name for name in features if any(token in name for token in OUTCOME_TOKENS)
    ]
    if forbidden:
        raise A2IntradayContextRankerError(
            f"outcome-derived features are forbidden: {forbidden}"
        )
    if contract.get("research_controls", {}).get(
        "same_iteration_feature_or_hyperparameter_tuning_authorized"
    ):
        raise A2IntradayContextRankerError("same-iteration tuning must remain disabled")
    for key, value in contract.get("authorization", {}).items():
        if value:
            raise A2IntradayContextRankerError(f"{key} must remain false")


def _load_and_validate_a2_source(
    storage_root: Path, contract: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    lock = contract["a2_source_lock"]
    source_root = (storage_root / lock["relative_root"]).resolve()
    paths: dict[str, Path] = {}
    for name, spec in lock["files"].items():
        path = source_root / spec["filename"]
        if not path.is_file():
            raise A2IntradayContextRankerError(f"A2 source is missing: {path}")
        if path.stat().st_size != int(spec["bytes"]):
            raise A2IntradayContextRankerError(f"A2 source byte count changed: {path}")
        if _sha256_file(path) != spec["sha256"]:
            raise A2IntradayContextRankerError(f"A2 source hash changed: {path}")
        paths[name] = path

    trades = pd.read_csv(
        paths["trades"],
        usecols=[
            "position_id",
            "entry_time",
            "direction",
            "entry_deal",
            "entry_order",
            "entry_price",
            "exit_time",
            "exit_deal",
            "exit_order",
            "exit_price",
            "profit_aed",
        ],
    )
    orders = pd.read_csv(
        paths["orders"],
        usecols=[
            "timestamp_utc",
            "action",
            "direction",
            "spread_at_order_points",
            "estimated_cost_R",
            "stop_distance_points",
            "sl",
            "tp",
            "order_ticket",
            "deal_ticket",
        ],
    )
    orders = orders.loc[orders["action"] == "ORDER_SEND_OK"].copy()
    deals = pd.read_csv(
        paths["deals"],
        usecols=["deal_ticket", "position_id", "entry_code", "direction"],
    )
    _validate_lifecycle_frames(trades, orders, deals, lock)
    merged = trades.merge(
        orders,
        left_on=["entry_deal", "entry_order"],
        right_on=["deal_ticket", "order_ticket"],
        how="left",
        validate="one_to_one",
        suffixes=("_trade", "_order"),
    )
    if merged["timestamp_utc"].isna().any():
        raise A2IntradayContextRankerError("trade/order join is incomplete")
    if not (merged["direction_trade"] == merged["direction_order"]).all():
        raise A2IntradayContextRankerError("trade/order directions disagree")
    merged["entry_timestamp"] = pd.to_datetime(
        merged["entry_time"], format="%Y.%m.%d %H:%M:%S", utc=True
    )
    merged["order_timestamp"] = pd.to_datetime(
        merged["timestamp_utc"], format="%Y.%m.%d %H:%M:%S", utc=True
    )
    merged["exit_timestamp"] = pd.to_datetime(
        merged["exit_time"], format="%Y.%m.%d %H:%M:%S", utc=True
    )
    if not (merged["entry_timestamp"] == merged["order_timestamp"]).all():
        raise A2IntradayContextRankerError(
            "entry and successful-order timestamps disagree"
        )
    merged = merged.rename(columns={"direction_trade": "direction"})
    return merged, {
        "source_root": str(source_root),
        "trades": len(trades),
        "successful_entry_orders": len(orders),
        "deals": len(deals),
        "unique_position_ids": int(trades["position_id"].nunique()),
        "hashes_verified": True,
        "trade_order_join_one_to_one": True,
        "two_deals_per_position": True,
        "history_quality_percentage_available": bool(
            lock["history_quality_percentage_available"]
        ),
    }


def _validate_lifecycle_frames(
    trades: pd.DataFrame,
    orders: pd.DataFrame,
    deals: pd.DataFrame,
    lock: Mapping[str, Any],
) -> None:
    integrity = lock["required_integrity"]
    expected = int(integrity["unique_position_ids"])
    if (
        len(trades) != int(lock["files"]["trades"]["rows"])
        or trades["position_id"].nunique() != expected
    ):
        raise A2IntradayContextRankerError(
            "trade population or position uniqueness changed"
        )
    if len(orders) != int(integrity["successful_entry_orders"]):
        raise A2IntradayContextRankerError("successful entry-order population changed")
    if orders[["deal_ticket", "order_ticket"]].duplicated().any():
        raise A2IntradayContextRankerError("successful entry orders are not unique")
    if len(deals) != int(lock["files"]["deals"]["rows"]):
        raise A2IntradayContextRankerError("deal population changed")
    if deals["deal_ticket"].duplicated().any():
        raise A2IntradayContextRankerError("deal tickets are not unique")
    deal_counts = deals.groupby("position_id").size()
    if (
        len(deal_counts) != expected
        or not (deal_counts == int(integrity["deals_per_position"])).all()
    ):
        raise A2IntradayContextRankerError(
            "position lifecycle does not contain exactly two deals"
        )
    codes = deals.groupby("position_id")["entry_code"].agg(
        lambda values: frozenset(values)
    )
    if not (codes == frozenset({0, 1})).all():
        raise A2IntradayContextRankerError(
            "position lifecycle lacks one entry and one exit"
        )
    if set(trades["position_id"]) != set(deals["position_id"]):
        raise A2IntradayContextRankerError(
            "trade and deal position populations disagree"
        )
    indexed_trades = trades.set_index("position_id")
    indexed_entries = deals.loc[deals["entry_code"] == 0].set_index("position_id")
    indexed_exits = deals.loc[deals["entry_code"] == 1].set_index("position_id")
    if not indexed_trades["entry_deal"].equals(indexed_entries["deal_ticket"]):
        raise A2IntradayContextRankerError(
            "trade entry deals do not match position lifecycles"
        )
    if not indexed_trades["exit_deal"].equals(indexed_exits["deal_ticket"]):
        raise A2IntradayContextRankerError(
            "trade exit deals do not match position lifecycles"
        )
    for lifecycle in (indexed_entries, indexed_exits):
        if not indexed_trades["direction"].equals(lifecycle["direction"]):
            raise A2IntradayContextRankerError("trade and deal directions disagree")
    numeric = orders[["sl", "tp", "stop_distance_points"]].apply(
        pd.to_numeric, errors="coerce"
    )
    if numeric.isna().any().any() or (numeric <= 0).any().any():
        raise A2IntradayContextRankerError("nonpositive stop, target, or risk distance")


def _load_feature_sources(
    root: Path, storage_root: Path, contract: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    micro_lock = contract["microstructure_source_lock"]
    macro_lock = contract["intraday_macro_source_lock"]
    cost_lock = contract["broker_cost_source_lock"]
    micro_path = storage_root / micro_lock["feature_path"]
    micro_manifest = storage_root / micro_lock["manifest_path"]
    macro_path = storage_root / macro_lock["feature_path"]
    macro_manifest = storage_root / macro_lock["manifest_path"]
    macro_report = root / macro_lock["report_path"]
    cost_report = root / cost_lock["report_path"]
    checks = [
        (micro_path, micro_lock["feature_sha256"]),
        (micro_manifest, micro_lock["manifest_sha256"]),
        (macro_path, macro_lock["feature_sha256"]),
        (macro_manifest, macro_lock["manifest_sha256"]),
        (macro_report, macro_lock["report_sha256"]),
        (cost_report, cost_lock["report_sha256"]),
    ]
    for path, expected in checks:
        if not path.is_file() or _sha256_file(path) != expected:
            raise A2IntradayContextRankerError(
                f"locked feature source missing or changed: {path}"
            )
    if micro_path.stat().st_size != int(micro_lock["feature_bytes"]):
        raise A2IntradayContextRankerError("microstructure feature byte count changed")
    macro_report_payload = json.loads(macro_report.read_text(encoding="utf-8"))
    cost_report_payload = json.loads(cost_report.read_text(encoding="utf-8"))
    if (
        macro_report_payload.get("classification")
        != macro_lock["required_classification"]
    ):
        raise A2IntradayContextRankerError("intraday macro source is not valid")
    if (
        cost_report_payload.get("classification")
        != cost_lock["required_classification"]
    ):
        raise A2IntradayContextRankerError("broker cost source is not valid")
    micro = pd.read_parquet(micro_path)
    macro = pd.read_parquet(macro_path)
    if len(micro) != int(micro_lock["feature_rows"]) or len(macro) != int(
        macro_lock["feature_rows"]
    ):
        raise A2IntradayContextRankerError("locked feature row count changed")
    macro_features = _build_macro_features(macro, contract["intraday_macro_features"])
    if (
        micro["timestamp_ms"].duplicated().any()
        or macro_features["timestamp_ms"].duplicated().any()
    ):
        raise A2IntradayContextRankerError("feature timestamps are not unique")
    joined = micro.merge(
        macro_features, on="timestamp_ms", how="left", validate="one_to_one"
    )
    return joined, {
        "microstructure_feature_path": str(micro_path),
        "microstructure_rows": len(micro),
        "intraday_macro_feature_path": str(macro_path),
        "intraday_macro_rows": len(macro),
        "feature_hashes_verified": True,
        "macro_source_classification": macro_report_payload["classification"],
        "broker_cost_classification": cost_report_payload["classification"],
    }


def _build_macro_features(
    frame: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    data = frame.sort_values("timestamp_ms").reset_index(drop=True).copy()
    result = pd.DataFrame({"timestamp_ms": data["timestamp_ms"].astype("int64")})
    step = data["timestamp_ms"].diff().eq(300_000)
    for prefix in ("dollaridxusd", "ustbondtrusd"):
        close = pd.to_numeric(data[f"{prefix}_mid_close"], errors="coerce")
        available = (
            data[f"{prefix}_available"].fillna(False).astype(bool) & close.notna()
        )
        one_bar = close.pct_change(fill_method=None).where(
            available & available.shift(1, fill_value=False) & step
        )
        volatility = (
            one_bar.rolling(
                int(config["volatility_window_m5_bars"]),
                min_periods=int(config["volatility_minimum_periods"]),
            )
            .std(ddof=0)
            .shift(int(config["volatility_scale_lag_bars"]))
        )
        short = "dollar" if prefix == "dollaridxusd" else "bond"
        for lookback in config["return_lookbacks_m5_bars"]:
            lookback = int(lookback)
            contiguous = (
                available.astype(int)
                .rolling(lookback + 1, min_periods=lookback + 1)
                .sum()
                == lookback + 1
            ) & data["timestamp_ms"].sub(data["timestamp_ms"].shift(lookback)).eq(
                lookback * 300_000
            )
            returns = close.pct_change(lookback, fill_method=None).where(contiguous)
            result[f"{short}_z_{lookback * 5}m"] = (returns / volatility).where(
                volatility > 0
            )
    return result


def _build_dataset(
    source: pd.DataFrame,
    features: pd.DataFrame,
    contract: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    data = source.copy()
    research_start = pd.Timestamp(contract["windows"]["train_start_utc"])
    research_end = pd.Timestamp(contract["windows"]["exam_end_exclusive_utc"])
    data = data.loc[
        (data["entry_timestamp"] >= research_start)
        & (data["entry_timestamp"] < research_end)
        & (data["exit_timestamp"] < research_end)
    ].copy()
    cutoff_minutes = int(contract["causal_join"]["feature_cutoff_minutes_before_entry"])
    data["feature_cutoff_timestamp"] = _feature_cutoff_timestamp(
        data["order_timestamp"], cutoff_minutes
    )
    data["feature_cutoff_timestamp_ms"] = _to_epoch_ms(data["feature_cutoff_timestamp"])
    data = data.merge(
        features,
        left_on="feature_cutoff_timestamp_ms",
        right_on="timestamp_ms",
        how="left",
        validate="many_to_one",
    )
    point = float(contract["a2_source_lock"]["point_size_price"])
    costs = contract["broker_cost_source_lock"]
    data["risk_price"] = pd.to_numeric(data["stop_distance_points"]) * point
    data["source_spread_price"] = pd.to_numeric(data["spread_at_order_points"]) * point
    holding_days = (
        data["exit_timestamp"] - data["entry_timestamp"]
    ).dt.total_seconds() / 86_400
    data["stress_cost"] = _stress_cost(data["source_spread_price"], holding_days, costs)
    data["source_profit"] = pd.to_numeric(
        data[contract["label"]["source_profit_field"]]
    )
    data["stress_net_r"] = (data["source_profit"] - data["stress_cost"]) / data[
        "risk_price"
    ]
    data["source_gross_r"] = data["source_profit"] / data["risk_price"]
    data["direction_sign"] = np.where(data["direction"] == "LONG", 1.0, -1.0)
    sign = data["direction_sign"]
    atr = data["atr"]
    close = data["xauusd_mid_close"]
    risk = data["risk_price"]
    data["source_estimated_cost_r"] = pd.to_numeric(data["estimated_cost_R"])
    data["source_spread_r"] = data["source_spread_price"] / risk
    data["source_stop_distance_atr"] = risk / atr
    for minutes in (5, 15, 60):
        data[f"xau_return_{minutes}m_directional_r"] = (
            sign * data[f"xau_return_{minutes}m_price"] / atr
        )
    data["ema_gap_directional_r"] = sign * (data["ema_fast"] - data["ema_slow"]) / atr
    data["ema_slope_directional_r"] = sign * data["ema_fast_slope_3"] / atr
    data["ema_distance_directional_r"] = sign * (close - data["ema_fast"]) / atr
    relevant_break = np.where(sign > 0, data["prior_high_12"], data["prior_low_12"])
    data["prior_break_distance_directional_r"] = sign * (close - relevant_break) / atr
    data["zscore_24_directional"] = sign * data["zscore_24"]
    for name in (
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "tick_imbalance_60m",
        "book_imbalance_5m",
        "book_imbalance_15m",
    ):
        data[f"{name}_directional"] = sign * data[name]
    for minutes in (5, 15):
        data[f"microprice_edge_{minutes}m_directional_r"] = (
            sign * data[f"microprice_edge_{minutes}m"] / atr
        )
    for market, minutes in (
        ("xag", 5),
        ("xag", 15),
        ("xag", 60),
        ("eurusd", 15),
        ("eurusd", 60),
        ("usdjpy", 15),
        ("usdjpy", 60),
    ):
        source_name = (
            f"{market}usd_return_{minutes}m"
            if market == "xag"
            else f"{market}_return_{minutes}m"
        )
        data[f"{market}_return_{minutes}m_directional"] = sign * data[source_name]
    for minutes in (15, 60, 180):
        data[f"dollar_z_{minutes}m_directional_gold"] = (
            -sign * data[f"dollar_z_{minutes}m"]
        )
        data[f"bond_z_{minutes}m_directional_gold"] = sign * data[f"bond_z_{minutes}m"]
    for minutes in (60, 180):
        data[f"macro_agreement_{minutes}m"] = np.minimum(
            data[f"dollar_z_{minutes}m_directional_gold"],
            data[f"bond_z_{minutes}m_directional_gold"],
        )
    data["atr_fraction_of_price"] = atr / close
    data["entry_spread_r"] = (
        data["xauusd_ask_close"] - data["xauusd_bid_close"]
    ) / risk
    hour = data["entry_timestamp"].dt.hour + data["entry_timestamp"].dt.minute / 60
    weekday = data["entry_timestamp"].dt.dayofweek
    data["hour_sin"] = np.sin(2 * math.pi * hour / 24)
    data["hour_cos"] = np.cos(2 * math.pi * hour / 24)
    data["weekday_sin"] = np.sin(2 * math.pi * weekday / 7)
    data["weekday_cos"] = np.cos(2 * math.pi * weekday / 7)
    data["regime_trend"] = data["regime"].isin(["TREND_UP", "TREND_DOWN"]).astype(float)
    data["regime_range"] = data["regime"].eq("RANGE").astype(float)
    data["regime_shock"] = data["regime"].eq("SHOCK").astype(float)
    data["entry_time_ms"] = _to_epoch_ms(data["entry_timestamp"])
    data["exit_time_ms"] = _to_epoch_ms(data["exit_timestamp"])
    data["entry_time_utc"] = data["entry_timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    data["exit_time_utc"] = data["exit_timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    population = len(data)
    feature_names = list(contract["features"])
    finite = np.isfinite(data[feature_names].apply(pd.to_numeric, errors="coerce")).all(
        axis=1
    )
    valid = (
        finite
        & np.isfinite(data[["stress_net_r", "source_gross_r"]]).all(axis=1)
        & (risk > 0)
    )
    joined = (
        data.loc[valid]
        .copy()
        .sort_values(["entry_time_ms", "position_id"])
        .reset_index(drop=True)
    )
    share = len(joined) / population if population else 0.0
    if share < float(contract["causal_join"]["minimum_joined_population_share"]):
        raise A2IntradayContextRankerError(
            f"causal feature join share is too low: {share:.4f}"
        )
    keep = list(
        dict.fromkeys(
            [
                "position_id",
                "direction",
                "entry_time_utc",
                "exit_time_utc",
                "entry_time_ms",
                "exit_time_ms",
                "feature_cutoff_timestamp_ms",
                "source_profit",
                "source_gross_r",
                "stress_cost",
                "stress_net_r",
                "risk_price",
            ]
            + feature_names
        )
    )
    return joined[keep], {
        "source_rows": population,
        "joined_finite_rows": len(joined),
        "joined_population_share": share,
        "dropped_rows": population - len(joined),
        "exact_feature_cutoff_minutes": cutoff_minutes,
        "all_model_features_finite": True,
    }


def _feature_cutoff_timestamp(
    order_timestamp: pd.Series, cutoff_minutes: int
) -> pd.Series:
    return order_timestamp - pd.Timedelta(minutes=cutoff_minutes)


def _to_epoch_ms(timestamp: pd.Series) -> pd.Series:
    return timestamp.map(lambda value: value.value // 1_000_000).astype("int64")


def _stress_cost(
    source_spread_price: pd.Series,
    holding_days: pd.Series,
    cost_config: Mapping[str, Any],
) -> pd.Series:
    return (
        (float(cost_config["broker_spread_floor_price"]) - source_spread_price).clip(
            lower=0
        )
        + float(cost_config["additional_execution_cost_usd_per_0p01_lot"])
        + holding_days * float(cost_config["holding_cost_per_24h_usd"])
    )


def _segment(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    lo = pd.Timestamp(start)
    hi = pd.Timestamp(end)
    entry = pd.to_datetime(frame["entry_time_utc"], utc=True)
    exit_time = pd.to_datetime(frame["exit_time_utc"], utc=True)
    return frame.loc[(entry >= lo) & (entry < hi) & (exit_time < hi)].copy()


def _purged_oof_predictions(
    train: pd.DataFrame, contract: Mapping[str, Any]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    pieces = []
    audits = []
    features = list(contract["features"])
    for fold in contract["purged_oof"]["folds"]:
        fit = _segment(train, fold["fit_start_utc"], fold["fit_end_exclusive_utc"])
        fit = fit.loc[
            pd.to_datetime(fit["exit_time_utc"], utc=True)
            < pd.Timestamp(fold["evaluation_start_utc"])
        ]
        evaluation = _segment(
            train, fold["evaluation_start_utc"], fold["evaluation_end_exclusive_utc"]
        )
        if (
            len(fit) < int(contract["model"]["min_samples_leaf"]) * 2
            or evaluation.empty
        ):
            raise A2IntradayContextRankerError(
                f"OOF fold is too small: {fold['fold_id']}"
            )
        model = _fit_model(fit, features, contract["model"])
        scored = evaluation.copy()
        scored["model_score"] = model.predict(_matrix(evaluation, features))
        scored["fold_id"] = fold["fold_id"]
        pieces.append(scored)
        audits.append(
            {
                "fold_id": fold["fold_id"],
                "fit_rows_after_actual_exit_purge": len(fit),
                "evaluation_rows": len(evaluation),
                "latest_fit_exit_utc": fit["exit_time_utc"].max(),
                "evaluation_start_utc": fold["evaluation_start_utc"],
            }
        )
    return pd.concat(pieces, ignore_index=True), audits


def _fit_model(
    rows: pd.DataFrame, features: Sequence[str], config: Mapping[str, Any]
) -> HistGradientBoostingRegressor:
    model = HistGradientBoostingRegressor(
        loss=str(config["loss"]),
        learning_rate=float(config["learning_rate"]),
        max_iter=int(config["max_iter"]),
        max_leaf_nodes=int(config["max_leaf_nodes"]),
        max_depth=int(config["max_depth"]),
        min_samples_leaf=int(config["min_samples_leaf"]),
        l2_regularization=float(config["l2_regularization"]),
        early_stopping=bool(config["early_stopping"]),
        random_state=int(config["random_state"]),
    )
    model.fit(_matrix(rows, features), rows["stress_net_r"].to_numpy(dtype=float))
    return model


def _matrix(rows: pd.DataFrame, features: Sequence[str]) -> np.ndarray:
    matrix = rows[list(features)].to_numpy(dtype=float)
    if matrix.ndim != 2 or not len(matrix) or not np.isfinite(matrix).all():
        raise A2IntradayContextRankerError("model matrix is empty or non-finite")
    return matrix


def _predictive_metrics(scored: pd.DataFrame) -> dict[str, Any]:
    outcomes = scored["stress_net_r"].to_numpy(dtype=float)
    scores = scored["model_score"].to_numpy(dtype=float)
    labels = (outcomes > 0).astype(int)
    auc = float(roc_auc_score(labels, scores)) if len(np.unique(labels)) == 2 else None
    spearman = float(pd.Series(scores).corr(pd.Series(outcomes), method="spearman"))
    return {"population": len(scored), "auc": auc, "spearman": spearman}


def _top_fraction_cutoff(scores: Sequence[float], fraction: float) -> float:
    ranked = np.sort(np.asarray(scores, dtype=float))[::-1]
    count = max(1, math.ceil(len(ranked) * fraction))
    return float(ranked[count - 1])


def _select_daily(
    scored: pd.DataFrame, cutoff: float, selection: Mapping[str, Any]
) -> pd.DataFrame:
    eligible = scored.loc[scored["model_score"] >= cutoff].copy()
    eligible["entry_day"] = eligible["entry_time_utc"].str[:10]
    eligible = eligible.sort_values(
        ["entry_day", "model_score", "entry_time_ms", "position_id"],
        ascending=[True, False, True, True],
    )
    selected = eligible.groupby("entry_day", sort=False).head(
        int(selection["maximum_selected_trades_per_utc_day"])
    )
    return selected.sort_values(["entry_time_ms", "position_id"]).reset_index(drop=True)


def _active_source_days(frame: pd.DataFrame) -> int:
    return int(frame["entry_time_utc"].str[:10].nunique())


def _economic_metrics(
    selected: pd.DataFrame,
    source_days: int,
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    ordered = selected.sort_values(["exit_time_ms", "position_id"])
    values = ordered["stress_net_r"].to_numpy(dtype=float)
    wins = values[values > 0]
    losses = values[values < 0]
    equity = np.cumsum(values)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    drawdown = peaks[1:] - equity if len(values) else np.asarray([], dtype=float)
    months = (
        ordered.assign(exit_month=ordered["exit_time_utc"].str[:7])
        .groupby("exit_month")["stress_net_r"]
        .sum()
    )
    counts = ordered["direction"].value_counts()
    minimum_direction_share = (
        min(int(counts.get("LONG", 0)), int(counts.get("SHORT", 0))) / len(ordered)
        if len(ordered)
        else 0.0
    )
    winners = np.sort(wins)[::-1]
    return {
        "trades": len(ordered),
        "wins": len(wins),
        "losses": len(losses),
        "stress_net_r": float(values.sum()),
        "average_stress_r": float(values.mean()) if len(values) else 0.0,
        "stress_profit_factor": float(wins.sum() / -losses.sum())
        if len(losses) and -losses.sum() > 0
        else None,
        "maximum_closed_drawdown_r": float(drawdown.max()) if len(drawdown) else 0.0,
        "trades_per_source_day": len(ordered) / source_days if source_days else 0.0,
        "source_active_days": source_days,
        "positive_exit_month_share": float((months > 0).mean()) if len(months) else 0.0,
        "top_ten_winners_removed_net_r": float(values.sum() - winners[:10].sum()),
        "direction_counts": {key: int(value) for key, value in counts.items()},
        "minimum_direction_share": minimum_direction_share,
        "bootstrap_mean_stress_r_p025": _calendar_month_bootstrap_p025(
            ordered,
            int(selection["calendar_month_bootstrap_samples"]),
            int(selection["bootstrap_seed"]),
        ),
    }


def _calendar_month_bootstrap_p025(
    frame: pd.DataFrame, samples: int, seed: int
) -> float | None:
    if frame.empty:
        return None
    groups = [
        group["stress_net_r"].to_numpy(dtype=float)
        for _, group in frame.assign(exit_month=frame["exit_time_utc"].str[:7]).groupby(
            "exit_month"
        )
    ]
    rng = np.random.default_rng(seed)
    means = []
    for _ in range(samples):
        chosen = rng.integers(0, len(groups), size=len(groups))
        values = np.concatenate([groups[index] for index in chosen])
        means.append(float(values.mean()))
    return float(np.quantile(means, 0.025))


def _segment_gates(
    predictive: Mapping[str, Any],
    economic: Mapping[str, Any],
    gate: Mapping[str, Any],
    *,
    require_bootstrap: bool = False,
) -> dict[str, bool]:
    checks = {
        "minimum_auc": float(predictive.get("auc") or 0.0)
        >= float(gate["minimum_auc"]),
        "minimum_spearman": float(predictive.get("spearman") or 0.0)
        >= float(gate["minimum_spearman"]),
        "minimum_trades": int(economic["trades"]) >= int(gate["minimum_trades"]),
        "minimum_frequency": float(economic["trades_per_source_day"])
        >= float(gate["minimum_trades_per_source_day"]),
        "maximum_frequency": float(economic["trades_per_source_day"])
        <= float(gate["maximum_trades_per_source_day"]),
        "minimum_stress_profit_factor": float(economic["stress_profit_factor"] or 0.0)
        >= float(gate["minimum_stress_profit_factor"]),
        "minimum_average_stress_r": float(economic["average_stress_r"])
        >= float(gate["minimum_average_stress_r"]),
        "minimum_positive_exit_month_share": float(
            economic["positive_exit_month_share"]
        )
        >= float(gate["minimum_positive_exit_month_share"]),
        "maximum_closed_drawdown_r": float(economic["maximum_closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "minimum_direction_share": float(economic["minimum_direction_share"])
        >= float(gate["minimum_direction_share"]),
        "top_ten_winners_removed_net_positive": (
            not gate["require_top_ten_winners_removed_net_positive"]
            or float(economic["top_ten_winners_removed_net_r"]) > 0
        ),
    }
    if require_bootstrap:
        checks["bootstrap_mean_stress_r_p025_above_zero"] = (
            not gate["require_bootstrap_mean_stress_r_p025_above_zero"]
            or float(economic["bootstrap_mean_stress_r_p025"] or 0.0) > 0
        )
    return checks


def _policy_sort_key(row: Mapping[str, Any]) -> tuple[float, float, float]:
    economic = row["economic_metrics"]
    return (
        -float(economic["bootstrap_mean_stress_r_p025"] or -math.inf),
        -float(economic["stress_profit_factor"] or 0.0),
        -float(row["retention_fraction"]),
    )


def _score_segment(
    dataset: pd.DataFrame,
    model: HistGradientBoostingRegressor,
    cutoff: float,
    start: str,
    end: str,
    stage: str,
    gates: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    population = _segment(dataset, start, end)
    scored = population.copy()
    scored["model_score"] = model.predict(_matrix(scored, contract["features"]))
    predictive = _predictive_metrics(scored)
    selected = _select_daily(scored, cutoff, contract["selection"])
    selected["stage"] = stage
    economic = _economic_metrics(
        selected, _active_source_days(scored), contract["selection"]
    )
    checks = _segment_gates(predictive, economic, gates)
    return selected, {
        "stage": stage,
        "policy_id": "FROZEN_OOF_CUTOFF",
        "retention_fraction": None,
        "score_cutoff": cutoff,
        "population": len(scored),
        "predictive_metrics": predictive,
        "economic_metrics": economic,
        "gates": checks,
        "passes": all(checks.values()),
    }


def _model_payload(
    model: HistGradientBoostingRegressor,
    features: Sequence[str],
    selected_policy: Mapping[str, Any],
    contract_file: Path,
) -> dict[str, Any]:
    return {
        "model": model,
        "features": list(features),
        "selected_policy": selected_policy,
        "contract_sha256": _sha256_file(contract_file),
        "execution_authorized": False,
    }


def _write_evaluations(path: Path, evaluations: Sequence[Mapping[str, Any]]) -> None:
    rows = []
    for evaluation in evaluations:
        rows.append(
            {
                "stage": evaluation["stage"],
                "policy_id": evaluation["policy_id"],
                "retention_fraction": evaluation["retention_fraction"],
                "score_cutoff": evaluation["score_cutoff"],
                **{
                    f"predictive_{key}": value
                    for key, value in evaluation["predictive_metrics"].items()
                },
                **evaluation["economic_metrics"],
                "passes": evaluation["passes"],
                "failed_gates": "|".join(
                    key for key, value in evaluation["gates"].items() if not value
                ),
            }
        )
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _artifact_manifest(outputs: Mapping[str, Path]) -> dict[str, Any]:
    return {
        key: {
            "path": str(path),
            "sha256": _sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for key, path in outputs.items()
        if key not in {"report_json", "report_markdown"} and path.exists()
    }


def _render(payload: Mapping[str, Any]) -> str:
    predictive = payload["oof_predictive_metrics"]
    lines = [
        "# A3 ML A2 Intraday Context Ranker V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"Dataset: {payload['dataset_rows']} rows. Train: {payload['train_rows']}. Purged OOF: {payload['oof_rows']}.",
        f"OOF AUC: {float(predictive.get('auc') or 0):.4f}. OOF Spearman: {float(predictive.get('spearman') or 0):.4f}.",
        "",
    ]
    for evaluation in payload["evaluations"]:
        economic = evaluation["economic_metrics"]
        lines.append(
            f"- {evaluation['stage']} {evaluation['policy_id']}: {economic['trades']} trades, "
            f"{economic['trades_per_source_day']:.3f}/active day, stress PF "
            f"{float(economic['stress_profit_factor'] or 0):.3f}, average "
            f"{economic['average_stress_r']:.4f}R, pass `{evaluation['passes']}`."
        )
    lines.extend(
        [
            "",
            f"Chronological stages opened: `{payload['chronological_stages_opened']}`.",
            "",
            "This is contaminated research evidence. Python demo, EA consumption, broker action, and live capital remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CONTRACT = Path("config") / "ml" / "a3_ml_historical_backtest_training.json"
SCHEMA_VERSION = "a3_ml_historical_backtest_training_status_v1"
NUMERIC_FEATURES = (
    "spread_points",
    "log_atr",
    "body_fraction",
    "aligned_close_location",
    "aligned_three_bar_move_atr",
    "break_distance_atr",
    "estimated_cost_r",
    "recent_range_atr",
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
)
CATEGORICAL_FEATURES = ("strategy_family", "direction")


def train_historical_backtest_model(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_path = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = _read_json(contract_path)
    _validate_contract(contract)

    outputs = contract["outputs"]
    status_json = _resolve(root, outputs["status_json"])
    model_path = _resolve(root, outputs["model_json"])
    dataset_path = _resolve(root, outputs["dataset_csv"])
    model_card_path = _resolve(root, outputs["model_card_md"])

    rows: list[dict[str, Any]] = []
    source_audits: list[dict[str, Any]] = []
    for source in contract["sources"]:
        source_rows, source_audit = _load_source(root, source, contract)
        rows.extend(source_rows)
        source_audits.append(source_audit)

    train_rows = sorted((row for row in rows if row["split"] == "train"), key=lambda row: row["entry_time"])
    validation_rows = sorted(
        (row for row in rows if row["split"] == "validation"), key=lambda row: row["entry_time"]
    )
    numeric_features = list(NUMERIC_FEATURES)
    if contract.get("market_data"):
        from .market_feature_enrichment import MARKET_NUMERIC_FEATURES, enrich_rows_with_completed_market_features

        combined_rows = enrich_rows_with_completed_market_features(root, train_rows + validation_rows, contract["market_data"])
        train_rows = [row for row in combined_rows if row["split"] == "train"]
        validation_rows = [row for row in combined_rows if row["split"] == "validation"]
        numeric_features.extend(MARKET_NUMERIC_FEATURES)
    _validate_population(train_rows, validation_rows, contract)
    _write_dataset(dataset_path, train_rows + validation_rows, numeric_features)

    model_parameters, metrics, coefficients = _fit_and_evaluate(
        train_rows, validation_rows, contract, numeric_features
    )
    artifact = {
        "schema_version": "a3_ml_historical_backtest_model_v1",
        "status": "TRAINED_RESEARCH_ONLY",
        "created_at_utc": _utc_now(),
        "model_family": contract["model_family"],
        "symbol": contract["symbol"],
        "numeric_features": numeric_features,
        "categorical_features": list(CATEGORICAL_FEATURES),
        "decision_threshold": float(contract["decision_threshold"]),
        "training_period": {
            "first_entry": train_rows[0]["entry_time"],
            "last_entry": train_rows[-1]["entry_time"],
        },
        "validation_period": {
            "first_entry": validation_rows[0]["entry_time"],
            "last_entry": validation_rows[-1]["entry_time"],
        },
        "metrics": metrics,
        "largest_absolute_coefficients": coefficients,
        "model_parameters": model_parameters,
        "source_audits": source_audits,
        "boundary": _boundary(),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(model_path, artifact)
    model_sha256 = _sha256_file(model_path)
    dataset_sha256 = _sha256_file(dataset_path)
    artifact["artifacts"] = {
        "model_json": str(model_path),
        "model_sha256": model_sha256,
        "dataset_csv": str(dataset_path),
        "dataset_sha256": dataset_sha256,
    }

    source_families = sorted({str(source["strategy_family"]) for source in contract["sources"]})
    limitations = [
        "The model was trained from MT5 Strategy Tester outcomes, not live fills.",
        "The source strategies were researched on overlapping historical windows, so validation is out-of-time but not a pristine untouched strategy-development holdout.",
        f"The model is specific to these source families: {', '.join(source_families)}.",
        "Live slippage and execution readiness must remain separate from historical model-fit evidence.",
    ]
    if any(float(audit["history_quality_pct"]) <= 0.0 for audit in source_audits):
        limitations.append(
            "MT5 omitted the HTML history-quality percentage for at least one source; its tester journal and position-ID deal ledger exist, but quality remains unverified."
        )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "status": "TRAINED_RESEARCH_ONLY",
        "stage": "C60-HISTORICAL-BACKTEST-TRAINING",
        "created_at_utc": artifact["created_at_utc"],
        "model_family": contract["model_family"],
        "training_population": _population(train_rows),
        "validation_population": _population(validation_rows),
        "metrics": metrics,
        "source_audits": source_audits,
        "artifacts": artifact["artifacts"],
        "authorization": _boundary(),
        "limitations": limitations,
        "next_allowed_stage": "Review metrics and run shadow-only scoring. Do not publish to MT5 or authorize broker action.",
    }
    _write_json(status_json, payload)
    model_card_path.parent.mkdir(parents=True, exist_ok=True)
    model_card_path.write_text(_render_model_card(payload), encoding="utf-8")
    return status_json


def _validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_historical_backtest_training_v1":
        raise ValueError("unsupported historical training contract schema")
    if not contract.get("research_only"):
        raise ValueError("historical training contract must remain research_only")
    for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if contract.get(key) is not False:
            raise ValueError(f"historical training contract requires {key}=false")
    splits = Counter(str(source.get("split")) for source in contract.get("sources", []))
    if not splits["train"] or not splits["validation"]:
        raise ValueError("historical training contract requires train and validation sources")


def _load_source(
    root: Path, source: dict[str, Any], contract: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    split = str(source["split"])
    strategy_family = str(source["strategy_family"])
    summary_path = _resolve(root, source["summary_json"])
    summary = _read_json(summary_path)
    if str(summary.get("name")) != strategy_family:
        raise ValueError(f"strategy family mismatch in {summary_path}")
    quality = _history_quality(summary)
    if quality < float(contract["minimum_history_quality_pct"]):
        raise ValueError(f"history quality {quality}% is below contract minimum in {summary_path}")

    signal_path = _resolve_summary_output(summary_path, summary.get("signal_csv"))
    trade_path = _resolve_summary_output(summary_path, summary.get("trade_csv"))
    trades = _read_trades(trade_path)
    total_completed_trades = len(trades)
    trades = _filter_trades_to_source_window(trades, source)
    signal_by_key, duplicate_signal_keys = _read_matching_signals(signal_path, set(trades))

    rows = []
    unmatched = []
    for key, trade in trades.items():
        signal = signal_by_key.get(key)
        if signal is None:
            unmatched.append(key)
            continue
        rows.append(_training_row(split, strategy_family, trade, signal, summary_path))
    if unmatched:
        raise ValueError(f"{len(unmatched)} completed trades have no exact WOULD_SIGNAL row in {signal_path}")
    if duplicate_signal_keys:
        raise ValueError(f"duplicate WOULD_SIGNAL keys found in {signal_path}: {len(duplicate_signal_keys)}")

    audit = {
        "split": split,
        "strategy_family": strategy_family,
        "summary_json": str(summary_path),
        "summary_sha256": _sha256_file(summary_path),
        "signal_csv": str(signal_path),
        "signal_sha256": _sha256_file(signal_path),
        "trade_csv": str(trade_path),
        "trade_sha256": _sha256_file(trade_path),
        "history_quality_pct": quality,
        "completed_trades_in_file": total_completed_trades,
        "completed_trades": len(trades),
        "joined_rows": len(rows),
        "entry_start": source.get("entry_start", ""),
        "entry_end": source.get("entry_end", ""),
    }
    return rows, audit


def _filter_trades_to_source_window(
    trades: dict[tuple[str, str], dict[str, str]], source: dict[str, Any]
) -> dict[tuple[str, str], dict[str, str]]:
    start_raw = str(source.get("entry_start", "")).strip()
    end_raw = str(source.get("entry_end", "")).strip()
    if not start_raw and not end_raw:
        return trades
    start = _parse_iso(start_raw) if start_raw else datetime.min.replace(tzinfo=timezone.utc)
    end = _parse_iso(end_raw) if end_raw else datetime.max.replace(tzinfo=timezone.utc)
    return {
        key: row
        for key, row in trades.items()
        if start <= _parse_broker_time(row["entry_time"]) <= end
    }


def _read_trades(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    output: dict[tuple[str, str], dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            entry_time = str(row.get("entry_time", "")).strip()
            direction = str(row.get("direction", "")).strip().upper()
            profit = _float(row.get("profit_aed"))
            if not entry_time or direction not in {"LONG", "SHORT"} or profit == 0.0:
                continue
            key = (entry_time, direction)
            if key in output:
                raise ValueError(f"duplicate completed trade key in {path}: {key}")
            output[key] = row
    return output


def _read_matching_signals(
    path: Path, trade_keys: set[tuple[str, str]]
) -> tuple[dict[tuple[str, str], dict[str, str]], set[tuple[str, str]]]:
    output: dict[tuple[str, str], dict[str, str]] = {}
    duplicates: set[tuple[str, str]] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = handle.readline()
        delimiter = "\t" if "\t" in header else ","
        handle.seek(0)
        for row in csv.DictReader(handle, delimiter=delimiter):
            if str(row.get("stage", "")).strip().upper() != "WOULD_SIGNAL":
                continue
            key = (
                str(row.get("timestamp_broker", "")).strip(),
                str(row.get("direction", "")).strip().upper(),
            )
            if key not in trade_keys:
                continue
            if key in output:
                duplicates.add(key)
            output[key] = row
    return output, duplicates


def _training_row(
    split: str,
    strategy_family: str,
    trade: dict[str, str],
    signal: dict[str, str],
    summary_path: Path,
) -> dict[str, Any]:
    timestamp = _parse_broker_time(trade["entry_time"])
    direction = str(trade["direction"]).upper()
    direction_sign = 1.0 if direction == "LONG" else -1.0
    atr = max(_float(signal.get("atr")), 1e-9)
    close_location = _float(signal.get("close_location"))
    recent_range = max(_float(signal.get("recent_high")) - _float(signal.get("recent_low")), 0.0)
    return {
        "split": split,
        "strategy_family": strategy_family,
        "direction": direction,
        "entry_time": _format_utc(timestamp),
        "source_summary": str(summary_path),
        "profit_aed": _float(trade.get("profit_aed")),
        "y_win": int(_float(trade.get("profit_aed")) > 0.0),
        "spread_points": _float(signal.get("spread_points")),
        "log_atr": math.log1p(atr),
        "body_fraction": _float(signal.get("body_fraction")),
        "aligned_close_location": close_location if direction == "LONG" else 1.0 - close_location,
        "aligned_three_bar_move_atr": direction_sign * _float(signal.get("three_bar_move_atr")),
        "break_distance_atr": _float(signal.get("break_distance_atr")),
        "estimated_cost_r": _float(signal.get("estimated_cost_r")),
        "recent_range_atr": recent_range / atr,
        "hour_sin": math.sin(2.0 * math.pi * timestamp.hour / 24.0),
        "hour_cos": math.cos(2.0 * math.pi * timestamp.hour / 24.0),
        "weekday_sin": math.sin(2.0 * math.pi * timestamp.weekday() / 7.0),
        "weekday_cos": math.cos(2.0 * math.pi * timestamp.weekday() / 7.0),
    }


def _validate_population(
    train_rows: list[dict[str, Any]], validation_rows: list[dict[str, Any]], contract: dict[str, Any]
) -> None:
    if len(train_rows) < int(contract["minimum_train_rows"]):
        raise ValueError(f"train rows {len(train_rows)} below contract minimum")
    if len(validation_rows) < int(contract["minimum_validation_rows"]):
        raise ValueError(f"validation rows {len(validation_rows)} below contract minimum")
    for name, rows in (("train", train_rows), ("validation", validation_rows)):
        if len({row["y_win"] for row in rows}) < 2:
            raise ValueError(f"{name} split must contain winning and losing trades")
        if {row["direction"] for row in rows} != {"LONG", "SHORT"}:
            raise ValueError(f"{name} split must contain LONG and SHORT trades")
    train_end = _parse_iso(contract["train_end"])
    validation_start = _parse_iso(contract["validation_start"])
    if max(_parse_iso(row["entry_time"]) for row in train_rows) > train_end:
        raise ValueError("train split contains rows after train_end")
    if min(_parse_iso(row["entry_time"]) for row in validation_rows) < validation_start:
        raise ValueError("validation split contains rows before validation_start")
    if max(_parse_iso(row["entry_time"]) for row in train_rows) >= min(
        _parse_iso(row["entry_time"]) for row in validation_rows
    ):
        raise ValueError("train and validation periods overlap")


def _fit_and_evaluate(
    train_rows: list[dict[str, Any]],
    validation_rows: list[dict[str, Any]],
    contract: dict[str, Any],
    numeric_features: list[str],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    if contract.get("model_family") == "PURE_NUMPY_GRADIENT_BOOSTED_TREES_V1":
        return _fit_gradient_boosted_trees(
            train_rows, validation_rows, contract, numeric_features
        )
    import numpy as np

    category_levels = {
        feature: sorted({str(row[feature]) for row in train_rows}) for feature in CATEGORICAL_FEATURES
    }
    means = np.array(
        [sum(float(row[feature]) for row in train_rows) / len(train_rows) for feature in numeric_features],
        dtype=float,
    )
    raw_numeric = np.array([[float(row[feature]) for feature in numeric_features] for row in train_rows])
    scales = raw_numeric.std(axis=0)
    scales[scales < 1e-12] = 1.0
    feature_names = list(numeric_features)
    for feature in CATEGORICAL_FEATURES:
        feature_names.extend(f"{feature}={level}" for level in category_levels[feature])

    def matrix(rows: list[dict[str, Any]]) -> Any:
        numeric = np.array([[float(row[feature]) for feature in numeric_features] for row in rows])
        parts = [(numeric - means) / scales]
        for feature in CATEGORICAL_FEATURES:
            levels = category_levels[feature]
            parts.append(np.array([[1.0 if str(row[feature]) == level else 0.0 for level in levels] for row in rows]))
        return np.column_stack(parts)

    x_train = matrix(train_rows)
    y_train = np.array([int(row["y_win"]) for row in train_rows], dtype=float)
    x_validation = matrix(validation_rows)
    y_validation = np.array([int(row["y_win"]) for row in validation_rows], dtype=float)
    coefficients = np.zeros(x_train.shape[1], dtype=float)
    intercept = 0.0
    first_moment = np.zeros_like(coefficients)
    second_moment = np.zeros_like(coefficients)
    first_intercept = 0.0
    second_intercept = 0.0
    # Preserve probability calibration: the target is p(win), so class reweighting is intentionally disabled.
    sample_weights = np.ones_like(y_train)
    learning_rate = 0.025
    l2 = 0.01
    beta1 = 0.9
    beta2 = 0.999
    epsilon = 1e-8
    iterations = 4000
    for step in range(1, iterations + 1):
        probabilities = _sigmoid_numpy(x_train @ coefficients + intercept, np)
        residual = (probabilities - y_train) * sample_weights
        gradient = x_train.T @ residual / len(y_train) + l2 * coefficients
        intercept_gradient = float(residual.mean())
        first_moment = beta1 * first_moment + (1.0 - beta1) * gradient
        second_moment = beta2 * second_moment + (1.0 - beta2) * gradient * gradient
        first_intercept = beta1 * first_intercept + (1.0 - beta1) * intercept_gradient
        second_intercept = beta2 * second_intercept + (1.0 - beta2) * intercept_gradient * intercept_gradient
        coefficients -= learning_rate * (first_moment / (1.0 - beta1**step)) / (
            np.sqrt(second_moment / (1.0 - beta2**step)) + epsilon
        )
        intercept -= learning_rate * (first_intercept / (1.0 - beta1**step)) / (
            math.sqrt(second_intercept / (1.0 - beta2**step)) + epsilon
        )

    threshold = float(contract["decision_threshold"])
    train_probabilities = _sigmoid_numpy(x_train @ coefficients + intercept, np)
    validation_probabilities = _sigmoid_numpy(x_validation @ coefficients + intercept, np)
    train_metrics = _binary_metrics(y_train, train_probabilities, threshold, np)
    validation_metrics = _binary_metrics(y_validation, validation_probabilities, threshold, np)
    baseline_probability = float(y_train.mean())
    baseline = np.full(len(y_validation), baseline_probability)
    validation_metrics["baseline_brier_score"] = round(float(np.mean((baseline - y_validation) ** 2)), 6)
    validation_metrics["baseline_log_loss"] = round(_binary_log_loss(y_validation, baseline, np), 6)
    validation_metrics["baseline_probability_from_train"] = round(baseline_probability, 6)
    subgroup_metrics: dict[str, dict[str, Any]] = {}
    for field in ("strategy_family", "direction"):
        subgroup_metrics[field] = {}
        for value in sorted({str(row[field]) for row in validation_rows}):
            mask = np.array([str(row[field]) == value for row in validation_rows])
            subgroup_metrics[field][value] = _binary_metrics(
                y_validation[mask], validation_probabilities[mask], threshold, np
            )
    metrics = {
        "train": train_metrics,
        "out_of_time_validation": validation_metrics,
        "out_of_time_validation_subgroups": subgroup_metrics,
    }
    ranked_coefficients = sorted(
        (
            {"feature": name, "coefficient": round(float(value), 8)}
            for name, value in zip(feature_names, coefficients)
        ),
        key=lambda item: abs(item["coefficient"]),
        reverse=True,
    )[:15]
    model_parameters = {
        "intercept": round(float(intercept), 12),
        "coefficients": [round(float(value), 12) for value in coefficients],
        "feature_names": feature_names,
        "numeric_means": [round(float(value), 12) for value in means],
        "numeric_scales": [round(float(value), 12) for value in scales],
        "category_levels": category_levels,
        "optimizer": {
            "name": "adam",
            "iterations": iterations,
            "learning_rate": learning_rate,
            "l2": l2,
            "class_weighting": "none_probability_calibration",
        },
    }
    return model_parameters, metrics, ranked_coefficients


def _fit_gradient_boosted_trees(
    train_rows: list[dict[str, Any]],
    validation_rows: list[dict[str, Any]],
    contract: dict[str, Any],
    numeric_features: list[str],
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    import numpy as np

    category_levels = {
        feature: sorted({str(row[feature]) for row in train_rows}) for feature in CATEGORICAL_FEATURES
    }
    raw_numeric = np.array([[float(row[feature]) for feature in numeric_features] for row in train_rows])
    means = raw_numeric.mean(axis=0)
    scales = raw_numeric.std(axis=0)
    scales[scales < 1e-12] = 1.0
    feature_names = list(numeric_features)
    for feature in CATEGORICAL_FEATURES:
        feature_names.extend(f"{feature}={level}" for level in category_levels[feature])

    def matrix(rows: list[dict[str, Any]]) -> Any:
        numeric = np.array([[float(row[feature]) for feature in numeric_features] for row in rows])
        parts = [(numeric - means) / scales]
        for feature in CATEGORICAL_FEATURES:
            levels = category_levels[feature]
            parts.append(np.array([[1.0 if str(row[feature]) == level else 0.0 for level in levels] for row in rows]))
        return np.column_stack(parts)

    x_train = matrix(train_rows)
    y_train = np.array([int(row["y_win"]) for row in train_rows], dtype=float)
    x_validation = matrix(validation_rows)
    y_validation = np.array([int(row["y_win"]) for row in validation_rows], dtype=float)
    inner_design_mask = np.array([_parse_iso(row["entry_time"]).year <= 2019 for row in train_rows])
    inner_validation_mask = ~inner_design_mask
    if inner_design_mask.sum() < 200 or inner_validation_mask.sum() < 80:
        raise ValueError("GBT inner time split requires at least 200 design and 80 early-stop rows")

    learning_rate = 0.05
    max_rounds = 200
    min_leaf = 25
    max_depth = 2
    l2 = 1.0
    design_prior = float(y_train[inner_design_mask].mean())
    design_intercept = math.log(max(design_prior, 1e-6) / max(1.0 - design_prior, 1e-6))
    design_scores = np.full(int(inner_design_mask.sum()), design_intercept)
    inner_scores = np.full(int(inner_validation_mask.sum()), design_intercept)
    design_trees: list[dict[str, Any]] = []
    best_rounds = 1
    best_inner_loss = float("inf")
    stale_rounds = 0
    for round_index in range(1, max_rounds + 1):
        probabilities = _sigmoid_numpy(design_scores, np)
        gradients = y_train[inner_design_mask] - probabilities
        hessians = probabilities * (1.0 - probabilities)
        tree = _fit_newton_tree(
            x_train[inner_design_mask], gradients, hessians, max_depth, min_leaf, l2, np
        )
        design_trees.append(tree)
        design_scores += learning_rate * _predict_tree(tree, x_train[inner_design_mask], np)
        inner_scores += learning_rate * _predict_tree(tree, x_train[inner_validation_mask], np)
        inner_loss = _binary_log_loss(
            y_train[inner_validation_mask], _sigmoid_numpy(inner_scores, np), np
        )
        if inner_loss < best_inner_loss - 1e-5:
            best_inner_loss = inner_loss
            best_rounds = round_index
            stale_rounds = 0
        else:
            stale_rounds += 1
        if round_index >= 30 and stale_rounds >= 25:
            break

    full_prior = float(y_train.mean())
    intercept = math.log(max(full_prior, 1e-6) / max(1.0 - full_prior, 1e-6))
    full_scores = np.full(len(y_train), intercept)
    trees: list[dict[str, Any]] = []
    for _ in range(best_rounds):
        probabilities = _sigmoid_numpy(full_scores, np)
        gradients = y_train - probabilities
        hessians = probabilities * (1.0 - probabilities)
        tree = _fit_newton_tree(x_train, gradients, hessians, max_depth, min_leaf, l2, np)
        trees.append(tree)
        full_scores += learning_rate * _predict_tree(tree, x_train, np)

    validation_scores = np.full(len(y_validation), intercept)
    for tree in trees:
        validation_scores += learning_rate * _predict_tree(tree, x_validation, np)
    train_probabilities = _sigmoid_numpy(full_scores, np)
    validation_probabilities = _sigmoid_numpy(validation_scores, np)
    threshold = float(contract["decision_threshold"])
    train_metrics = _binary_metrics(y_train, train_probabilities, threshold, np)
    validation_metrics = _binary_metrics(y_validation, validation_probabilities, threshold, np)
    baseline = np.full(len(y_validation), full_prior)
    validation_metrics["baseline_brier_score"] = round(float(np.mean((baseline - y_validation) ** 2)), 6)
    validation_metrics["baseline_log_loss"] = round(_binary_log_loss(y_validation, baseline, np), 6)
    validation_metrics["baseline_probability_from_train"] = round(full_prior, 6)
    subgroup_metrics: dict[str, dict[str, Any]] = {}
    for field in ("strategy_family", "direction"):
        subgroup_metrics[field] = {}
        for value in sorted({str(row[field]) for row in validation_rows}):
            mask = np.array([str(row[field]) == value for row in validation_rows])
            subgroup_metrics[field][value] = _binary_metrics(
                y_validation[mask], validation_probabilities[mask], threshold, np
            )
    importance = [0.0] * len(feature_names)
    for tree in trees:
        _accumulate_tree_importance(tree, importance)
    ranked = sorted(
        (
            {"feature": name, "coefficient": round(float(value), 8)}
            for name, value in zip(feature_names, importance)
        ),
        key=lambda item: item["coefficient"],
        reverse=True,
    )[:15]
    model_parameters = {
        "intercept": round(intercept, 12),
        "trees": trees,
        "feature_names": feature_names,
        "numeric_means": [round(float(value), 12) for value in means],
        "numeric_scales": [round(float(value), 12) for value in scales],
        "category_levels": category_levels,
        "optimizer": {
            "name": "newton_gradient_boosted_trees",
            "learning_rate": learning_rate,
            "rounds_selected_inside_2016_2021": best_rounds,
            "inner_validation_log_loss": round(best_inner_loss, 8),
            "max_depth": max_depth,
            "min_leaf": min_leaf,
            "l2": l2,
            "inner_design_end": "2019-12-31",
            "inner_early_stop_period": "2020-01-01 through 2021-12-31",
        },
    }
    metrics = {
        "train": train_metrics,
        "out_of_time_validation": validation_metrics,
        "out_of_time_validation_subgroups": subgroup_metrics,
    }
    return model_parameters, metrics, ranked


def _fit_newton_tree(
    x: Any,
    gradients: Any,
    hessians: Any,
    max_depth: int,
    min_leaf: int,
    l2: float,
    np: Any,
) -> dict[str, Any]:
    def build(indices: Any, depth: int) -> dict[str, Any]:
        gradient_sum = float(gradients[indices].sum())
        hessian_sum = float(hessians[indices].sum())
        leaf_value = gradient_sum / (hessian_sum + l2)
        if depth >= max_depth or len(indices) < 2 * min_leaf:
            return {"value": round(leaf_value, 12)}
        parent_score = gradient_sum * gradient_sum / (hessian_sum + l2)
        best: tuple[float, int, float, Any, Any] | None = None
        for feature_index in range(x.shape[1]):
            values = x[indices, feature_index]
            for threshold in np.unique(np.quantile(values, [0.1, 0.25, 0.5, 0.75, 0.9])):
                left_mask = values <= threshold
                left = indices[left_mask]
                right = indices[~left_mask]
                if len(left) < min_leaf or len(right) < min_leaf:
                    continue
                left_g = float(gradients[left].sum())
                left_h = float(hessians[left].sum())
                right_g = gradient_sum - left_g
                right_h = hessian_sum - left_h
                gain = left_g * left_g / (left_h + l2) + right_g * right_g / (right_h + l2) - parent_score
                if best is None or gain > best[0]:
                    best = (gain, feature_index, float(threshold), left, right)
        if best is None or best[0] <= 1e-10:
            return {"value": round(leaf_value, 12)}
        gain, feature_index, threshold, left, right = best
        return {
            "feature": feature_index,
            "threshold": round(threshold, 12),
            "gain": round(gain, 12),
            "left": build(left, depth + 1),
            "right": build(right, depth + 1),
        }

    return build(np.arange(len(x)), 0)


def _predict_tree(tree: dict[str, Any], x: Any, np: Any) -> Any:
    output = np.empty(len(x), dtype=float)

    def assign(node: dict[str, Any], indices: Any) -> None:
        if "value" in node:
            output[indices] = float(node["value"])
            return
        feature = int(node["feature"])
        threshold = float(node["threshold"])
        mask = x[indices, feature] <= threshold
        assign(node["left"], indices[mask])
        assign(node["right"], indices[~mask])

    assign(tree, np.arange(len(x)))
    return output


def _accumulate_tree_importance(tree: dict[str, Any], importance: list[float]) -> None:
    if "value" in tree:
        return
    importance[int(tree["feature"])] += float(tree.get("gain", 0.0))
    _accumulate_tree_importance(tree["left"], importance)
    _accumulate_tree_importance(tree["right"], importance)


def _sigmoid_numpy(values: Any, np: Any) -> Any:
    return 1.0 / (1.0 + np.exp(-np.clip(values, -35.0, 35.0)))


def _binary_metrics(y_true: Any, probabilities: Any, threshold: float, np: Any) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(int)
    selected = probabilities >= threshold
    positive = y_true == 1
    negative = ~positive
    true_positive_rate = float((predictions[positive] == 1).mean())
    true_negative_rate = float((predictions[negative] == 0).mean())
    selected_win_rate = float(y_true[selected].mean()) if selected.any() else None
    positive_rate = float(y_true.mean())
    return {
        "rows": int(len(y_true)),
        "positive_rate": round(positive_rate, 6),
        "roc_auc": round(_roc_auc(y_true, probabilities), 6),
        "accuracy": round(float((predictions == y_true).mean()), 6),
        "balanced_accuracy": round((true_positive_rate + true_negative_rate) / 2.0, 6),
        "brier_score": round(float(np.mean((probabilities - y_true) ** 2)), 6),
        "log_loss": round(_binary_log_loss(y_true, probabilities, np), 6),
        "threshold": threshold,
        "selected_rows": int(selected.sum()),
        "selected_coverage": round(float(selected.mean()), 6),
        "selected_win_rate": round(selected_win_rate, 6) if selected_win_rate is not None else None,
        "selected_win_rate_lift": (
            round(selected_win_rate - positive_rate, 6) if selected_win_rate is not None else None
        ),
    }


def _binary_log_loss(y_true: Any, probabilities: Any, np: Any) -> float:
    clipped = np.clip(probabilities, 1e-12, 1.0 - 1e-12)
    return float(-np.mean(y_true * np.log(clipped) + (1.0 - y_true) * np.log(1.0 - clipped)))


def _roc_auc(y_true: Any, probabilities: Any) -> float:
    positives = [float(score) for label, score in zip(y_true, probabilities) if int(label) == 1]
    negatives = [float(score) for label, score in zip(y_true, probabilities) if int(label) == 0]
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            wins += 1.0 if positive > negative else 0.5 if positive == negative else 0.0
    return wins / (len(positives) * len(negatives))


def _write_dataset(path: Path, rows: list[dict[str, Any]], numeric_features: list[str]) -> None:
    fields = [
        "split",
        "strategy_family",
        "direction",
        "entry_time",
        "source_summary",
        "profit_aed",
        "y_win",
        *numeric_features,
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _population(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(row["y_win"] for row in rows)
    return {
        "rows": len(rows),
        "wins": labels[1],
        "losses": labels[0],
        "win_rate": round(labels[1] / len(rows), 6),
        "directions": dict(sorted(Counter(row["direction"] for row in rows).items())),
        "strategy_families": dict(sorted(Counter(row["strategy_family"] for row in rows).items())),
    }


def _boundary() -> dict[str, bool]:
    return {
        "research_only": True,
        "official_c05_model": False,
        "python_demo_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }


def _render_model_card(payload: dict[str, Any]) -> str:
    train = payload["training_population"]
    validation = payload["validation_population"]
    metrics = payload["metrics"]["out_of_time_validation"]
    limitations = "\n".join(f"- {item}" for item in payload["limitations"])
    return "\n".join(
        [
            "# A3 ML Historical Backtest Model Card",
            "",
            f"Status: {payload['status']}",
            "",
            "## Population",
            "",
            f"- Training: {train['rows']} trades ({train['wins']} wins, {train['losses']} losses).",
            f"- Out-of-time validation: {validation['rows']} trades ({validation['wins']} wins, {validation['losses']} losses).",
            "",
            "## Validation",
            "",
            f"- ROC AUC: {metrics['roc_auc']}",
            f"- Brier score: {metrics['brier_score']} (baseline {metrics['baseline_brier_score']})",
            f"- Log loss: {metrics['log_loss']} (baseline {metrics['baseline_log_loss']})",
            f"- Threshold coverage: {metrics['selected_coverage']}",
            f"- Threshold-selected win rate: {metrics['selected_win_rate']}",
            "",
            "## Limitations",
            "",
            limitations,
            "",
            "## Boundary",
            "",
            "Research only. Python demo predictions, EA consumption, and broker action remain unauthorized.",
            "",
        ]
    )


def _resolve(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _resolve_summary_output(summary_path: Path, value: Any) -> Path:
    if not value:
        raise ValueError(f"summary output path missing in {summary_path}")
    path = Path(str(value))
    if path.exists():
        return path.resolve()
    fallback = summary_path.parent / path.name
    if fallback.exists():
        return fallback.resolve()
    raise FileNotFoundError(path)


def _history_quality(summary: dict[str, Any]) -> float:
    value = str(summary.get("mt5_report_metrics", {}).get("History Quality", "0")).replace("%", "")
    return float(value or 0.0)


def _float(value: Any) -> float:
    try:
        parsed = float(str(value or "0").replace(" ", ""))
    except ValueError as exc:
        raise ValueError(f"invalid numeric value: {value!r}") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite numeric value: {value!r}")
    return parsed


def _parse_broker_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y.%m.%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_now() -> str:
    return _format_utc(datetime.now(timezone.utc))


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_label_ranker.json")


class RankerError(RuntimeError):
    pass


def run_dukascopy_label_ranker(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)

    labels_path = (root / contract["input_labels_csv"]).resolve()
    factory_report_path = (root / contract["input_factory_report_json"]).resolve()
    factory_report = json.loads(factory_report_path.read_text(encoding="utf-8"))
    _validate_upstream(contract, labels_path, factory_report_path, factory_report)
    rows = _read_resolved_rows(labels_path)
    split_rows = {name: [row for row in rows if row["split"] == name] for name in ("train", "validation", "test")}
    _validate_population(split_rows, factory_report)

    feature_names = list(contract["features"])
    matrices = {name: _feature_matrix(values, feature_names) for name, values in split_rows.items()}
    y_train = np.array([int(row[contract["target"]]) for row in split_rows["train"]], dtype=float)
    model = _fit_logistic(matrices["train"], y_train, feature_names, contract["model"])
    probabilities = {
        name: _score(model, matrix) for name, matrix in matrices.items()
    }

    validation_selected, cutoff = _select_validation(
        split_rows["validation"],
        probabilities["validation"],
        float(contract["selection"]["validation_top_fraction"]),
    )
    test_selected = {
        row["candidate_id"]
        for row, probability in zip(split_rows["test"], probabilities["test"])
        if float(probability) >= cutoff
    }
    selected_rows = {
        "validation": [row for row in split_rows["validation"] if row["candidate_id"] in validation_selected],
        "test": [row for row in split_rows["test"] if row["candidate_id"] in test_selected],
    }

    train_prior = float(y_train.mean())
    model_metrics = {
        name: _classification_metrics(
            [int(row[contract["target"]]) for row in split_rows[name]],
            probabilities[name],
            train_prior,
        )
        for name in ("train", "validation", "test")
    }
    selected_metrics = {
        name: _selected_stats(selected_rows[name]) for name in ("validation", "test")
    }
    selected_metrics["validation"]["coverage"] = len(selected_rows["validation"]) / len(split_rows["validation"])
    selected_metrics["test"]["coverage"] = len(selected_rows["test"]) / len(split_rows["test"])
    bootstrap = _calendar_month_bootstrap(
        selected_rows["test"],
        samples=int(contract["bootstrap"]["calendar_month_samples"]),
        seed=int(contract["bootstrap"]["seed"]),
    )
    gates = _evaluate_gates(
        contract["acceptance_gates"],
        model_metrics,
        selected_metrics,
        bootstrap,
    )
    classification = (
        "DUKASCOPY_LABEL_RANKER_RESEARCH_SURVIVOR"
        if all(gates.values())
        else "DUKASCOPY_LABEL_RANKER_NO_SURVIVOR"
    )

    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    outputs["model_json"].parent.mkdir(parents=True, exist_ok=True)
    model_payload = {
        "schema_version": "a3_ml_dukascopy_label_ranker_model_v1",
        "model": model,
        "selection_probability_cutoff": cutoff,
        "train_prior": train_prior,
        "features": feature_names,
        "authorization": contract["authorization"],
    }
    outputs["model_json"].write_text(json.dumps(model_payload, indent=2), encoding="utf-8")
    predictions = _prediction_rows(split_rows, probabilities, validation_selected, test_selected)
    _write_rows(outputs["predictions_csv"], predictions)

    payload = {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "input_labels_csv": str(labels_path),
        "input_labels_sha256": _sha256_file(labels_path),
        "input_factory_report_json": str(factory_report_path),
        "input_factory_source_composite_sha256": factory_report["source_composite_sha256"],
        "population": {name: len(values) for name, values in split_rows.items()},
        "model_metrics": model_metrics,
        "selection": {
            "validation_top_fraction": float(contract["selection"]["validation_top_fraction"]),
            "validation_probability_cutoff": cutoff,
            "validation_selected_rows": len(selected_rows["validation"]),
            "test_selected_rows": len(selected_rows["test"]),
        },
        "selected_metrics": selected_metrics,
        "test_calendar_month_bootstrap": bootstrap,
        "gates": gates,
        "model": model,
        "artifacts": {
            "model_json": str(outputs["model_json"]),
            "model_sha256": _sha256_file(outputs["model_json"]),
            "predictions_csv": str(outputs["predictions_csv"]),
            "predictions_sha256": _sha256_file(outputs["predictions_csv"]),
        },
        "authorization": {
            **contract["authorization"],
            "candidate_family_promotion_authorized": False,
            "ranker_execution_authorized": False,
        },
        "limitations": [
            "The underlying candidate family is independently unprofitable before ranking.",
            "The raw-family aggregate test result was known before this ranker was fitted.",
            "Selected candidates overlap and are not a shared-account portfolio equity curve.",
            "A research survivor would still require independent-family, portfolio, shadow, and demo validation.",
        ],
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _read_resolved_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("status") == "RESOLVED"]
    rows.sort(key=lambda row: (row["decision_time_utc"], row["candidate_id"]))
    return rows


def _feature_matrix(rows: Sequence[Mapping[str, str]], feature_names: Sequence[str]) -> np.ndarray:
    matrix = np.array([[_feature_value(row, name) for name in feature_names] for row in rows], dtype=float)
    if not np.isfinite(matrix).all():
        raise RankerError("feature matrix contains a non-finite value")
    return matrix


def _feature_value(row: Mapping[str, str], name: str) -> float:
    direction_sign = 1.0 if row["direction"] == "LONG" else -1.0
    atr = float(row["atr"])
    stop_distance = float(row["stop_distance"])
    signal_close = float(row["signal_close"])
    if atr <= 0.0 or stop_distance <= 0.0 or signal_close <= 0.0:
        raise RankerError("non-positive causal feature denominator")
    values = {
        "direction_long": float(row["direction"] == "LONG"),
        "trend_strength_atr": direction_sign * float(row["ema_fast_slope_atr"]),
        "ema_gap_atr": abs(float(row["ema_fast"]) - float(row["ema_slow"])) / atr,
        "close_fast_distance_atr": abs(signal_close - float(row["ema_fast"])) / atr,
        "body_fraction": float(row["body_fraction"]),
        "directional_close_location": float(row["close_location"]) if direction_sign > 0 else 1.0 - float(row["close_location"]),
        "touch_distance_atr": float(row["touch_distance_atr"]),
        "stop_distance_atr": float(row["stop_distance_atr"]),
        "log1p_signal_tick_count": math.log1p(float(row["signal_tick_count"])),
        "atr_fraction_of_price": atr / signal_close,
        "entry_spread_r": float(row["entry_spread"]) / stop_distance,
    }
    decision = _parse_utc(row["decision_time_utc"])
    values.update(
        {
            "decision_hour_sin": math.sin(2.0 * math.pi * decision.hour / 24.0),
            "decision_hour_cos": math.cos(2.0 * math.pi * decision.hour / 24.0),
            "decision_weekday_sin": math.sin(2.0 * math.pi * decision.weekday() / 7.0),
            "decision_weekday_cos": math.cos(2.0 * math.pi * decision.weekday() / 7.0),
        }
    )
    if name not in values:
        raise RankerError(f"unknown or forbidden ranker feature: {name}")
    return float(values[name])


def _fit_logistic(
    x_train: np.ndarray,
    y_train: np.ndarray,
    feature_names: Sequence[str],
    model_config: Mapping[str, Any],
) -> dict[str, Any]:
    means = x_train.mean(axis=0)
    scales = x_train.std(axis=0)
    scales[scales < 1e-12] = 1.0
    x = (x_train - means) / scales
    coefficients = np.zeros(x.shape[1], dtype=float)
    prior = float(y_train.mean())
    intercept = math.log(max(prior, 1e-9) / max(1.0 - prior, 1e-9))
    first = np.zeros_like(coefficients)
    second = np.zeros_like(coefficients)
    first_intercept = 0.0
    second_intercept = 0.0
    beta1, beta2, epsilon = 0.9, 0.999, 1e-8
    learning_rate = float(model_config["learning_rate"])
    l2 = float(model_config["l2"])
    iterations = int(model_config["iterations"])
    for step in range(1, iterations + 1):
        probability = _sigmoid(x @ coefficients + intercept)
        residual = probability - y_train
        gradient = x.T @ residual / len(y_train) + l2 * coefficients
        intercept_gradient = float(residual.mean())
        first = beta1 * first + (1.0 - beta1) * gradient
        second = beta2 * second + (1.0 - beta2) * gradient * gradient
        first_intercept = beta1 * first_intercept + (1.0 - beta1) * intercept_gradient
        second_intercept = beta2 * second_intercept + (1.0 - beta2) * intercept_gradient**2
        coefficients -= learning_rate * (first / (1.0 - beta1**step)) / (
            np.sqrt(second / (1.0 - beta2**step)) + epsilon
        )
        intercept -= learning_rate * (first_intercept / (1.0 - beta1**step)) / (
            math.sqrt(second_intercept / (1.0 - beta2**step)) + epsilon
        )
    return {
        "family": str(model_config["family"]),
        "feature_names": list(feature_names),
        "means": means.tolist(),
        "scales": scales.tolist(),
        "coefficients": coefficients.tolist(),
        "intercept": intercept,
        "iterations": iterations,
        "learning_rate": learning_rate,
        "l2": l2,
    }


def _score(model: Mapping[str, Any], matrix: np.ndarray) -> np.ndarray:
    standardized = (matrix - np.array(model["means"])) / np.array(model["scales"])
    return _sigmoid(standardized @ np.array(model["coefficients"]) + float(model["intercept"]))


def _sigmoid(values: np.ndarray) -> np.ndarray:
    clipped = np.clip(values, -35.0, 35.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def _select_validation(
    rows: Sequence[Mapping[str, str]], probabilities: Sequence[float], fraction: float
) -> tuple[set[str], float]:
    count = math.ceil(len(rows) * fraction)
    ranked = sorted(
        zip(rows, probabilities),
        key=lambda item: (-float(item[1]), item[0]["candidate_id"]),
    )
    selected = ranked[:count]
    return {row["candidate_id"] for row, _ in selected}, float(selected[-1][1])


def _classification_metrics(
    labels: Sequence[int], probabilities: Sequence[float], train_prior: float
) -> dict[str, float]:
    y = np.array(labels, dtype=float)
    p = np.clip(np.array(probabilities, dtype=float), 1e-12, 1.0 - 1e-12)
    return {
        "rows": len(labels),
        "roc_auc": _roc_auc(labels, probabilities),
        "brier_score": float(np.mean((p - y) ** 2)),
        "train_prior_brier_score": float(np.mean((train_prior - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))),
    }


def _roc_auc(labels: Sequence[int], probabilities: Sequence[float]) -> float:
    pairs = sorted(zip(probabilities, labels), key=lambda item: float(item[0]))
    positives = sum(int(label) for _, label in pairs)
    negatives = len(pairs) - positives
    if positives == 0 or negatives == 0:
        raise RankerError("ROC AUC requires both labels")
    rank_sum = 0.0
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and float(pairs[end][0]) == float(pairs[index][0]):
            end += 1
        average_rank = ((index + 1) + end) / 2.0
        rank_sum += average_rank * sum(int(label) for _, label in pairs[index:end])
        index = end
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def _selected_stats(rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row["exit_time_utc"], row["candidate_id"]))
    pnl = [float(row["stress_net_pnl_usd"]) for row in ordered]
    returns = [float(row["stress_net_r"]) for row in ordered]
    gross_profit = sum(value for value in pnl if value > 0.0)
    gross_loss = -sum(value for value in pnl if value < 0.0)
    by_direction = defaultdict(int)
    by_month = defaultdict(float)
    for row in ordered:
        by_direction[row["direction"]] += 1
        by_month[row["exit_time_utc"][:7]] += float(row["stress_net_pnl_usd"])
    positive_months = sum(value > 0.0 for value in by_month.values())
    return {
        "trades": len(ordered),
        "wins": sum(value > 0.0 for value in pnl),
        "win_rate_pct": 100.0 * sum(value > 0.0 for value in pnl) / len(pnl) if pnl else 0.0,
        "stress_net_usd": sum(pnl),
        "stress_profit_factor": gross_profit / gross_loss if gross_loss > 0.0 else None,
        "average_stress_r": sum(returns) / len(returns) if returns else 0.0,
        "max_closed_drawdown_r": _max_drawdown(returns),
        "direction_counts": dict(by_direction),
        "active_exit_months": len(by_month),
        "positive_exit_months": positive_months,
        "positive_exit_month_share": positive_months / len(by_month) if by_month else 0.0,
    }


def _calendar_month_bootstrap(
    rows: Sequence[Mapping[str, str]], *, samples: int, seed: int
) -> dict[str, Any]:
    by_month: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_month[row["exit_time_utc"][:7]].append(float(row["stress_net_r"]))
    months = sorted(by_month)
    if len(months) < 6:
        raise RankerError("test bootstrap requires at least six active exit months")
    rng = random.Random(seed)
    estimates = []
    for _ in range(samples):
        sampled = [rng.choice(months) for _ in months]
        values = [value for month in sampled for value in by_month[month]]
        estimates.append(sum(values) / len(values))
    estimates.sort()
    return {
        "samples": samples,
        "seed": seed,
        "active_exit_months": len(months),
        "average_stress_r_p025": _percentile(estimates, 0.025),
        "average_stress_r_p50": _percentile(estimates, 0.5),
        "average_stress_r_p975": _percentile(estimates, 0.975),
    }


def _evaluate_gates(
    configured: Mapping[str, Any],
    model_metrics: Mapping[str, Mapping[str, float]],
    selected: Mapping[str, Mapping[str, Any]],
    bootstrap: Mapping[str, Any],
) -> dict[str, bool]:
    validation, test = selected["validation"], selected["test"]
    test_directions = test["direction_counts"]
    return {
        "validation_auc_ge_minimum": model_metrics["validation"]["roc_auc"] >= float(configured["minimum_validation_auc"]),
        "test_auc_ge_minimum": model_metrics["test"]["roc_auc"] >= float(configured["minimum_test_auc"]),
        "validation_selected_rows_ge_minimum": validation["trades"] >= int(configured["minimum_validation_selected_rows"]),
        "test_selected_rows_ge_minimum": test["trades"] >= int(configured["minimum_test_selected_rows"]),
        "test_each_direction_rows_ge_minimum": all(test_directions.get(direction, 0) >= int(configured["minimum_test_selected_rows_each_direction"]) for direction in ("LONG", "SHORT")),
        "validation_selected_pf_ge_minimum": (validation["stress_profit_factor"] or 0.0) >= float(configured["minimum_validation_selected_stress_profit_factor"]),
        "test_selected_pf_ge_minimum": (test["stress_profit_factor"] or 0.0) >= float(configured["minimum_test_selected_stress_profit_factor"]),
        "validation_selected_average_r_ge_minimum": validation["average_stress_r"] >= float(configured["minimum_validation_selected_average_stress_r"]),
        "test_selected_average_r_ge_minimum": test["average_stress_r"] >= float(configured["minimum_test_selected_average_stress_r"]),
        "test_selected_drawdown_r_lte_maximum": test["max_closed_drawdown_r"] <= float(configured["maximum_test_selected_closed_drawdown_r"]),
        "test_coverage_inside_bounds": float(configured["minimum_test_selection_coverage"]) <= test["coverage"] <= float(configured["maximum_test_selection_coverage"]),
        "validation_positive_month_share_ge_minimum": validation["positive_exit_month_share"] >= float(configured["minimum_validation_positive_month_share"]),
        "test_positive_month_share_ge_minimum": test["positive_exit_month_share"] >= float(configured["minimum_test_positive_month_share"]),
        "test_average_r_bootstrap_p025_above_zero": float(bootstrap["average_stress_r_p025"]) > 0.0,
        "validation_brier_better_than_train_prior": model_metrics["validation"]["brier_score"] < model_metrics["validation"]["train_prior_brier_score"],
        "test_brier_better_than_train_prior": model_metrics["test"]["brier_score"] < model_metrics["test"]["train_prior_brier_score"],
    }


def _prediction_rows(
    split_rows: Mapping[str, Sequence[Mapping[str, str]]],
    probabilities: Mapping[str, Sequence[float]],
    validation_selected: set[str],
    test_selected: set[str],
) -> list[dict[str, Any]]:
    output = []
    for split in ("train", "validation", "test"):
        selected_ids = validation_selected if split == "validation" else test_selected if split == "test" else set()
        for row, probability in zip(split_rows[split], probabilities[split]):
            output.append(
                {
                    "candidate_id": row["candidate_id"],
                    "split": split,
                    "decision_time_utc": row["decision_time_utc"],
                    "exit_time_utc": row["exit_time_utc"],
                    "direction": row["direction"],
                    "probability_profitable": float(probability),
                    "selected": int(row["candidate_id"] in selected_ids),
                    "label_profitable_after_stress": int(row["label_profitable_after_stress"]),
                    "stress_net_pnl_usd": float(row["stress_net_pnl_usd"]),
                    "stress_net_r": float(row["stress_net_r"]),
                }
            )
    return output


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_label_ranker_v1":
        raise ValueError("unexpected ranker contract version")
    if contract.get("model", {}).get("family") != "L2_LOGISTIC_ADAM_V1":
        raise ValueError("ranker V1 requires the frozen logistic model")
    if not 0.0 < float(contract["selection"]["validation_top_fraction"]) < 1.0:
        raise ValueError("validation selection fraction must be between zero and one")
    if int(contract["bootstrap"]["calendar_month_samples"]) < 1000:
        raise ValueError("ranker bootstrap requires at least 1,000 samples")
    allowed = {
        "direction_long", "trend_strength_atr", "ema_gap_atr", "close_fast_distance_atr",
        "body_fraction", "directional_close_location", "touch_distance_atr", "stop_distance_atr",
        "log1p_signal_tick_count", "atr_fraction_of_price", "entry_spread_r",
        "decision_hour_sin", "decision_hour_cos", "decision_weekday_sin", "decision_weekday_cos",
    }
    if set(contract["features"]) != allowed or len(contract["features"]) != len(allowed):
        raise ValueError("ranker feature set differs from the frozen causal set")
    if not contract["authorization"].get("research_only"):
        raise ValueError("ranker must remain research-only")
    if any(contract["authorization"].get(key) for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized")):
        raise ValueError("ranker contract contains forbidden execution authorization")


def _validate_upstream(
    contract: Mapping[str, Any],
    labels_path: Path,
    factory_report_path: Path,
    factory_report: Mapping[str, Any],
) -> None:
    if factory_report.get("classification") != contract["required_factory_classification"]:
        raise RankerError("upstream label-factory classification is not eligible")
    if not all(factory_report.get("quality_gates", {}).values()):
        raise RankerError("upstream label-factory quality gates are not all passing")
    artifact = factory_report.get("artifacts", {}).get("labels_csv", {})
    if artifact.get("sha256") != _sha256_file(labels_path):
        raise RankerError("label CSV does not match the upstream report hash")
    if not factory_report_path.is_file():
        raise FileNotFoundError(factory_report_path)


def _validate_population(
    split_rows: Mapping[str, Sequence[Mapping[str, str]]],
    factory_report: Mapping[str, Any],
) -> None:
    if any(not split_rows[name] for name in ("train", "validation", "test")):
        raise RankerError("ranker population has an empty split")
    all_rows = [row for values in split_rows.values() for row in values]
    if len(all_rows) != int(factory_report.get("resolved_count", -1)):
        raise RankerError("ranker population does not match upstream resolved count")
    expected_splits = factory_report.get("by_split", {})
    for split, rows in split_rows.items():
        if len(rows) != int(expected_splits.get(split, {}).get("trades", -1)):
            raise RankerError(f"ranker {split} count does not match upstream report")
    ids = [row["candidate_id"] for row in all_rows]
    if len(ids) != len(set(ids)):
        raise RankerError("ranker population contains duplicate candidate IDs")
    for split, rows in split_rows.items():
        if any(row["split"] != split for row in rows):
            raise RankerError("ranker split identity mismatch")
        if {row["direction"] for row in rows} != {"LONG", "SHORT"}:
            raise RankerError(f"ranker {split} split does not contain both directions")


def _max_drawdown(values: Sequence[float]) -> float:
    equity = peak = maximum = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        maximum = max(maximum, peak - equity)
    return maximum


def _percentile(values: Sequence[float], probability: float) -> float:
    position = probability * (len(values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(values[lower])
    weight = position - lower
    return float(values[lower] * (1.0 - weight) + values[upper] * weight)


def _render(payload: Mapping[str, Any]) -> str:
    validation = payload["selected_metrics"]["validation"]
    test = payload["selected_metrics"]["test"]
    lines = [
        "# A3 ML Dukascopy Label Ranker V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "Offline historical research only. No demo or broker action is authorized.",
        "",
        "## Model",
        "",
        f"- Validation AUC: `{payload['model_metrics']['validation']['roc_auc']:.6f}`",
        f"- Test AUC: `{payload['model_metrics']['test']['roc_auc']:.6f}`",
        f"- Frozen validation cutoff: `{payload['selection']['validation_probability_cutoff']:.8f}`",
        "",
        "## Selected Subsets",
        "",
        "| Split | Selected | Coverage | Stress PF | Average stress R | Stress net USD | Max DD R | Positive months |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| Validation | {validation['trades']} | {validation['coverage'] * 100.0:.2f}% | {(validation['stress_profit_factor'] or 0.0):.4f} | {validation['average_stress_r']:.4f} | {validation['stress_net_usd']:.2f} | {validation['max_closed_drawdown_r']:.2f} | {validation['positive_exit_months']}/{validation['active_exit_months']} |",
        f"| Test | {test['trades']} | {test['coverage'] * 100.0:.2f}% | {(test['stress_profit_factor'] or 0.0):.4f} | {test['average_stress_r']:.4f} | {test['stress_net_usd']:.2f} | {test['max_closed_drawdown_r']:.2f} | {test['positive_exit_months']}/{test['active_exit_months']} |",
        "",
        f"Test month-bootstrap 95% interval for average stress R: `{payload['test_calendar_month_bootstrap']['average_stress_r_p025']:.4f}` to `{payload['test_calendar_month_bootstrap']['average_stress_r_p975']:.4f}`.",
        "",
        "## Gates",
        "",
    ]
    for name, passed in payload["gates"].items():
        lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(["", "Candidate-family promotion, demo prediction, EA consumption, and broker action remain disabled.", ""])
    return "\n".join(lines)


def _write_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-aware: {value}")
    return parsed.astimezone(UTC)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

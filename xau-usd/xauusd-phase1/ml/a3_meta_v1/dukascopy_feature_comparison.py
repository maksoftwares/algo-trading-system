from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .historical_backtest_training import train_historical_backtest_model


DEFAULT_CONTRACT = Path("config") / "ml" / "a3_ml_dukascopy_feature_comparison.json"


def run_dukascopy_feature_comparison(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_path = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = _read_json(contract_path)
    _validate_contract(contract)

    baseline_status_path = train_historical_backtest_model(root, _resolve(root, contract["baseline_contract"]))
    enhanced_status_path = train_historical_backtest_model(root, _resolve(root, contract["enhanced_contract"]))
    baseline_status = _read_json(baseline_status_path)
    enhanced_status = _read_json(enhanced_status_path)
    baseline_model = _read_json(Path(baseline_status["artifacts"]["model_json"]))
    enhanced_model = _read_json(Path(enhanced_status["artifacts"]["model_json"]))
    baseline_rows = _read_dataset(Path(baseline_status["artifacts"]["dataset_csv"]))
    enhanced_rows = _read_dataset(Path(enhanced_status["artifacts"]["dataset_csv"]))

    exact_population, population_reason = _paired_population(baseline_rows, enhanced_rows)
    if not exact_population:
        raise ValueError(f"baseline and enhanced populations differ: {population_reason}")
    validation_rows = [row for row in enhanced_rows if row["split"] == "validation"]
    baseline_probabilities = _score_logistic(baseline_model, validation_rows)
    enhanced_probabilities = _score_logistic(enhanced_model, validation_rows)
    labels = [int(row["y_win"]) for row in validation_rows]
    bootstrap = _block_bootstrap_auc_delta(
        validation_rows,
        labels,
        baseline_probabilities,
        enhanced_probabilities,
        samples=int(contract["bootstrap_month_samples"]),
        seed=int(contract["bootstrap_seed"]),
    )
    gates = _gate_audit(contract, baseline_status, enhanced_status, exact_population, bootstrap)
    all_pass = all(item["pass"] for item in gates)
    classification = (
        "DUKASCOPY_FEATURES_RESEARCH_SURVIVOR"
        if all_pass
        else "DUKASCOPY_FEATURES_NO_RESEARCH_SURVIVOR"
    )

    prediction_path = _resolve(root, contract["outputs"]["validation_predictions_csv"])
    _write_predictions(
        prediction_path, validation_rows, baseline_probabilities, enhanced_probabilities
    )
    payload = {
        "schema_version": "a3_ml_dukascopy_feature_comparison_result_v1",
        "experiment_id": contract["experiment_id"],
        "created_at_utc": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "classification": classification,
        "population": {
            "exact_same_rows_and_labels": exact_population,
            "training_rows": int(enhanced_status["training_population"]["rows"]),
            "validation_rows": int(enhanced_status["validation_population"]["rows"]),
        },
        "baseline_validation": baseline_status["metrics"]["out_of_time_validation"],
        "enhanced_validation": enhanced_status["metrics"]["out_of_time_validation"],
        "baseline_validation_subgroups": baseline_status["metrics"]["out_of_time_validation_subgroups"],
        "enhanced_validation_subgroups": enhanced_status["metrics"]["out_of_time_validation_subgroups"],
        "auc_improvement": round(
            float(enhanced_status["metrics"]["out_of_time_validation"]["roc_auc"])
            - float(baseline_status["metrics"]["out_of_time_validation"]["roc_auc"]),
            6,
        ),
        "month_block_bootstrap": bootstrap,
        "dukascopy_feature_audit": enhanced_status.get("dukascopy_feature_audit"),
        "gate_audit": gates,
        "artifacts": {
            "baseline_status_json": str(baseline_status_path),
            "enhanced_status_json": str(enhanced_status_path),
            "validation_predictions_csv": str(prediction_path),
        },
        "authorization": _boundary(),
        "limitations": [
            "Dukascopy and MT5 observe the same historical market events; this is cross-feed feature evidence, not an independent time holdout.",
            "Labels are MT5 Strategy Tester outcomes rather than live fills.",
            "Only the frozen R1 long and R2 short candidate families are represented.",
        ],
    }
    output_json = _resolve(root, contract["outputs"]["comparison_json"])
    output_md = _resolve(root, contract["outputs"]["comparison_md"])
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(_render_markdown(payload), encoding="utf-8")
    return output_json


def _validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_feature_comparison_v1":
        raise ValueError("unsupported Dukascopy comparison schema")
    if not contract.get("research_only"):
        raise ValueError("Dukascopy comparison must remain research_only")
    for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if contract.get(key) is not False:
            raise ValueError(f"Dukascopy comparison requires {key}=false")
    if int(contract.get("bootstrap_month_samples", 0)) < 100:
        raise ValueError("Dukascopy comparison requires at least 100 bootstrap samples")


def _read_dataset(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _paired_population(
    baseline_rows: list[dict[str, str]], enhanced_rows: list[dict[str, str]]
) -> tuple[bool, str]:
    fields = ("split", "strategy_family", "direction", "entry_time", "source_summary", "profit_aed", "y_win")
    baseline = [tuple(row[field] for field in fields) for row in baseline_rows]
    enhanced = [tuple(row[field] for field in fields) for row in enhanced_rows]
    if len(baseline) != len(enhanced):
        return False, f"row count {len(baseline)} != {len(enhanced)}"
    if baseline != enhanced:
        return False, "ordered identity or label mismatch"
    return True, "exact"


def _score_logistic(model: dict[str, Any], rows: list[dict[str, str]]) -> list[float]:
    if model.get("model_family") != "LOGISTIC_REGRESSION_V1":
        raise ValueError("Dukascopy comparison scorer is frozen to LOGISTIC_REGRESSION_V1")
    parameters = model["model_parameters"]
    feature_names = list(parameters["feature_names"])
    coefficients = [float(value) for value in parameters["coefficients"]]
    numeric_features = list(model["numeric_features"])
    means = dict(zip(numeric_features, map(float, parameters["numeric_means"])))
    scales = dict(zip(numeric_features, map(float, parameters["numeric_scales"])))
    probabilities = []
    for row in rows:
        values = []
        for feature in feature_names:
            if feature in means:
                values.append((float(row[feature]) - means[feature]) / scales[feature])
            else:
                category, level = feature.split("=", 1)
                values.append(1.0 if row[category] == level else 0.0)
        score = float(parameters["intercept"]) + sum(value * coefficient for value, coefficient in zip(values, coefficients))
        probabilities.append(1.0 / (1.0 + math.exp(-max(min(score, 40.0), -40.0))))
    return probabilities


def _block_bootstrap_auc_delta(
    rows: list[dict[str, str]],
    labels: list[int],
    baseline: list[float],
    enhanced: list[float],
    samples: int,
    seed: int,
) -> dict[str, Any]:
    by_month: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        by_month[row["entry_time"][:7]].append(index)
    months = sorted(by_month)
    if len(months) < 12:
        raise ValueError("month-block bootstrap requires at least 12 active validation months")
    generator = random.Random(seed)
    deltas = []
    for _ in range(samples):
        indices = []
        for _ in months:
            indices.extend(by_month[generator.choice(months)])
        sampled_labels = [labels[index] for index in indices]
        if len(set(sampled_labels)) < 2:
            continue
        baseline_auc = _roc_auc(sampled_labels, [baseline[index] for index in indices])
        enhanced_auc = _roc_auc(sampled_labels, [enhanced[index] for index in indices])
        deltas.append(enhanced_auc - baseline_auc)
    if len(deltas) < samples * 0.95:
        raise ValueError("too many invalid month-block bootstrap samples")
    deltas.sort()
    return {
        "unit": "calendar_month",
        "seed": seed,
        "requested_samples": samples,
        "valid_samples": len(deltas),
        "auc_delta_p025": round(_percentile(deltas, 0.025), 6),
        "auc_delta_median": round(_percentile(deltas, 0.5), 6),
        "auc_delta_p975": round(_percentile(deltas, 0.975), 6),
    }


def _gate_audit(
    contract: dict[str, Any],
    baseline: dict[str, Any],
    enhanced: dict[str, Any],
    exact_population: bool,
    bootstrap: dict[str, Any],
) -> list[dict[str, Any]]:
    configured = contract["gates"]
    baseline_metrics = baseline["metrics"]["out_of_time_validation"]
    enhanced_metrics = enhanced["metrics"]["out_of_time_validation"]
    auc_delta = float(enhanced_metrics["roc_auc"]) - float(baseline_metrics["roc_auc"])
    gates = [
        _gate("exact_same_population", exact_population, "baseline and enhanced rows and labels must match"),
        _gate(
            "minimum_training_rows",
            int(enhanced["training_population"]["rows"]) >= int(configured["minimum_training_rows"]),
            f"{enhanced['training_population']['rows']} >= {configured['minimum_training_rows']}",
        ),
        _gate(
            "minimum_validation_rows",
            int(enhanced["validation_population"]["rows"]) >= int(configured["minimum_validation_rows"]),
            f"{enhanced['validation_population']['rows']} >= {configured['minimum_validation_rows']}",
        ),
        _gate(
            "minimum_enhanced_auc",
            float(enhanced_metrics["roc_auc"]) >= float(configured["minimum_enhanced_auc"]),
            f"{enhanced_metrics['roc_auc']} >= {configured['minimum_enhanced_auc']}",
        ),
        _gate(
            "minimum_auc_improvement",
            auc_delta >= float(configured["minimum_auc_improvement"]),
            f"{auc_delta:.6f} >= {configured['minimum_auc_improvement']}",
        ),
        _gate(
            "auc_delta_ci_lower_above_zero",
            float(bootstrap["auc_delta_p025"]) > 0.0,
            f"{bootstrap['auc_delta_p025']} > 0",
        ),
        _gate(
            "brier_no_regression",
            float(enhanced_metrics["brier_score"])
            <= float(baseline_metrics["brier_score"]) + float(configured["maximum_brier_regression"]),
            f"{enhanced_metrics['brier_score']} <= {baseline_metrics['brier_score']}",
        ),
        _gate(
            "log_loss_no_regression",
            float(enhanced_metrics["log_loss"])
            <= float(baseline_metrics["log_loss"]) + float(configured["maximum_log_loss_regression"]),
            f"{enhanced_metrics['log_loss']} <= {baseline_metrics['log_loss']}",
        ),
    ]
    allowed_regression = float(configured["maximum_direction_auc_regression"])
    for direction in ("LONG", "SHORT"):
        baseline_auc = float(baseline["metrics"]["out_of_time_validation_subgroups"]["direction"][direction]["roc_auc"])
        enhanced_auc = float(enhanced["metrics"]["out_of_time_validation_subgroups"]["direction"][direction]["roc_auc"])
        gates.append(
            _gate(
                f"{direction.lower()}_auc_no_material_regression",
                enhanced_auc >= baseline_auc - allowed_regression,
                f"{enhanced_auc} >= {baseline_auc - allowed_regression:.6f}",
            )
        )
    audit = enhanced.get("dukascopy_feature_audit") or {}
    gates.append(
        _gate(
            "causal_complete_dukascopy_features",
            int(audit.get("missing_rows", -1)) == 0 and int(audit.get("future_ticks_used", -1)) == 0,
            f"missing={audit.get('missing_rows')} future={audit.get('future_ticks_used')}",
        )
    )
    gates.append(
        _gate(
            "execution_boundary_closed",
            baseline.get("authorization") == _boundary() and enhanced.get("authorization") == _boundary(),
            "all authorization fields remain false",
        )
    )
    return gates


def _gate(name: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"gate": name, "pass": bool(passed), "evidence": evidence}


def _write_predictions(
    path: Path,
    rows: list[dict[str, str]],
    baseline: list[float],
    enhanced: list[float],
) -> None:
    fields = [
        "entry_time",
        "strategy_family",
        "direction",
        "y_win",
        "baseline_probability",
        "enhanced_probability",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row, baseline_probability, enhanced_probability in zip(rows, baseline, enhanced):
            writer.writerow(
                {
                    "entry_time": row["entry_time"],
                    "strategy_family": row["strategy_family"],
                    "direction": row["direction"],
                    "y_win": row["y_win"],
                    "baseline_probability": f"{baseline_probability:.12f}",
                    "enhanced_probability": f"{enhanced_probability:.12f}",
                }
            )


def _roc_auc(labels: list[int], probabilities: list[float]) -> float:
    positives = [score for label, score in zip(labels, probabilities) if label == 1]
    negatives = [score for label, score in zip(labels, probabilities) if label == 0]
    if not positives or not negatives:
        raise ValueError("ROC AUC requires both classes")
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            wins += 1.0 if positive > negative else 0.5 if positive == negative else 0.0
    return wins / (len(positives) * len(negatives))


def _percentile(values: list[float], probability: float) -> float:
    position = (len(values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[lower]
    weight = position - lower
    return values[lower] * (1.0 - weight) + values[upper] * weight


def _render_markdown(payload: dict[str, Any]) -> str:
    baseline = payload["baseline_validation"]
    enhanced = payload["enhanced_validation"]
    lines = [
        "# A3 ML Dukascopy Feature Comparison",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"Population: {payload['population']['training_rows']} training / {payload['population']['validation_rows']} validation trades.",
        "",
        "| Metric | Baseline | Dukascopy enhanced |",
        "| --- | ---: | ---: |",
        f"| ROC AUC | {baseline['roc_auc']:.6f} | {enhanced['roc_auc']:.6f} |",
        f"| Brier score | {baseline['brier_score']:.6f} | {enhanced['brier_score']:.6f} |",
        f"| Log loss | {baseline['log_loss']:.6f} | {enhanced['log_loss']:.6f} |",
        "",
        f"AUC improvement: `{payload['auc_improvement']:.6f}`.",
        f"Month-block 95% interval: `{payload['month_block_bootstrap']['auc_delta_p025']:.6f}` to `{payload['month_block_bootstrap']['auc_delta_p975']:.6f}`.",
        "",
        "## Gates",
        "",
    ]
    for item in payload["gate_audit"]:
        lines.append(f"- `{'PASS' if item['pass'] else 'FAIL'}` {item['gate']}: {item['evidence']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Research only. Python demo predictions, EA consumption, and broker action remain unauthorized.",
            "",
        ]
    )
    return "\n".join(lines)


def _boundary() -> dict[str, bool]:
    return {
        "research_only": True,
        "official_c05_model": False,
        "python_demo_predictions_authorized": False,
        "ea_consumption_authorized": False,
        "broker_action_authorized": False,
    }


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

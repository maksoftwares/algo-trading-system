from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from joblib import dump
from sklearn.ensemble import HistGradientBoostingClassifier

from ml.a3_meta_v1.dukascopy_label_ranker import (
    _calendar_month_bootstrap,
    _classification_metrics,
    _sha256_file,
)
from ml.a3_meta_v1.dukascopy_m5_candidate_ranker import (
    _economic_stats,
    _feature_matrix,
    _fraction_cutoff,
    _load_inputs,
    _parse_utc,
    _portfolio_select,
    _prediction_rows,
    _split_rows,
    _test_gates,
    _validate_contract as _validate_base_contract,
    _validate_population,
    _validation_gates,
    _write_prediction_rows,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_m5_nonlinear_ranker.json")


def run_dukascopy_m5_nonlinear_ranker(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    base_path = (root / str(contract["base_contract_path"])).resolve()
    if _sha256_file(base_path) != str(contract["base_contract_sha256"]):
        raise ValueError("nonlinear ranker base-contract hash mismatch")
    base = json.loads(base_path.read_text(encoding="utf-8"))
    _validate_base_contract(base)
    rows, input_audits = _load_inputs(root, base)
    split_rows = _split_rows(rows, base["windows"])
    _validate_population(split_rows, base)
    feature_names = list(base["features"])
    matrices = {
        name: _feature_matrix(values, feature_names, base)
        for name, values in split_rows.items()
    }
    labels = {
        name: np.array(
            [int(row["label_profitable_after_stress"]) for row in values], dtype=int
        )
        for name, values in split_rows.items()
    }
    model = _fit_model(contract["model"])
    model.fit(matrices["train"], labels["train"])
    validation_scores = model.predict_proba(matrices["validation"])[:, 1]
    validation_classification = _classification_metrics(
        labels["validation"].tolist(),
        validation_scores.tolist(),
        float(labels["train"].mean()),
    )
    evaluations = []
    for fraction in base["validation_top_fractions"]:
        cutoff = _fraction_cutoff(validation_scores, float(fraction))
        selected = _portfolio_select(
            split_rows["validation"], validation_scores, cutoff, base["portfolio"]
        )
        stats = _economic_stats(selected, int(base["source_days"]["validation"]))
        gates = _validation_gates(
            validation_classification, stats, base["validation_gates"]
        )
        evaluations.append(
            {
                "top_fraction": float(fraction),
                "probability_cutoff": cutoff,
                "classification_metrics": validation_classification,
                "selected_metrics": stats,
                "gates": gates,
            }
        )
    passing = [row for row in evaluations if all(row["gates"].values())]
    passing.sort(
        key=lambda row: (
            -float(row["selected_metrics"]["stress_profit_factor"] or 0.0),
            -float(row["selected_metrics"]["trades_per_source_day"]),
            -float(row["top_fraction"]),
        )
    )
    chosen = passing[0] if passing else None
    test_classification = None
    test_metrics = None
    test_bootstrap = None
    test_gates = None
    prediction_rows: list[dict[str, Any]] = []
    if chosen is not None:
        cutoff = float(chosen["probability_cutoff"])
        test_scores = model.predict_proba(matrices["test"])[:, 1]
        test_classification = _classification_metrics(
            labels["test"].tolist(), test_scores.tolist(), float(labels["train"].mean())
        )
        selected_test = _portfolio_select(
            split_rows["test"], test_scores, cutoff, base["portfolio"]
        )
        test_metrics = _economic_stats(
            selected_test, int(base["source_days"]["test"])
        )
        test_bootstrap = _calendar_month_bootstrap(
            selected_test,
            samples=int(base["bootstrap"]["calendar_month_samples"]),
            seed=int(base["bootstrap"]["seed"]),
        )
        test_gates = _test_gates(
            test_classification, test_metrics, test_bootstrap, base["test_gates"]
        )
        prediction_rows.extend(
            _prediction_rows(
                split_rows["test"],
                test_scores,
                {row["candidate_id"] for row in selected_test},
                "test",
            )
        )
        selected_validation = _portfolio_select(
            split_rows["validation"], validation_scores, cutoff, base["portfolio"]
        )
        prediction_rows.extend(
            _prediction_rows(
                split_rows["validation"],
                validation_scores,
                {row["candidate_id"] for row in selected_validation},
                "validation",
            )
        )
    if chosen is None:
        classification = "DUKASCOPY_M5_NONLINEAR_RANKER_NO_VALIDATION_SURVIVOR"
    elif test_gates is not None and all(test_gates.values()):
        classification = "DUKASCOPY_M5_NONLINEAR_RANKER_RESEARCH_SURVIVOR"
    else:
        classification = "DUKASCOPY_M5_NONLINEAR_RANKER_INTERNAL_TEST_REJECTED"
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    outputs["model_joblib"].parent.mkdir(parents=True, exist_ok=True)
    dump(model, outputs["model_joblib"], compress=0, protocol=4)
    _write_prediction_rows(outputs["predictions_csv"], prediction_rows)
    payload = {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "base_contract": str(base_path),
        "base_contract_sha256": _sha256_file(base_path),
        "inputs": input_audits,
        "model_config": contract["model"],
        "population": {name: len(values) for name, values in split_rows.items()},
        "source_days": base["source_days"],
        "validation_classification_metrics": validation_classification,
        "validation_evaluations": evaluations,
        "validation_passing_count": len(passing),
        "selected_validation_candidate": chosen,
        "internal_test_outcomes_opened": chosen is not None,
        "internal_test_classification_metrics": test_classification,
        "internal_test_selected_metrics": test_metrics,
        "internal_test_calendar_month_bootstrap": test_bootstrap,
        "internal_test_gates": test_gates,
        "reserved_outcomes_after_2021_07_opened": False,
        "artifacts": {
            "model_joblib": {
                "path": str(outputs["model_joblib"]),
                "sha256": _sha256_file(outputs["model_joblib"]),
            },
            "predictions_csv": {
                "path": str(outputs["predictions_csv"]),
                "sha256": _sha256_file(outputs["predictions_csv"]),
            },
        },
        "authorization": {
            **contract["authorization"],
            "ranker_execution_authorized": False,
            "strategy_promotion_authorized": False,
        },
        "limitations": [
            "This is one bounded nonlinear test, not a hyperparameter search.",
            "The candidate families have negative unconditional training expectancy.",
            "Any survivor still requires untouched later-period and prospective evidence.",
        ],
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _fit_model(config: Mapping[str, Any]) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(
        learning_rate=float(config["learning_rate"]),
        max_iter=int(config["max_iter"]),
        max_leaf_nodes=int(config["max_leaf_nodes"]),
        max_depth=int(config["max_depth"]),
        min_samples_leaf=int(config["min_samples_leaf"]),
        l2_regularization=float(config["l2_regularization"]),
        early_stopping=bool(config["early_stopping"]),
        random_state=int(config["random_state"]),
    )


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_m5_nonlinear_ranker_v1":
        raise ValueError("unexpected nonlinear-ranker contract version")
    authorization = contract.get("authorization", {})
    if not authorization.get("research_only"):
        raise ValueError("nonlinear ranker must remain research only")
    for key in (
        "reserved_validation_outcomes_authorized",
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if authorization.get(key):
            raise ValueError(f"nonlinear ranker requires {key}=false")
    expected = {
        "family": "HIST_GRADIENT_BOOSTING_V1",
        "learning_rate": 0.05,
        "max_iter": 200,
        "max_leaf_nodes": 7,
        "max_depth": 3,
        "min_samples_leaf": 100,
        "l2_regularization": 1.0,
        "early_stopping": False,
        "random_state": 20260715,
    }
    if contract.get("model") != expected:
        raise ValueError("nonlinear-ranker model configuration changed")


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy M5 Nonlinear Ranker V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"- Validation AUC: `{payload['validation_classification_metrics']['roc_auc']:.4f}`",
        f"- Validation survivors: `{payload['validation_passing_count']}`",
        f"- Internal test opened: `{payload['internal_test_outcomes_opened']}`",
        "",
    ]
    chosen = payload.get("selected_validation_candidate")
    if chosen:
        lines.append(
            f"Selected top fraction: `{chosen['top_fraction']}` at cutoff `{chosen['probability_cutoff']:.6f}`."
        )
        lines.append("")
    test = payload.get("internal_test_selected_metrics")
    if test:
        lines.append(
            f"Internal test trades: `{test['trades']}`; PF: `{test['stress_profit_factor']:.4f}`; average R: `{test['average_stress_r']:.4f}`."
        )
        lines.append("")
    lines.append("No prediction, EA, demo, live, or broker action is authorized.")
    lines.append("")
    return "\n".join(lines)

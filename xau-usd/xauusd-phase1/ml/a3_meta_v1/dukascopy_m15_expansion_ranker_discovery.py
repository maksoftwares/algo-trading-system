from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

import joblib
import pandas as pd

from ml.a3_meta_v1.dukascopy_m15_range_expansion import _generate_candidates
from ml.a3_meta_v1.dukascopy_m15_range_rotation import (
    _aggregate_m15,
    _flatten,
    _source_days,
    _storage_root,
    _write_csv,
)
from ml.a3_meta_v1.dukascopy_microstructure_regime import (
    _economic_metrics,
    _fit_model,
    _matrix,
    _portfolio_select,
    _prediction_rows,
    _predictive_metrics,
    _segment_gates,
    _sha256_file,
    _top_fraction_cutoff,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_m15_expansion_ranker_discovery_v1.json")


class ExpansionRankerDiscoveryError(RuntimeError):
    pass


def run_expansion_ranker_discovery(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    expansion_contract_path = (root / str(contract["base_expansion_contract_path"])).resolve()
    if _sha256_file(expansion_contract_path) != contract["base_expansion_contract_sha256"]:
        raise ExpansionRankerDiscoveryError("base expansion contract hash mismatch")
    expansion = json.loads(expansion_contract_path.read_text(encoding="utf-8"))
    storage_root = _storage_root(expansion)
    cache_path = storage_root / str(expansion["base_feature_cache"]["relative_path"])
    if not cache_path.is_file() or _sha256_file(cache_path) != expansion["base_feature_cache"]["sha256"]:
        raise ExpansionRankerDiscoveryError("causal feature cache is missing or changed")
    feature_contract_path = (root / str(expansion["base_feature_cache"]["feature_contract_path"])).resolve()
    if _sha256_file(feature_contract_path) != expansion["base_feature_cache"]["feature_contract_sha256"]:
        raise ExpansionRankerDiscoveryError("feature contract hash mismatch")
    feature_names = list(json.loads(feature_contract_path.read_text(encoding="utf-8"))["features"])
    frame = _aggregate_m15(pd.read_parquet(cache_path), expansion)
    windows = contract["windows"]
    fit_rows = _generate_candidates(
        frame,
        windows["fit_start_utc"],
        windows["fit_end_exclusive_utc"],
        expansion,
        "fit",
    )
    evaluation_rows = _generate_candidates(
        frame,
        windows["fit_end_exclusive_utc"],
        windows["development_evaluation_end_exclusive_utc"],
        expansion,
        "development_evaluation",
    )
    if not fit_rows or not evaluation_rows:
        raise ExpansionRankerDiscoveryError("empty chronological discovery split")
    model = _fit_model(fit_rows, feature_names, expansion["model"])
    fit_scores = model.predict(_matrix(fit_rows, feature_names))
    evaluation_scores = model.predict(_matrix(evaluation_rows, feature_names))
    predictive = _predictive_metrics(evaluation_rows, evaluation_scores)
    source_days = _source_days(
        frame,
        windows["fit_end_exclusive_utc"],
        windows["development_evaluation_end_exclusive_utc"],
    )
    evaluations = []
    selections: dict[float, list[dict[str, Any]]] = {}
    for fraction in contract["train_score_top_fractions"]:
        fraction = float(fraction)
        cutoff = _top_fraction_cutoff(fit_scores, fraction)
        selected = _portfolio_select(
            evaluation_rows,
            evaluation_scores,
            cutoff,
            contract["selection"],
        )
        selections[fraction] = selected
        economic = _economic_metrics(selected, source_days)
        gates = _segment_gates(
            predictive,
            economic,
            contract["development_gates"],
            predictive_gate_required=True,
        )
        evaluations.append(
            {
                "policy_id": f"ML_TOP_{int(100 * fraction)}",
                "policy_kind": "MODEL_TOP_FRACTION",
                "top_fraction": fraction,
                "fit_score_cutoff": cutoff,
                "predictive_metrics": predictive,
                "economic_metrics": economic,
                "gates": gates,
                "passes": all(gates.values()),
            }
        )
    passing = [row for row in evaluations if row["passes"]]
    passing.sort(
        key=lambda row: (
            -float(row["economic_metrics"]["stress_profit_factor"] or 0.0),
            -float(row["economic_metrics"]["average_stress_r"]),
            float(row["top_fraction"]),
        )
    )
    chosen = passing[0] if passing else None
    classification = (
        "DUKASCOPY_M15_EXPANSION_RANKER_DEVELOPMENT_SURVIVOR"
        if chosen is not None
        else "DUKASCOPY_M15_EXPANSION_RANKER_NO_DEVELOPMENT_SURVIVOR"
    )
    predictions = _prediction_rows(selections[float(chosen["top_fraction"])], "development_evaluation") if chosen else []
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": feature_names,
            "selected_policy": chosen,
            "contract_sha256": _sha256_file(contract_file),
            "base_expansion_contract_sha256": contract["base_expansion_contract_sha256"],
        },
        outputs["model_joblib"],
        compress=3,
    )
    _write_csv(outputs["evaluations_csv"], _flatten(evaluations))
    _write_csv(outputs["predictions_csv"], predictions)
    payload = {
        "schema_version": contract["schema_version"],
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "base_expansion_contract": str(expansion_contract_path),
        "base_expansion_contract_sha256": contract["base_expansion_contract_sha256"],
        "fit_population": len(fit_rows),
        "development_evaluation_population": len(evaluation_rows),
        "development_evaluation_source_days": source_days,
        "predictive_metrics": predictive,
        "evaluations": evaluations,
        "selected_policy": chosen,
        "outcomes_after_2020_07_opened": False,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key != "report_json" and path.exists()
        },
        "authorization": contract["authorization"],
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _render(payload: Mapping[str, Any]) -> str:
    predictive = payload["predictive_metrics"]
    lines = [
        "# A3 ML Dukascopy M15 Expansion Ranker Discovery V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"Development evaluation AUC: `{float(predictive['auc'] or 0):.4f}`.",
        f"Development evaluation Spearman: `{float(predictive['spearman'] or 0):.4f}`.",
        f"Outcomes after 2020-07 opened: `{payload['outcomes_after_2020_07_opened']}`.",
        "",
    ]
    for row in payload["evaluations"]:
        metrics = row["economic_metrics"]
        lines.append(
            f"- Top {100 * row['top_fraction']:.0f}%: {metrics['trades']} trades, {metrics['trades_per_source_day']:.3f}/day, PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{row['passes']}`."
        )
    lines.extend(["", "This diagnostic cannot authorize strategy promotion, demo, live, EA, or broker action.", ""])
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_m15_expansion_ranker_discovery_v1":
        raise ValueError("unexpected expansion-ranker discovery contract")
    windows = contract.get("windows", {})
    if windows.get("development_evaluation_end_exclusive_utc") != "2020-07-01T00:00:00Z":
        raise ValueError("development outcome boundary changed")
    if windows.get("outcomes_after_2020_07_authorized"):
        raise ValueError("post-development outcomes must remain closed")
    if contract.get("train_score_top_fractions") != [0.60, 0.45, 0.30, 0.20]:
        raise ValueError("retention policies changed")
    authorization = contract.get("authorization", {})
    if not authorization.get("research_only") or not authorization.get("development_diagnostic_only"):
        raise ValueError("diagnostic authorization required")
    for key in (
        "strategy_promotion_authorized",
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if authorization.get(key):
            raise ValueError(f"{key} must remain false")

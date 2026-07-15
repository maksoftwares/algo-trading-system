from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_microstructure_regime import (
    _economic_metrics,
    _fit_model,
    _matrix,
    _portfolio_select,
    _predictive_metrics,
    _sha256_file,
    _top_fraction_cutoff,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_external_candidate_ranker_v1.json")
FAMILY_FEATURES = {
    "REAL_YIELD_SHOCK": "family_real_yield_shock",
    "YIELD_USD_AGREEMENT": "family_yield_usd_agreement",
    "INFLATION_REPRICING": "family_inflation_repricing",
    "COT_TREND_CONFIRM": "family_cot_trend_confirm",
    "COT_CROWDED_REVERSAL": "family_cot_crowded_reversal",
    "COT_PRODUCER_CONFIRM": "family_cot_producer_confirm",
}
FORBIDDEN_FEATURE_TOKENS = ("net_r", "mfe", "mae", "exit_", "target_", "stop_price", "entry_price")


class ExternalCandidateRankerError(RuntimeError):
    pass


def run_external_candidate_ranker(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    rows = _load_rows(root, contract)
    windows = contract["windows"]
    fit = _window(rows, windows["fit_start_utc"], windows["fit_end_exclusive_utc"])
    evaluation = _window(
        rows,
        windows["fit_end_exclusive_utc"],
        windows["development_evaluation_end_exclusive_utc"],
    )
    if len(fit) < 100 or len(evaluation) < 100:
        raise ExternalCandidateRankerError("chronological ranker splits are too small")
    features = list(contract["features"])
    model = _fit_model(fit, features, contract["model"])
    fit_scores = model.predict(_matrix(fit, features))
    evaluation_scores = model.predict(_matrix(evaluation, features))
    predictive = _predictive_metrics(evaluation, evaluation_scores)
    source_days = int(
        np.busday_count(
            np.datetime64(windows["fit_end_exclusive_utc"][:10]),
            np.datetime64(windows["development_evaluation_end_exclusive_utc"][:10]),
        )
    )
    raw_selected = _portfolio_select(
        evaluation,
        np.zeros(len(evaluation)),
        -float("inf"),
        contract["selection"],
    )
    evaluations: list[dict[str, Any]] = [
        {
            "policy_id": "RAW_ALL",
            "top_fraction": 1.0,
            "fit_score_cutoff": None,
            "predictive_metrics": predictive,
            "economic_metrics": _economic_metrics(raw_selected, source_days),
            "gates": {},
            "passes": False,
        }
    ]
    selections: dict[float, list[dict[str, Any]]] = {}
    for fraction in contract["train_score_top_fractions"]:
        fraction = float(fraction)
        cutoff = _top_fraction_cutoff(fit_scores, fraction)
        selected = _portfolio_select(evaluation, evaluation_scores, cutoff, contract["selection"])
        economic = _economic_metrics(selected, source_days)
        gates = _development_gates(predictive, economic, contract["development_gates"])
        evaluations.append(
            {
                "policy_id": f"ML_TOP_{int(fraction * 100)}",
                "top_fraction": fraction,
                "fit_score_cutoff": cutoff,
                "predictive_metrics": predictive,
                "economic_metrics": economic,
                "gates": gates,
                "passes": all(gates.values()),
            }
        )
        selections[fraction] = selected
    passing = [row for row in evaluations if row["policy_id"] != "RAW_ALL" and row["passes"]]
    passing.sort(
        key=lambda row: (
            -float(row["economic_metrics"]["stress_profit_factor"] or 0.0),
            -float(row["economic_metrics"]["average_stress_r"]),
            float(row["top_fraction"]),
        )
    )
    selected_policy = passing[0] if passing else None
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": features,
            "selected_policy": selected_policy,
            "contract_sha256": _sha256_file(contract_file),
        },
        outputs["model_joblib"],
        compress=3,
    )
    _write_csv(outputs["evaluations_csv"], _flatten_evaluations(evaluations))
    _write_csv(outputs["scored_candidates_csv"], _scored_rows(evaluation, evaluation_scores))
    payload = {
        "schema_version": contract["schema_version"],
        "classification": (
            "EXTERNAL_CANDIDATE_RANKER_DEVELOPMENT_SURVIVOR"
            if selected_policy
            else "EXTERNAL_CANDIDATE_RANKER_NO_DEVELOPMENT_SURVIVOR"
        ),
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "source_files": [
            {**source, "resolved_path": str((root / source["path"]).resolve())}
            for source in contract["sources"]
        ],
        "fit_population": len(fit),
        "development_evaluation_population": len(evaluation),
        "development_source_days": source_days,
        "predictive_metrics": predictive,
        "evaluations": evaluations,
        "selected_policy": selected_policy,
        "outcomes_after_2020_07_opened": False,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key != "report_json" and path.exists()
        },
        "authorization": {
            **contract["authorization"],
            "model_execution_authorized": False,
            "demo_or_live_authorized": False,
        },
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _load_rows(root: Path, contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for source in contract["sources"]:
        path = (root / source["path"]).resolve()
        if not path.is_file() or _sha256_file(path) != source["sha256"]:
            raise ExternalCandidateRankerError(f"candidate source missing or changed: {path}")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for raw in csv.DictReader(handle):
                row: dict[str, Any] = dict(raw)
                for key, value in list(row.items()):
                    if key not in {
                        "candidate_id",
                        "campaign_id",
                        "family_id",
                        "regime",
                        "direction",
                        "decision_time_utc",
                        "entry_time_utc",
                        "exit_time_utc",
                        "exit_reason",
                    }:
                        row[key] = float(value)
                for family, feature in FAMILY_FEATURES.items():
                    row[feature] = 1.0 if row["family_id"] == family else 0.0
                rows.append(row)
    identifiers = [row["candidate_id"] for row in rows]
    if len(identifiers) != len(set(identifiers)):
        raise ExternalCandidateRankerError("duplicate candidate identifiers")
    return sorted(rows, key=lambda row: (int(row["decision_time_ms"]), row["candidate_id"]))


def _window(rows: Sequence[Mapping[str, Any]], start: str, end: str) -> list[dict[str, Any]]:
    lo = int(pd.Timestamp(start).timestamp() * 1000)
    hi = int(pd.Timestamp(end).timestamp() * 1000)
    return [dict(row) for row in rows if lo <= int(row["decision_time_ms"]) < hi]


def _development_gates(
    predictive: Mapping[str, Any], economic: Mapping[str, Any], gate: Mapping[str, Any]
) -> dict[str, bool]:
    return {
        "minimum_auc": float(predictive.get("auc") or 0.0) >= float(gate["minimum_auc"]),
        "minimum_spearman": float(predictive.get("spearman") or 0.0) >= float(gate["minimum_spearman"]),
        "minimum_trades": int(economic["trades"]) >= int(gate["minimum_trades"]),
        "minimum_frequency": float(economic["trades_per_source_day"])
        >= float(gate["minimum_trades_per_source_day"]),
        "maximum_frequency": float(economic["trades_per_source_day"])
        <= float(gate["maximum_trades_per_source_day"]),
        "stress_profit_factor": float(economic["stress_profit_factor"] or 0.0)
        >= float(gate["minimum_stress_profit_factor"]),
        "average_stress_r": float(economic["average_stress_r"]) >= float(gate["minimum_average_stress_r"]),
        "positive_month_share": float(economic["positive_month_share"])
        >= float(gate["minimum_positive_month_share"]),
        "maximum_closed_drawdown": float(economic["maximum_closed_drawdown_r"])
        <= float(gate["maximum_closed_drawdown_r"]),
        "top10_winners_removed": (
            not gate["require_top10_winners_removed_net_positive"]
            or float(economic["top10_winners_removed_net_r"]) > 0
        ),
    }


def _scored_rows(rows: Sequence[Mapping[str, Any]], scores: Sequence[float]) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "campaign_id": row["campaign_id"],
            "family_id": row["family_id"],
            "direction": row["direction"],
            "decision_time_utc": row["decision_time_utc"],
            "entry_time_utc": row["entry_time_utc"],
            "model_score": float(score),
            "stress_net_r": float(row["stress_net_r"]),
        }
        for row, score in zip(rows, scores)
    ]


def _flatten_evaluations(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "policy_id": row["policy_id"],
            "top_fraction": row["top_fraction"],
            "fit_score_cutoff": row["fit_score_cutoff"],
            **{f"predictive_{key}": value for key, value in row["predictive_metrics"].items()},
            **row["economic_metrics"],
            "passes": row["passes"],
            "failed_gates": "|".join(key for key, value in row["gates"].items() if not value),
        }
        for row in rows
    ]


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    rows = list(rows)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fields:
            return
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _render(payload: Mapping[str, Any]) -> str:
    predictive = payload["predictive_metrics"]
    lines = [
        "# A3 ML External Candidate Ranker V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"Fit population: {payload['fit_population']}. Development evaluation: {payload['development_evaluation_population']}.",
        f"Development AUC: {float(predictive.get('auc') or 0):.4f}. Spearman: {float(predictive.get('spearman') or 0):.4f}.",
        "",
    ]
    for row in payload["evaluations"]:
        metrics = row["economic_metrics"]
        lines.append(
            f"- {row['policy_id']}: {metrics['trades']} trades, {metrics['trades_per_source_day']:.3f}/day, stress PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{row['passes']}`."
        )
    lines.extend(["", "Outcomes after 2020-07 remained closed. No demo or live action is authorized.", ""])
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_external_candidate_ranker_v1":
        raise ExternalCandidateRankerError("unexpected ranker contract")
    if contract.get("windows", {}).get("later_outcomes_opened"):
        raise ExternalCandidateRankerError("later outcomes must remain closed")
    features = list(contract.get("features", []))
    forbidden = [name for name in features if any(token in name for token in FORBIDDEN_FEATURE_TOKENS)]
    if forbidden:
        raise ExternalCandidateRankerError(f"outcome-derived features are forbidden: {forbidden}")
    if set(FAMILY_FEATURES.values()) - set(features):
        raise ExternalCandidateRankerError("family one-hot features missing")
    authorization = contract.get("authorization", {})
    if not authorization.get("later_outcomes_require_development_pass"):
        raise ExternalCandidateRankerError("chronological firewall weakened")
    for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if authorization.get(key):
            raise ExternalCandidateRankerError(f"{key} must remain false")

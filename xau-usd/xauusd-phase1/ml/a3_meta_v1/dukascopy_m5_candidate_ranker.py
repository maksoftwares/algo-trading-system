from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from ml.a3_meta_v1.dukascopy_label_ranker import (
    _calendar_month_bootstrap,
    _classification_metrics,
    _fit_logistic,
    _max_drawdown,
    _parse_utc,
    _score,
    _sha256_file,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_m5_candidate_ranker.json")
FAMILY_FEATURES = {
    "family_pullback": "pullback_h1_rr1p5",
    "family_breakout": "breakout_h1_rr1p5",
    "family_trend_sweep": "sweep_h1_rr1p5",
    "family_band_fade": "band_fade_any_rr1p5",
    "family_impulse_fade": "impulse_fade_any_rr1p5",
    "family_mean_sweep": "sweep_fade_any_rr1p5",
}


class M5CandidateRankerError(RuntimeError):
    pass


def run_dukascopy_m5_candidate_ranker(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    rows, input_audits = _load_inputs(root, contract)
    split_rows = _split_rows(rows, contract["windows"])
    _validate_population(split_rows, contract)
    feature_names = list(contract["features"])
    matrices = {
        name: _feature_matrix(values, feature_names, contract)
        for name, values in split_rows.items()
    }
    labels = {
        name: np.array(
            [int(row["label_profitable_after_stress"]) for row in values], dtype=float
        )
        for name, values in split_rows.items()
    }

    validation_evaluations = []
    fitted_models: dict[str, dict[str, Any]] = {}
    validation_scores: dict[str, np.ndarray] = {}
    for model_config in contract["models"]:
        model_id = str(model_config["model_id"])
        model = _fit_logistic(
            matrices["train"], labels["train"], feature_names, model_config
        )
        fitted_models[model_id] = model
        scores = _score(model, matrices["validation"])
        validation_scores[model_id] = scores
        classification = _classification_metrics(
            labels["validation"].astype(int).tolist(),
            scores.tolist(),
            float(labels["train"].mean()),
        )
        for fraction in contract["validation_top_fractions"]:
            cutoff = _fraction_cutoff(scores, float(fraction))
            selected = _portfolio_select(
                split_rows["validation"], scores, cutoff, contract["portfolio"]
            )
            stats = _economic_stats(
                selected, int(contract["source_days"]["validation"])
            )
            gates = _validation_gates(
                classification, stats, contract["validation_gates"]
            )
            validation_evaluations.append(
                {
                    "model_id": model_id,
                    "top_fraction": float(fraction),
                    "probability_cutoff": cutoff,
                    "classification_metrics": classification,
                    "selected_metrics": stats,
                    "gates": gates,
                }
            )

    passing = [row for row in validation_evaluations if all(row["gates"].values())]
    passing.sort(
        key=lambda row: (
            -float(row["selected_metrics"]["stress_profit_factor"] or 0.0),
            -float(row["selected_metrics"]["trades_per_source_day"]),
            str(row["model_id"]),
            -float(row["top_fraction"]),
        )
    )
    chosen = passing[0] if passing else None
    test_metrics = None
    test_classification = None
    test_bootstrap = None
    test_gates = None
    prediction_rows: list[dict[str, Any]] = []

    if chosen is not None:
        model_id = str(chosen["model_id"])
        cutoff = float(chosen["probability_cutoff"])
        test_scores = _score(fitted_models[model_id], matrices["test"])
        test_classification = _classification_metrics(
            labels["test"].astype(int).tolist(),
            test_scores.tolist(),
            float(labels["train"].mean()),
        )
        selected_test = _portfolio_select(
            split_rows["test"], test_scores, cutoff, contract["portfolio"]
        )
        test_metrics = _economic_stats(
            selected_test, int(contract["source_days"]["test"])
        )
        test_bootstrap = _calendar_month_bootstrap(
            selected_test,
            samples=int(contract["bootstrap"]["calendar_month_samples"]),
            seed=int(contract["bootstrap"]["seed"]),
        )
        test_gates = _test_gates(
            test_classification,
            test_metrics,
            test_bootstrap,
            contract["test_gates"],
        )
        selected_ids = {row["candidate_id"] for row in selected_test}
        prediction_rows.extend(
            _prediction_rows(split_rows["test"], test_scores, selected_ids, "test")
        )
        validation_selected = _portfolio_select(
            split_rows["validation"],
            validation_scores[model_id],
            cutoff,
            contract["portfolio"],
        )
        prediction_rows.extend(
            _prediction_rows(
                split_rows["validation"],
                validation_scores[model_id],
                {row["candidate_id"] for row in validation_selected},
                "validation",
            )
        )

    if chosen is None:
        classification = "DUKASCOPY_M5_CANDIDATE_RANKER_NO_VALIDATION_SURVIVOR"
    elif test_gates is not None and all(test_gates.values()):
        classification = "DUKASCOPY_M5_CANDIDATE_RANKER_RESEARCH_SURVIVOR"
    else:
        classification = "DUKASCOPY_M5_CANDIDATE_RANKER_INTERNAL_TEST_REJECTED"

    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    model_payload = {
        "schema_version": "a3_ml_dukascopy_m5_candidate_ranker_model_v1",
        "selected_model_id": str(chosen["model_id"]) if chosen else None,
        "selection_probability_cutoff": float(chosen["probability_cutoff"])
        if chosen
        else None,
        "selected_top_fraction": float(chosen["top_fraction"]) if chosen else None,
        "model": fitted_models[str(chosen["model_id"])] if chosen else None,
        "features": feature_names,
        "input_sha256": [row["sha256"] for row in input_audits],
        "authorization": contract["authorization"],
    }
    outputs["model_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["model_json"].write_text(json.dumps(model_payload, indent=2), encoding="utf-8")
    _write_prediction_rows(outputs["predictions_csv"], prediction_rows)
    payload = {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "inputs": input_audits,
        "population": {name: len(values) for name, values in split_rows.items()},
        "source_days": contract["source_days"],
        "train_positive_share": float(labels["train"].mean()),
        "validation_evaluations": validation_evaluations,
        "validation_passing_count": len(passing),
        "selected_validation_candidate": chosen,
        "internal_test_outcomes_opened": chosen is not None,
        "internal_test_classification_metrics": test_classification,
        "internal_test_selected_metrics": test_metrics,
        "internal_test_calendar_month_bootstrap": test_bootstrap,
        "internal_test_gates": test_gates,
        "reserved_outcomes_after_2021_07_opened": False,
        "artifacts": {
            "model_json": {
                "path": str(outputs["model_json"]),
                "sha256": _sha256_file(outputs["model_json"]),
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
            "The input families have negative unconditional training expectancy.",
            "The internal test is inside an older period whose aggregate family outcomes were previously known.",
            "A research survivor still requires untouched later-period and prospective evidence.",
        ],
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _load_inputs(
    root: Path, contract: Mapping[str, Any]
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    rows: list[dict[str, str]] = []
    audits = []
    for configured in contract["inputs"]:
        path = (root / str(configured["path"])).resolve()
        digest = _sha256_file(path)
        if digest != str(configured["sha256"]):
            raise M5CandidateRankerError(f"input hash mismatch: {path}")
        families = {str(value) for value in configured["families"]}
        count = 0
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("status") == "RESOLVED" and row.get("family_id") in families:
                    rows.append(row)
                    count += 1
        audits.append({"path": str(path), "sha256": digest, "selected_rows": count})
    rows.sort(key=lambda row: (row["decision_time_utc"], row["candidate_id"]))
    if len({row["candidate_id"] for row in rows}) != len(rows):
        raise M5CandidateRankerError("duplicate candidate IDs across ranker inputs")
    return rows, audits


def _split_rows(
    rows: Sequence[Mapping[str, str]], windows: Mapping[str, str]
) -> dict[str, list[dict[str, str]]]:
    boundaries = [
        _parse_utc(windows["train_start_utc"]),
        _parse_utc(windows["train_end_exclusive_utc"]),
        _parse_utc(windows["validation_end_exclusive_utc"]),
        _parse_utc(windows["internal_test_end_exclusive_utc"]),
    ]
    output = {"train": [], "validation": [], "test": []}
    for raw in rows:
        row = dict(raw)
        decision = _parse_utc(row["decision_time_utc"])
        if boundaries[0] <= decision < boundaries[1]:
            output["train"].append(row)
        elif boundaries[1] <= decision < boundaries[2]:
            output["validation"].append(row)
        elif boundaries[2] <= decision < boundaries[3]:
            output["test"].append(row)
    return output


def _feature_matrix(
    rows: Sequence[Mapping[str, str]],
    feature_names: Sequence[str],
    contract: Mapping[str, Any],
) -> np.ndarray:
    matrix = np.array(
        [[_feature_value(row, name, contract) for name in feature_names] for row in rows],
        dtype=float,
    )
    if not np.isfinite(matrix).all():
        raise M5CandidateRankerError("feature matrix contains non-finite values")
    return matrix


def _feature_value(
    row: Mapping[str, str], name: str, contract: Mapping[str, Any]
) -> float:
    direction_sign = 1.0 if row["direction"] == "LONG" else -1.0
    atr = float(row["atr"])
    stop_distance = float(row["stop_distance"])
    signal_close = float(row["signal_close"])
    if atr <= 0.0 or stop_distance <= 0.0 or signal_close <= 0.0:
        raise M5CandidateRankerError("non-positive feature denominator")
    decision = _parse_utc(row["decision_time_utc"]) + timedelta(
        hours=int(contract["portfolio"]["server_utc_offset_hours"])
    )
    values = {
        "direction_long": float(row["direction"] == "LONG"),
        "trend_strength_atr": direction_sign * float(row["ema_fast_slope_atr"]),
        "ema_gap_atr": abs(float(row["ema_fast"]) - float(row["ema_slow"])) / atr,
        "close_fast_distance_atr": abs(signal_close - float(row["ema_fast"])) / atr,
        "body_fraction": float(row["body_fraction"]),
        "directional_close_location": float(row["close_location"])
        if direction_sign > 0
        else 1.0 - float(row["close_location"]),
        "touch_distance_atr": float(row["touch_distance_atr"]),
        "stop_distance_atr": float(row["stop_distance_atr"]),
        "log1p_signal_tick_count": math.log1p(float(row["signal_tick_count"])),
        "atr_fraction_of_price": atr / signal_close,
        "entry_spread_r": float(row["entry_spread"]) / stop_distance,
        "server_hour_sin": math.sin(2.0 * math.pi * decision.hour / 24.0),
        "server_hour_cos": math.cos(2.0 * math.pi * decision.hour / 24.0),
        "weekday_sin": math.sin(2.0 * math.pi * decision.weekday() / 7.0),
        "weekday_cos": math.cos(2.0 * math.pi * decision.weekday() / 7.0),
    }
    for feature, family_id in FAMILY_FEATURES.items():
        values[feature] = float(row["family_id"] == family_id)
    if name not in values:
        raise M5CandidateRankerError(f"unknown or forbidden feature: {name}")
    return float(values[name])


def _fraction_cutoff(scores: Sequence[float], fraction: float) -> float:
    count = max(1, math.ceil(len(scores) * fraction))
    ranked = sorted((float(value) for value in scores), reverse=True)
    return ranked[count - 1]


def _portfolio_select(
    rows: Sequence[Mapping[str, str]],
    scores: Sequence[float],
    cutoff: float,
    portfolio: Mapping[str, Any],
) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], tuple[dict[str, str], float]] = {}
    for raw, score in zip(rows, scores):
        probability = float(score)
        if probability < cutoff:
            continue
        row = dict(raw)
        key = (row["decision_time_utc"], row["direction"])
        current = grouped.get(key)
        if current is None or (-probability, row["candidate_id"]) < (
            -current[1],
            current[0]["candidate_id"],
        ):
            grouped[key] = (row, probability)
    candidates = sorted(
        grouped.values(),
        key=lambda item: (item[0]["entry_time_utc"], -item[1], item[0]["candidate_id"]),
    )
    selected = []
    open_exits: list[datetime] = []
    last_entry: datetime | None = None
    daily_entries: Counter[str] = Counter()
    offset = int(portfolio["server_utc_offset_hours"])
    cooldown = timedelta(minutes=int(portfolio["cooldown_minutes"]))
    for row, _ in candidates:
        entry = _parse_utc(row["entry_time_utc"])
        open_exits = [value for value in open_exits if value > entry]
        if len(open_exits) >= int(portfolio["maximum_concurrent_trades"]):
            continue
        if last_entry is not None and entry - last_entry < cooldown:
            continue
        server_day = (entry + timedelta(hours=offset)).date().isoformat()
        if daily_entries[server_day] >= int(portfolio["maximum_trades_per_server_day"]):
            continue
        selected.append(row)
        open_exits.append(_parse_utc(row["exit_time_utc"]))
        last_entry = entry
        daily_entries[server_day] += 1
    return selected


def _economic_stats(
    rows: Sequence[Mapping[str, str]], source_days: int
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row["exit_time_utc"], row["candidate_id"]))
    pnl = [float(row["stress_net_pnl_usd"]) for row in ordered]
    returns = [float(row["stress_net_r"]) for row in ordered]
    profit = sum(value for value in pnl if value > 0.0)
    loss = -sum(value for value in pnl if value < 0.0)
    directions = Counter(row["direction"] for row in ordered)
    months: dict[str, float] = defaultdict(float)
    for row in ordered:
        months[row["exit_time_utc"][:7]] += float(row["stress_net_pnl_usd"])
    top10 = sorted((value for value in pnl if value > 0.0), reverse=True)[:10]
    minimum_direction_share = (
        min(directions.get("LONG", 0), directions.get("SHORT", 0)) / len(ordered)
        if ordered
        else 0.0
    )
    return {
        "trades": len(ordered),
        "trades_per_source_day": len(ordered) / source_days if source_days else 0.0,
        "wins": sum(value > 0.0 for value in pnl),
        "win_rate_pct": 100.0 * sum(value > 0.0 for value in pnl) / len(pnl)
        if pnl
        else 0.0,
        "stress_net_usd": sum(pnl),
        "stress_profit_factor": profit / loss if loss > 0.0 else None,
        "average_stress_r": sum(returns) / len(returns) if returns else 0.0,
        "max_closed_drawdown_r": _max_drawdown(returns),
        "max_closed_drawdown_usd": _max_drawdown(pnl),
        "minimum_direction_share": minimum_direction_share,
        "direction_counts": dict(directions),
        "positive_exit_month_share": sum(value > 0.0 for value in months.values())
        / len(months)
        if months
        else 0.0,
        "top10_winners_removed_net_usd": sum(pnl) - sum(top10),
    }


def _validation_gates(
    classification: Mapping[str, float],
    stats: Mapping[str, Any],
    configured: Mapping[str, Any],
) -> dict[str, bool]:
    pf = stats.get("stress_profit_factor")
    return {
        "auc_ge_minimum": float(classification["roc_auc"]) >= float(configured["minimum_auc"]),
        "trades_ge_minimum": int(stats["trades"]) >= int(configured["minimum_trades"]),
        "trades_per_source_day_ge_minimum": float(stats["trades_per_source_day"])
        >= float(configured["minimum_trades_per_source_day"]),
        "stress_profit_factor_ge_minimum": pf is not None
        and float(pf) >= float(configured["minimum_stress_profit_factor"]),
        "average_stress_r_ge_minimum": float(stats["average_stress_r"])
        >= float(configured["minimum_average_stress_r"]),
        "direction_share_ge_minimum": float(stats["minimum_direction_share"])
        >= float(configured["minimum_direction_share"]),
        "top10_winners_removed_net_positive": float(
            stats["top10_winners_removed_net_usd"]
        )
        > 0.0,
    }


def _test_gates(
    classification: Mapping[str, float],
    stats: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    configured: Mapping[str, Any],
) -> dict[str, bool]:
    pf = stats.get("stress_profit_factor")
    return {
        "auc_ge_minimum": float(classification["roc_auc"]) >= float(configured["minimum_auc"]),
        "trades_ge_minimum": int(stats["trades"]) >= int(configured["minimum_trades"]),
        "trades_per_source_day_ge_minimum": float(stats["trades_per_source_day"])
        >= float(configured["minimum_trades_per_source_day"]),
        "stress_profit_factor_ge_minimum": pf is not None
        and float(pf) >= float(configured["minimum_stress_profit_factor"]),
        "average_stress_r_ge_minimum": float(stats["average_stress_r"])
        >= float(configured["minimum_average_stress_r"]),
        "direction_share_ge_minimum": float(stats["minimum_direction_share"])
        >= float(configured["minimum_direction_share"]),
        "positive_month_share_ge_minimum": float(stats["positive_exit_month_share"])
        >= float(configured["minimum_positive_exit_month_share"]),
        "closed_drawdown_r_lte_maximum": float(stats["max_closed_drawdown_r"])
        <= float(configured["maximum_closed_drawdown_r"]),
        "closed_drawdown_usd_lte_maximum": float(stats["max_closed_drawdown_usd"])
        <= float(configured["maximum_closed_drawdown_usd"]),
        "top10_winners_removed_net_positive": float(
            stats["top10_winners_removed_net_usd"]
        )
        > 0.0,
        "calendar_month_bootstrap_p025_above_zero": bootstrap.get(
            "average_stress_r_p025"
        )
        is not None
        and float(bootstrap["average_stress_r_p025"]) > 0.0,
    }


def _prediction_rows(
    rows: Sequence[Mapping[str, str]],
    scores: Sequence[float],
    selected_ids: set[str],
    split: str,
) -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": row["candidate_id"],
            "split": split,
            "decision_time_utc": row["decision_time_utc"],
            "family_id": row["family_id"],
            "direction": row["direction"],
            "probability": float(score),
            "selected": int(row["candidate_id"] in selected_ids),
        }
        for row, score in zip(rows, scores)
    ]


def _write_prediction_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fields = [
        "candidate_id",
        "split",
        "decision_time_utc",
        "family_id",
        "direction",
        "probability",
        "selected",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _validate_population(
    split_rows: Mapping[str, Sequence[Mapping[str, str]]], contract: Mapping[str, Any]
) -> None:
    for name, rows in split_rows.items():
        if len(rows) < 500:
            raise M5CandidateRankerError(f"insufficient {name} population")
        labels = {int(row["label_profitable_after_stress"]) for row in rows}
        if labels != {0, 1}:
            raise M5CandidateRankerError(f"{name} requires both target classes")
    if set(contract["source_days"]) != {"train", "validation", "test"}:
        raise ValueError("ranker source-day keys changed")


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_m5_candidate_ranker_v1":
        raise ValueError("unexpected M5 candidate-ranker contract version")
    authorization = contract.get("authorization", {})
    if not authorization.get("research_only"):
        raise ValueError("candidate ranker must remain research only")
    for key in (
        "reserved_validation_outcomes_authorized",
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if authorization.get(key):
            raise ValueError(f"candidate ranker requires {key}=false")
    if len(contract.get("inputs", [])) != 2:
        raise ValueError("candidate ranker requires exactly two frozen inputs")
    expected_features = {
        "direction_long",
        "trend_strength_atr",
        "ema_gap_atr",
        "close_fast_distance_atr",
        "body_fraction",
        "directional_close_location",
        "touch_distance_atr",
        "stop_distance_atr",
        "log1p_signal_tick_count",
        "atr_fraction_of_price",
        "entry_spread_r",
        "server_hour_sin",
        "server_hour_cos",
        "weekday_sin",
        "weekday_cos",
        *FAMILY_FEATURES.keys(),
    }
    if set(contract.get("features", [])) != expected_features:
        raise ValueError("candidate-ranker feature set changed")
    if [float(value) for value in contract.get("validation_top_fractions", [])] != [
        0.5,
        0.4,
        0.3,
        0.2,
    ]:
        raise ValueError("validation retention fractions changed")
    model_ids = [str(row["model_id"]) for row in contract.get("models", [])]
    if model_ids != ["logistic_l2_0p01", "logistic_l2_0p10"]:
        raise ValueError("candidate-ranker model matrix changed")
    boundaries = [
        _parse_utc(contract["windows"][key])
        for key in (
            "train_start_utc",
            "train_end_exclusive_utc",
            "validation_end_exclusive_utc",
            "internal_test_end_exclusive_utc",
        )
    ]
    if boundaries != sorted(boundaries) or len(set(boundaries)) != len(boundaries):
        raise ValueError("candidate-ranker time boundaries are invalid")
    if contract.get("selection_order") != [
        "stress_profit_factor_desc",
        "trades_per_source_day_desc",
        "model_id_asc",
        "fraction_desc",
    ]:
        raise ValueError("candidate-ranker selection order changed")


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy M5 Candidate Ranker V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"- Train rows: `{payload['population']['train']}`",
        f"- Validation rows: `{payload['population']['validation']}`",
        f"- Internal test rows: `{payload['population']['test']}`",
        f"- Validation survivors: `{payload['validation_passing_count']}`",
        f"- Internal test opened: `{payload['internal_test_outcomes_opened']}`",
        "",
    ]
    chosen = payload.get("selected_validation_candidate")
    if chosen:
        lines.extend(
            [
                f"Selected model: `{chosen['model_id']}` at top fraction `{chosen['top_fraction']}`.",
                "",
            ]
        )
    test = payload.get("internal_test_selected_metrics")
    if test:
        lines.extend(
            [
                f"Internal test trades: `{test['trades']}`; PF: `{test['stress_profit_factor']:.4f}`; average R: `{test['average_stress_r']:.4f}`; trades/source day: `{test['trades_per_source_day']:.3f}`.",
                "",
            ]
        )
    lines.append("No prediction, EA, demo, live, or broker action is authorized.")
    lines.append("")
    return "\n".join(lines)

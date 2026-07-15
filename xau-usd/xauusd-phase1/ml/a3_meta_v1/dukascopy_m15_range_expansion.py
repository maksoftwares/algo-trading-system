from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_m15_range_rotation import (
    M15_WIDTH_MS,
    _aggregate_m15,
    _apply_frozen_policy,
    _apply_policy,
    _finite_row,
    _flatten,
    _iso_ms,
    _raw_metrics,
    _raw_train_gates,
    _source_days,
    _storage_root,
    _write_csv,
)
from ml.a3_meta_v1.dukascopy_microstructure_regime import (
    _candidate_features,
    _economic_metrics,
    _fit_model,
    _matrix,
    _parse_utc_ms,
    _prediction_rows,
    _predictive_metrics,
    _segment_gates,
    _sha256_file,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_m15_range_expansion_v1.json")


class M15RangeExpansionError(RuntimeError):
    pass


def run_m15_range_expansion(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _storage_root(contract)
    cache_config = contract["base_feature_cache"]
    cache_path = storage_root / str(cache_config["relative_path"])
    if not cache_path.is_file() or _sha256_file(cache_path) != cache_config["sha256"]:
        raise M15RangeExpansionError("base causal feature cache is missing or changed")
    feature_contract_path = (root / str(cache_config["feature_contract_path"])).resolve()
    aggregation_contract_path = (root / str(cache_config["aggregation_contract_path"])).resolve()
    if _sha256_file(feature_contract_path) != cache_config["feature_contract_sha256"]:
        raise M15RangeExpansionError("feature contract hash mismatch")
    if _sha256_file(aggregation_contract_path) != cache_config["aggregation_contract_sha256"]:
        raise M15RangeExpansionError("M15 aggregation contract hash mismatch")
    feature_names = list(json.loads(feature_contract_path.read_text(encoding="utf-8"))["features"])
    frame = _aggregate_m15(pd.read_parquet(cache_path), contract)
    windows = contract["windows"]
    source_days = {
        "train": _source_days(frame, windows["train_start_utc"], windows["train_end_exclusive_utc"]),
        "validation": _source_days(frame, windows["train_end_exclusive_utc"], windows["validation_end_exclusive_utc"]),
        "internal_test": _source_days(frame, windows["validation_end_exclusive_utc"], windows["internal_test_end_exclusive_utc"]),
        "exam": _source_days(frame, windows["internal_test_end_exclusive_utc"], windows["exam_end_exclusive_utc"]),
    }
    train = _generate_candidates(
        frame,
        windows["train_start_utc"],
        windows["train_end_exclusive_utc"],
        contract,
        "train",
    )
    raw_train = _raw_metrics(train)
    raw_gates = _raw_train_gates(raw_train, contract["train_raw_gate"])
    raw_pass = all(raw_gates.values())

    model = None
    validation: list[dict[str, Any]] = []
    evaluations: list[dict[str, Any]] = []
    chosen: dict[str, Any] | None = None
    internal_payload: dict[str, Any] | None = None
    exam_payload: dict[str, Any] | None = None
    predictions: list[dict[str, Any]] = []
    train_scores: np.ndarray | None = None

    if raw_pass:
        validation = _generate_candidates(
            frame,
            windows["train_end_exclusive_utc"],
            windows["validation_end_exclusive_utc"],
            contract,
            "validation",
        )
        model = _fit_model(train, feature_names, contract["model"])
        train_scores = model.predict(_matrix(train, feature_names))
        validation_scores = model.predict(_matrix(validation, feature_names))
        predictive = _predictive_metrics(validation, validation_scores)
        for policy in contract["policies"]:
            selected, cutoff, predictive_required = _apply_policy(
                validation,
                validation_scores,
                train_scores,
                policy,
                contract["selection"],
            )
            economic = _economic_metrics(selected, source_days["validation"])
            gates = _segment_gates(
                predictive,
                economic,
                contract["validation_gates"],
                predictive_gate_required=predictive_required,
            )
            evaluations.append(
                {
                    "policy_id": policy["policy_id"],
                    "policy_kind": policy["kind"],
                    "train_score_cutoff": cutoff,
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
                str(row["policy_id"]),
            )
        )
        chosen = passing[0] if passing else None
        if chosen is not None and train_scores is not None:
            policy = _policy(contract, str(chosen["policy_id"]))
            selected, _, _ = _apply_frozen_policy(
                validation,
                validation_scores,
                policy,
                float(chosen["train_score_cutoff"]),
                contract["selection"],
            )
            predictions.extend(_prediction_rows(selected, "validation"))
            internal, internal_payload, internal_selected = _evaluate_later_segment(
                frame,
                windows["validation_end_exclusive_utc"],
                windows["internal_test_end_exclusive_utc"],
                "internal_test",
                source_days["internal_test"],
                model,
                feature_names,
                policy,
                float(chosen["train_score_cutoff"]),
                contract["selection"],
                contract["test_gates"],
                contract,
            )
            predictions.extend(_prediction_rows(internal_selected, "internal_test"))
            if internal_payload["passes"]:
                _, exam_payload, exam_selected = _evaluate_later_segment(
                    frame,
                    windows["internal_test_end_exclusive_utc"],
                    windows["exam_end_exclusive_utc"],
                    "exam",
                    source_days["exam"],
                    model,
                    feature_names,
                    policy,
                    float(chosen["train_score_cutoff"]),
                    contract["selection"],
                    contract["exam_gates"],
                    contract,
                )
                predictions.extend(_prediction_rows(exam_selected, "exam"))

    classification = _classification(raw_pass, chosen, internal_payload, exam_payload)
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": feature_names,
            "selected_policy": chosen,
            "contract_sha256": _sha256_file(contract_file),
            "base_feature_sha256": cache_config["sha256"],
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
        "base_feature_cache": {
            "path": str(cache_path),
            "sha256": cache_config["sha256"],
            "source_manifest_sha256": cache_config["source_manifest_sha256"],
        },
        "m15_rows": len(frame),
        "source_days": source_days,
        "train_population": len(train),
        "raw_train_metrics": raw_train,
        "raw_train_gates": raw_gates,
        "raw_train_passes": raw_pass,
        "validation_opened": raw_pass,
        "validation_population": len(validation),
        "validation_evaluations": evaluations,
        "selected_validation_policy": chosen,
        "internal_test_opened": chosen is not None,
        "internal_test": internal_payload,
        "exam_opened": bool(internal_payload and internal_payload["passes"]),
        "exam": exam_payload,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key != "report_json" and path.exists()
        },
        "authorization": {
            **contract["authorization"],
            "strategy_promotion_authorized": False,
            "demo_or_live_authorized": False,
        },
    }
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def _evaluate_later_segment(
    frame: pd.DataFrame,
    start: str,
    end: str,
    segment: str,
    source_days: int,
    model: Any,
    feature_names: Sequence[str],
    policy: Mapping[str, Any],
    cutoff: float,
    selection: Mapping[str, Any],
    gate: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    rows = _generate_candidates(frame, start, end, contract, segment)
    scores = model.predict(_matrix(rows, feature_names))
    selected, _, predictive_required = _apply_frozen_policy(rows, scores, policy, cutoff, selection)
    predictive = _predictive_metrics(rows, scores)
    economic = _economic_metrics(selected, source_days)
    gates = _segment_gates(predictive, economic, gate, predictive_gate_required=predictive_required)
    return rows, {
        "population": len(rows),
        "predictive_metrics": predictive,
        "economic_metrics": economic,
        "gates": gates,
        "passes": all(gates.values()),
    }, selected


def _generate_candidates(
    frame: pd.DataFrame,
    start_utc: str,
    end_utc: str,
    contract: Mapping[str, Any],
    segment: str,
) -> list[dict[str, Any]]:
    start_ms, end_ms = _parse_utc_ms(start_utc), _parse_utc_ms(end_utc)
    threshold = float(contract["range_regime"]["excursion_zscore"])
    horizon = int(contract["execution"]["maximum_holding_bars"])
    cooldown = int(contract["execution"]["signal_cooldown_minutes"]) * 60_000
    last_signal = -10**18
    rows = []
    for index in range(1, len(frame) - horizon - 1):
        row = frame.iloc[index]
        decision = int(row["timestamp_ms"]) + M15_WIDTH_MS
        if decision < start_ms or decision + horizon * M15_WIDTH_MS > end_ms:
            continue
        if not bool(row["range_active"]) or not _finite_row(row):
            continue
        previous_z = float(frame.iloc[index - 1]["zscore"])
        direction = None
        if float(row["zscore"]) >= threshold and previous_z < threshold:
            direction = "LONG"
        elif float(row["zscore"]) <= -threshold and previous_z > -threshold:
            direction = "SHORT"
        if direction is None or decision - last_signal < cooldown:
            continue
        outcome = _simulate_expansion_trade(frame, index, direction, contract["execution"])
        if outcome is None:
            continue
        last_signal = decision
        features = _candidate_features(row, "TREND_BREAKOUT", "RANGE", direction, outcome["entry_spread_r"])
        rows.append(
            {
                "candidate_id": f"{segment}:{decision}:M15_RANGE_EXPANSION:{direction}",
                "segment": segment,
                "family_id": "M15_RANGE_EXPANSION",
                "regime": "RANGE_TRANSITION",
                "direction": direction,
                "decision_time_ms": decision,
                "decision_time_utc": _iso_ms(decision),
                **outcome,
                **features,
            }
        )
    return rows


def _simulate_expansion_trade(
    frame: pd.DataFrame,
    signal_index: int,
    direction: str,
    execution: Mapping[str, Any],
) -> dict[str, Any] | None:
    horizon = int(execution["maximum_holding_bars"])
    entry_index = signal_index + 1
    last_index = entry_index + horizon - 1
    expected = int(frame.iloc[entry_index]["timestamp_ms"]) + np.arange(horizon) * M15_WIDTH_MS
    observed = frame.iloc[entry_index : last_index + 1]["timestamp_ms"].to_numpy(dtype=np.int64)
    if len(observed) != horizon or not np.array_equal(expected, observed):
        return None
    signal = frame.iloc[signal_index]
    entry = frame.iloc[entry_index]
    atr = float(signal["atr"])
    entry_bid = float(entry["xauusd_bid_open"])
    entry_ask = float(entry["xauusd_ask_open"])
    minimum_stop = float(execution["minimum_stop_atr"]) * atr
    buffer = float(execution["structural_stop_buffer_atr"]) * atr
    reward = float(execution["reward_r"])
    if direction == "LONG":
        entry_price = entry_ask
        stop = min(entry_price - minimum_stop, float(signal["xauusd_mid_low"]) - buffer)
        risk = entry_price - stop
        target = entry_price + reward * risk
    else:
        entry_price = entry_bid
        stop = max(entry_price + minimum_stop, float(signal["xauusd_mid_high"]) + buffer)
        risk = stop - entry_price
        target = entry_price - reward * risk
    if risk <= 0:
        return None
    spread_r = (entry_ask - entry_bid) / risk
    if spread_r < 0 or spread_r > float(execution["maximum_entry_spread_r"]):
        return None
    bars = frame.iloc[entry_index : last_index + 1]
    if direction == "LONG":
        favorable = (bars["xauusd_bid_high"] - entry_price).max() / risk
        adverse = (bars["xauusd_bid_low"] - entry_price).min() / risk
    else:
        favorable = (entry_price - bars["xauusd_ask_low"]).max() / risk
        adverse = (entry_price - bars["xauusd_ask_high"]).min() / risk
    exit_price = math.nan
    exit_reason = "EXPIRY"
    exit_index = last_index
    for offset, (_, bar) in enumerate(bars.iterrows()):
        if direction == "LONG":
            stop_hit = float(bar["xauusd_bid_low"]) <= stop
            target_hit = float(bar["xauusd_bid_high"]) >= target
        else:
            stop_hit = float(bar["xauusd_ask_high"]) >= stop
            target_hit = float(bar["xauusd_ask_low"]) <= target
        if stop_hit:
            exit_price, exit_reason, exit_index = stop, "STOP", entry_index + offset
            break
        if target_hit:
            exit_price, exit_reason, exit_index = target, "TARGET", entry_index + offset
            break
    if not math.isfinite(exit_price):
        last = frame.iloc[last_index]
        exit_price = float(last["xauusd_bid_close"] if direction == "LONG" else last["xauusd_ask_close"])
    baseline_r = (exit_price - entry_price) / risk if direction == "LONG" else (entry_price - exit_price) / risk
    return {
        "entry_time_ms": int(entry["timestamp_ms"]),
        "entry_time_utc": _iso_ms(int(entry["timestamp_ms"])),
        "exit_time_ms": int(frame.iloc[exit_index]["timestamp_ms"]) + M15_WIDTH_MS,
        "exit_time_utc": _iso_ms(int(frame.iloc[exit_index]["timestamp_ms"]) + M15_WIDTH_MS),
        "entry_price": entry_price,
        "exit_price": exit_price,
        "stop_price": stop,
        "target_price": target,
        "initial_risk_price": risk,
        "entry_spread_r": spread_r,
        "exit_reason": exit_reason,
        "baseline_net_r": baseline_r,
        "stress_net_r": baseline_r - float(execution["stress_slippage_r"]),
        "mfe_r": float(favorable),
        "mae_r": float(adverse),
    }


def _policy(contract: Mapping[str, Any], policy_id: str) -> Mapping[str, Any]:
    return next(row for row in contract["policies"] if row["policy_id"] == policy_id)


def _classification(
    raw_pass: bool,
    chosen: Mapping[str, Any] | None,
    internal: Mapping[str, Any] | None,
    exam: Mapping[str, Any] | None,
) -> str:
    if not raw_pass:
        return "DUKASCOPY_M15_RANGE_EXPANSION_TRAIN_REJECTED"
    if chosen is None:
        return "DUKASCOPY_M15_RANGE_EXPANSION_NO_VALIDATION_SURVIVOR"
    if not internal or not internal["passes"]:
        return "DUKASCOPY_M15_RANGE_EXPANSION_INTERNAL_TEST_REJECTED"
    if not exam or not exam["passes"]:
        return "DUKASCOPY_M15_RANGE_EXPANSION_EXAM_REJECTED"
    return "DUKASCOPY_M15_RANGE_EXPANSION_RESEARCH_SURVIVOR"


def _render(payload: Mapping[str, Any]) -> str:
    raw = payload["raw_train_metrics"]
    lines = [
        "# A3 ML Dukascopy M15 Range Expansion V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        f"Train: `{raw['trades']}` trades, baseline PF `{float(raw['baseline_profit_factor'] or 0):.3f}`, stress PF `{float(raw['stress_profit_factor'] or 0):.3f}`, average stress `{raw['average_stress_r']:.4f}R`.",
        f"Validation opened: `{payload['validation_opened']}`.",
        f"Internal test opened: `{payload['internal_test_opened']}`.",
        f"Exam opened: `{payload['exam_opened']}`.",
        "",
    ]
    for row in payload["validation_evaluations"]:
        metrics = row["economic_metrics"]
        lines.append(
            f"- {row['policy_id']}: {metrics['trades']} trades, {metrics['trades_per_source_day']:.3f}/day, PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{row['passes']}`."
        )
    if payload["internal_test"]:
        metrics = payload["internal_test"]["economic_metrics"]
        lines.extend(["", f"Internal test: {metrics['trades']} trades, PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{payload['internal_test']['passes']}`."])
    if payload["exam"]:
        metrics = payload["exam"]["economic_metrics"]
        lines.extend(["", f"Exam: {metrics['trades']} trades, PF {float(metrics['stress_profit_factor'] or 0):.3f}, average {metrics['average_stress_r']:.4f}R, pass `{payload['exam']['passes']}`."])
    lines.extend(["", "No demo, live, EA, or broker action is authorized.", ""])
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_m15_range_expansion_v1":
        raise ValueError("unexpected M15 range-expansion contract")
    authorization = contract.get("authorization", {})
    for key in (
        "validation_requires_train_raw_pass",
        "internal_test_requires_validation_pass",
        "exam_requires_internal_test_pass",
    ):
        if not authorization.get(key):
            raise ValueError("chronological firewall weakened")
    for key in ("python_demo_predictions_authorized", "ea_consumption_authorized", "broker_action_authorized"):
        if authorization.get(key):
            raise ValueError(f"{key} must remain false")
    if contract.get("execution", {}).get("same_bar_collision_policy") != "STOP_FIRST":
        raise ValueError("collision policy changed")
    if contract.get("model", {}).get("random_state") != 20260716:
        raise ValueError("model seed changed")
    policies = [row["policy_id"] for row in contract.get("policies", [])]
    if policies != ["RAW_ALL", "ML_TOP_60", "ML_TOP_45", "ML_TOP_30"]:
        raise ValueError("policy set changed")

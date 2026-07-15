from __future__ import annotations

import csv
import json
import math
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd

from ml.a3_meta_v1.dukascopy_microstructure_regime import (
    _candidate_features,
    _economic_metrics,
    _fit_model,
    _matrix,
    _parse_utc_ms,
    _portfolio_select,
    _prediction_rows,
    _predictive_metrics,
    _return_metrics,
    _segment_gates,
    _sha256_file,
    _top_fraction_cutoff,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_m15_range_rotation_v1.json")
M15_WIDTH_MS = 900_000


class M15RangeRotationError(RuntimeError):
    pass


def run_m15_range_rotation(root: Path, contract_path: Path | None = None) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _storage_root(contract)
    cache_path = storage_root / str(contract["base_feature_cache"]["relative_path"])
    if not cache_path.is_file() or _sha256_file(cache_path) != contract["base_feature_cache"]["sha256"]:
        raise M15RangeRotationError("base causal feature cache is missing or changed")
    base_contract = (root / str(contract["base_feature_cache"]["base_contract_path"])).resolve()
    if _sha256_file(base_contract) != contract["base_feature_cache"]["base_contract_sha256"]:
        raise M15RangeRotationError("base feature contract hash mismatch")
    feature_names = list(json.loads(base_contract.read_text(encoding="utf-8"))["features"])
    m5 = pd.read_parquet(cache_path)
    frame = _aggregate_m15(m5, contract)
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
    raw_train_gates = _raw_train_gates(raw_train, contract["train_raw_gate"])
    raw_train_passes = all(raw_train_gates.values())
    validation: list[dict[str, Any]] = []
    validation_evaluations: list[dict[str, Any]] = []
    model = None
    chosen: dict[str, Any] | None = None
    prediction_rows: list[dict[str, Any]] = []
    internal_payload: dict[str, Any] | None = None
    exam_payload: dict[str, Any] | None = None

    if raw_train_passes:
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
        validation_predictive = _predictive_metrics(validation, validation_scores)
        for policy in contract["policies"]:
            selected, cutoff, predictive_required = _apply_policy(
                validation,
                validation_scores,
                train_scores,
                policy,
                contract["selection"],
            )
            metrics = _economic_metrics(selected, source_days["validation"])
            gates = _segment_gates(
                validation_predictive,
                metrics,
                contract["validation_gates"],
                predictive_gate_required=predictive_required,
            )
            validation_evaluations.append(
                {
                    "policy_id": policy["policy_id"],
                    "policy_kind": policy["kind"],
                    "train_score_cutoff": cutoff,
                    "predictive_metrics": validation_predictive,
                    "economic_metrics": metrics,
                    "gates": gates,
                    "passes": all(gates.values()),
                }
            )
        passing = [row for row in validation_evaluations if row["passes"]]
        passing.sort(
            key=lambda row: (
                -float(row["economic_metrics"]["stress_profit_factor"] or 0.0),
                -float(row["economic_metrics"]["average_stress_r"]),
                str(row["policy_id"]),
            )
        )
        chosen = passing[0] if passing else None
        if chosen is not None:
            chosen_policy = next(row for row in contract["policies"] if row["policy_id"] == chosen["policy_id"])
            chosen_selected, _, _ = _apply_policy(
                validation,
                validation_scores,
                train_scores,
                chosen_policy,
                contract["selection"],
            )
            prediction_rows.extend(_prediction_rows(chosen_selected, "validation"))
            internal = _generate_candidates(
                frame,
                windows["validation_end_exclusive_utc"],
                windows["internal_test_end_exclusive_utc"],
                contract,
                "internal_test",
            )
            internal_scores = model.predict(_matrix(internal, feature_names))
            internal_selected, _, predictive_required = _apply_frozen_policy(
                internal,
                internal_scores,
                chosen_policy,
                float(chosen["train_score_cutoff"]),
                contract["selection"],
            )
            internal_predictive = _predictive_metrics(internal, internal_scores)
            internal_metrics = _economic_metrics(internal_selected, source_days["internal_test"])
            internal_gates = _segment_gates(
                internal_predictive,
                internal_metrics,
                contract["test_gates"],
                predictive_gate_required=predictive_required,
            )
            internal_payload = {
                "population": len(internal),
                "predictive_metrics": internal_predictive,
                "economic_metrics": internal_metrics,
                "gates": internal_gates,
                "passes": all(internal_gates.values()),
            }
            prediction_rows.extend(_prediction_rows(internal_selected, "internal_test"))
            if internal_payload["passes"]:
                exam = _generate_candidates(
                    frame,
                    windows["internal_test_end_exclusive_utc"],
                    windows["exam_end_exclusive_utc"],
                    contract,
                    "exam",
                )
                exam_scores = model.predict(_matrix(exam, feature_names))
                exam_selected, _, predictive_required = _apply_frozen_policy(
                    exam,
                    exam_scores,
                    chosen_policy,
                    float(chosen["train_score_cutoff"]),
                    contract["selection"],
                )
                exam_predictive = _predictive_metrics(exam, exam_scores)
                exam_metrics = _economic_metrics(exam_selected, source_days["exam"])
                exam_gates = _segment_gates(
                    exam_predictive,
                    exam_metrics,
                    contract["exam_gates"],
                    predictive_gate_required=predictive_required,
                )
                exam_payload = {
                    "population": len(exam),
                    "predictive_metrics": exam_predictive,
                    "economic_metrics": exam_metrics,
                    "gates": exam_gates,
                    "passes": all(exam_gates.values()),
                }
                prediction_rows.extend(_prediction_rows(exam_selected, "exam"))

    classification = _classification(raw_train_passes, chosen, internal_payload, exam_payload)
    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    for path in outputs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": feature_names,
            "selected_policy": chosen,
            "contract_sha256": _sha256_file(contract_file),
            "base_feature_sha256": contract["base_feature_cache"]["sha256"],
        },
        outputs["model_joblib"],
        compress=3,
    )
    _write_csv(outputs["evaluations_csv"], _flatten(validation_evaluations))
    _write_csv(outputs["predictions_csv"], prediction_rows)
    payload = {
        "schema_version": contract["schema_version"],
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "base_feature_cache": {
            "path": str(cache_path),
            "sha256": contract["base_feature_cache"]["sha256"],
            "source_manifest_sha256": contract["base_feature_cache"]["source_manifest_sha256"],
        },
        "m15_rows": len(frame),
        "source_days": source_days,
        "train_population": len(train),
        "raw_train_metrics": raw_train,
        "raw_train_gates": raw_train_gates,
        "raw_train_passes": raw_train_passes,
        "validation_opened": raw_train_passes,
        "validation_population": len(validation),
        "validation_evaluations": validation_evaluations,
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


def _storage_root(contract: Mapping[str, Any]) -> Path:
    name = str(contract["storage_environment_variable"])
    raw = os.environ.get(name, "").strip()
    if not raw:
        raise M15RangeRotationError(f"{name} is required")
    path = Path(raw).resolve()
    if not path.is_dir():
        raise M15RangeRotationError(f"storage root does not exist: {path}")
    return path


def _aggregate_m15(frame: pd.DataFrame, contract: Mapping[str, Any]) -> pd.DataFrame:
    work = frame.sort_values("timestamp_ms", kind="mergesort").copy()
    work["m15_bucket"] = work["timestamp_ms"] - work["timestamp_ms"] % M15_WIDTH_MS
    work["spread_weighted"] = work["tick_spread_mean"] * work["xau_tick_count"]
    work["book_weighted"] = work["tick_book_imbalance_mean"] * work["xau_tick_count"]
    work["micro_weighted"] = work["tick_microprice_edge_mean"] * work["xau_tick_count"]
    group = work.groupby("m15_bucket", sort=True)
    named: dict[str, tuple[str, str]] = {
        "timestamp_first": ("timestamp_ms", "min"),
        "timestamp_last": ("timestamp_ms", "max"),
        "source_bar_count": ("timestamp_ms", "count"),
        "xau_tick_count": ("xau_tick_count", "sum"),
        "tick_signed_move": ("tick_signed_move", "sum"),
        "tick_move_count": ("tick_move_count", "sum"),
        "tick_realized_variance": ("tick_realized_variance", "sum"),
        "spread_weighted": ("spread_weighted", "sum"),
        "tick_spread_last": ("tick_spread_last", "last"),
        "tick_spread_max": ("tick_spread_max", "max"),
        "book_weighted": ("book_weighted", "sum"),
        "micro_weighted": ("micro_weighted", "sum"),
        "tick_imbalance_5m": ("tick_imbalance_5m", "last"),
        "book_imbalance_5m": ("book_imbalance_5m", "last"),
        "microprice_edge_5m": ("microprice_edge_5m", "last"),
        "price_efficiency_5m": ("price_efficiency_5m", "last"),
        "xau_return_5m_price": ("xau_return_5m_price", "last"),
        "xagusd_return_5m": ("xagusd_return_5m", "last"),
    }
    for prefix in ("xauusd_mid", "xauusd_bid", "xauusd_ask"):
        named[f"{prefix}_open"] = (f"{prefix}_open", "first")
        named[f"{prefix}_high"] = (f"{prefix}_high", "max")
        named[f"{prefix}_low"] = (f"{prefix}_low", "min")
        named[f"{prefix}_close"] = (f"{prefix}_close", "last")
    for symbol in ("xagusd", "eurusd", "usdjpy"):
        named[f"{symbol}_mid_close"] = (f"{symbol}_mid_close", "last")
    out = group.agg(**named).reset_index().rename(columns={"m15_bucket": "timestamp_ms"})
    required = int(contract["aggregation"]["required_source_bars"])
    out = out[
        (out["source_bar_count"] == required)
        & (out["timestamp_first"] == out["timestamp_ms"])
        & (out["timestamp_last"] == out["timestamp_ms"] + (required - 1) * 300_000)
    ].copy()
    count = out["xau_tick_count"].replace(0, np.nan)
    out["tick_spread_mean"] = out["spread_weighted"] / count
    out["tick_imbalance_15m"] = out["tick_signed_move"] / out["tick_move_count"].replace(0, np.nan)
    out["tick_imbalance_60m"] = (
        out["tick_signed_move"].rolling(4, min_periods=4).sum()
        / out["tick_move_count"].rolling(4, min_periods=4).sum().replace(0, np.nan)
    )
    out["book_imbalance_15m"] = out["book_weighted"] / count
    out["microprice_edge_15m"] = out["micro_weighted"] / count
    quote_rate = out["xau_tick_count"] / 900.0
    out["quote_intensity_ratio"] = quote_rate / quote_rate.rolling(4, min_periods=4).mean()
    realized = np.sqrt(out["tick_realized_variance"].clip(lower=0.0))
    out["realized_volatility_ratio"] = realized / realized.rolling(4, min_periods=4).mean()
    out["spread_shock_ratio"] = out["tick_spread_last"] / out["tick_spread_mean"].rolling(4, min_periods=4).mean()
    close = out["xauusd_mid_close"]
    high = out["xauusd_mid_high"]
    low = out["xauusd_mid_low"]
    previous = close.shift(1)
    true_range = pd.concat([(high - low).abs(), (high - previous).abs(), (low - previous).abs()], axis=1).max(axis=1)
    regime = contract["range_regime"]
    out["atr"] = true_range.ewm(alpha=1 / int(regime["atr_bars"]), adjust=False, min_periods=int(regime["atr_bars"])).mean()
    out["ema_fast"] = close.ewm(span=int(regime["ema_fast_bars"]), adjust=False).mean()
    out["ema_slow"] = close.ewm(span=int(regime["ema_slow_bars"]), adjust=False).mean()
    out["ema_fast_slope_3"] = out["ema_fast"] - out["ema_fast"].shift(3)
    out["xau_return_15m_price"] = close - close.shift(1)
    out["xau_return_60m_price"] = close - close.shift(4)
    midline_bars = int(regime["range_midline_bars"])
    out["range_midline"] = close.rolling(midline_bars, min_periods=midline_bars).mean()
    range_std = close.rolling(midline_bars, min_periods=midline_bars).std(ddof=1)
    out["zscore"] = (close - out["range_midline"]) / range_std
    out["atr_ratio_1d"] = out["atr"] / out["atr"].rolling(96, min_periods=48).median()
    for symbol in ("xagusd", "eurusd", "usdjpy"):
        series = out[f"{symbol}_mid_close"]
        out[f"{symbol}_return_15m"] = 10_000.0 * (series / series.shift(1) - 1.0)
        out[f"{symbol}_return_60m"] = 10_000.0 * (series / series.shift(4) - 1.0)
    gap_r = (out["ema_fast"] - out["ema_slow"]).abs() / out["atr"]
    shock_r = out["xau_return_15m_price"].abs() / out["atr"]
    out["range_active"] = (
        (gap_r <= float(regime["range_gap_atr"]))
        & (out["atr_ratio_1d"] <= float(regime["maximum_atr_ratio"]))
        & (shock_r < float(regime["shock_return_atr"]))
    )
    return out.replace([np.inf, -np.inf], np.nan).reset_index(drop=True)


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
            direction = "SHORT"
        elif float(row["zscore"]) <= -threshold and previous_z > -threshold:
            direction = "LONG"
        if direction is None or decision - last_signal < cooldown:
            continue
        outcome = _simulate_range_trade(frame, index, direction, contract["execution"])
        if outcome is None:
            continue
        last_signal = decision
        features = _candidate_features(row, "RANGE_FADE", "RANGE", direction, outcome["entry_spread_r"])
        rows.append(
            {
                "candidate_id": f"{segment}:{decision}:M15_RANGE_ROTATION:{direction}",
                "segment": segment,
                "family_id": "M15_RANGE_ROTATION",
                "regime": "RANGE",
                "direction": direction,
                "decision_time_ms": decision,
                "decision_time_utc": _iso_ms(decision),
                **outcome,
                **features,
            }
        )
    return rows


def _finite_row(row: pd.Series) -> bool:
    names = (
        "atr",
        "range_midline",
        "zscore",
        "tick_imbalance_5m",
        "tick_imbalance_15m",
        "tick_imbalance_60m",
        "book_imbalance_5m",
        "book_imbalance_15m",
        "microprice_edge_5m",
        "microprice_edge_15m",
        "quote_intensity_ratio",
        "realized_volatility_ratio",
        "spread_shock_ratio",
        "xagusd_return_60m",
        "eurusd_return_60m",
        "usdjpy_return_60m",
    )
    return all(math.isfinite(float(row[name])) for name in names) and float(row["atr"]) > 0


def _simulate_range_trade(
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
    midline = float(signal["range_midline"])
    entry_bid = float(entry["xauusd_bid_open"])
    entry_ask = float(entry["xauusd_ask_open"])
    minimum_stop = float(execution["minimum_stop_atr"]) * atr
    buffer = float(execution["structural_stop_buffer_atr"]) * atr
    if direction == "LONG":
        entry_price = entry_ask
        target = midline
        stop = min(entry_price - minimum_stop, float(signal["xauusd_mid_low"]) - buffer)
        risk = entry_price - stop
        target_r = (target - entry_price) / risk
    else:
        entry_price = entry_bid
        target = midline
        stop = max(entry_price + minimum_stop, float(signal["xauusd_mid_high"]) + buffer)
        risk = stop - entry_price
        target_r = (entry_price - target) / risk
    if risk <= 0 or target_r < float(execution["minimum_target_r"]):
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
            exit_price, exit_reason, exit_index = target, "MIDLINE_TARGET", entry_index + offset
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
        "initial_target_r": target_r,
        "entry_spread_r": spread_r,
        "exit_reason": exit_reason,
        "baseline_net_r": baseline_r,
        "stress_net_r": baseline_r - float(execution["stress_slippage_r"]),
        "mfe_r": float(favorable),
        "mae_r": float(adverse),
    }


def _raw_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    baseline = _return_metrics(rows, "baseline_net_r")
    stress = _return_metrics(rows, "stress_net_r")
    return {
        "trades": baseline["trades"],
        "baseline_profit_factor": baseline["profit_factor"],
        "baseline_average_r": baseline["average_r"],
        "baseline_net_r": baseline["net_r"],
        "stress_profit_factor": stress["profit_factor"],
        "average_stress_r": stress["average_r"],
        "stress_net_r": stress["net_r"],
        "maximum_closed_drawdown_r": stress["maximum_closed_drawdown_r"],
    }


def _raw_train_gates(metrics: Mapping[str, Any], gate: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "minimum_trades": int(metrics["trades"]) >= int(gate["minimum_trades"]),
        "baseline_profit_factor": float(metrics["baseline_profit_factor"] or 0.0) >= float(gate["minimum_baseline_profit_factor"]),
        "stress_profit_factor": float(metrics["stress_profit_factor"] or 0.0) >= float(gate["minimum_stress_profit_factor"]),
        "average_stress_r": float(metrics["average_stress_r"]) >= float(gate["minimum_average_stress_r"]),
    }


def _apply_policy(
    rows: Sequence[Mapping[str, Any]],
    scores: Sequence[float],
    train_scores: Sequence[float],
    policy: Mapping[str, Any],
    selection: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], float, bool]:
    if policy["kind"] == "DETERMINISTIC_ALL":
        cutoff = -math.inf
        return _portfolio_select(rows, np.zeros(len(rows)), cutoff, selection), cutoff, False
    cutoff = _top_fraction_cutoff(train_scores, float(policy["train_top_fraction"]))
    return _portfolio_select(rows, scores, cutoff, selection), cutoff, True


def _apply_frozen_policy(
    rows: Sequence[Mapping[str, Any]],
    scores: Sequence[float],
    policy: Mapping[str, Any],
    cutoff: float,
    selection: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], float, bool]:
    if policy["kind"] == "DETERMINISTIC_ALL":
        return _portfolio_select(rows, np.zeros(len(rows)), -math.inf, selection), -math.inf, False
    return _portfolio_select(rows, scores, cutoff, selection), cutoff, True


def _classification(
    raw_pass: bool,
    chosen: Mapping[str, Any] | None,
    internal: Mapping[str, Any] | None,
    exam: Mapping[str, Any] | None,
) -> str:
    if not raw_pass:
        return "DUKASCOPY_M15_RANGE_ROTATION_TRAIN_REJECTED"
    if chosen is None:
        return "DUKASCOPY_M15_RANGE_ROTATION_NO_VALIDATION_SURVIVOR"
    if not internal or not internal["passes"]:
        return "DUKASCOPY_M15_RANGE_ROTATION_INTERNAL_TEST_REJECTED"
    if not exam or not exam["passes"]:
        return "DUKASCOPY_M15_RANGE_ROTATION_EXAM_REJECTED"
    return "DUKASCOPY_M15_RANGE_ROTATION_RESEARCH_SURVIVOR"


def _source_days(frame: pd.DataFrame, start: str, end: str) -> int:
    lo, hi = _parse_utc_ms(start), _parse_utc_ms(end)
    selected = frame[(frame["timestamp_ms"] >= lo) & (frame["timestamp_ms"] < hi)]
    return len({_iso_ms(int(value))[:10] for value in selected["timestamp_ms"]})


def _flatten(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "policy_id": row["policy_id"],
            "policy_kind": row["policy_kind"],
            "train_score_cutoff": row["train_score_cutoff"],
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
    raw = payload["raw_train_metrics"]
    lines = [
        "# A3 ML Dukascopy M15 Range Rotation V1",
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
    if contract.get("schema_version") != "a3_ml_dukascopy_m15_range_rotation_v1":
        raise ValueError("unexpected M15 range-rotation contract")
    if contract.get("policies") != [
        {"policy_id": "RAW_ALL", "kind": "DETERMINISTIC_ALL"},
        {"policy_id": "ML_TOP_60", "kind": "MODEL_TOP_FRACTION", "train_top_fraction": 0.60},
        {"policy_id": "ML_TOP_45", "kind": "MODEL_TOP_FRACTION", "train_top_fraction": 0.45},
        {"policy_id": "ML_TOP_30", "kind": "MODEL_TOP_FRACTION", "train_top_fraction": 0.30},
    ]:
        raise ValueError("policy set changed")
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
    if not authorization.get("research_only"):
        raise ValueError("campaign must remain research only")
    execution = contract.get("execution", {})
    if execution.get("same_bar_collision_policy") != "STOP_FIRST":
        raise ValueError("collision policy changed")
    if contract.get("model", {}).get("random_state") != 20260716:
        raise ValueError("model seed changed")


def _iso_ms(value: int) -> str:
    return datetime.fromtimestamp(value / 1000, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")

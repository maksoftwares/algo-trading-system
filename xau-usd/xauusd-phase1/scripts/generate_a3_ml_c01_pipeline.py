from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import sys
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


DEFAULT_ACCOUNT_SCOPES = ("1025742", "1033030", "1033669")
ACCOUNT_LABELS = {
    "1025742": "A1",
    "1033030": "A2",
    "1033669": "A3",
}
SYMBOL = "XAUUSD"
BASE_FAMILY = "breakout_retest"
RAW_CANDIDATE_ID = "B0_RAW_ALL_SESSION"
MAX_HOLD_ACTIVE_M5_BARS = 288
PRIMARY_HORIZON = timedelta(hours=24)
EMBARGO = PRIMARY_HORIZON + timedelta(minutes=5)
OUTER_FOLDS = 5
CALIBRATION_TAIL_FRACTION = 0.20

DEFAULT_DECISIONS_CSV = (
    Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_OFFLINE_DISCOVERY_DECISIONS_2026_06_18.csv"
)
DEFAULT_TRADES_CSV = Path("outputs") / "reports" / "A3_SIGNAL_QUALITY_OFFLINE_DISCOVERY_TRADES_2026_06_18.csv"
DEFAULT_BARS_DIR = Path("outputs") / "reports" / "m5_replay_bars"
DEFAULT_FEATURE_REGISTRY = Path("docs") / "A3_ML_FEATURE_REGISTRY_V1.csv"
DEFAULT_DATA_AUDIT_JSON = Path("outputs") / "reports" / "A3_ML_C01_DATA_AUDIT.json"
DEFAULT_SNAPSHOT_CSV = Path("outputs") / "reports" / "A3_ML_C01_SNAPSHOT_ROWS.csv"
DEFAULT_FEATURE_MATRIX_CSV = Path("outputs") / "reports" / "A3_ML_C01_FEATURE_MATRIX.csv"
DEFAULT_OFFLINE_REPORT_JSON = Path("outputs") / "reports" / "A3_ML_OFFLINE_REPORT.json"
DEFAULT_OFFLINE_SCORES_CSV = Path("outputs") / "reports" / "a3_ml_offline_scores.csv"

NON_TRAINABLE_LABEL_STATUSES = {
    "CANCELLED_NO_FRESH_TICK",
    "DATA_UNRESOLVED_TIMEOUT",
    "EXECUTION_AMBIGUITY",
    "DATA_UNRESOLVED",
    "OPTIMISTIC_DIAGNOSTIC_ONLY",
}

PROHIBITED_FEATURE_COLUMNS = {
    "final_r",
    "final_r_if_raw",
    "pnl",
    "pnl_aed",
    "profit_aed",
    "mfe",
    "mfe_r",
    "mae",
    "mae_r",
    "exit_reason",
    "exit_source",
    "exit_time",
    "exit_price",
    "y_win_expected",
    "y_net_R_expected",
    "y_win_p95_stress",
    "y_net_R_p95_stress",
    "y_outcome",
    "y_loss_class",
    "y_MFE_R",
    "y_MAE_R",
}


@dataclass(frozen=True)
class C01PipelineOutput:
    status: str
    data_audit_json: Path
    data_audit_md: Path
    snapshot_csv: Path
    feature_matrix_csv: Path
    offline_report_json: Path
    offline_report_md: Path
    offline_scores_csv: Path


@dataclass(frozen=True)
class SignalParts:
    account_scope: str
    symbol: str
    base_family: str
    direction: str
    break_bar_time_utc: datetime
    retest_bar_time_utc: datetime
    confirmation_bar_time_utc: datetime
    normalized_level_price: float


def generate_a3_ml_c01_pipeline(
    root: Path,
    decisions_csv: Path | None = None,
    trades_csv: Path | None = None,
    bars_dir: Path | None = None,
    feature_registry_csv: Path | None = None,
    data_audit_json: Path | None = None,
    account_scopes: tuple[str, ...] | list[str] | None = None,
) -> C01PipelineOutput:
    root = root.resolve()
    account_scopes = _normalize_account_scopes(account_scopes)
    contract_scope = _contract_scope(root)
    allowed_families = contract_scope["active_families"]
    decisions_csv = (decisions_csv or root / DEFAULT_DECISIONS_CSV).resolve()
    trades_csv = (trades_csv or root / DEFAULT_TRADES_CSV).resolve()
    bars_dir = (bars_dir or root / DEFAULT_BARS_DIR).resolve()
    feature_registry_csv = (feature_registry_csv or root / DEFAULT_FEATURE_REGISTRY).resolve()
    data_audit_json = (data_audit_json or root / DEFAULT_DATA_AUDIT_JSON).resolve()
    data_audit_md = data_audit_json.with_suffix(".md")
    snapshot_csv = data_audit_json.with_name(DEFAULT_SNAPSHOT_CSV.name)
    feature_matrix_csv = data_audit_json.with_name(DEFAULT_FEATURE_MATRIX_CSV.name)
    offline_report_json = data_audit_json.with_name(DEFAULT_OFFLINE_REPORT_JSON.name)
    offline_report_md = offline_report_json.with_suffix(".md")
    offline_scores_csv = data_audit_json.with_name(DEFAULT_OFFLINE_SCORES_CSV.name)
    data_audit_json.parent.mkdir(parents=True, exist_ok=True)

    feature_registry = _load_feature_registry(feature_registry_csv)
    bars = _load_bar_bundle(bars_dir)
    source_decisions = _read_csv(decisions_csv)
    source_trades = _read_csv(trades_csv) if trades_csv.exists() else []
    trades_by_signal = {
        (row.get("signal_id", ""), row.get("candidate_id", "")): row
        for row in source_trades
        if row.get("signal_id") and row.get("candidate_id")
    }
    slippage = _slippage_adequacy(source_trades, account_scopes, allowed_families)
    label_promotion = _label_promotion_scope(root, slippage["slippage_model_status"])

    raw_rows, rejected_rows, parse_errors = _scope_source_rows(source_decisions, account_scopes, allowed_families)
    exact_rows = _exact_deduplicate(raw_rows)
    snapshot_rows = [
        _build_snapshot_row(row, trades_by_signal.get((row["signal_id"], row["candidate_id"]), {}), bars, label_promotion)
        for row in exact_rows
    ]
    _assign_setup_groups(snapshot_rows, bars)
    leakage_violations = _leakage_violations(snapshot_rows)
    feature_columns = [row["feature_name"] for row in feature_registry if row["priority"].isdigit()]
    feature_availability = _feature_availability(snapshot_rows, feature_columns)
    fold_diagnostics = _fold_diagnostics(snapshot_rows)
    global_feature_budget, binding_fold = _global_feature_budget(fold_diagnostics)
    dataset_status = _dataset_status(
        leakage_violations=leakage_violations,
        global_feature_budget=global_feature_budget,
        slippage_status=slippage["slippage_model_status"],
    )
    selected_features = feature_columns[:global_feature_budget] if dataset_status != "PIPELINE_ONLY" else []
    training_decision = _training_decision(dataset_status, global_feature_budget, selected_features)

    payload: dict[str, Any] = {
        "status": dataset_status,
        "created_at_utc": _utc_now(),
        "authority": (
            "C01 Python ML pipeline bootstrap only for configured A1/A2/A3 account scopes. "
            "It reads frozen local data and writes offline shadow artifacts. "
            "It does not touch MT5 runtime, orders, positions, profiles, charts, presets, or running EAs."
        ),
        "scope": {
            "account_scopes": list(account_scopes),
            "account_labels": {account: ACCOUNT_LABELS.get(account, "UNKNOWN") for account in account_scopes},
            "symbol": SYMBOL,
            "base_family": BASE_FAMILY,
            "allowed_families": list(allowed_families),
            "contract_scope": contract_scope["scope_name"],
            "contract_expansion_authorized": contract_scope["contract_expansion_authorized"],
            "raw_candidate_id": RAW_CANDIDATE_ID,
        },
        "label_promotion_scope": label_promotion,
        "source_manifest": [
            _file_manifest(decisions_csv),
            _file_manifest(trades_csv),
            _file_manifest(feature_registry_csv),
            _file_manifest(bars_dir / "XAUUSD_M5_20260601_to_latest.csv"),
            _file_manifest(bars_dir / "XAUUSD_H1_20260601_to_latest.csv"),
            _file_manifest(bars_dir / "XAUUSD_D1_20260601_to_latest.csv"),
        ],
        "raw_source_row_counts": {
            "decisions_rows": len(source_decisions),
            "trades_rows": len(source_trades),
            "scoped_raw_rows": len(raw_rows),
            "rejected_rows": len(rejected_rows),
            "parse_errors": len(parse_errors),
            "exact_unique_signals": len(exact_rows),
            "snapshot_rows": len(snapshot_rows),
        },
        "per_account_counts": _per_account_counts(snapshot_rows, account_scopes),
        "exact_signal_counts": _counter(snapshot_rows, "direction"),
        "fuzzy_setup_group_counts": {
            "groups": len({row["setup_group_id"] for row in snapshot_rows}),
            "max_group_size": max(Counter(row["setup_group_id"] for row in snapshot_rows).values(), default=0),
        },
        "labeled_and_trainable_setup_groups": {
            "diagnostic_labeled_groups": len(
                {row["setup_group_id"] for row in snapshot_rows if row["label_status"] == "OPTIMISTIC_DIAGNOSTIC_ONLY"}
            ),
            "candidate_trainable_groups": len(
                {row["setup_group_id"] for row in snapshot_rows if _is_candidate_trainable(row)}
            ),
        },
        "class_balance": _class_balance(snapshot_rows),
        "direction_balance": _counter(snapshot_rows, "direction"),
        "regime_balance": _counter(snapshot_rows, "regime"),
        "event_duration_distribution": _duration_distribution(snapshot_rows),
        "missingness": _missingness(snapshot_rows),
        "unresolved_label_counts": _counter(snapshot_rows, "label_status"),
        "duplicate_and_fuzzy_duplicate_rates": _duplicate_rates(raw_rows, exact_rows, snapshot_rows),
        "slippage_adequacy_status": slippage,
        "feature_availability": feature_availability,
        "selected_features": selected_features,
        "leakage_violations": leakage_violations,
        "fold_diagnostics": fold_diagnostics,
        "minority_events_min": min(
            [fold["minority_events_fit_fold"] for fold in fold_diagnostics],
            default=0,
        ),
        "global_feature_budget": global_feature_budget,
        "budget_binding_fold_id": binding_fold,
        "training_decision": training_decision,
        "outputs": {
            "data_audit_json": str(data_audit_json),
            "data_audit_md": str(data_audit_md),
            "snapshot_csv": str(snapshot_csv),
            "feature_matrix_csv": str(feature_matrix_csv),
            "offline_report_json": str(offline_report_json),
            "offline_report_md": str(offline_report_md),
            "offline_scores_csv": str(offline_scores_csv),
        },
        "notes": [
            "Current labels are discovery labels and are marked OPTIMISTIC_DIAGNOSTIC_ONLY until tick labels and an adequate slippage model exist.",
            "Label promotion is reviewer gated by config/ml/a3_ml_label_promotion.json and defaults to false.",
            "No supervised candidate training is allowed while dataset_status is PIPELINE_ONLY.",
            "Blocked raw signals are retained in the snapshot, matching the data contract's source-universe rule.",
            "Feature columns are computed from completed bars only and the feature matrix excludes prohibited label/outcome fields.",
        ],
    }

    _write_csv(snapshot_csv, snapshot_rows, _snapshot_fields(feature_columns))
    _write_csv(feature_matrix_csv, _feature_matrix_rows(snapshot_rows, feature_columns), _feature_matrix_fields(feature_columns))
    _write_offline_scores(offline_scores_csv, snapshot_rows, dataset_status, training_decision)
    data_audit_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    data_audit_md.write_text(_render_data_audit_md(payload), encoding="utf-8")
    offline_payload = _offline_payload(payload)
    offline_report_json.write_text(json.dumps(offline_payload, indent=2), encoding="utf-8")
    offline_report_md.write_text(_render_offline_report_md(offline_payload), encoding="utf-8")

    return C01PipelineOutput(
        status=dataset_status,
        data_audit_json=data_audit_json,
        data_audit_md=data_audit_md,
        snapshot_csv=snapshot_csv,
        feature_matrix_csv=feature_matrix_csv,
        offline_report_json=offline_report_json,
        offline_report_md=offline_report_md,
        offline_scores_csv=offline_scores_csv,
    )


def _scope_source_rows(
    rows: list[dict[str, str]],
    account_scopes: tuple[str, ...],
    allowed_families: tuple[str, ...],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    scoped: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    parse_errors: list[str] = []
    for row in rows:
        try:
            parts = _parse_signal_id(row.get("signal_id", ""))
        except ValueError as exc:
            rejected.append(row)
            parse_errors.append(str(exc))
            continue
        keep = (
            row.get("candidate_id") == RAW_CANDIDATE_ID
            and parts.account_scope in account_scopes
            and parts.symbol == SYMBOL
            and parts.base_family in allowed_families
        )
        if keep:
            scoped.append(row)
        else:
            rejected.append(row)
    return scoped, rejected, parse_errors


def _exact_deduplicate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for row in rows:
        exact_id = _exact_signal_id(_parse_signal_id(row["signal_id"]))
        previous = by_id.get(exact_id)
        if previous is None or _parse_dt(row.get("decision_time", "")) < _parse_dt(previous.get("decision_time", "")):
            by_id[exact_id] = row
    return sorted(by_id.values(), key=lambda row: _parse_dt(row.get("decision_time", "")))


def _build_snapshot_row(
    source: dict[str, str],
    trade: dict[str, str],
    bars: dict[str, list[dict[str, Any]]],
    label_promotion: dict[str, Any],
) -> dict[str, Any]:
    parts = _parse_signal_id(source["signal_id"])
    decision_time = _parse_dt(source["decision_time"])
    confirmation_complete = parts.confirmation_bar_time_utc + timedelta(minutes=5)
    entry_eligible = decision_time + timedelta(seconds=1)
    label_end = _parse_dt(trade.get("exit_time", "")) if trade.get("exit_time") else decision_time + PRIMARY_HORIZON
    final_r = _float_or_none(source.get("final_r_if_raw"))
    y_win = 1 if final_r is not None and final_r > 0 else 0
    y_outcome = _outcome_from_r(final_r)
    label_decision = _label_promotion_for_row(source, label_promotion)
    row: dict[str, Any] = {
        "account_scope": parts.account_scope,
        "account_label": ACCOUNT_LABELS.get(parts.account_scope, "UNKNOWN"),
        "symbol": SYMBOL,
        "base_family": parts.base_family,
        "candidate_id": source.get("candidate_id", ""),
        "source_signal_id": source.get("signal_id", ""),
        "exact_signal_id": _exact_signal_id(parts),
        "setup_group_id": "",
        "direction": parts.direction,
        "direction_sign": 1 if parts.direction == "LONG" else -1,
        "break_bar_time_utc": _iso(parts.break_bar_time_utc),
        "retest_bar_time_utc": _iso(parts.retest_bar_time_utc),
        "confirmation_bar_time_utc": _iso(parts.confirmation_bar_time_utc),
        "feature_time_utc": _iso(confirmation_complete),
        "decision_time_utc": _iso(decision_time),
        "entry_eligible_from_utc": _iso(entry_eligible),
        "label_end_time_utc": _iso(label_end),
        "normalized_level_price": _format_float(parts.normalized_level_price),
        "opened": source.get("opened", ""),
        "reason": source.get("reason", ""),
        "session_bucket": source.get("session_bucket", ""),
        "regime": _regime_at(decision_time, bars),
        "y_win_expected": y_win,
        "y_net_R_expected": _format_optional(final_r),
        "y_win_p95_stress": y_win,
        "y_net_R_p95_stress": _format_optional(final_r),
        "y_outcome": y_outcome,
        "y_loss_class": trade.get("loss_class", "WIN" if y_win else "UNSPECIFIED_LOSS"),
        "y_MFE_R": "",
        "y_MAE_R": "",
        "y_holding_seconds": int(max((label_end - entry_eligible).total_seconds(), 0)),
        "y_holding_active_m5_bars": min(MAX_HOLD_ACTIVE_M5_BARS, max(math.ceil((label_end - entry_eligible).total_seconds() / 300), 0)),
        "label_status": label_decision["label_status"],
        "candidate_trainable": "true" if label_decision["candidate_trainable"] else "false",
        "slippage_model_status": label_promotion["slippage_model_status"],
        "row_status": label_decision["row_status"],
    }
    row.update(_features_for_signal(parts, decision_time, source, bars))
    return row


def _label_promotion_for_row(source: dict[str, str], label_promotion: dict[str, Any]) -> dict[str, Any]:
    if not label_promotion["label_promotion_authorized"]:
        return {
            "label_status": "OPTIMISTIC_DIAGNOSTIC_ONLY",
            "candidate_trainable": False,
            "row_status": "DISCOVERY_PIPELINE_ROW",
        }
    if label_promotion["require_slippage_adequate"] and label_promotion["slippage_model_status"] != "ADEQUATE":
        return {
            "label_status": "OPTIMISTIC_DIAGNOSTIC_ONLY",
            "candidate_trainable": False,
            "row_status": "PROMOTION_BLOCKED_SLIPPAGE",
        }
    source_status = str(source.get("label_status", "")).strip().upper()
    if source_status in label_promotion["allowed_label_statuses"]:
        return {
            "label_status": source_status,
            "candidate_trainable": True,
            "row_status": "REVIEWER_PROMOTED_TRAINABLE_ROW",
        }
    if source_status:
        return {
            "label_status": source_status,
            "candidate_trainable": False,
            "row_status": "LABEL_STATUS_NOT_TRAINABLE",
        }
    return {
        "label_status": "OPTIMISTIC_DIAGNOSTIC_ONLY",
        "candidate_trainable": False,
        "row_status": "PROMOTION_BLOCKED_MISSING_SOURCE_LABEL",
    }


def _features_for_signal(
    parts: SignalParts,
    decision_time: datetime,
    source: dict[str, str],
    bars: dict[str, list[dict[str, Any]]],
) -> dict[str, str]:
    features = {
        "h1_ema20_slope_aligned_atr": "",
        "retest_penetration_atr": "",
        "confirmation_body_ratio": "",
        "cost_R": "",
        "confirmation_close_location_aligned": "",
        "break_distance_atr": "",
        "m15_ema20_slope_aligned_atr": "",
        "bars_break_to_retest_scaled": "",
        "impulse_alignment_12": "",
        "price_h1_ema20_distance_aligned_atr": "",
        "m5_atr_percentile_trailing_20d": "",
        "spread_percentile_session_trailing_20d": "",
        "d1_trend_score_aligned": "",
        "range_compression_ratio_20": "",
        "tick_volume_ratio_20": "",
        "minutes_from_session_start_scaled": "",
    }
    direction_sign = 1 if parts.direction == "LONG" else -1
    m5 = bars.get("M5", [])
    m15 = bars.get("M15", [])
    h1 = bars.get("H1", [])
    d1 = bars.get("D1", [])
    m5_idx = _completed_index(m5, decision_time)
    m15_idx = _completed_index(m15, decision_time)
    h1_idx = _completed_index(h1, decision_time)
    d1_idx = _completed_index(d1, decision_time)
    confirmation_bar = _bar_by_start(m5, parts.confirmation_bar_time_utc)
    break_bar = _bar_by_start(m5, parts.break_bar_time_utc)

    if h1_idx is not None and h1_idx >= 3:
        value = _aligned_ema_slope(h1, h1_idx, 3, direction_sign)
        features["h1_ema20_slope_aligned_atr"] = _format_optional(value)
        distance = _price_ema_distance(m5, m5_idx, h1, h1_idx, direction_sign)
        features["price_h1_ema20_distance_aligned_atr"] = _format_optional(distance)

    if confirmation_bar:
        ratio = _body_ratio(confirmation_bar)
        features["confirmation_body_ratio"] = _format_optional(ratio)
        location = _close_location(confirmation_bar, parts.direction)
        features["confirmation_close_location_aligned"] = _format_optional(location)

    decision_cost = _decision_time_cost_r(source)
    if decision_cost is not None:
        features["cost_R"] = _format_optional(decision_cost)

    if break_bar:
        atr = _float_or_none(str(break_bar.get("atr14", "")))
        if atr and atr > 0:
            features["break_distance_atr"] = _format_optional(abs(float(break_bar["close"]) - parts.normalized_level_price) / atr)

    if m15_idx is not None and m15_idx >= 3:
        features["m15_ema20_slope_aligned_atr"] = _format_optional(_aligned_ema_slope(m15, m15_idx, 3, direction_sign))

    bars_break_to_retest = max((parts.retest_bar_time_utc - parts.break_bar_time_utc).total_seconds() / 300, 0)
    features["bars_break_to_retest_scaled"] = _format_optional(min(bars_break_to_retest, 20) / 20)

    if m5_idx is not None and m5_idx >= 12:
        atr = _float_or_none(str(m5[m5_idx].get("atr14", "")))
        if atr and atr > 0:
            impulse = direction_sign * (float(m5[m5_idx]["close"]) - float(m5[m5_idx - 12]["close"])) / atr
            features["impulse_alignment_12"] = _format_optional(impulse)

    if m5_idx is not None:
        current_atr = _float_or_none(str(m5[m5_idx].get("atr14", "")))
        prior_atrs = [
            _float_or_none(str(row.get("atr14", "")))
            for row in m5[max(0, m5_idx - 5760) : m5_idx]
        ]
        prior_atrs = [value for value in prior_atrs if value is not None]
        if current_atr is not None and len(prior_atrs) >= 20:
            features["m5_atr_percentile_trailing_20d"] = _format_optional(_percentile(current_atr, prior_atrs))
        prior_same_session_spreads = [
            _float_or_none(str(row.get("spread", "")))
            for row in m5[max(0, m5_idx - 5760) : m5_idx]
            if _session_bucket(row["bar_start_utc"]) == _session_bucket(decision_time)
        ]
        prior_same_session_spreads = [value for value in prior_same_session_spreads if value is not None]
        current_spread = _float_or_none(str(m5[m5_idx].get("spread", "")))
        if current_spread is not None and len(prior_same_session_spreads) >= 20:
            features["spread_percentile_session_trailing_20d"] = _format_optional(
                _percentile(current_spread, prior_same_session_spreads)
            )
        features["range_compression_ratio_20"] = _format_optional(_range_compression(m5, m5_idx))
        features["tick_volume_ratio_20"] = _format_optional(_tick_volume_ratio(m5, m5_idx))

    if d1_idx is not None and d1_idx >= 5:
        features["d1_trend_score_aligned"] = _format_optional(_aligned_ema_slope(d1, d1_idx, 5, direction_sign))

    features["minutes_from_session_start_scaled"] = _format_optional(_minutes_from_session_start_scaled(decision_time))
    return features


def _assign_setup_groups(rows: list[dict[str, Any]], bars: dict[str, list[dict[str, Any]]]) -> None:
    if not rows:
        return
    rows.sort(key=lambda row: _parse_dt(row["decision_time_utc"]))
    graph: dict[int, set[int]] = defaultdict(set)
    for i, left in enumerate(rows):
        for j in range(i + 1, len(rows)):
            right = rows[j]
            if (_parse_dt(right["decision_time_utc"]) - _parse_dt(left["decision_time_utc"])) > timedelta(minutes=10):
                break
            if _fuzzy_edge(left, right, bars):
                graph[i].add(j)
                graph[j].add(i)

    visited: set[int] = set()
    group_number = 1
    for index in range(len(rows)):
        if index in visited:
            continue
        stack = [index]
        component: list[int] = []
        visited.add(index)
        while stack:
            current = stack.pop()
            component.append(current)
            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        component.sort(key=lambda idx: _parse_dt(rows[idx]["decision_time_utc"]))
        current_start: datetime | None = None
        for idx in component:
            decision = _parse_dt(rows[idx]["decision_time_utc"])
            if current_start is None or decision - current_start > timedelta(minutes=20):
                group_id = f"A3_ML_C01_G{group_number:05d}"
                group_number += 1
                current_start = decision
            rows[idx]["setup_group_id"] = group_id


def _fuzzy_edge(left: dict[str, Any], right: dict[str, Any], bars: dict[str, list[dict[str, Any]]]) -> bool:
    if (
        left["account_scope"] != right["account_scope"]
        or left["symbol"] != right["symbol"]
        or left["base_family"] != right["base_family"]
        or left["direction"] != right["direction"]
    ):
        return False
    left_decision = _parse_dt(left["decision_time_utc"])
    right_decision = _parse_dt(right["decision_time_utc"])
    if abs((right_decision - left_decision).total_seconds()) > 600:
        return False
    left_level = _float_or_none(str(left["normalized_level_price"]))
    right_level = _float_or_none(str(right["normalized_level_price"]))
    if left_level is None or right_level is None:
        return False
    m5_idx = _completed_index(bars.get("M5", []), left_decision)
    atr = None if m5_idx is None else _float_or_none(str(bars["M5"][m5_idx].get("atr14", "")))
    if atr is None or atr <= 0:
        return False
    if abs(left_level - right_level) > 0.10 * atr:
        return False
    left_start = _parse_dt(left["break_bar_time_utc"])
    left_end = _parse_dt(left["retest_bar_time_utc"])
    right_start = _parse_dt(right["break_bar_time_utc"])
    right_end = _parse_dt(right["retest_bar_time_utc"])
    return max(left_start, right_start) <= min(left_end, right_end)


def _fold_diagnostics(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups = _groups_by_time(rows)
    blocks = _chronological_blocks(groups, OUTER_FOLDS + 1)
    diagnostics: list[dict[str, Any]] = []
    if len(blocks) < OUTER_FOLDS + 1:
        return diagnostics
    group_rows = _rows_by_group(rows)
    for fold_index in range(OUTER_FOLDS):
        train_groups_before = [group for block in blocks[: fold_index + 1] for group in block]
        test_groups = blocks[fold_index + 1]
        train_rows_before = [row for group in train_groups_before for row in group_rows[group]]
        test_rows = [row for group in test_groups for row in group_rows[group]]
        purged_groups = _purged_groups(train_groups_before, test_rows, group_rows)
        embargo_groups = _embargo_groups(train_groups_before, test_rows, group_rows, purged_groups)
        eligible_groups = [
            group
            for group in train_groups_before
            if group not in purged_groups and group not in embargo_groups and _group_candidate_trainable(group_rows[group])
        ]
        unresolved_groups = [
            group
            for group in train_groups_before
            if group not in purged_groups and group not in embargo_groups and not _group_candidate_trainable(group_rows[group])
        ]
        calibration_count = math.ceil(len(eligible_groups) * CALIBRATION_TAIL_FRACTION) if eligible_groups else 0
        calibration_count = min(calibration_count, max(len(eligible_groups) - 1, 0))
        calibration_groups = eligible_groups[-calibration_count:] if calibration_count else []
        model_fit_groups = eligible_groups[:-calibration_count] if calibration_count else eligible_groups
        calibration_rows = [row for group in calibration_groups for row in group_rows[group]]
        model_fit_rows = [row for group in model_fit_groups for row in group_rows[group]]
        model_fit_positive = sum(1 for row in model_fit_rows if int(row["y_win_expected"]) == 1)
        model_fit_negative = sum(1 for row in model_fit_rows if int(row["y_win_expected"]) == 0)
        minority = min(model_fit_positive, model_fit_negative)
        train_start, train_end = _time_bounds(train_rows_before)
        test_start, test_end = _time_bounds(test_rows)
        diagnostics.append(
            {
                "fold_id": f"outer_{fold_index + 1}",
                "train_start_utc": _iso(train_start) if train_start else "",
                "train_end_utc": _iso(train_end) if train_end else "",
                "test_start_utc": _iso(test_start) if test_start else "",
                "test_end_utc": _iso(test_end) if test_end else "",
                "pre_grouping_rows": len(train_rows_before),
                "exact_unique_signals": len({row["exact_signal_id"] for row in train_rows_before}),
                "fuzzy_setup_groups": len(set(train_groups_before)),
                "outer_train_groups_before_purge": len(train_groups_before),
                "purged_overlap_groups": len(purged_groups),
                "purge_loss_pct": round(len(purged_groups) / len(train_groups_before), 6) if train_groups_before else 0.0,
                "embargo_excluded_groups": len(embargo_groups),
                "unresolved_label_groups": len(unresolved_groups),
                "eligible_outer_train_groups": len(eligible_groups),
                "calibration_groups": len(calibration_groups),
                "calibration_positive": sum(1 for row in calibration_rows if int(row["y_win_expected"]) == 1),
                "calibration_negative": sum(1 for row in calibration_rows if int(row["y_win_expected"]) == 0),
                "model_fit_groups": len(model_fit_groups),
                "model_fit_positive": model_fit_positive,
                "model_fit_negative": model_fit_negative,
                "minority_events_fit_fold": minority,
                "feature_budget_fold": min(16, minority // 15),
            }
        )
    return diagnostics


def _groups_by_time(rows: list[dict[str, Any]]) -> list[str]:
    first_time: dict[str, datetime] = {}
    for row in rows:
        group = str(row["setup_group_id"])
        first_time[group] = min(first_time.get(group, _parse_dt(row["decision_time_utc"])), _parse_dt(row["decision_time_utc"]))
    return [group for group, _ in sorted(first_time.items(), key=lambda item: item[1])]


def _rows_by_group(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["setup_group_id"])].append(row)
    return grouped


def _chronological_blocks(groups: list[str], block_count: int) -> list[list[str]]:
    if not groups:
        return []
    blocks: list[list[str]] = []
    total = len(groups)
    for block_index in range(block_count):
        start = round(block_index * total / block_count)
        end = round((block_index + 1) * total / block_count)
        blocks.append(groups[start:end])
    return blocks


def _purged_groups(
    train_groups: list[str],
    test_rows: list[dict[str, Any]],
    group_rows: dict[str, list[dict[str, Any]]],
) -> set[str]:
    test_intervals = [(_parse_dt(row["entry_eligible_from_utc"]), _parse_dt(row["label_end_time_utc"])) for row in test_rows]
    purged: set[str] = set()
    for group in train_groups:
        for row in group_rows[group]:
            row_interval = (_parse_dt(row["entry_eligible_from_utc"]), _parse_dt(row["label_end_time_utc"]))
            if any(_intervals_overlap(row_interval, test_interval) for test_interval in test_intervals):
                purged.add(group)
                break
    return purged


def _embargo_groups(
    train_groups: list[str],
    test_rows: list[dict[str, Any]],
    group_rows: dict[str, list[dict[str, Any]]],
    purged_groups: set[str],
) -> set[str]:
    if not test_rows:
        return set()
    _, test_end = _time_bounds(test_rows)
    assert test_end is not None
    embargo_end = test_end + EMBARGO
    embargoed: set[str] = set()
    for group in train_groups:
        if group in purged_groups:
            continue
        for row in group_rows[group]:
            decision = _parse_dt(row["decision_time_utc"])
            if test_end < decision <= embargo_end:
                embargoed.add(group)
                break
    return embargoed


def _group_candidate_trainable(rows: list[dict[str, Any]]) -> bool:
    return any(_is_candidate_trainable(row) for row in rows)


def _is_candidate_trainable(row: dict[str, Any]) -> bool:
    return str(row.get("candidate_trainable", "")).lower() == "true" and row.get("label_status") not in NON_TRAINABLE_LABEL_STATUSES


def _global_feature_budget(folds: list[dict[str, Any]]) -> tuple[int, str]:
    if not folds:
        return 0, ""
    binding = min(folds, key=lambda fold: fold["minority_events_fit_fold"])
    return min(16, binding["minority_events_fit_fold"] // 15), binding["fold_id"]


def _dataset_status(*, leakage_violations: list[dict[str, str]], global_feature_budget: int, slippage_status: str) -> str:
    if leakage_violations:
        return "DATA_LEAKAGE_FAIL"
    if global_feature_budget < 5:
        return "PIPELINE_ONLY"
    if slippage_status != "ADEQUATE":
        return "EXPLORATORY_MODEL"
    return "CANDIDATE_MODEL"


def _training_decision(dataset_status: str, global_feature_budget: int, selected_features: list[str]) -> dict[str, Any]:
    if dataset_status == "DATA_LEAKAGE_FAIL":
        return {
            "supervised_training_allowed": False,
            "model_family": "",
            "reason": "DATA_LEAKAGE_FAIL",
        }
    if dataset_status == "PIPELINE_ONLY":
        return {
            "supervised_training_allowed": False,
            "model_family": "",
            "reason": f"global_feature_budget={global_feature_budget} is below the contract minimum of 5",
        }
    return {
        "supervised_training_allowed": True,
        "model_family": "M0_BASE_RATE_FIRST",
        "reason": "Eligible only for offline research; live authority remains disabled.",
        "selected_features": selected_features,
    }


def _leakage_violations(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for row in rows:
        feature_time = _parse_dt(row["feature_time_utc"])
        decision_time = _parse_dt(row["decision_time_utc"])
        entry_time = _parse_dt(row["entry_eligible_from_utc"])
        label_end = _parse_dt(row["label_end_time_utc"])
        if not (feature_time <= decision_time < entry_time <= label_end):
            violations.append(
                {
                    "source_signal_id": row["source_signal_id"],
                    "feature_time_utc": row["feature_time_utc"],
                    "decision_time_utc": row["decision_time_utc"],
                    "entry_eligible_from_utc": row["entry_eligible_from_utc"],
                    "label_end_time_utc": row["label_end_time_utc"],
                }
            )
    return violations


def _load_feature_registry(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return [
            {"priority": str(index + 1), "feature_name": name}
            for index, name in enumerate(
                [
                    "h1_ema20_slope_aligned_atr",
                    "retest_penetration_atr",
                    "confirmation_body_ratio",
                    "cost_R",
                    "confirmation_close_location_aligned",
                    "break_distance_atr",
                    "m15_ema20_slope_aligned_atr",
                    "bars_break_to_retest_scaled",
                    "impulse_alignment_12",
                    "price_h1_ema20_distance_aligned_atr",
                    "m5_atr_percentile_trailing_20d",
                    "spread_percentile_session_trailing_20d",
                    "d1_trend_score_aligned",
                    "range_compression_ratio_20",
                    "tick_volume_ratio_20",
                    "minutes_from_session_start_scaled",
                ]
            )
        ]
    return _read_csv(path)


def _load_bar_bundle(bars_dir: Path) -> dict[str, list[dict[str, Any]]]:
    m5 = _load_bars(bars_dir / "XAUUSD_M5_20260601_to_latest.csv")
    h1 = _load_bars(bars_dir / "XAUUSD_H1_20260601_to_latest.csv")
    d1 = _load_bars(bars_dir / "XAUUSD_D1_20260601_to_latest.csv")
    return {
        "M5": m5,
        "M15": _derive_m15_bars(m5),
        "H1": h1,
        "D1": d1,
    }


def _load_bars(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    bars = []
    for row in _read_csv(path):
        try:
            bars.append(
                {
                    "bar_start_utc": _parse_dt(row.get("bar_start_utc", "")),
                    "bar_end_utc": _parse_dt(row.get("bar_end_utc", "")),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "tick_volume": float(row.get("tick_volume", "0") or 0),
                    "spread": float(row.get("spread", "0") or 0),
                }
            )
        except (KeyError, ValueError):
            continue
    bars.sort(key=lambda row: row["bar_start_utc"])
    _add_indicators(bars)
    return bars


def _derive_m15_bars(m5: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
    for row in m5:
        start = row["bar_start_utc"].replace(minute=(row["bar_start_utc"].minute // 15) * 15, second=0, microsecond=0)
        grouped[start].append(row)
    bars: list[dict[str, Any]] = []
    for start, rows in sorted(grouped.items()):
        rows.sort(key=lambda row: row["bar_start_utc"])
        bars.append(
            {
                "bar_start_utc": start,
                "bar_end_utc": start + timedelta(minutes=15),
                "open": rows[0]["open"],
                "high": max(row["high"] for row in rows),
                "low": min(row["low"] for row in rows),
                "close": rows[-1]["close"],
                "tick_volume": sum(float(row.get("tick_volume", 0)) for row in rows),
                "spread": sum(float(row.get("spread", 0)) for row in rows) / len(rows),
            }
        )
    _add_indicators(bars)
    return bars


def _add_indicators(bars: list[dict[str, Any]]) -> None:
    alpha = 2 / (20 + 1)
    ema20: float | None = None
    true_ranges: list[float] = []
    previous_close: float | None = None
    for index, row in enumerate(bars):
        close = float(row["close"])
        high = float(row["high"])
        low = float(row["low"])
        ema20 = close if ema20 is None else alpha * close + (1 - alpha) * ema20
        row["ema20"] = ema20
        if previous_close is None:
            true_range = high - low
        else:
            true_range = max(high - low, abs(high - previous_close), abs(low - previous_close))
        true_ranges.append(true_range)
        if index >= 13:
            row["atr14"] = sum(true_ranges[index - 13 : index + 1]) / 14
        else:
            row["atr14"] = None
        previous_close = close


def _completed_index(bars: list[dict[str, Any]], timestamp: datetime) -> int | None:
    if not bars:
        return None
    end_times = [row["bar_end_utc"] for row in bars]
    index = bisect.bisect_right(end_times, timestamp) - 1
    return index if index >= 0 else None


def _bar_by_start(bars: list[dict[str, Any]], timestamp: datetime) -> dict[str, Any] | None:
    for row in bars:
        if row["bar_start_utc"] == timestamp:
            return row
    return None


def _aligned_ema_slope(bars: list[dict[str, Any]], index: int, lag: int, direction_sign: int) -> float | None:
    if index < lag:
        return None
    current = bars[index]
    previous = bars[index - lag]
    atr = _float_or_none(str(current.get("atr14", "")))
    if atr is None or atr <= 0:
        return None
    return direction_sign * (float(current["ema20"]) - float(previous["ema20"])) / atr


def _price_ema_distance(
    m5: list[dict[str, Any]],
    m5_idx: int | None,
    h1: list[dict[str, Any]],
    h1_idx: int,
    direction_sign: int,
) -> float | None:
    if m5_idx is None:
        return None
    atr = _float_or_none(str(h1[h1_idx].get("atr14", "")))
    if atr is None or atr <= 0:
        return None
    return direction_sign * (float(m5[m5_idx]["close"]) - float(h1[h1_idx]["ema20"])) / atr


def _body_ratio(bar: dict[str, Any]) -> float | None:
    rng = float(bar["high"]) - float(bar["low"])
    if rng <= 0:
        return None
    return abs(float(bar["close"]) - float(bar["open"])) / rng


def _close_location(bar: dict[str, Any], direction: str) -> float | None:
    rng = float(bar["high"]) - float(bar["low"])
    if rng <= 0:
        return None
    location = (float(bar["close"]) - float(bar["low"])) / rng
    return location if direction == "LONG" else 1 - location


def _percentile(value: float, prior_values: list[float]) -> float:
    sorted_values = sorted(prior_values)
    return bisect.bisect_right(sorted_values, value) / len(sorted_values)


def _range_compression(m5: list[dict[str, Any]], index: int) -> float | None:
    if index < 24:
        return None
    recent = [float(row["high"]) - float(row["low"]) for row in m5[index - 3 : index + 1]]
    baseline = [float(row["high"]) - float(row["low"]) for row in m5[index - 23 : index - 3]]
    baseline_mean = sum(baseline) / len(baseline)
    if baseline_mean <= 0:
        return None
    return (sum(recent) / len(recent)) / baseline_mean


def _tick_volume_ratio(m5: list[dict[str, Any]], index: int) -> float | None:
    if index < 20:
        return None
    baseline = [float(row.get("tick_volume", 0)) for row in m5[index - 20 : index]]
    baseline_mean = sum(baseline) / len(baseline)
    if baseline_mean <= 0:
        return None
    return float(m5[index].get("tick_volume", 0)) / baseline_mean


def _minutes_from_session_start_scaled(timestamp: datetime) -> float:
    minutes = timestamp.hour * 60 + timestamp.minute
    if 6 * 60 <= minutes < 12 * 60:
        return (minutes - 6 * 60) / (6 * 60)
    if 12 * 60 <= minutes < 16 * 60:
        return (minutes - 12 * 60) / (4 * 60)
    if 16 * 60 <= minutes < 20 * 60:
        return (minutes - 16 * 60) / (4 * 60)
    if minutes >= 20 * 60:
        return (minutes - 20 * 60) / (10 * 60)
    return (minutes + 4 * 60) / (10 * 60)


def _session_bucket(timestamp: datetime) -> str:
    minutes = timestamp.hour * 60 + timestamp.minute
    if 6 * 60 <= minutes < 12 * 60:
        return "Morning 06:00-11:59"
    if 12 * 60 <= minutes < 16 * 60:
        return "Afternoon 12:00-15:59"
    if 16 * 60 <= minutes < 20 * 60:
        return "Evening 16:00-19:59"
    return "Night 20:00-05:59"


def _regime_at(decision_time: datetime, bars: dict[str, list[dict[str, Any]]]) -> str:
    d1 = bars.get("D1", [])
    idx = _completed_index(d1, decision_time)
    if idx is None or idx < 5:
        return "UNKNOWN"
    score = _aligned_ema_slope(d1, idx, 5, 1)
    atr = _float_or_none(str(d1[idx].get("atr14", "")))
    if score is None or atr is None or atr <= 0:
        return "UNKNOWN"
    close = float(d1[idx]["close"])
    ema = float(d1[idx]["ema20"])
    if close > ema and score >= 0.25:
        return "RISING"
    if close < ema and score <= -0.25:
        return "FALLING"
    return "MIXED"


def _slippage_adequacy(
    trades: list[dict[str, str]],
    account_scopes: tuple[str, ...],
    allowed_families: tuple[str, ...],
) -> dict[str, Any]:
    scoped = []
    for row in trades:
        if row.get("candidate_id") != RAW_CANDIDATE_ID:
            continue
        try:
            parts = _parse_signal_id(row.get("signal_id", ""))
        except ValueError:
            continue
        if parts.account_scope in account_scopes and parts.symbol == SYMBOL and parts.base_family in allowed_families:
            scoped.append(row)
    entry_fills = len(scoped)
    sl_exits = sum(1 for row in scoped if row.get("outcome") == "LOSS")
    tp_exits = sum(1 for row in scoped if row.get("outcome") == "WIN")
    adequate = entry_fills >= 200 and sl_exits >= 100 and tp_exits >= 50
    by_account = {}
    for account in account_scopes:
        account_rows = [row for row in scoped if row.get("signal_id", "").startswith(f"{account}|")]
        by_account[account] = {
            "account_label": ACCOUNT_LABELS.get(account, "UNKNOWN"),
            "entry_fills": len(account_rows),
            "sl_exits": sum(1 for row in account_rows if row.get("outcome") == "LOSS"),
            "tp_exits": sum(1 for row in account_rows if row.get("outcome") == "WIN"),
        }
    return {
        "slippage_model_status": "ADEQUATE" if adequate else "INSUFFICIENT",
        "entry_fills": entry_fills,
        "sl_exits": sl_exits,
        "tp_exits": tp_exits,
        "by_account": by_account,
        "required_entry_fills": 200,
        "required_sl_exits": 100,
        "required_tp_exits": 50,
    }


def _per_account_counts(rows: list[dict[str, Any]], account_scopes: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for account in account_scopes:
        account_rows = [row for row in rows if row.get("account_scope") == account]
        output[account] = {
            "account_label": ACCOUNT_LABELS.get(account, "UNKNOWN"),
            "snapshot_rows": len(account_rows),
            "setup_groups": len({row["setup_group_id"] for row in account_rows}),
            "positive": sum(1 for row in account_rows if int(row["y_win_expected"]) == 1),
            "negative": sum(1 for row in account_rows if int(row["y_win_expected"]) == 0),
            "long": sum(1 for row in account_rows if row["direction"] == "LONG"),
            "short": sum(1 for row in account_rows if row["direction"] == "SHORT"),
        }
    return output


def _decision_time_cost_r(row: dict[str, str]) -> float | None:
    for key in ("cost_R", "cost_r", "estimated_total_cost_R", "estimated_cost_R", "estimated_cost_r"):
        value = _float_or_none(row.get(key))
        if value is not None:
            return value
    return None


def _feature_availability(rows: list[dict[str, Any]], feature_columns: list[str]) -> list[dict[str, Any]]:
    output = []
    total = len(rows)
    for name in feature_columns:
        present = sum(1 for row in rows if str(row.get(name, "")) != "")
        output.append(
            {
                "feature_name": name,
                "present_rows": present,
                "missing_rows": total - present,
                "present_pct": round(present / total, 6) if total else 0.0,
            }
        )
    return output


def _feature_matrix_rows(rows: list[dict[str, Any]], feature_columns: list[str]) -> list[dict[str, Any]]:
    matrix = []
    for row in rows:
        matrix_row: dict[str, Any] = {
            "account_scope": row["account_scope"],
            "account_label": row["account_label"],
            "exact_signal_id": row["exact_signal_id"],
            "setup_group_id": row["setup_group_id"],
            "decision_time_utc": row["decision_time_utc"],
            "direction": row["direction"],
        }
        for feature in feature_columns:
            matrix_row[feature] = row.get(feature, "")
            matrix_row[f"{feature}__missing"] = "1" if row.get(feature, "") == "" else "0"
        leaked = sorted(PROHIBITED_FEATURE_COLUMNS.intersection(matrix_row))
        if leaked:
            raise RuntimeError(f"prohibited feature columns leaked into matrix: {leaked}")
        matrix.append(matrix_row)
    return matrix


def _write_offline_scores(
    path: Path,
    rows: list[dict[str, Any]],
    dataset_status: str,
    training_decision: dict[str, Any],
) -> None:
    score_rows = []
    for row in rows:
        score_rows.append(
            {
                "account_scope": row["account_scope"],
                "account_label": row["account_label"],
                "exact_signal_id": row["exact_signal_id"],
                "setup_group_id": row["setup_group_id"],
                "decision_time_utc": row["decision_time_utc"],
                "symbol": row["symbol"],
                "direction": row["direction"],
                "probability": "",
                "threshold": "",
                "action": "ABSTAIN",
                "drift_status": "NOT_EVALUATED",
                "model_hash": "",
                "dataset_status": dataset_status,
                "reason": training_decision["reason"],
            }
        )
    _write_csv(
        path,
        score_rows,
        [
            "account_scope",
            "account_label",
            "exact_signal_id",
            "setup_group_id",
            "decision_time_utc",
            "symbol",
            "direction",
            "probability",
            "threshold",
            "action",
            "drift_status",
            "model_hash",
            "dataset_status",
            "reason",
        ],
    )


def _offline_payload(data_audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": data_audit["status"],
        "created_at_utc": data_audit["created_at_utc"],
        "authority": data_audit["authority"],
        "supervised_training_allowed": data_audit["training_decision"]["supervised_training_allowed"],
        "training_decision": data_audit["training_decision"],
        "global_feature_budget": data_audit["global_feature_budget"],
        "slippage_adequacy_status": data_audit["slippage_adequacy_status"],
        "offline_scores_csv": data_audit["outputs"]["offline_scores_csv"],
        "data_audit_json": data_audit["outputs"]["data_audit_json"],
        "boundary": "Offline shadow only. No broker action is authorized.",
    }


def _parse_signal_id(signal_id: str) -> SignalParts:
    parts = signal_id.split("|")
    if len(parts) != 8:
        raise ValueError(f"invalid signal_id shape: {signal_id!r}")
    return SignalParts(
        account_scope=parts[0],
        symbol=parts[1],
        base_family=parts[2],
        direction=_normalize_direction(parts[3]),
        break_bar_time_utc=_parse_dt(parts[4]),
        retest_bar_time_utc=_parse_dt(parts[5]),
        confirmation_bar_time_utc=_parse_dt(parts[6]),
        normalized_level_price=float(parts[7]),
    )


def _normalize_account_scopes(account_scopes: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if account_scopes is None:
        return DEFAULT_ACCOUNT_SCOPES
    normalized = tuple(str(account).strip() for account in account_scopes if str(account).strip())
    if not normalized:
        return DEFAULT_ACCOUNT_SCOPES
    return normalized


def _contract_scope(root: Path) -> dict[str, Any]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from ml.a3_meta_v1.contract_scope import load_contract_scope  # noqa: PLC0415
    except (ImportError, ModuleNotFoundError):
        return {
            "scope_name": "breakout_retest_only",
            "contract_expansion_authorized": False,
            "active_families": (BASE_FAMILY,),
        }
    scope = load_contract_scope(root)
    return {
        "scope_name": scope.scope_name,
        "contract_expansion_authorized": scope.contract_expansion_authorized,
        "active_families": scope.active_families,
    }


def _label_promotion_scope(root: Path, slippage_status: str) -> dict[str, Any]:
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    try:
        from ml.a3_meta_v1.label_promotion_scope import load_label_promotion_scope  # noqa: PLC0415
    except (ImportError, ModuleNotFoundError):
        return {
            "schema_version": "a3_ml_label_promotion_v1",
            "scope_name": "label_promotion_locked",
            "label_promotion_authorized": False,
            "review_reference": "",
            "allowed_label_statuses": [
                "TP",
                "SL",
                "TIMEOUT_POSITIVE",
                "TIMEOUT_NEGATIVE",
                "TIMEOUT_FLAT",
            ],
            "minimum_mature_labels": 300,
            "minimum_minority_labels": 90,
            "require_slippage_adequate": True,
            "slippage_model_status": slippage_status,
            "promotion_active": False,
        }
    scope = load_label_promotion_scope(root)
    return {
        "schema_version": scope.schema_version,
        "scope_name": scope.scope_name,
        "label_promotion_authorized": scope.label_promotion_authorized,
        "review_reference": scope.review_reference,
        "allowed_label_statuses": list(scope.allowed_label_statuses),
        "minimum_mature_labels": scope.minimum_mature_labels,
        "minimum_minority_labels": scope.minimum_minority_labels,
        "require_slippage_adequate": scope.require_slippage_adequate,
        "slippage_model_status": slippage_status,
        "promotion_active": scope.promotion_active(slippage_status),
    }


def _exact_signal_id(parts: SignalParts) -> str:
    normalized = "|".join(
        [
            parts.account_scope,
            parts.symbol,
            parts.base_family,
            parts.direction,
            f"{parts.normalized_level_price:.2f}",
            _iso(parts.break_bar_time_utc),
            _iso(parts.retest_bar_time_utc),
            _iso(parts.confirmation_bar_time_utc),
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _normalize_direction(value: str) -> str:
    text = value.strip().upper()
    if text in {"BUY", "LONG"}:
        return "LONG"
    if text in {"SELL", "SHORT"}:
        return "SHORT"
    raise ValueError(f"unsupported direction: {value!r}")


def _outcome_from_r(value: float | None) -> str:
    if value is None:
        return "DATA_UNRESOLVED"
    if value >= 1.45:
        return "TP"
    if value <= -0.95:
        return "SL"
    if value > 0:
        return "TIMEOUT_POSITIVE"
    if value < 0:
        return "TIMEOUT_NEGATIVE"
    return "TIMEOUT_FLAT"


def _class_balance(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "positive": sum(1 for row in rows if int(row["y_win_expected"]) == 1),
        "negative": sum(1 for row in rows if int(row["y_win_expected"]) == 0),
    }


def _duration_distribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    durations = sorted(int(row["y_holding_seconds"]) for row in rows)
    if not durations:
        return {"count": 0}
    return {
        "count": len(durations),
        "min_seconds": durations[0],
        "median_seconds": durations[len(durations) // 2],
        "p95_seconds": durations[min(math.ceil(len(durations) * 0.95) - 1, len(durations) - 1)],
        "max_seconds": durations[-1],
    }


def _missingness(rows: list[dict[str, Any]]) -> dict[str, int]:
    missing: Counter[str] = Counter()
    for row in rows:
        for key, value in row.items():
            if value == "":
                missing[key] += 1
    return dict(sorted(missing.items()))


def _duplicate_rates(
    raw_rows: list[dict[str, str]],
    exact_rows: list[dict[str, str]],
    snapshot_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_count = len(raw_rows)
    exact_count = len(exact_rows)
    group_count = len({row["setup_group_id"] for row in snapshot_rows})
    return {
        "raw_rows": raw_count,
        "exact_unique_signals": exact_count,
        "fuzzy_setup_groups": group_count,
        "exact_duplicate_rate": round((raw_count - exact_count) / raw_count, 6) if raw_count else 0.0,
        "fuzzy_duplicate_rate": round((exact_count - group_count) / exact_count, 6) if exact_count else 0.0,
    }


def _counter(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "")) for row in rows).items()))


def _time_bounds(rows: list[dict[str, Any]]) -> tuple[datetime | None, datetime | None]:
    if not rows:
        return None, None
    times = [_parse_dt(row["decision_time_utc"]) for row in rows]
    return min(times), max(times)


def _intervals_overlap(left: tuple[datetime, datetime], right: tuple[datetime, datetime]) -> bool:
    return left[0] <= right[1] and right[0] <= left[1]


def _snapshot_fields(feature_columns: list[str]) -> list[str]:
    return [
        "account_scope",
        "account_label",
        "symbol",
        "base_family",
        "candidate_id",
        "source_signal_id",
        "exact_signal_id",
        "setup_group_id",
        "direction",
        "direction_sign",
        "break_bar_time_utc",
        "retest_bar_time_utc",
        "confirmation_bar_time_utc",
        "feature_time_utc",
        "decision_time_utc",
        "entry_eligible_from_utc",
        "label_end_time_utc",
        "normalized_level_price",
        "opened",
        "reason",
        "session_bucket",
        "regime",
        *feature_columns,
        "y_win_expected",
        "y_net_R_expected",
        "y_win_p95_stress",
        "y_net_R_p95_stress",
        "y_outcome",
        "y_loss_class",
        "y_MFE_R",
        "y_MAE_R",
        "y_holding_seconds",
        "y_holding_active_m5_bars",
        "label_status",
        "candidate_trainable",
        "slippage_model_status",
        "row_status",
    ]


def _feature_matrix_fields(feature_columns: list[str]) -> list[str]:
    fields = ["account_scope", "account_label", "exact_signal_id", "setup_group_id", "decision_time_utc", "direction"]
    for feature in feature_columns:
        fields.extend([feature, f"{feature}__missing"])
    return fields


def _render_data_audit_md(payload: dict[str, Any]) -> str:
    lines = [
        "# A3 ML C01 Data Audit",
        "",
        f"Overall status: {payload['status']}",
        "",
        "## Boundary",
        "",
        payload["authority"],
        "",
        "## Scope",
        "",
        f"- Accounts: {', '.join(payload['scope']['account_scopes'])}",
        f"- Symbol: {payload['scope']['symbol']}",
        f"- Family: {payload['scope']['base_family']}",
        f"- Allowed families: {', '.join(payload['scope'].get('allowed_families', [payload['scope']['base_family']]))}",
        f"- Contract scope: {payload['scope'].get('contract_scope', 'breakout_retest_only')}",
        f"- Candidate source: {payload['scope']['raw_candidate_id']}",
        f"- Label promotion: {payload['label_promotion_scope'].get('scope_name', 'label_promotion_locked')}",
        f"- Label promotion active: {str(payload['label_promotion_scope'].get('promotion_active', False)).lower()}",
        f"- Label promotion slippage status: {payload['label_promotion_scope'].get('slippage_model_status', 'UNKNOWN')}",
        "",
        "## Per-Account Counts",
        "",
    ]
    for account, counts in payload["per_account_counts"].items():
        lines.append(
            f"- {counts['account_label']} {account}: snapshot_rows={counts['snapshot_rows']}, "
            f"setup_groups={counts['setup_groups']}, positive={counts['positive']}, negative={counts['negative']}"
        )
    lines.extend(
        [
        "",
        "## Counts",
        "",
        ]
    )
    for key, value in payload["raw_source_row_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Training Gate",
            "",
            f"- supervised_training_allowed: {str(payload['training_decision']['supervised_training_allowed']).lower()}",
            f"- reason: {payload['training_decision']['reason']}",
            f"- global_feature_budget: {payload['global_feature_budget']}",
            f"- budget_binding_fold_id: {payload['budget_binding_fold_id']}",
            f"- slippage_model_status: {payload['slippage_adequacy_status']['slippage_model_status']}",
            "",
            "## Outputs",
            "",
        ]
    )
    for key, value in payload["outputs"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    return "\n".join(lines)


def _render_offline_report_md(payload: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# A3 ML Offline Report",
            "",
            f"Overall status: {payload['status']}",
            "",
            "## Boundary",
            "",
            payload["boundary"],
            "",
            "## Training Decision",
            "",
            f"- supervised_training_allowed: {str(payload['supervised_training_allowed']).lower()}",
            f"- reason: {payload['training_decision']['reason']}",
            f"- global_feature_budget: {payload['global_feature_budget']}",
            f"- slippage_model_status: {payload['slippage_adequacy_status']['slippage_model_status']}",
            "",
        ]
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _file_manifest(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "rows": len(_read_csv(path)) if path.exists() and path.is_file() and path.suffix.lower() == ".csv" else None,
        "sha256": _sha256_file(path) if path.exists() and path.is_file() else "",
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_dt(value: str) -> datetime:
    text = str(value).strip()
    if not text:
        raise ValueError("empty datetime")
    text = text.replace("T", " ").replace("Z", "").replace("+00:00", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(text).replace(tzinfo=None)


def _iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat(sep=" ") + "Z"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _float_or_none(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def _format_optional(value: float | None) -> str:
    if value is None:
        return ""
    return _format_float(value)


def _format_float(value: float) -> str:
    return f"{value:.10f}".rstrip("0").rstrip(".")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the A3 ML C01 pipeline snapshot and shadow audit.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--decisions-csv", type=Path)
    parser.add_argument("--trades-csv", type=Path)
    parser.add_argument("--bars-dir", type=Path)
    parser.add_argument("--feature-registry-csv", type=Path)
    parser.add_argument("--data-audit-json", type=Path)
    parser.add_argument(
        "--account-scopes",
        default=",".join(DEFAULT_ACCOUNT_SCOPES),
        help="Comma-separated account logins to include. Defaults to A1,A2,A3.",
    )
    args = parser.parse_args()
    output = generate_a3_ml_c01_pipeline(
        args.root,
        decisions_csv=args.decisions_csv,
        trades_csv=args.trades_csv,
        bars_dir=args.bars_dir,
        feature_registry_csv=args.feature_registry_csv,
        data_audit_json=args.data_audit_json,
        account_scopes=tuple(part.strip() for part in args.account_scopes.split(",") if part.strip()),
    )
    print(f"A3 ML C01 status: {output.status}")
    print(f"Data audit: {output.data_audit_json}")
    print(f"Offline report: {output.offline_report_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

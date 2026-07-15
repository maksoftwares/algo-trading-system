from __future__ import annotations

import bisect
import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from ml.a3_meta_v1.dukascopy_compression_breakout import aggregate_h1_bid_bars
from ml.a3_meta_v1.dukascopy_label_factory import (
    Candidate,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _sha256_file,
    _validate_candidates,
    _write_rows,
    prepare_verified_h1_bars,
    replay_candidates,
)
from ml.a3_meta_v1.dukascopy_m5_momentum_portability import (
    M5_MS,
    _iso_ms,
    _month_bootstrap,
    _parse_utc,
    _resolve_storage_root,
    _sha256_json,
    _stats,
    _trend_allows,
    _trend_frame,
    prepare_verified_m5_bars,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_m5_discovery_train.json")
PATTERNS = {
    "TREND_PULLBACK",
    "CONTINUATION_BREAKOUT",
    "TREND_SWEEP_RECLAIM",
}
TREND_SCOPES = {"H1", "H1_H4"}


class M5DiscoveryError(RuntimeError):
    pass


def run_dukascopy_m5_discovery_train(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _resolve_storage_root(contract)
    months = _month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    foundation = _load_foundation(root.parents[1])
    h1_bars, h1_audits = prepare_verified_h1_bars(
        storage_root,
        storage_root / "research" / "xau-label-factory-v1" / "bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    m5_bars, m5_audits = prepare_verified_m5_bars(
        storage_root,
        storage_root / str(contract["m5_cache_subdirectory"]),
        str(contract["symbol"]),
        months,
        foundation,
    )
    candidates = generate_discovery_candidates(m5_bars, h1_bars, contract)
    _validate_candidates(candidates)
    store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=set(months),
    )
    raw_labels = replay_candidates(candidates, h1_bars, store, contract)
    candidate_by_id = {row.candidate_id: row for row in candidates}
    executed_labels, execution_reasons = apply_profile_execution_controls(
        raw_labels, candidate_by_id, contract
    )

    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    _write_rows(outputs["raw_candidates_csv"], [asdict(row) for row in candidates])
    _write_rows(outputs["raw_labels_csv"], [asdict(row) for row in raw_labels])
    _write_rows(outputs["executed_labels_csv"], [asdict(row) for row in executed_labels])
    payload = _build_report(
        contract=contract,
        contract_file=contract_file,
        storage_root=storage_root,
        h1_audits=h1_audits,
        m5_audits=m5_audits,
        m5_bars=m5_bars,
        candidates=candidates,
        raw_labels=raw_labels,
        executed_labels=executed_labels,
        execution_reasons=execution_reasons,
        outputs=outputs,
    )
    outputs["report_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def generate_discovery_candidates(
    m5_bars: Sequence[Mapping[str, Any]],
    h1_bars: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
) -> list[Candidate]:
    m5 = _m5_frame(m5_bars, contract)
    signal = contract["signal"]
    h1 = _trend_frame(
        [{"timestamp_ms": row["timestamp_ms"], "close": row["bid_close"]} for row in h1_bars],
        width_hours=1,
        fast_period=int(signal["h1_ema_fast_period"]),
        slow_period=int(signal["h1_ema_slow_period"]),
        slope_bars=int(signal["h1_slope_bars"]),
    )
    h4_bars = aggregate_h1_bid_bars(h1_bars, width_hours=4, minimum_active_hours=1)
    h4 = _trend_frame(
        [{"timestamp_ms": row["timestamp_ms"], "close": row["close"]} for row in h4_bars],
        width_hours=4,
        fast_period=int(signal["h4_ema_fast_period"]),
        slow_period=int(signal["h4_ema_slow_period"]),
        slope_bars=int(signal["h4_slope_bars"]),
    )
    if m5.empty or h1.empty or h4.empty:
        return []
    h1_ends = [int(value) for value in h1["end_timestamp_ms"]]
    h4_ends = [int(value) for value in h4["end_timestamp_ms"]]
    start_ms = _utc_ms(contract["training_window"]["start_utc"])
    end_ms = _utc_ms(contract["training_window"]["end_exclusive_utc"])
    lookback = int(signal["pattern_lookback_m5_bars"])
    point = float(signal["point_size"])
    profiles = sorted(contract["profiles"], key=lambda row: str(row["family_id"]))
    output: list[Candidate] = []

    for index in range(max(lookback, 3, int(signal["m5_ema_period"])), len(m5)):
        row = m5.iloc[index]
        decision_ms = int(row["timestamp_ms"]) + M5_MS
        if not start_ms <= decision_ms < end_ms or pd.isna(row["atr"]):
            continue
        h1_index = bisect.bisect_right(h1_ends, decision_ms) - 1
        h4_index = bisect.bisect_right(h4_ends, decision_ms) - 1
        if h1_index < 0 or h4_index < 0:
            continue
        h1_row = h1.iloc[h1_index]
        h4_row = h4.iloc[h4_index]
        required = ("ema_fast", "ema_slow", "ema_fast_prior")
        if any(pd.isna(h1_row[name]) or pd.isna(h4_row[name]) for name in required):
            continue
        h1_long = _trend_allows(h1_row, "LONG")
        h1_short = _trend_allows(h1_row, "SHORT")
        if not h1_long and not h1_short:
            continue
        direction = "LONG" if h1_long else "SHORT"
        atr = float(row["atr"])
        bar_range = float(row["bid_high"] - row["bid_low"])
        if atr <= 0.0 or bar_range < float(signal["minimum_range_atr"]) * atr:
            continue
        opened = float(row["bid_open"])
        closed = float(row["bid_close"])
        body_fraction = abs(closed - opened) / bar_range
        if body_fraction < float(signal["minimum_body_fraction"]):
            continue
        close_location = (closed - float(row["bid_low"])) / bar_range
        stop_distance = max(
            float(signal["stop_atr_multiple"]) * atr,
            int(signal["stop_floor_points"]) * point,
        )
        if stop_distance / point > int(signal["stop_ceiling_points"]):
            continue

        for profile in profiles:
            scope = str(profile["trend_scope"])
            if scope == "H1_H4" and not _trend_allows(h4_row, direction):
                continue
            pattern = str(profile["pattern"])
            matched, distance_atr = _pattern_allows(
                pattern, direction, row, m5.iloc[index - 1], signal
            )
            if not matched:
                continue
            family_id = str(profile["family_id"])
            candidate_id = hashlib.sha256(
                f"{family_id}|{contract['symbol']}|{decision_ms}|{direction}".encode("ascii")
            ).hexdigest()[:24]
            output.append(
                Candidate(
                    candidate_id=candidate_id,
                    family_id=family_id,
                    symbol=str(contract["symbol"]),
                    split="train",
                    direction=direction,
                    signal_bar_start_utc=_iso_ms(int(row["timestamp_ms"])),
                    decision_time_utc=_iso_ms(decision_ms),
                    decision_timestamp_ms=decision_ms,
                    signal_open=opened,
                    signal_high=float(row["bid_high"]),
                    signal_low=float(row["bid_low"]),
                    signal_close=closed,
                    ema_fast=float(h1_row["ema_fast"]),
                    ema_slow=float(h1_row["ema_slow"]),
                    ema_fast_slope_atr=(
                        float(h1_row["ema_fast"]) - float(h1_row["ema_fast_prior"])
                    )
                    / atr,
                    atr=atr,
                    body_fraction=body_fraction,
                    close_location=close_location,
                    touch_distance_atr=distance_atr,
                    stop_distance=stop_distance,
                    stop_distance_atr=stop_distance / atr,
                    reward_r=float(profile["reward_r"]),
                    signal_tick_count=int(row["tick_count"]),
                )
            )
    output.sort(key=lambda row: (row.decision_timestamp_ms, row.direction, row.family_id))
    return output


def _m5_frame(
    bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> pd.DataFrame:
    frame = pd.DataFrame(bars).copy()
    if frame.empty:
        return frame
    for name in ("timestamp_ms", "tick_count"):
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype("int64")
    for name in ("bid_open", "bid_high", "bid_low", "bid_close"):
        frame[name] = pd.to_numeric(frame[name], errors="raise").astype(float)
    frame = frame.sort_values("timestamp_ms").reset_index(drop=True)
    previous_close = frame["bid_close"].shift(1)
    true_range = pd.concat(
        [
            frame["bid_high"] - frame["bid_low"],
            (frame["bid_high"] - previous_close).abs(),
            (frame["bid_low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    signal = contract["signal"]
    frame["atr"] = true_range.ewm(
        alpha=1.0 / int(signal["atr_period"]),
        adjust=False,
        min_periods=int(signal["atr_period"]),
    ).mean()
    ema_period = int(signal["m5_ema_period"])
    frame["m5_ema"] = frame["bid_close"].ewm(
        span=ema_period, adjust=False, min_periods=ema_period
    ).mean()
    frame["m5_ema_prior"] = frame["m5_ema"].shift(1)
    lookback = int(signal["pattern_lookback_m5_bars"])
    frame["prior_high"] = frame["bid_high"].shift(1).rolling(lookback).max()
    frame["prior_low"] = frame["bid_low"].shift(1).rolling(lookback).min()
    frame["three_bar_move"] = frame["bid_close"] - frame["bid_close"].shift(3)
    return frame


def _pattern_allows(
    pattern: str,
    direction: str,
    row: Mapping[str, Any],
    previous: Mapping[str, Any],
    signal: Mapping[str, Any],
) -> tuple[bool, float]:
    required = ("atr", "m5_ema", "m5_ema_prior", "prior_high", "prior_low")
    if any(pd.isna(row[name]) for name in required):
        return False, 0.0
    atr = float(row["atr"])
    opened = float(row["bid_open"])
    high = float(row["bid_high"])
    low = float(row["bid_low"])
    closed = float(row["bid_close"])
    prior_high = float(row["prior_high"])
    prior_low = float(row["prior_low"])
    ema = float(row["m5_ema"])
    ema_prior = float(row["m5_ema_prior"])
    previous_close = float(previous["bid_close"])
    bar_range = high - low
    body = abs(closed - opened) / bar_range if bar_range > 0.0 else 0.0
    location = (closed - low) / bar_range if bar_range > 0.0 else 0.5
    directional_location = float(signal["directional_close_location"])

    if pattern == "TREND_PULLBACK":
        if direction == "LONG":
            matched = (
                low <= ema
                and previous_close <= ema_prior
                and closed > ema
                and closed > opened
                and location >= directional_location
            )
        else:
            matched = (
                high >= ema
                and previous_close >= ema_prior
                and closed < ema
                and closed < opened
                and location <= 1.0 - directional_location
            )
        return matched, abs(closed - ema) / atr

    if pattern == "CONTINUATION_BREAKOUT":
        threshold = float(signal["breakout_atr_multiple"]) * atr
        minimum_move = float(signal["breakout_three_bar_move_atr"]) * atr
        breakout_location = float(signal["breakout_close_location"])
        if direction == "LONG":
            matched = (
                closed >= prior_high + threshold
                and closed > opened
                and body >= float(signal["breakout_minimum_body_fraction"])
                and location >= breakout_location
                and float(row["three_bar_move"]) >= minimum_move
            )
            distance = (closed - prior_high) / atr
        else:
            matched = (
                closed <= prior_low - threshold
                and closed < opened
                and body >= float(signal["breakout_minimum_body_fraction"])
                and location <= 1.0 - breakout_location
                and float(row["three_bar_move"]) <= -minimum_move
            )
            distance = (prior_low - closed) / atr
        return matched, max(0.0, distance)

    if pattern == "TREND_SWEEP_RECLAIM":
        sweep = float(signal["sweep_atr_multiple"]) * atr
        reclaim = float(signal["reclaim_atr_multiple"]) * atr
        if direction == "LONG":
            matched = (
                low <= prior_low - sweep
                and closed >= prior_low + reclaim
                and closed > opened
                and location >= directional_location
            )
            distance = (prior_low - low) / atr
        else:
            matched = (
                high >= prior_high + sweep
                and closed <= prior_high - reclaim
                and closed < opened
                and location <= 1.0 - directional_location
            )
            distance = (high - prior_high) / atr
        return matched, max(0.0, distance)

    raise ValueError(f"unsupported pattern: {pattern}")


def apply_profile_execution_controls(
    labels: Sequence[Any],
    candidates: Mapping[str, Candidate],
    contract: Mapping[str, Any],
) -> tuple[list[Any], dict[str, int]]:
    signal = contract["signal"]
    execution = contract["execution"]
    point = float(signal["point_size"])
    profile_ids = [str(row["family_id"]) for row in contract["profiles"]]
    selected: list[Any] = []
    reasons: Counter[str] = Counter()
    for family_id in profile_ids:
        rows = sorted(
            [row for row in labels if row.family_id == family_id],
            key=lambda row: (candidates[row.candidate_id].decision_timestamp_ms, row.candidate_id),
        )
        open_until: datetime | None = None
        last_trade: datetime | None = None
        daily_entries: Counter[str] = Counter()
        for row in rows:
            if row.status != "RESOLVED":
                reasons[f"raw_{row.status.lower()}_{row.exit_reason}"] += 1
                continue
            if row.entry_spread is None or not row.entry_time_utc:
                reasons["missing_entry_quote"] += 1
                continue
            if float(row.entry_spread) / point > float(signal["maximum_spread_points"]):
                reasons["spread_above_maximum"] += 1
                continue
            if float(row.entry_spread) / float(row.stop_distance) > float(
                signal["maximum_estimated_cost_r"]
            ):
                reasons["estimated_cost_r_above_maximum"] += 1
                continue
            entry = _parse_utc(row.entry_time_utc)
            exit_time = _parse_utc(row.exit_time_utc)
            if bool(execution["one_position_per_profile"]) and open_until is not None and entry < open_until:
                reasons["profile_position_already_open"] += 1
                continue
            cooldown = timedelta(minutes=int(execution["cooldown_minutes"]))
            if last_trade is not None and entry - last_trade < cooldown:
                reasons["profile_cooldown"] += 1
                continue
            server_day = (
                entry + timedelta(hours=int(contract["server_time"]["utc_offset_hours"]))
            ).date().isoformat()
            if daily_entries[server_day] >= int(execution["maximum_trades_per_server_day"]):
                reasons["profile_daily_cap"] += 1
                continue
            selected.append(row)
            open_until = exit_time
            last_trade = entry
            daily_entries[server_day] += 1
    selected.sort(key=lambda row: (row.entry_time_utc, row.candidate_id))
    return selected, dict(reasons)


def _build_report(
    *,
    contract: Mapping[str, Any],
    contract_file: Path,
    storage_root: Path,
    h1_audits: Sequence[Mapping[str, Any]],
    m5_audits: Sequence[Mapping[str, Any]],
    m5_bars: Sequence[Mapping[str, Any]],
    candidates: Sequence[Candidate],
    raw_labels: Sequence[Any],
    executed_labels: Sequence[Any],
    execution_reasons: Mapping[str, int],
    outputs: Mapping[str, Path],
) -> dict[str, Any]:
    source_days = _training_source_days(m5_bars, contract)
    evidence: dict[str, dict[str, Any]] = {}
    bootstrap: dict[str, dict[str, Any]] = {}
    gates: dict[str, dict[str, bool]] = {}
    for profile in contract["profiles"]:
        family_id = str(profile["family_id"])
        rows = [row for row in executed_labels if row.family_id == family_id]
        profile_stats = _stats(rows, source_days, contract)
        profile_stats.update(_direction_and_concentration(rows))
        evidence[family_id] = profile_stats
        bootstrap[family_id] = _month_bootstrap(
            rows,
            samples=int(contract["bootstrap"]["calendar_month_samples"]),
            seed=int(contract["bootstrap"]["seed"]),
        )
        gates[family_id] = _profile_gates(
            profile_stats, bootstrap[family_id], contract["selection_gates"]
        )

    raw_eligible = [row for row in raw_labels if row.status != "INELIGIBLE"]
    raw_resolved = [row for row in raw_labels if row.status == "RESOLVED"]
    timeout_share = (
        sum(row.exit_reason == "TIMEOUT" for row in executed_labels) / len(executed_labels)
        if executed_labels
        else 0.0
    )
    quality = contract["quality_gates"]
    profile_ids = {str(row["family_id"]) for row in contract["profiles"]}
    quality_gates = {
        "verified_h1_months_eq_expected": len(h1_audits) == int(quality["expected_months"]),
        "verified_m5_months_eq_expected": len(m5_audits) == int(quality["expected_months"]),
        "raw_candidates_ge_minimum": len(candidates) >= int(quality["minimum_raw_candidates"]),
        "resolved_share_ge_minimum": (
            len(raw_resolved) / len(raw_eligible) >= float(quality["minimum_resolved_share"])
            if raw_eligible
            else False
        ),
        "selected_timeout_share_lte_maximum": timeout_share
        <= float(quality["maximum_selected_timeout_share"]),
        "candidate_ids_unique": len({row.candidate_id for row in candidates}) == len(candidates),
        "executed_candidate_ids_unique": len({row.candidate_id for row in executed_labels})
        == len(executed_labels),
        "all_profiles_have_candidates": {row.family_id for row in candidates} == profile_ids,
        "all_profiles_have_executed_trades": {row.family_id for row in executed_labels} == profile_ids,
        "training_only_candidates": all(row.split == "train" for row in candidates),
    }
    passing = sorted(
        [family_id for family_id, row in gates.items() if all(row.values())],
        key=lambda family_id: (
            -float(evidence[family_id]["stress_profit_factor"] or 0.0),
            -float(evidence[family_id]["trades_per_source_day"]),
            family_id,
        ),
    )
    selected_profile = passing[0] if all(quality_gates.values()) and passing else None
    if not all(quality_gates.values()):
        classification = "DUKASCOPY_M5_DISCOVERY_TRAIN_INVALID"
    elif selected_profile:
        classification = "DUKASCOPY_M5_DISCOVERY_TRAIN_SURVIVOR_FROZEN"
    else:
        classification = "DUKASCOPY_M5_DISCOVERY_TRAIN_NO_SURVIVOR"
    return {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "storage_root": str(storage_root),
        "source_months": len(m5_audits),
        "source_composite_sha256": _sha256_json(
            [(row["month"], row["source_files_composite_sha256"]) for row in m5_audits]
        ),
        "m5_bar_count": len(m5_bars),
        "m5_cache_reused_months": sum(bool(row["bar_cache_reused"]) for row in m5_audits),
        "training_source_days": source_days,
        "raw_candidate_count": len(candidates),
        "raw_resolved_count": len(raw_resolved),
        "raw_resolved_share": len(raw_resolved) / len(raw_eligible) if raw_eligible else 0.0,
        "executed_trade_count": len(executed_labels),
        "selected_timeout_share": timeout_share,
        "candidates_by_profile": dict(Counter(row.family_id for row in candidates)),
        "executed_trades_by_profile": dict(Counter(row.family_id for row in executed_labels)),
        "execution_reasons": dict(execution_reasons),
        "quality_gates": quality_gates,
        "profile_evidence": evidence,
        "calendar_month_bootstrap": bootstrap,
        "profile_selection_gates": gates,
        "passing_profiles": passing,
        "selected_profile": selected_profile,
        "reserved_outcomes_opened": False,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key in {"raw_candidates_csv", "raw_labels_csv", "executed_labels_csv"}
        },
        "authorization": {
            **contract["authorization"],
            "strategy_promotion_authorized": False,
        },
        "limitations": [
            "Only old-period training outcomes are evaluated in this stage.",
            "A train survivor is permission to freeze one profile, not evidence of holdout profitability.",
            "Fixed 0.01-lot results are not account-relative sizing or risk-of-ruin evidence.",
        ],
    }


def _direction_and_concentration(rows: Sequence[Any]) -> dict[str, Any]:
    directions = Counter(row.direction for row in rows)
    minimum_share = (
        min(directions.get("LONG", 0), directions.get("SHORT", 0)) / len(rows)
        if rows
        else 0.0
    )
    monthly: dict[str, float] = defaultdict(float)
    for row in rows:
        monthly[row.exit_time_utc[:7]] += float(row.stress_net_pnl_usd)
    positive_values = [value for value in monthly.values() if value > 0.0]
    total_positive = sum(positive_values)
    maximum_share = max(positive_values, default=0.0) / total_positive if total_positive else 1.0
    return {
        "long_trades": directions.get("LONG", 0),
        "short_trades": directions.get("SHORT", 0),
        "minimum_direction_share": minimum_share,
        "maximum_single_month_profit_share": maximum_share,
    }


def _profile_gates(
    evidence: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    configured: Mapping[str, Any],
) -> dict[str, bool]:
    profit_factor = evidence.get("stress_profit_factor")
    return {
        "trades_ge_minimum": int(evidence["trades"]) >= int(configured["minimum_trades"]),
        "trades_per_source_day_ge_minimum": float(evidence["trades_per_source_day"])
        >= float(configured["minimum_trades_per_source_day"]),
        "trades_per_active_day_ge_minimum": float(evidence["trades_per_active_trade_day"])
        >= float(configured["minimum_trades_per_active_trade_day"]),
        "active_day_coverage_ge_minimum": float(evidence["active_trade_day_coverage"])
        >= float(configured["minimum_active_trade_day_coverage"]),
        "stress_profit_factor_ge_minimum": profit_factor is not None
        and float(profit_factor) >= float(configured["minimum_stress_profit_factor"]),
        "average_stress_r_ge_minimum": float(evidence["average_stress_r"])
        >= float(configured["minimum_average_stress_r"]),
        "positive_month_share_ge_minimum": float(evidence["positive_exit_month_share"])
        >= float(configured["minimum_positive_exit_month_share"]),
        "closed_drawdown_r_lte_maximum": float(evidence["max_closed_drawdown_r"])
        <= float(configured["maximum_closed_drawdown_r"]),
        "closed_drawdown_usd_lte_maximum": float(evidence["max_closed_drawdown_usd"])
        <= float(configured["maximum_closed_drawdown_usd"]),
        "direction_share_ge_minimum": float(evidence["minimum_direction_share"])
        >= float(configured["minimum_direction_share"]),
        "single_month_profit_share_lte_maximum": float(
            evidence["maximum_single_month_profit_share"]
        )
        <= float(configured["maximum_single_month_profit_share"]),
        "top25_winners_removed_net_positive": float(
            evidence["top25_winners_removed_net_usd"]
        )
        > 0.0,
        "bootstrap_average_r_p025_above_zero": bootstrap.get("average_stress_r_p025")
        is not None
        and float(bootstrap["average_stress_r_p025"]) > 0.0,
    }


def _training_source_days(
    m5_bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> int:
    start_ms = _utc_ms(contract["training_window"]["start_utc"])
    end_ms = _utc_ms(contract["training_window"]["end_exclusive_utc"])
    offset = int(contract["server_time"]["utc_offset_hours"])
    minimum = int(contract["quality_gates"]["minimum_m5_bars_per_source_day"])
    counts: Counter[str] = Counter()
    for row in m5_bars:
        timestamp_ms = int(row["timestamp_ms"])
        decision_ms = timestamp_ms + M5_MS
        if start_ms <= decision_ms < end_ms:
            server_date = (
                datetime.fromtimestamp(timestamp_ms / 1000, UTC) + timedelta(hours=offset)
            ).date().isoformat()
            counts[server_date] += 1
    return sum(value >= minimum for value in counts.values())


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy M5 Discovery Train V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "Training-only historical research. Reserved validation, test, and new-holdout outcomes were not opened.",
        "",
        f"- Training source days: `{payload['training_source_days']}`",
        f"- Raw candidates: `{payload['raw_candidate_count']}`",
        f"- Executed trades across profiles: `{payload['executed_trade_count']}`",
        f"- Selected profile: `{payload['selected_profile'] or 'none'}`",
        "",
        "| Profile | Trades | Trades/day | PF | Avg R | Net USD | DD USD | Gate |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for family_id, row in payload["profile_evidence"].items():
        pf = row["stress_profit_factor"]
        passed = all(payload["profile_selection_gates"][family_id].values())
        lines.append(
            f"| {family_id} | {row['trades']} | {row['trades_per_source_day']:.3f} | "
            f"{pf:.3f} | {row['average_stress_r']:.4f} | {row['stress_net_usd']:.2f} | "
            f"{row['max_closed_drawdown_usd']:.2f} | {'PASS' if passed else 'FAIL'} |"
            if pf is not None
            else f"| {family_id} | {row['trades']} | {row['trades_per_source_day']:.3f} | n/a | "
            f"{row['average_stress_r']:.4f} | {row['stress_net_usd']:.2f} | "
            f"{row['max_closed_drawdown_usd']:.2f} | {'PASS' if passed else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "No prediction, EA consumption, demo, live, or broker action is authorized.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_m5_discovery_train_v1":
        raise ValueError("unexpected M5 discovery contract version")
    authorization = contract.get("authorization", {})
    if not authorization.get("research_only"):
        raise ValueError("M5 discovery must remain research only")
    for key in (
        "validation_outcomes_authorized",
        "test_outcomes_authorized",
        "python_demo_predictions_authorized",
        "ea_consumption_authorized",
        "broker_action_authorized",
    ):
        if authorization.get(key):
            raise ValueError(f"M5 discovery requires {key}=false")
    profiles = list(contract.get("profiles", []))
    if len(profiles) != 12:
        raise ValueError("M5 discovery requires exactly 12 frozen profiles")
    ids = [str(row["family_id"]) for row in profiles]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate M5 discovery profile ID")
    combinations = {
        (str(row["pattern"]), str(row["trend_scope"]), float(row["reward_r"]))
        for row in profiles
    }
    expected = {(pattern, scope, reward) for pattern in PATTERNS for scope in TREND_SCOPES for reward in (1.0, 1.5)}
    if combinations != expected:
        raise ValueError("M5 discovery profile matrix is incomplete")
    if contract.get("selection_order") != [
        "stress_profit_factor_desc",
        "trades_per_source_day_desc",
        "family_id_asc",
    ]:
        raise ValueError("M5 discovery selection order changed")
    start = _utc_ms(contract["training_window"]["start_utc"])
    end = _utc_ms(contract["training_window"]["end_exclusive_utc"])
    reserved = _utc_ms(contract["reserved_windows"]["validation_start_utc"])
    if start >= end or end != reserved:
        raise ValueError("training and reserved window boundary is invalid")
    if int(contract["server_time"]["utc_offset_hours"]) != 4:
        raise ValueError("broker server offset must remain UTC+4")
    if float(contract["signal"]["maximum_estimated_cost_r"]) != 0.1:
        raise ValueError("cost-to-risk ceiling must remain 0.10R")
    if int(contract["quality_gates"]["expected_months"]) != len(
        _month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    ):
        raise ValueError("expected source-month count does not match period")


def _utc_ms(value: Any) -> int:
    return int(_parse_utc(value).timestamp() * 1000)

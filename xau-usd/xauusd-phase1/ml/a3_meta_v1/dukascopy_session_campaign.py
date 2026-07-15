from __future__ import annotations

import hashlib
import json
import math
import os
import random
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from ml.a3_meta_v1.dukascopy_label_factory import (
    HOUR_MS,
    Candidate,
    VerifiedTickStore,
    _load_foundation,
    _month_range,
    _sha256_file,
    _split_for_timestamp,
    _validate_candidates,
    _write_rows,
    prepare_verified_h1_bars,
    replay_candidates,
)


DEFAULT_CONTRACT = Path("config/ml/a3_ml_dukascopy_session_campaign.json")


class SessionCampaignError(RuntimeError):
    pass


def run_dukascopy_session_campaign(
    root: Path, contract_path: Path | None = None
) -> Path:
    root = root.resolve()
    contract_file = (contract_path or root / DEFAULT_CONTRACT).resolve()
    contract = json.loads(contract_file.read_text(encoding="utf-8"))
    _validate_contract(contract)
    storage_root = _resolve_storage_root(contract)
    external_root = storage_root / str(contract["external_output_subdirectory"])
    foundation = _load_foundation(root.parents[1])
    months = _month_range(contract["period"]["start_month"], contract["period"]["end_month"])
    bars, source_audits = prepare_verified_h1_bars(
        storage_root,
        external_root / "bars",
        str(contract["symbol"]),
        months,
        foundation,
    )
    candidates = generate_session_candidates(bars, contract)
    _validate_candidates(candidates)
    store = VerifiedTickStore(
        storage_root=storage_root,
        symbol=str(contract["symbol"]),
        foundation=foundation,
        prevalidated_months=set(months),
    )
    labels = replay_candidates(candidates, bars, store, contract)

    outputs = {key: (root / value).resolve() for key, value in contract["outputs"].items()}
    _write_rows(outputs["candidates_csv"], [asdict(row) for row in candidates])
    _write_rows(outputs["labels_csv"], [asdict(row) for row in labels])
    payload = _build_report(
        contract=contract,
        contract_file=contract_file,
        storage_root=storage_root,
        source_audits=source_audits,
        bars=bars,
        candidates=candidates,
        labels=labels,
        outputs=outputs,
    )
    outputs["report_json"].parent.mkdir(parents=True, exist_ok=True)
    outputs["report_json"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    outputs["report_markdown"].write_text(_render(payload), encoding="utf-8")
    return outputs["report_json"]


def generate_session_candidates(
    bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> list[Candidate]:
    frame = _indicator_frame(bars, contract)
    if frame.empty:
        return []
    signal = contract["signal"]
    session_hours = {
        int(hour): name
        for name, hours in contract["sessions"].items()
        for hour in hours
    }
    maximum_lookback = max(int(row["lookback_h1_bars"]) for row in contract["profiles"])
    consumed: set[tuple[str, str, str]] = set()
    output: list[Candidate] = []

    for index in range(maximum_lookback, len(frame)):
        row = frame.iloc[index]
        start_ms = int(row["timestamp_ms"])
        start = datetime.fromtimestamp(start_ms / 1000, UTC)
        session = session_hours.get(start.hour)
        if session is None or start.weekday() >= 5:
            continue
        required = ("atr", "ema", "ema_prior")
        if any(pd.isna(row[name]) for name in required):
            continue
        signal_range = float(row["bid_high"] - row["bid_low"])
        atr = float(row["atr"])
        if signal_range <= 0.0 or atr <= 0.0:
            continue
        range_atr = signal_range / atr
        if not (
            float(signal["minimum_signal_range_atr"])
            <= range_atr
            <= float(signal["maximum_signal_range_atr"])
        ):
            continue
        signal_open = float(row["bid_open"])
        signal_close = float(row["bid_close"])
        body_fraction = abs(signal_close - signal_open) / signal_range
        if body_fraction < float(signal["minimum_body_fraction"]):
            continue
        close_location = (signal_close - float(row["bid_low"])) / signal_range

        for profile in contract["profiles"]:
            family_id = str(profile["family_id"])
            opportunity = (family_id, start.date().isoformat(), session)
            if opportunity in consumed:
                continue
            lookback = int(profile["lookback_h1_bars"])
            prior = frame.iloc[index - lookback : index]
            first_prior_ms = int(prior.iloc[0]["timestamp_ms"])
            elapsed_hours = (start_ms - first_prior_ms) / HOUR_MS
            if elapsed_hours > lookback + int(signal["maximum_lookback_gap_hours"]):
                continue
            prior_high = float(prior["bid_high"].max())
            prior_low = float(prior["bid_low"].min())
            direction, stop_distance, distance_atr = _profile_signal(
                row=row,
                profile=profile,
                signal=signal,
                prior_high=prior_high,
                prior_low=prior_low,
                atr=atr,
                close_location=close_location,
            )
            if not direction:
                continue
            decision_ms = start_ms + HOUR_MS
            decision = datetime.fromtimestamp(decision_ms / 1000, UTC)
            split = _split_for_timestamp(decision, contract["splits"])
            if split is None:
                continue
            candidate_id = hashlib.sha256(
                f"{family_id}|{contract['symbol']}|{decision_ms}|{direction}".encode("ascii")
            ).hexdigest()[:24]
            output.append(
                Candidate(
                    candidate_id=candidate_id,
                    family_id=family_id,
                    symbol=str(contract["symbol"]),
                    split=split,
                    direction=direction,
                    signal_bar_start_utc=_iso_ms(start_ms),
                    decision_time_utc=_iso_ms(decision_ms),
                    decision_timestamp_ms=decision_ms,
                    signal_open=signal_open,
                    signal_high=float(row["bid_high"]),
                    signal_low=float(row["bid_low"]),
                    signal_close=signal_close,
                    ema_fast=float(row["ema"]),
                    ema_slow=float(row["ema_prior"]),
                    ema_fast_slope_atr=(float(row["ema"]) - float(row["ema_prior"])) / atr,
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
            consumed.add(opportunity)
    return output


def _profile_signal(
    *,
    row: Mapping[str, Any],
    profile: Mapping[str, Any],
    signal: Mapping[str, Any],
    prior_high: float,
    prior_low: float,
    atr: float,
    close_location: float,
) -> tuple[str, float, float]:
    opened = float(row["bid_open"])
    high = float(row["bid_high"])
    low = float(row["bid_low"])
    closed = float(row["bid_close"])
    ema = float(row["ema"])
    ema_prior = float(row["ema_prior"])
    minimum_distance = float(signal["breakout_minimum_distance_atr"]) * atr
    mechanism = str(profile["mechanism"])

    if mechanism == "BREAKOUT":
        location = float(signal["breakout_minimum_close_location"])
        if (
            closed > opened
            and close_location >= location
            and closed >= prior_high + minimum_distance
            and closed > ema
            and ema >= ema_prior
        ):
            return "LONG", float(profile["stop_atr"]) * atr, (closed - prior_high) / atr
        if (
            closed < opened
            and close_location <= 1.0 - location
            and closed <= prior_low - minimum_distance
            and closed < ema
            and ema <= ema_prior
        ):
            return "SHORT", float(profile["stop_atr"]) * atr, (prior_low - closed) / atr
        return "", 0.0, 0.0

    if mechanism != "SWEEP_REVERSAL":
        raise ValueError(f"unsupported session mechanism: {mechanism}")
    reentry = float(signal["sweep_reentry_distance_atr"]) * atr
    location = float(signal["sweep_minimum_close_location"])
    buffer_distance = float(signal["sweep_stop_buffer_atr"]) * atr
    minimum_stop = float(signal["sweep_minimum_stop_atr"]) * atr
    maximum_stop = float(signal["sweep_maximum_stop_atr"]) * atr
    if (
        closed > opened
        and close_location >= location
        and low <= prior_low - reentry
        and closed >= prior_low + reentry
    ):
        stop = max(minimum_stop, closed - low + buffer_distance)
        if stop <= maximum_stop:
            return "LONG", stop, (prior_low - low) / atr
    if (
        closed < opened
        and close_location <= 1.0 - location
        and high >= prior_high + reentry
        and closed <= prior_high - reentry
    ):
        stop = max(minimum_stop, high - closed + buffer_distance)
        if stop <= maximum_stop:
            return "SHORT", stop, (high - prior_high) / atr
    return "", 0.0, 0.0


def _indicator_frame(
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
    atr_period = int(contract["signal"]["atr_period"])
    frame["atr"] = true_range.ewm(
        alpha=1.0 / atr_period, adjust=False, min_periods=atr_period
    ).mean()
    ema_period = int(contract["signal"]["ema_period"])
    frame["ema"] = frame["bid_close"].ewm(
        span=ema_period, adjust=False, min_periods=ema_period
    ).mean()
    frame["ema_prior"] = frame["ema"].shift(
        int(contract["signal"]["ema_slope_lag_bars"])
    )
    return frame


def _build_report(
    *,
    contract: Mapping[str, Any],
    contract_file: Path,
    storage_root: Path,
    source_audits: Sequence[Mapping[str, Any]],
    bars: Sequence[Mapping[str, Any]],
    candidates: Sequence[Candidate],
    labels: Sequence[Any],
    outputs: Mapping[str, Path],
) -> dict[str, Any]:
    candidate_by_id = {row.candidate_id: row for row in candidates}
    resolved = [row for row in labels if row.status == "RESOLVED"]
    eligible = [row for row in labels if row.status != "INELIGIBLE"]
    active_days = _active_days_by_split(bars, contract)
    selected_family, train_profiles = _select_train_profile(
        labels=resolved,
        candidates=candidate_by_id,
        active_days=active_days,
        contract=contract,
    )
    selected_evidence: dict[str, Any] = {}
    test_bootstrap: dict[str, Any] | None = None
    final_gates: dict[str, bool] = {}
    if selected_family is not None:
        selected_rows = [row for row in resolved if row.family_id == selected_family]
        selected_evidence = {
            split: _stats(
                [row for row in selected_rows if row.split == split],
                candidate_by_id,
                active_days.get(split, 0),
                contract,
            )
            for split in ("train", "validation", "test")
        }
        test_bootstrap = _month_bootstrap(
            [row for row in selected_rows if row.split == "test"],
            samples=int(contract["bootstrap"]["calendar_month_samples"]),
            seed=int(contract["bootstrap"]["seed"]),
        )
        final_gates = _final_gates(
            selected_evidence, test_bootstrap, contract["strategy_gates"]
        )

    quality = contract["quality_gates"]
    quality_gates = {
        "verified_months_eq_expected": len(source_audits) == int(quality["expected_months"]),
        "resolved_share_ge_minimum": (
            len(resolved) / len(eligible) >= float(quality["minimum_resolved_share"])
            if eligible
            else False
        ),
        "candidate_ids_unique": len(candidate_by_id) == len(candidates),
        "candidate_keys_unique": len(
            {(row.family_id, row.decision_timestamp_ms, row.direction) for row in candidates}
        )
        == len(candidates),
        "all_declared_profiles_represented": {
            row.family_id for row in candidates
        }
        == {str(row["family_id"]) for row in contract["profiles"]},
    }
    if not all(quality_gates.values()):
        classification = "DUKASCOPY_SESSION_CAMPAIGN_INVALID"
    elif selected_family is None:
        classification = "DUKASCOPY_SESSION_CAMPAIGN_NO_TRAIN_SURVIVOR"
    elif all(final_gates.values()):
        classification = "DUKASCOPY_SESSION_CAMPAIGN_RESEARCH_SURVIVOR"
    else:
        classification = "DUKASCOPY_SESSION_CAMPAIGN_NO_FINAL_SURVIVOR"

    return {
        "schema_version": str(contract["schema_version"]),
        "classification": classification,
        "created_at_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "contract": str(contract_file),
        "contract_sha256": _sha256_file(contract_file),
        "storage_root": str(storage_root),
        "source_months": len(source_audits),
        "source_composite_sha256": _sha256_json(
            [(row["month"], row["source_files_composite_sha256"]) for row in source_audits]
        ),
        "h1_bars": len(bars),
        "active_days_by_split": active_days,
        "candidate_count": len(candidates),
        "resolved_count": len(resolved),
        "resolved_share": len(resolved) / len(eligible) if eligible else 0.0,
        "candidates_by_profile": dict(Counter(row.family_id for row in candidates)),
        "ineligible_reasons": dict(
            Counter(row.exit_reason for row in labels if row.status == "INELIGIBLE")
        ),
        "unresolved_reasons": dict(
            Counter(row.exit_reason for row in labels if row.status == "UNRESOLVED")
        ),
        "quality_gates": quality_gates,
        "train_profiles": train_profiles,
        "selected_family_id": selected_family,
        "selected_evidence": selected_evidence,
        "test_calendar_month_bootstrap": test_bootstrap,
        "strategy_gates": final_gates,
        "artifacts": {
            key: {"path": str(path), "sha256": _sha256_file(path)}
            for key, path in outputs.items()
            if key in {"candidates_csv", "labels_csv"}
        },
        "authorization": {
            **contract["authorization"],
            "strategy_promotion_authorized": False,
        },
        "limitations": [
            "A research survivor is not demo or live authorization.",
            "Fixed 0.01-lot results are not account-relative sizing or risk-of-ruin evidence.",
            "Dukascopy-to-broker feed differences require shadow and demo calibration.",
            "Repeated research campaigns increase program-level holdout contamination risk.",
        ],
    }


def _select_train_profile(
    *,
    labels: Sequence[Any],
    candidates: Mapping[str, Candidate],
    active_days: Mapping[str, int],
    contract: Mapping[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    output: dict[str, Any] = {}
    passing: list[str] = []
    for profile in contract["profiles"]:
        family_id = str(profile["family_id"])
        rows = [
            row
            for row in labels
            if row.status == "RESOLVED"
            and row.split == "train"
            and row.family_id == family_id
        ]
        metrics = _stats(rows, candidates, active_days.get("train", 0), contract)
        bootstrap = _month_bootstrap(
            rows,
            samples=int(contract["bootstrap"]["calendar_month_samples"]),
            seed=int(contract["bootstrap"]["seed"]),
        )
        gates = _train_gates(metrics, bootstrap, contract["train_selection_gates"])
        output[family_id] = {
            "mechanism": str(profile["mechanism"]),
            "lookback_h1_bars": int(profile["lookback_h1_bars"]),
            "reward_r": float(profile["reward_r"]),
            "train": metrics,
            "train_calendar_month_bootstrap": bootstrap,
            "train_gates": gates,
            "train_eligible": all(gates.values()),
        }
        if all(gates.values()):
            passing.append(family_id)
    if not passing:
        return None, output
    passing.sort(
        key=lambda family_id: (
            -float(
                output[family_id]["train_calendar_month_bootstrap"][
                    "average_stress_r_p025"
                ]
            ),
            -float(output[family_id]["train"]["stress_profit_factor"] or 0.0),
            -float(output[family_id]["train"]["average_stress_r"]),
            -float(output[family_id]["train"]["trades_per_active_day"]),
            family_id,
        )
    )
    return passing[0], output


def _train_gates(
    metrics: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    configured: Mapping[str, Any],
) -> dict[str, bool]:
    p025 = bootstrap.get("average_stress_r_p025")
    return {
        "rows_ge_minimum": metrics["trades"] >= int(configured["minimum_resolved_rows"]),
        "each_direction_rows_ge_minimum": all(
            metrics["direction_counts"].get(direction, 0)
            >= int(configured["minimum_rows_each_direction"])
            for direction in ("LONG", "SHORT")
        ),
        "each_session_rows_ge_minimum": all(
            metrics["session_counts"].get(session, 0)
            >= int(configured["minimum_rows_each_session"])
            for session in ("LONDON", "NEW_YORK")
        ),
        "trades_per_active_day_ge_minimum": metrics["trades_per_active_day"]
        >= float(configured["minimum_trades_per_active_day"]),
        "pf_ge_minimum": (metrics["stress_profit_factor"] or 0.0)
        >= float(configured["minimum_stress_profit_factor"]),
        "average_r_ge_minimum": metrics["average_stress_r"]
        >= float(configured["minimum_average_stress_r"]),
        "drawdown_r_lte_maximum": metrics["max_closed_drawdown_r"]
        <= float(configured["maximum_closed_drawdown_r"]),
        "positive_month_share_ge_minimum": metrics["positive_exit_month_share"]
        >= float(configured["minimum_positive_exit_month_share"]),
        "bootstrap_p025_ge_minimum": p025 is not None
        and float(p025) >= float(configured["minimum_bootstrap_average_r_p025"]),
    }


def _final_gates(
    evidence: Mapping[str, Mapping[str, Any]],
    bootstrap: Mapping[str, Any],
    configured: Mapping[str, Any],
) -> dict[str, bool]:
    validation = evidence["validation"]
    test = evidence["test"]
    p025 = bootstrap.get("average_stress_r_p025")
    return {
        "validation_rows_ge_minimum": validation["trades"]
        >= int(configured["minimum_validation_rows"]),
        "test_rows_ge_minimum": test["trades"] >= int(configured["minimum_test_rows"]),
        "validation_each_direction_rows_ge_minimum": all(
            validation["direction_counts"].get(direction, 0)
            >= int(configured["minimum_validation_rows_each_direction"])
            for direction in ("LONG", "SHORT")
        ),
        "test_each_direction_rows_ge_minimum": all(
            test["direction_counts"].get(direction, 0)
            >= int(configured["minimum_test_rows_each_direction"])
            for direction in ("LONG", "SHORT")
        ),
        "validation_each_session_rows_ge_minimum": all(
            validation["session_counts"].get(session, 0)
            >= int(configured["minimum_validation_rows_each_session"])
            for session in ("LONDON", "NEW_YORK")
        ),
        "test_each_session_rows_ge_minimum": all(
            test["session_counts"].get(session, 0)
            >= int(configured["minimum_test_rows_each_session"])
            for session in ("LONDON", "NEW_YORK")
        ),
        "validation_frequency_ge_minimum": validation["trades_per_active_day"]
        >= float(configured["minimum_validation_trades_per_active_day"]),
        "test_frequency_ge_minimum": test["trades_per_active_day"]
        >= float(configured["minimum_test_trades_per_active_day"]),
        "validation_pf_ge_minimum": (validation["stress_profit_factor"] or 0.0)
        >= float(configured["minimum_validation_stress_profit_factor"]),
        "test_pf_ge_minimum": (test["stress_profit_factor"] or 0.0)
        >= float(configured["minimum_test_stress_profit_factor"]),
        "validation_average_r_ge_minimum": validation["average_stress_r"]
        >= float(configured["minimum_validation_average_stress_r"]),
        "test_average_r_ge_minimum": test["average_stress_r"]
        >= float(configured["minimum_test_average_stress_r"]),
        "test_drawdown_r_lte_maximum": test["max_closed_drawdown_r"]
        <= float(configured["maximum_test_closed_drawdown_r"]),
        "validation_positive_month_share_ge_minimum": validation[
            "positive_exit_month_share"
        ]
        >= float(configured["minimum_validation_positive_exit_month_share"]),
        "test_positive_month_share_ge_minimum": test["positive_exit_month_share"]
        >= float(configured["minimum_test_positive_exit_month_share"]),
        "concurrent_trades_lte_maximum": max(
            validation["maximum_concurrent_trades"], test["maximum_concurrent_trades"]
        )
        <= int(configured["maximum_concurrent_trades"]),
        "test_bootstrap_p025_above_zero": p025 is not None and float(p025) > 0.0,
    }


def _stats(
    rows: Sequence[Any],
    candidates: Mapping[str, Candidate],
    active_days: int,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: (row.exit_time_utc, row.candidate_id))
    pnl = [float(row.stress_net_pnl_usd) for row in ordered]
    returns = [float(row.stress_net_r) for row in ordered]
    gross_profit = sum(value for value in pnl if value > 0.0)
    gross_loss = -sum(value for value in pnl if value < 0.0)
    direction_counts = Counter(row.direction for row in ordered)
    session_counts = Counter(
        _session_for_candidate(candidates[row.candidate_id], contract) for row in ordered
    )
    by_month: dict[str, float] = defaultdict(float)
    by_day: dict[str, float] = defaultdict(float)
    trade_count_by_day: Counter[str] = Counter()
    for row in ordered:
        by_month[row.exit_time_utc[:7]] += float(row.stress_net_pnl_usd)
        by_day[row.exit_time_utc[:10]] += float(row.stress_net_pnl_usd)
        trade_count_by_day[row.exit_time_utc[:10]] += 1
    positive_months = sum(value > 0.0 for value in by_month.values())
    positive_days = sum(value > 0.0 for value in by_day.values())
    return {
        "trades": len(ordered),
        "wins": sum(value > 0.0 for value in pnl),
        "win_rate_pct": 100.0 * sum(value > 0.0 for value in pnl) / len(pnl) if pnl else 0.0,
        "stress_net_usd": sum(pnl),
        "stress_profit_factor": gross_profit / gross_loss if gross_loss > 0.0 else None,
        "average_stress_r": sum(returns) / len(returns) if returns else 0.0,
        "max_closed_drawdown_r": _max_drawdown(returns),
        "max_closed_drawdown_usd": _max_drawdown(pnl),
        "active_source_days": active_days,
        "trades_per_active_day": len(ordered) / active_days if active_days else 0.0,
        "active_trade_days": len(by_day),
        "positive_trade_days": positive_days,
        "positive_trade_day_share": positive_days / len(by_day) if by_day else 0.0,
        "maximum_trades_one_exit_day": max(trade_count_by_day.values(), default=0),
        "direction_counts": dict(direction_counts),
        "session_counts": dict(session_counts),
        "active_exit_months": len(by_month),
        "positive_exit_months": positive_months,
        "positive_exit_month_share": positive_months / len(by_month) if by_month else 0.0,
        "maximum_concurrent_trades": _maximum_concurrency(ordered),
    }


def _month_bootstrap(
    rows: Sequence[Any], *, samples: int, seed: int
) -> dict[str, Any]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[row.exit_time_utc[:7]].append(float(row.stress_net_r))
    months = sorted(groups)
    if len(months) < 6:
        return {
            "samples": samples,
            "seed": seed,
            "active_exit_months": len(months),
            "average_stress_r_p025": None,
            "average_stress_r_p50": None,
            "average_stress_r_p975": None,
        }
    rng = random.Random(seed)
    estimates = []
    for _ in range(samples):
        selected = [rng.choice(months) for _ in months]
        values = [value for month in selected for value in groups[month]]
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


def _active_days_by_split(
    bars: Sequence[Mapping[str, Any]], contract: Mapping[str, Any]
) -> dict[str, int]:
    signal_hours = {
        int(hour) for hours in contract["sessions"].values() for hour in hours
    }
    days: dict[str, set[str]] = defaultdict(set)
    for row in bars:
        timestamp_ms = int(row["timestamp_ms"])
        start = datetime.fromtimestamp(timestamp_ms / 1000, UTC)
        if start.weekday() >= 5 or start.hour not in signal_hours:
            continue
        split = _split_for_timestamp(
            datetime.fromtimestamp((timestamp_ms + HOUR_MS) / 1000, UTC),
            contract["splits"],
        )
        if split is not None:
            days[split].add(start.date().isoformat())
    return {split: len(days.get(split, set())) for split in ("train", "validation", "test")}


def _maximum_concurrency(rows: Sequence[Any]) -> int:
    events = []
    for row in rows:
        if not row.entry_time_utc or not row.exit_time_utc:
            continue
        events.append((_parse_utc(row.entry_time_utc), 1))
        events.append((_parse_utc(row.exit_time_utc), -1))
    current = maximum = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        current += delta
        maximum = max(maximum, current)
    return maximum


def _session_for_candidate(
    candidate: Candidate, contract: Mapping[str, Any]
) -> str:
    hour = _parse_utc(candidate.signal_bar_start_utc).hour
    matches = [
        name for name, hours in contract["sessions"].items() if hour in {int(value) for value in hours}
    ]
    if len(matches) != 1:
        raise SessionCampaignError(f"candidate session is ambiguous: {candidate.candidate_id}")
    return matches[0]


def _render(payload: Mapping[str, Any]) -> str:
    lines = [
        "# A3 ML Dukascopy Session Campaign V1",
        "",
        f"Classification: `{payload['classification']}`",
        "",
        "Historical Dukascopy research only. No demo or broker action is authorized.",
        "",
        "## Population",
        "",
        f"- Candidates: `{payload['candidate_count']}`",
        f"- Resolved: `{payload['resolved_count']}` ({payload['resolved_share'] * 100.0:.2f}%)",
        f"- Selected family: `{payload['selected_family_id']}`",
        "",
        "## Train-Only Profile Screen",
        "",
        "| Profile | Trades | Trades/day | PF | Avg R | DD R | Positive months | Eligible |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for family_id, profile in payload["train_profiles"].items():
        row = profile["train"]
        lines.append(
            f"| {family_id} | {row['trades']} | {row['trades_per_active_day']:.3f} | "
            f"{(row['stress_profit_factor'] or 0.0):.4f} | {row['average_stress_r']:.4f} | "
            f"{row['max_closed_drawdown_r']:.2f} | {row['positive_exit_months']}/{row['active_exit_months']} | "
            f"{'YES' if profile['train_eligible'] else 'NO'} |"
        )
    if payload["selected_family_id"] is None:
        lines.extend(
            [
                "",
                "No profile passed every train-selection gate. Validation and test metrics are suppressed.",
            ]
        )
    else:
        lines.extend(
            [
                "",
                "## Frozen Profile Evidence",
                "",
                "| Split | Trades | Trades/day | Win rate | Net USD | PF | Avg R | DD R | Positive months |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for split in ("train", "validation", "test"):
            row = payload["selected_evidence"][split]
            lines.append(
                f"| {split} | {row['trades']} | {row['trades_per_active_day']:.3f} | "
                f"{row['win_rate_pct']:.2f}% | {row['stress_net_usd']:.2f} | "
                f"{(row['stress_profit_factor'] or 0.0):.4f} | {row['average_stress_r']:.4f} | "
                f"{row['max_closed_drawdown_r']:.2f} | {row['positive_exit_months']}/{row['active_exit_months']} |"
            )
        lines.extend(["", "## Final Gates", ""])
        for name, passed in payload["strategy_gates"].items():
            lines.append(f"- `{name}`: {'PASS' if passed else 'FAIL'}")
    lines.extend(
        [
            "",
            "Strategy promotion, demo prediction, EA consumption, and broker action remain disabled.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_contract(contract: Mapping[str, Any]) -> None:
    if contract.get("schema_version") != "a3_ml_dukascopy_session_campaign_v1":
        raise ValueError("unexpected session-campaign contract version")
    if contract.get("symbol") != "XAUUSD":
        raise ValueError("session campaign V1 is locked to XAUUSD")
    if contract.get("sessions") != {"LONDON": [6, 7], "NEW_YORK": [12, 13]}:
        raise ValueError("session-campaign hours differ from the frozen lock")
    expected = {
        (mechanism, lookback, reward)
        for mechanism in ("BREAKOUT", "SWEEP_REVERSAL")
        for lookback in (4, 8)
        for reward in (1.5, 2.0)
    }
    actual = {
        (
            str(row["mechanism"]),
            int(row["lookback_h1_bars"]),
            float(row["reward_r"]),
        )
        for row in contract["profiles"]
    }
    family_ids = [str(row["family_id"]) for row in contract["profiles"]]
    if actual != expected or len(family_ids) != 8 or len(set(family_ids)) != 8:
        raise ValueError("session-campaign profile set differs from the frozen lock")
    if not contract["authorization"].get("research_only"):
        raise ValueError("session campaign must remain research-only")
    if any(
        contract["authorization"].get(key)
        for key in (
            "python_demo_predictions_authorized",
            "ea_consumption_authorized",
            "broker_action_authorized",
        )
    ):
        raise ValueError("session-campaign contract contains forbidden authorization")
    if int(contract["execution"]["maximum_hold_hours"]) != 8:
        raise ValueError("session campaign V1 requires the frozen eight-hour hold")
    if float(contract["train_selection_gates"]["minimum_trades_per_active_day"]) != 0.75:
        raise ValueError("session campaign V1 requires the frozen train frequency gate")


def _resolve_storage_root(contract: Mapping[str, Any]) -> Path:
    name = str(contract["storage_environment_variable"])
    value = os.environ.get(name, "").strip() or str(contract["default_storage_root"])
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(root)
    return root


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


def _parse_utc(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-aware: {value}")
    return parsed.astimezone(UTC)


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _iso_ms(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, UTC).isoformat(
        timespec="milliseconds"
    ).replace("+00:00", "Z")

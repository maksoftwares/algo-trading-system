from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


def candidate_id(origin_attempt: int, signal_time: pd.Timestamp) -> str:
    payload = f"{origin_attempt}|{signal_time.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def generate_candidates(
    decisions: pd.DataFrame,
    execution_frame: pd.DataFrame,
    campaign: Any,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    definition = config["candidate"]
    params = definition["parameters"]
    mask, direction = campaign.signal_mask_direction(
        decisions, str(definition["mechanic"]), params
    )
    raw_signals = int(mask.sum())
    if raw_signals != int(definition["expected_raw_signals"]):
        raise ValueError(
            f"Origin signal count changed: {raw_signals} != "
            f"{definition['expected_raw_signals']}"
        )
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    geometry = definition["geometry"]
    hold = pd.Timedelta(hours=float(geometry["maximum_hold_hours"]))
    rows: list[dict[str, Any]] = []
    for decision_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
        signal = decisions.iloc[int(decision_index)]
        signal_index = int(signal["execution_index"])
        entry_index = signal_index + 1
        if entry_index >= len(execution_frame):
            continue
        entry_bar = execution_frame.iloc[entry_index]
        signal_time = pd.Timestamp(signal["timestamp_utc"])
        scheduled = pd.Timestamp(entry_bar["bar_start_utc"])
        if scheduled < signal_time:
            raise ValueError("Scheduled entry precedes its signal")
        gap_minutes = (scheduled - signal_time).total_seconds() / 60.0
        if gap_minutes > float(config["execution"]["maximum_entry_gap_minutes"]):
            continue
        if scheduled + hold >= end:
            continue
        sign = int(direction.iat[int(decision_index)])
        if sign not in (-1, 1):
            raise ValueError("Candidate direction is not executable")
        rows.append(
            {
                "candidate_id": candidate_id(
                    int(definition["origin_attempt"]), signal_time
                ),
                "origin_attempt": int(definition["origin_attempt"]),
                "origin_variant_id": str(definition["origin_variant_id"]),
                "regime_owner": str(definition["regime_owner"]),
                "mechanic": str(definition["mechanic"]),
                "geometry_id": str(definition["geometry_id"]),
                "decision_index": int(decision_index),
                "execution_signal_index": signal_index,
                "signal_time": signal_time,
                "scheduled_entry_time": scheduled,
                "direction_sign": sign,
                "direction": "LONG" if sign > 0 else "SHORT",
                "signal_atr": float(signal["atr14"]),
                "stop_atr": float(geometry["stop_atr"]),
                "target_r": float(geometry["target_r"]),
                "hold_hours": float(geometry["maximum_hold_hours"]),
                "parameters_json": json.dumps(
                    params, sort_keys=True, separators=(",", ":")
                ),
            }
        )
    if not rows:
        raise ValueError("Candidate generation produced no executable rows")
    result = pd.DataFrame(rows).sort_values(
        ["scheduled_entry_time", "candidate_id"], kind="mergesort"
    ).reset_index(drop=True)
    if result["candidate_id"].duplicated().any():
        raise ValueError("Duplicate candidate IDs")
    return result


def _segments(
    tick_store: Any, start_ms: int, end_ms: int
) -> Iterable[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    iterator = getattr(tick_store, "segments", None)
    if iterator is not None:
        return iterator(start_ms, end_ms)
    return tick_store._segments(start_ms, end_ms)  # noqa: SLF001


def first_exit_hit(
    tick_store: Any,
    start_ms: int,
    end_ms: int,
    direction: int,
    stop: float,
    target: float,
    quote_type: Any,
) -> tuple[Any, float, str] | None:
    if end_ms < start_ms:
        return None
    for times, bids, asks in _segments(tick_store, start_ms, end_ms):
        executable = bids if direction > 0 else asks
        stop_hit = executable <= stop if direction > 0 else executable >= stop
        target_hit = executable >= target if direction > 0 else executable <= target
        indices = np.flatnonzero(stop_hit | target_hit)
        if len(indices) == 0:
            continue
        index = int(indices[0])
        quote = quote_type(
            int(times[index]), float(bids[index]), float(asks[index])
        )
        price = float(executable[index])
        if bool(stop_hit[index]):
            reason = "STOP" if price == stop else "STOP_SLIPPAGE"
            return quote, price, reason
        return quote, float(target), "TARGET"
    return None


def execute_candidate(
    candidate: Any,
    tick_store: Any,
    quote_type: Any,
    execution: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    scheduled = pd.Timestamp(candidate.scheduled_entry_time)
    scheduled_ms = int(scheduled.value // 1_000_000)
    entry_quote = tick_store.first_quote_at_or_after(
        scheduled_ms,
        int(float(execution["maximum_entry_gap_minutes"]) * 60_000),
    )
    if entry_quote is None:
        return None, "NO_TIMELY_ENTRY_QUOTE"
    direction = int(candidate.direction_sign)
    entry = float(entry_quote.ask if direction > 0 else entry_quote.bid)
    risk = float(candidate.stop_atr) * float(candidate.signal_atr)
    if not np.isfinite(risk) or risk <= 0.0:
        return None, "INVALID_RISK"
    spread = float(entry_quote.ask - entry_quote.bid)
    if spread < 0.0 or spread / risk > float(execution["maximum_entry_spread_r"]):
        return None, "ENTRY_SPREAD_R"
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None, "RISK_CEILING"
    stop = entry - direction * risk
    target = entry + direction * float(candidate.target_r) * risk
    deadline = scheduled + pd.Timedelta(hours=float(candidate.hold_hours))
    deadline_ms = int(deadline.value // 1_000_000)
    horizon_quote = tick_store.first_quote_at_or_after(
        deadline_ms,
        int(float(execution["maximum_horizon_gap_hours"]) * 3_600_000),
    )
    if horizon_quote is None:
        return None, "NO_HORIZON_QUOTE"
    observed = first_exit_hit(
        tick_store,
        int(entry_quote.timestamp_ms),
        int(horizon_quote.timestamp_ms) - 1,
        direction,
        stop,
        target,
        quote_type,
    )
    if observed is None:
        exit_quote = horizon_quote
        exit_price = float(
            horizon_quote.bid if direction > 0 else horizon_quote.ask
        )
        exit_reason = "FIXED_HORIZON"
    else:
        exit_quote, exit_price, exit_reason = observed
    entry_time = pd.Timestamp(entry_quote.timestamp_ms, unit="ms", tz="UTC")
    exit_time = pd.Timestamp(exit_quote.timestamp_ms, unit="ms", tz="UTC")
    gross_r = direction * (float(exit_price) - entry) / risk
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86_400.0)
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return (
        {
            "candidate_id": str(candidate.candidate_id),
            "origin_attempt": int(candidate.origin_attempt),
            "origin_variant_id": str(candidate.origin_variant_id),
            "regime_owner": str(candidate.regime_owner),
            "mechanic": str(candidate.mechanic),
            "geometry_id": str(candidate.geometry_id),
            "signal_time": pd.Timestamp(candidate.signal_time),
            "scheduled_entry_time": scheduled,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "entry_tick_timestamp_ms": int(entry_quote.timestamp_ms),
            "exit_tick_timestamp_ms": int(exit_quote.timestamp_ms),
            "direction": "LONG" if direction > 0 else "SHORT",
            "direction_sign": direction,
            "entry_price": entry,
            "exit_price": float(exit_price),
            "stop": stop,
            "target": target,
            "risk_price": risk,
            "risk_usd": risk_usd,
            "entry_spread_r": spread / risk,
            "gross_r": gross_r,
            "stress_net_r": gross_r
            - extra_cost_r
            - float(execution["stress_slippage_r"]),
            "holding_minutes": (exit_time - entry_time).total_seconds() / 60.0,
            "horizon_delay_minutes": max(
                0.0,
                (
                    pd.Timestamp(horizon_quote.timestamp_ms, unit="ms", tz="UTC")
                    - deadline
                ).total_seconds()
                / 60.0,
            ),
            "exit_reason": exit_reason,
            "raw_tick_execution": True,
        },
        None,
    )


def simulate_candidate_stream(
    candidates: pd.DataFrame,
    tick_store: Any,
    quote_type: Any,
    execution: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    rows: list[dict[str, Any]] = []
    rejections: dict[str, int] = {}
    position_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for candidate in candidates.sort_values(
        ["scheduled_entry_time", "candidate_id"], kind="mergesort"
    ).itertuples(index=False):
        outcome, reason = execute_candidate(
            candidate, tick_store, quote_type, execution
        )
        if outcome is None:
            label = str(reason)
            rejections[label] = rejections.get(label, 0) + 1
            continue
        entry_time = pd.Timestamp(outcome["entry_time"])
        if entry_time < position_until:
            rejections["POSITION_OVERLAP"] = (
                rejections.get("POSITION_OVERLAP", 0) + 1
            )
            continue
        day = entry_time.date()
        maximum = int(execution["maximum_trades_per_variant_utc_day"])
        if daily_count.get(day, 0) >= maximum:
            rejections["DAILY_CAP"] = rejections.get("DAILY_CAP", 0) + 1
            continue
        rows.append(outcome)
        position_until = pd.Timestamp(outcome["exit_time"])
        daily_count[day] = daily_count.get(day, 0) + 1
    result = (
        pd.DataFrame(rows).sort_values("entry_time", kind="mergesort").reset_index(drop=True)
        if rows
        else pd.DataFrame()
    )
    return result, dict(sorted(rejections.items()))


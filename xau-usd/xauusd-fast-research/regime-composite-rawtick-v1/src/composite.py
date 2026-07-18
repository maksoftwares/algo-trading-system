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
    frame: pd.DataFrame,
    v1_manifest: pd.DataFrame,
    config: Mapping[str, Any],
    v1_campaign: Any,
) -> pd.DataFrame:
    requested = {
        int(attempt)
        for composite in config["composites"]
        for attempt in composite["component_attempts"]
    }
    indexed = v1_manifest.set_index("attempt_no", drop=False)
    missing = sorted(requested.difference(int(value) for value in indexed.index))
    if missing:
        raise ValueError(f"V1 component attempts are unavailable: {missing}")
    memberships = {
        int(attempt): str(composite["composite_id"])
        for composite in config["composites"]
        for attempt in composite["component_attempts"]
    }
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    rows: list[dict[str, Any]] = []
    for origin_attempt in sorted(requested):
        source = indexed.loc[origin_attempt]
        params = json.loads(str(source["parameters_json"]))
        mask, direction = v1_campaign.signal_mask_direction(
            frame, str(source["mechanic"]), params
        )
        for signal_index in np.flatnonzero(mask.to_numpy(dtype=bool)):
            entry_index = int(signal_index) + 1
            if entry_index >= len(frame):
                continue
            signal = frame.iloc[int(signal_index)]
            entry_bar = frame.iloc[entry_index]
            signal_time = pd.Timestamp(signal["timestamp_utc"])
            scheduled_entry = pd.Timestamp(entry_bar["bar_start_utc"])
            if scheduled_entry < signal_time or scheduled_entry >= end:
                continue
            if (scheduled_entry - signal_time).total_seconds() > 600.0:
                continue
            sign = int(direction.iat[int(signal_index)])
            rows.append(
                {
                    "candidate_id": candidate_id(origin_attempt, signal_time),
                    "composite_id": memberships[origin_attempt],
                    "origin_attempt": origin_attempt,
                    "origin_variant_id": str(source["variant_id"]),
                    "regime_owner": str(source["regime_owner"]),
                    "mechanic": str(source["mechanic"]),
                    "signal_index": int(signal_index),
                    "signal_time": signal_time,
                    "scheduled_entry_time": scheduled_entry,
                    "direction_sign": sign,
                    "direction": "LONG" if sign > 0 else "SHORT",
                    "signal_atr": float(signal["atr14"]),
                    "stop_atr": float(params["stop_atr"]),
                    "hold_hours": float(params["hold_hours"]),
                    "parameters_json": str(source["parameters_json"]),
                }
            )
    result = pd.DataFrame(rows).sort_values(
        ["scheduled_entry_time", "origin_attempt"], kind="mergesort"
    ).reset_index(drop=True)
    if result.empty:
        raise ValueError("Candidate generation produced no rows")
    if result["candidate_id"].duplicated().any():
        raise ValueError("Duplicate raw-tick candidate IDs")
    if result["scheduled_entry_time"].ge(end).any():
        raise ValueError("Candidate escaped the locked data boundary")
    return result


def _segments(
    tick_store: Any, start_ms: int, end_ms: int
) -> Iterable[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    iterator = getattr(tick_store, "segments", None)
    if iterator is not None:
        return iterator(start_ms, end_ms)
    return tick_store._segments(start_ms, end_ms)  # noqa: SLF001


def first_stop_hit(
    tick_store: Any,
    start_ms: int,
    end_ms: int,
    direction: int,
    stop: float,
    quote_type: Any,
) -> tuple[Any, float, str] | None:
    for times, bids, asks in _segments(tick_store, start_ms, end_ms):
        executable = bids if direction > 0 else asks
        hit = executable <= stop if direction > 0 else executable >= stop
        indices = np.flatnonzero(hit)
        if len(indices) == 0:
            continue
        index = int(indices[0])
        quote = quote_type(
            int(times[index]), float(bids[index]), float(asks[index])
        )
        price = float(executable[index])
        reason = "STOP" if price == stop else "STOP_SLIPPAGE"
        return quote, price, reason
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
    if spread < 0.0 or spread / risk > float(
        execution["maximum_entry_spread_r"]
    ):
        return None, "ENTRY_SPREAD_R"
    risk_usd = risk * float(execution["ounces_at_lot_size"])
    if risk_usd > float(execution["maximum_research_risk_usd"]):
        return None, "RISK_CEILING"
    stop = entry - direction * risk
    deadline = scheduled + pd.Timedelta(hours=float(candidate.hold_hours))
    deadline_ms = int(deadline.value // 1_000_000)
    horizon_quote = tick_store.first_quote_at_or_after(
        deadline_ms,
        int(float(execution["maximum_horizon_gap_hours"]) * 3_600_000),
    )
    if horizon_quote is None:
        return None, "NO_HORIZON_QUOTE"
    observed = first_stop_hit(
        tick_store,
        int(entry_quote.timestamp_ms),
        int(horizon_quote.timestamp_ms),
        direction,
        stop,
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
    holding_days = max(0.0, (exit_time - entry_time).total_seconds() / 86400.0)
    extra_cost_r = (
        float(execution["ticket_cost_usd"])
        + holding_days * float(execution["holding_cost_per_24h_usd"])
    ) / risk_usd
    return (
        {
            "candidate_id": str(candidate.candidate_id),
            "composite_id": str(candidate.composite_id),
            "origin_attempt": int(candidate.origin_attempt),
            "origin_variant_id": str(candidate.origin_variant_id),
            "regime_owner": str(candidate.regime_owner),
            "mechanic": str(candidate.mechanic),
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
                (pd.Timestamp(horizon_quote.timestamp_ms, unit="ms", tz="UTC") - deadline).total_seconds()
                / 60.0,
            ),
            "exit_reason": exit_reason,
            "raw_tick_execution": True,
        },
        None,
    )


def simulate_components(
    candidates: pd.DataFrame,
    tick_store: Any,
    quote_type: Any,
    execution: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    rows: list[dict[str, Any]] = []
    rejections: dict[str, int] = {}
    for origin_attempt, group in candidates.groupby("origin_attempt", sort=True):
        position_until = pd.Timestamp.min.tz_localize("UTC")
        daily_count: dict[Any, int] = {}
        for candidate in group.sort_values(
            "scheduled_entry_time", kind="mergesort"
        ).itertuples(index=False):
            scheduled = pd.Timestamp(candidate.scheduled_entry_time)
            if scheduled < position_until:
                rejections["COMPONENT_POSITION_OVERLAP"] = (
                    rejections.get("COMPONENT_POSITION_OVERLAP", 0) + 1
                )
                continue
            day = scheduled.date()
            if daily_count.get(day, 0) >= int(
                execution["maximum_trades_per_component_utc_day"]
            ):
                rejections["COMPONENT_DAILY_CAP"] = (
                    rejections.get("COMPONENT_DAILY_CAP", 0) + 1
                )
                continue
            outcome, reason = execute_candidate(
                candidate, tick_store, quote_type, execution
            )
            if outcome is None:
                label = str(reason)
                rejections[label] = rejections.get(label, 0) + 1
                continue
            rows.append(outcome)
            position_until = pd.Timestamp(outcome["exit_time"])
            daily_count[day] = daily_count.get(day, 0) + 1
    result = (
        pd.DataFrame(rows).sort_values(
            ["entry_time", "origin_attempt"], kind="mergesort"
        ).reset_index(drop=True)
        if rows
        else pd.DataFrame()
    )
    return result, dict(sorted(rejections.items()))


def build_composite_trades(
    component_trades: pd.DataFrame, config: Mapping[str, Any]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for composite in config["composites"]:
        attempts = {int(value) for value in composite["component_attempts"]}
        selected = component_trades.loc[
            component_trades["origin_attempt"].isin(attempts)
        ].sort_values(["entry_time", "origin_attempt"], kind="mergesort")
        position_until = pd.Timestamp.min.tz_localize("UTC")
        for trade in selected.itertuples(index=False):
            if pd.Timestamp(trade.entry_time) < position_until:
                continue
            row = trade._asdict()
            row["attempt_no"] = int(composite["attempt_no"])
            row["composite_id"] = str(composite["composite_id"])
            rows.append(row)
            position_until = pd.Timestamp(trade.exit_time)
    return (
        pd.DataFrame(rows).sort_values(
            ["entry_time", "attempt_no"], kind="mergesort"
        ).reset_index(drop=True)
        if rows
        else pd.DataFrame()
    )

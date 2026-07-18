from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


def candidate_id(origin_attempt: int, signal_time: pd.Timestamp) -> str:
    payload = f"{origin_attempt}|{signal_time.isoformat()}".encode("ascii")
    return hashlib.sha256(payload).hexdigest()[:24]


def signal_stream_sha256(
    frame: pd.DataFrame, mask: pd.Series, direction: pd.Series
) -> str:
    rows = [
        f"{pd.Timestamp(frame['bar_end_utc'].iat[index]).isoformat()}|"
        f"{int(direction.iat[index])}"
        for index in np.flatnonzero(mask.to_numpy(dtype=bool))
    ]
    return hashlib.sha256("\n".join(rows).encode("ascii")).hexdigest()


def _session_mask(frame: pd.DataFrame, session: str) -> pd.Series:
    if session == "ALL":
        return pd.Series(True, index=frame.index)
    bounds = {"ASIA": (0, 6), "LONDON": (6, 12), "NY": (12, 18)}
    if session not in bounds:
        raise KeyError(session)
    start, end = bounds[session]
    return frame["hour_utc_custom"].ge(start) & frame["hour_utc_custom"].lt(end)


def independent_signal_mask_direction(
    frame: pd.DataFrame, mechanic: str, params: Mapping[str, Any]
) -> tuple[pd.Series, pd.Series]:
    window = int(params["stationarity_window"])
    z_score = frame[f"z_{window}"]
    direction = pd.Series(np.sign(z_score.fillna(0.0)).astype(int), index=frame.index)
    risk_atr = frame["risk_atr"].replace(0.0, np.nan)
    move_3 = frame["return_3"].div(risk_atr)
    move_12 = frame["return_12"].div(risk_atr)
    imbalance = frame["tick_imbalance_15m"]
    if mechanic == "CHOP_COUNTERFLOW_TIERED_ENVELOPE":
        horizon = int(params["variance_horizon"])
        variance_ratio = frame[f"variance_ratio_{horizon}_{window}"]
        strong = (
            z_score.abs().ge(float(params["strong_z_abs_min"]))
            & variance_ratio.le(float(params["strong_variance_ratio_max"]))
        )
        moderate = (
            z_score.abs().ge(float(params["moderate_z_abs_min"]))
            & variance_ratio.le(float(params["moderate_variance_ratio_max"]))
        )
        state = (
            (strong | moderate)
            & frame[f"return_acf_1_{window}"].le(float(params["return_acf_max"]))
            & frame[f"mean_slope_atr_{window}"].abs().le(
                float(params["mean_slope_abs_max"])
            )
        )
        move = move_3 if int(params["m5_confirmation_window"]) == 3 else move_12
        confirmation = (
            direction.mul(move).le(float(params["counter_move_max"]))
            & direction.mul(imbalance).le(float(params["counter_flow_max"]))
        )
    elif mechanic == "CHOP_Z_EXPANSION_DUAL_WINDOW_ENVELOPE":
        state = (
            z_score.abs().ge(float(params["z_abs_min"]))
            & direction.mul(frame[f"z_delta_{window}"]).ge(
                float(params["z_delta_min"])
            )
            & frame[f"variance_ratio_4_{window}"].le(
                float(params["variance_ratio_max"])
            )
            & frame[f"mean_slope_atr_{window}"].abs().le(
                float(params["mean_slope_abs_max"])
            )
        )
        confirmation = (
            (
                direction.mul(move_3).ge(float(params["m5_alignment_3_min"]))
                | direction.mul(move_12).ge(float(params["m5_alignment_12_min"]))
            )
            & direction.mul(imbalance).ge(float(params["flow_alignment_min"]))
        )
    elif mechanic == "CHOP_FAILED_REVERSION_DUAL_MODE_ENVELOPE":
        state = (
            z_score.abs().ge(float(params["z_abs_min"]))
            & frame[f"variance_ratio_4_{window}"].le(
                float(params["variance_ratio_max"])
            )
            & frame[f"return_acf_1_{window}"].le(float(params["return_acf_max"]))
            & frame[f"mean_slope_atr_{window}"].abs().le(
                float(params["mean_slope_abs_max"])
            )
        )
        move = move_3 if int(params["m5_confirmation_window"]) == 3 else move_12
        counterflow = (
            direction.mul(move).le(float(params["counter_move_max"]))
            & direction.mul(imbalance).le(float(params["counter_flow_max"]))
        )
        expansion = (
            direction.mul(frame[f"z_delta_{window}"]).ge(
                float(params["z_delta_min"])
            )
            & direction.mul(move).ge(float(params["direct_move_min"]))
            & direction.mul(imbalance).ge(float(params["direct_flow_min"]))
        )
        confirmation = counterflow | expansion
    else:
        raise KeyError(mechanic)
    valid = (
        pd.Series(state, index=frame.index).fillna(False)
        & frame["regime"].eq("CHOP")
        & frame["m15_state_age_m5"].between(
            0, int(params["m15_state_age_m5_max"]), inclusive="both"
        )
        & _session_mask(frame, str(params["session"]))
        & confirmation
        & direction.ne(0)
        & np.isfinite(frame["risk_atr"])
        & np.isfinite(frame["spread_ratio"])
    )
    return valid.astype(bool), direction.astype(int)


def generate_candidates(
    frame: pd.DataFrame,
    reference_campaign: Any,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, int]]:
    geometry = config["geometry"]
    hold_bars = int(geometry["hold_bars"])
    end = pd.Timestamp(config["source"]["end_exclusive_utc"])
    starts = frame["bar_start_utc"].dt.tz_localize(None).to_numpy()
    ends = frame["bar_end_utc"].dt.tz_localize(None).to_numpy()
    rows: list[dict[str, Any]] = []
    parity: dict[str, Any] = {}
    total_raw_signals = 0
    for definition in config["components"]:
        params = definition["parameters"]
        mechanic = str(definition["mechanic"])
        independent_mask, independent_direction = independent_signal_mask_direction(
            frame, mechanic, params
        )
        reference_mask, reference_direction = reference_campaign.signal_mask_direction(
            frame, mechanic, params
        )
        component_parity = {
            "mask_equal": bool(independent_mask.equals(reference_mask)),
            "direction_equal": bool(
                independent_direction.equals(reference_direction)
            ),
            "independent_signal_sha256": signal_stream_sha256(
                frame, independent_mask, independent_direction
            ),
            "reference_signal_sha256": signal_stream_sha256(
                frame, reference_mask, reference_direction
            ),
        }
        if not all(
            (component_parity["mask_equal"], component_parity["direction_equal"])
        ):
            raise ValueError(
                f"Independent signal logic differs for {mechanic}: {component_parity}"
            )
        raw_signals = int(independent_mask.sum())
        if raw_signals != int(definition["expected_raw_signals"]):
            raise ValueError(
                f"Origin {definition['origin_attempt']} signal count changed: "
                f"{raw_signals} != {definition['expected_raw_signals']}"
            )
        total_raw_signals += raw_signals
        parity[str(definition["origin_attempt"])] = component_parity
        for signal_index in np.flatnonzero(independent_mask.to_numpy(dtype=bool)):
            signal_index = int(signal_index)
            entry_index = signal_index + 1
            final_index = entry_index + hold_bars
            if entry_index >= len(frame) or final_index >= len(frame):
                continue
            if starts[entry_index] != ends[signal_index]:
                continue
            expected = starts[entry_index] + np.arange(
                hold_bars + 1
            ) * np.timedelta64(5, "m")
            if not np.array_equal(
                starts[entry_index : final_index + 1], expected
            ):
                continue
            scheduled = pd.Timestamp(frame["bar_start_utc"].iat[entry_index])
            deadline = pd.Timestamp(frame["bar_start_utc"].iat[final_index])
            if deadline >= end:
                continue
            signal_time = pd.Timestamp(frame["bar_end_utc"].iat[signal_index])
            sign = int(independent_direction.iat[signal_index])
            rows.append(
                {
                    "candidate_id": candidate_id(
                        int(definition["origin_attempt"]), signal_time
                    ),
                    "component_priority": int(definition["priority"]),
                    "origin_attempt": int(definition["origin_attempt"]),
                    "origin_variant_id": str(definition["origin_variant_id"]),
                    "regime_owner": str(definition["regime_owner"]),
                    "mechanic": mechanic,
                    "geometry_id": str(definition["geometry_id"]),
                    "signal_index": signal_index,
                    "signal_time": signal_time,
                    "scheduled_entry_time": scheduled,
                    "scheduled_deadline": deadline,
                    "direction_sign": sign,
                    "direction": "LONG" if sign > 0 else "SHORT",
                    "signal_atr": float(frame["risk_atr"].iat[signal_index]),
                    "stop_atr": float(geometry["stop_atr"]),
                    "target_r": float(geometry["target_r"]),
                    "hold_hours": float(geometry["maximum_hold_hours"]),
                    "parameters_json": json.dumps(
                        params, sort_keys=True, separators=(",", ":")
                    ),
                }
            )
    all_candidates = pd.DataFrame(rows).sort_values(
        ["scheduled_entry_time", "component_priority", "candidate_id"],
        kind="mergesort",
    )
    valid_component_candidates = int(len(all_candidates))
    duplicate_mask = all_candidates.duplicated(
        ["signal_time", "direction_sign", "geometry_id"], keep="first"
    )
    result = all_candidates.loc[~duplicate_mask].reset_index(drop=True)
    if result.empty or result["candidate_id"].duplicated().any():
        raise ValueError("Candidate stream is empty or contains duplicate IDs")
    audit = {
        "total_raw_signals": total_raw_signals,
        "valid_component_candidates": valid_component_candidates,
        "duplicate_candidates_removed": int(duplicate_mask.sum()),
        "unique_candidates": int(len(result)),
    }
    composite = config["composite"]
    expected = {
        "total_raw_signals": int(composite["expected_total_raw_signals"]),
        "valid_component_candidates": int(
            composite["expected_valid_component_candidates"]
        ),
        "unique_candidates": int(composite["expected_unique_candidates"]),
    }
    if any(audit[key] != value for key, value in expected.items()):
        raise ValueError(f"Composite candidate counts changed: {audit} != {expected}")
    return result, parity, audit


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
    deadline = pd.Timestamp(candidate.scheduled_deadline)
    deadline_ms = int(deadline.value // 1_000_000)
    horizon_quote = tick_store.first_quote_at_or_after(
        deadline_ms,
        int(float(execution["maximum_horizon_gap_minutes"]) * 60_000),
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
            "component_priority": int(candidate.component_priority),
            "attempt_no": int(candidate.origin_attempt),
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
    cooldown_until = pd.Timestamp.min.tz_localize("UTC")
    daily_count: dict[Any, int] = {}
    for candidate in candidates.sort_values(
        ["scheduled_entry_time", "component_priority", "candidate_id"],
        kind="mergesort",
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
        if entry_time < cooldown_until:
            rejections["COOLDOWN"] = rejections.get("COOLDOWN", 0) + 1
            continue
        day = entry_time.date()
        maximum = int(execution["maximum_trades_per_variant_utc_day"])
        if daily_count.get(day, 0) >= maximum:
            rejections["DAILY_CAP"] = rejections.get("DAILY_CAP", 0) + 1
            continue
        rows.append(outcome)
        position_until = pd.Timestamp(outcome["exit_time"])
        cooldown_until = position_until + pd.Timedelta(
            minutes=float(execution["cooldown_minutes"])
        )
        daily_count[day] = daily_count.get(day, 0) + 1
    result = (
        pd.DataFrame(rows).sort_values("entry_time", kind="mergesort").reset_index(
            drop=True
        )
        if rows
        else pd.DataFrame()
    )
    return result, dict(sorted(rejections.items()))

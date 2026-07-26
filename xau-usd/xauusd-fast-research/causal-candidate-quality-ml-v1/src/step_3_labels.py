from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

from step_3_common import timestamp_ms, timestamp_utc_ms
from step_3_sources import LockedDukascopyStore, SourceDataError


LABEL_COLUMNS = [
    "candidate_id",
    "action_row_id",
    "entry_time",
    "label_end_time",
    "initial_risk_price",
    "initial_risk_usd_0p01",
    "entry_price",
    "exit_price",
    "stop_price",
    "target_price",
    "gross_r",
    "base_cost_r",
    "stress_cost_r",
    "base_net_r",
    "stress_net_r",
    "stress_net_r_positive",
    "target_before_stop",
    "mfe_r",
    "mae_r",
    "holding_minutes",
    "exit_reason",
    "label_status",
]


def unresolved_label(
    row: Mapping[str, Any],
    *,
    status: str,
    label_end_ms: int | None = None,
    entry: tuple[int, float, float] | None = None,
    risk: float | None = None,
) -> dict[str, Any]:
    direction = str(row["direction"])
    entry_price = None
    if entry is not None:
        entry_price = float(entry[2] if direction == "LONG" else entry[1])
    return {
        "candidate_id": str(row["candidate_id"]),
        "action_row_id": str(row.get("action_row_id", "")),
        "entry_time": timestamp_utc_ms(entry[0]) if entry else pd.NaT,
        "label_end_time": timestamp_utc_ms(label_end_ms),
        "initial_risk_price": risk,
        "initial_risk_usd_0p01": risk,
        "entry_price": entry_price,
        "exit_price": None,
        "stop_price": None,
        "target_price": None,
        "gross_r": None,
        "base_cost_r": None,
        "stress_cost_r": None,
        "base_net_r": None,
        "stress_net_r": None,
        "stress_net_r_positive": None,
        "target_before_stop": None,
        "mfe_r": None,
        "mae_r": None,
        "holding_minutes": None,
        "exit_reason": status,
        "label_status": status,
    }


def _update_excursions(
    side_prices: np.ndarray,
    *,
    entry_price: float,
    sign: float,
    mfe: float,
    mae: float,
) -> tuple[float, float]:
    if not len(side_prices):
        return mfe, mae
    moves = sign * (side_prices - entry_price)
    return max(mfe, float(np.max(moves))), max(mae, float(np.max(-moves)))


def label_one(
    row: Mapping[str, Any],
    *,
    store: LockedDukascopyStore,
    label_contract: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_id = str(row["candidate_id"])
    direction = str(row["direction"])
    family = str(row.get("family_id", ""))
    if direction not in {"LONG", "SHORT"}:
        return unresolved_label(row, status="UNRESOLVED_INVALID_INITIAL_RISK")
    eligible_ms = timestamp_ms(row["entry_eligible_time"])
    if eligible_ms < store.start_ms:
        return unresolved_label(
            row,
            status="UNRESOLVED_BEFORE_SOURCE_START",
            label_end_ms=eligible_ms,
        )
    if eligible_ms >= store.end_ms:
        return unresolved_label(
            row, status="UNRESOLVED_AFTER_SOURCE_END", label_end_ms=eligible_ms
        )
    entry_gaps = label_contract["entry"]["maximum_gap_minutes_by_family"]
    maximum_gap = int(entry_gaps.get(family, min(entry_gaps.values()))) * 60_000
    try:
        entry = store.first_quote_at_or_after(eligible_ms, maximum_gap)
    except SourceDataError:
        return unresolved_label(
            row, status="UNRESOLVED_CORRUPT_QUOTE", label_end_ms=eligible_ms
        )
    if entry is None:
        return unresolved_label(
            row,
            status="UNRESOLVED_NO_TIMELY_ENTRY_QUOTE",
            label_end_ms=eligible_ms + maximum_gap,
        )

    risk = float(row["planned_stop_price"])
    if not np.isfinite(risk) or risk <= 0.0:
        return unresolved_label(
            row,
            status="UNRESOLVED_INVALID_INITIAL_RISK",
            label_end_ms=entry[0],
            entry=entry,
            risk=risk,
        )
    sign = 1.0 if direction == "LONG" else -1.0
    entry_ms, entry_bid, entry_ask = entry
    entry_price = float(entry_ask if direction == "LONG" else entry_bid)
    stop_price = entry_price - sign * risk
    target_r = row.get("target_r")
    has_target = str(row["target_mode"]) == "R_MULTIPLE" and pd.notna(target_r)
    target_price = entry_price + sign * float(target_r) * risk if has_target else None
    barrier_only = str(row["maximum_hold_mode"]) == "BARRIER_ONLY_NO_TIME_STOP"
    cap_minutes = float(row["label_observation_cap_minutes"])
    deadline_ms = entry_ms + int(round(cap_minutes * 60_000))
    observable_end_ms = min(deadline_ms, store.end_ms - 1)
    executable_index = 1 if direction == "LONG" else 2
    mfe = 0.0
    mae = 0.0

    resolved: tuple[int, float, str, str] | None = None
    try:
        for hour_key in store.hours_between(entry_ms, observable_end_ms):
            values = store.load_hour(hour_key)
            times = values[0]
            side = values[executable_index]
            left = int(np.searchsorted(times, entry_ms, side="left"))
            right = int(np.searchsorted(times, observable_end_ms, side="right"))
            if right <= left:
                continue
            local_times = times[left:right]
            prices = side[left:right]
            stop_hits = (
                prices <= stop_price if direction == "LONG" else prices >= stop_price
            )
            if target_price is None:
                target_hits = np.zeros(len(prices), dtype=bool)
            else:
                target_hits = (
                    prices >= target_price
                    if direction == "LONG"
                    else prices <= target_price
                )
            stop_positions = np.flatnonzero(stop_hits)
            target_positions = np.flatnonzero(target_hits)
            stop_index = int(stop_positions[0]) if len(stop_positions) else len(prices)
            target_index = (
                int(target_positions[0]) if len(target_positions) else len(prices)
            )
            hit_index = min(stop_index, target_index)
            if hit_index < len(prices):
                path = prices[: hit_index + 1]
                mfe, mae = _update_excursions(
                    path,
                    entry_price=entry_price,
                    sign=sign,
                    mfe=mfe,
                    mae=mae,
                )
                if stop_index <= target_index:
                    observed = float(prices[hit_index])
                    slipped = (
                        observed < stop_price
                        if direction == "LONG"
                        else observed > stop_price
                    )
                    resolved = (
                        int(local_times[hit_index]),
                        observed,
                        "STOP",
                        "RESOLVED_STOP_SLIPPAGE" if slipped else "RESOLVED_STOP",
                    )
                else:
                    resolved = (
                        int(local_times[hit_index]),
                        float(target_price),
                        "TARGET",
                        "RESOLVED_TARGET",
                    )
                break
            mfe, mae = _update_excursions(
                prices,
                entry_price=entry_price,
                sign=sign,
                mfe=mfe,
                mae=mae,
            )
    except SourceDataError:
        return unresolved_label(
            row,
            status="UNRESOLVED_CORRUPT_QUOTE",
            label_end_ms=deadline_ms,
            entry=entry,
            risk=risk,
        )

    if resolved is None and barrier_only:
        status = (
            "UNRESOLVED_AFTER_SOURCE_END"
            if deadline_ms >= store.end_ms
            else "CENSORED_R1_OBSERVATION_CAP"
        )
        return unresolved_label(
            row,
            status=status,
            label_end_ms=min(deadline_ms, store.end_ms - 1),
            entry=entry,
            risk=risk,
        )

    if resolved is None:
        if deadline_ms >= store.end_ms:
            return unresolved_label(
                row,
                status="UNRESOLVED_AFTER_SOURCE_END",
                label_end_ms=store.end_ms - 1,
                entry=entry,
                risk=risk,
            )
        horizon_gaps = label_contract["exit"]["maximum_horizon_gap_minutes_by_family"]
        horizon_gap_minutes = int(horizon_gaps.get(family, min(horizon_gaps.values())))
        try:
            horizon = store.first_quote_at_or_after(
                deadline_ms, horizon_gap_minutes * 60_000
            )
        except SourceDataError:
            return unresolved_label(
                row,
                status="UNRESOLVED_CORRUPT_QUOTE",
                label_end_ms=deadline_ms,
                entry=entry,
                risk=risk,
            )
        if horizon is None:
            return unresolved_label(
                row,
                status="UNRESOLVED_NO_HORIZON_QUOTE",
                label_end_ms=deadline_ms + horizon_gap_minutes * 60_000,
                entry=entry,
                risk=risk,
            )
        exit_ms = horizon[0]
        exit_price = float(horizon[1] if direction == "LONG" else horizon[2])
        mfe, mae = _update_excursions(
            np.array([exit_price]),
            entry_price=entry_price,
            sign=sign,
            mfe=mfe,
            mae=mae,
        )
        resolved = (
            exit_ms,
            exit_price,
            "FIXED_HORIZON",
            "RESOLVED_FIXED_HORIZON",
        )

    exit_ms, exit_price, exit_reason, label_status = resolved
    gross_r = sign * (exit_price - entry_price) / risk
    holding_minutes = max(0.0, (exit_ms - entry_ms) / 60_000.0)
    costs = label_contract["costs"]
    base_cost_r = (
        float(costs["ticket_cost_usd"])
        + holding_minutes / (24.0 * 60.0) * float(costs["holding_cost_per_24h_usd"])
    ) / risk
    stress_cost_r = base_cost_r + float(costs["stress_slippage_r"])
    base_net_r = gross_r - base_cost_r
    stress_net_r = gross_r - stress_cost_r
    target_before_stop: bool | None
    if exit_reason == "TARGET":
        target_before_stop = True
    elif exit_reason == "STOP":
        target_before_stop = False
    else:
        target_before_stop = None
    return {
        "candidate_id": candidate_id,
        "action_row_id": str(row.get("action_row_id", "")),
        "entry_time": timestamp_utc_ms(entry_ms),
        "label_end_time": timestamp_utc_ms(exit_ms),
        "initial_risk_price": risk,
        "initial_risk_usd_0p01": risk,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "stop_price": stop_price,
        "target_price": target_price,
        "gross_r": gross_r,
        "base_cost_r": base_cost_r,
        "stress_cost_r": stress_cost_r,
        "base_net_r": base_net_r,
        "stress_net_r": stress_net_r,
        "stress_net_r_positive": bool(stress_net_r > 0.0),
        "target_before_stop": target_before_stop,
        "mfe_r": max(0.0, mfe) / risk,
        "mae_r": max(0.0, mae) / risk,
        "holding_minutes": holding_minutes,
        "exit_reason": exit_reason,
        "label_status": label_status,
    }


def label_frame(
    frame: pd.DataFrame,
    *,
    store: LockedDukascopyStore,
    label_contract: Mapping[str, Any],
    progress_every: int = 0,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    ordered = frame.sort_values(
        ["entry_eligible_time", "candidate_id", "action_row_id"],
        kind="stable",
        na_position="last",
    )
    for index, row in enumerate(ordered.to_dict("records"), start=1):
        rows.append(label_one(row, store=store, label_contract=label_contract))
        if progress_every and index % progress_every == 0:
            print(f"labeled_rows={index}/{len(ordered)}", flush=True)
    result = pd.DataFrame(rows, columns=LABEL_COLUMNS)
    identity = (
        "action_row_id"
        if frame["action_row_id"].astype(str).ne("").any()
        else "candidate_id"
    )
    if result[identity].duplicated().any():
        raise ValueError(f"Step 3 labels duplicate {identity}")
    return result

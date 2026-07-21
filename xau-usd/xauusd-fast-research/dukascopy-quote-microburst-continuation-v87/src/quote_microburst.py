from __future__ import annotations

from collections import deque
import itertools
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from catchup import clock_ms


def _ordered_quotes(quotes: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp_ms", "bid", "ask", "mid"}
    missing = sorted(required - set(quotes.columns))
    if missing:
        raise ValueError(f"V87 quotes are missing columns: {missing}")
    ordered = (
        quotes.sort_values("timestamp_ms", kind="stable")
        .drop_duplicates("timestamp_ms", keep="last")
        .reset_index(drop=True)
    )
    if not ordered.empty:
        timestamps = ordered["timestamp_ms"].to_numpy(dtype=np.int64)
        if np.any(np.diff(timestamps) <= 0):
            raise ValueError("V87 quote timestamps are not strictly increasing")
        if bool((ordered["ask"] < ordered["bid"]).any()):
            raise ValueError("V87 found crossed quotes")
    return ordered


def session_quality(
    date: pd.Timestamp, quotes: pd.DataFrame, rule: Mapping[str, Any]
) -> dict[str, Any]:
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    ordered = _ordered_quotes(quotes)
    session = ordered.loc[ordered["timestamp_ms"].between(start_ms, end_ms - 1)]
    if session.empty:
        coverage = 0.0
    else:
        coverage = (
            int(session["timestamp_ms"].iloc[-1])
            - int(session["timestamp_ms"].iloc[0])
        ) / 60_000
    eligible = bool(
        date.weekday() < 5
        and len(session) >= int(rule["minimum_session_quotes"])
        and coverage >= float(rule["minimum_session_coverage_minutes"])
    )
    return {
        "date_utc": date.date().isoformat(),
        "weekday": int(date.weekday()),
        "eligible_full_weekday": eligible,
        "xau_quotes": int(len(session)),
        "xau_coverage_minutes": coverage,
    }


def _rolling_internal_max_gap(gaps: np.ndarray, starts: np.ndarray) -> np.ndarray:
    maximum = np.zeros(len(gaps), dtype=np.int64)
    candidates: deque[int] = deque()
    for index in range(len(gaps)):
        while candidates and candidates[0] <= int(starts[index]):
            candidates.popleft()
        if index > int(starts[index]):
            while candidates and gaps[candidates[-1]] <= gaps[index]:
                candidates.pop()
            candidates.append(index)
        maximum[index] = gaps[candidates[0]] if candidates else 0
    return maximum


def build_microburst_features(
    date: pd.Timestamp,
    quotes: pd.DataFrame,
    *,
    lookback_ms: int,
    rule: Mapping[str, Any],
) -> pd.DataFrame:
    ordered = _ordered_quotes(quotes)
    if ordered.empty:
        return pd.DataFrame()
    times = ordered["timestamp_ms"].to_numpy(dtype=np.int64)
    bid = ordered["bid"].to_numpy(dtype=float)
    ask = ordered["ask"].to_numpy(dtype=float)
    mid = ordered["mid"].to_numpy(dtype=float)
    spread_bps = np.divide(
        ask - bid,
        mid,
        out=np.full(len(mid), np.inf, dtype=float),
        where=mid > 0,
    ) * 10_000.0
    targets = times - int(lookback_ms)
    starts = np.searchsorted(times, targets, side="right") - 1
    valid_start = starts >= 0
    safe_starts = np.maximum(starts, 0)
    boundary_age = targets - times[safe_starts]
    mid_delta = np.diff(mid, prepend=mid[0])
    update_sign = np.sign(mid_delta)
    nonzero = update_sign != 0
    signed_prefix = np.concatenate(([0.0], np.cumsum(update_sign)))
    count_prefix = np.concatenate(([0], np.cumsum(nonzero.astype(np.int64))))
    indices = np.arange(len(times), dtype=np.int64)
    update_sum = signed_prefix[indices + 1] - signed_prefix[safe_starts + 1]
    update_count = count_prefix[indices + 1] - count_prefix[safe_starts + 1]
    imbalance = np.divide(
        update_sum,
        update_count,
        out=np.zeros(len(times), dtype=float),
        where=update_count > 0,
    )
    displacement_bps = np.divide(
        mid,
        mid[safe_starts],
        out=np.ones(len(mid), dtype=float),
        where=mid[safe_starts] > 0,
    )
    displacement_bps = (displacement_bps - 1.0) * 10_000.0
    gaps = np.diff(times, prepend=times[0])
    maximum_internal_gap = _rolling_internal_max_gap(gaps, safe_starts)
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    return pd.DataFrame(
        {
            "feature_time_utc": pd.to_datetime(times, unit="ms", utc=True),
            "decision_timestamp_ms": times,
            "date_utc": pd.Timestamp(date).date().isoformat(),
            "is_session": (times >= start_ms) & (times < end_ms),
            "lookback_ms": int(lookback_ms),
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "spread_bps": spread_bps,
            "lookback_timestamp_ms": times[safe_starts],
            "boundary_quote_age_ms": boundary_age,
            "maximum_internal_quote_gap_ms": maximum_internal_gap,
            "nonzero_mid_updates": update_count,
            "signed_update_imbalance": imbalance,
            "displacement_bps": displacement_bps,
            "valid_start": valid_start,
        }
    )


def policy_grid(calibration: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "lookback_ms": int(lookback),
            "minimum_nonzero_mid_updates": int(updates),
            "minimum_absolute_update_imbalance": float(imbalance),
            "minimum_absolute_displacement_bps": float(displacement),
            "maximum_spread_bps": float(spread),
        }
        for lookback, updates, imbalance, displacement, spread in itertools.product(
            calibration["lookback_ms_grid"],
            calibration["minimum_nonzero_mid_updates_grid"],
            calibration["minimum_absolute_update_imbalance_grid"],
            calibration["minimum_absolute_displacement_bps_grid"],
            calibration["maximum_spread_bps_grid"],
        )
    ]


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"LB{int(policy['lookback_ms']):05d}"
        f"__UC{int(policy['minimum_nonzero_mid_updates']):02d}"
        f"__IM{int(round(float(policy['minimum_absolute_update_imbalance']) * 100)):02d}"
        f"__DP{int(round(float(policy['minimum_absolute_displacement_bps']) * 100)):03d}"
        f"__SP{int(round(float(policy['maximum_spread_bps']) * 100)):03d}"
    )


def _policy_gate(
    features: pd.DataFrame,
    policy: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> np.ndarray:
    imbalance = features["signed_update_imbalance"].to_numpy(dtype=float)
    displacement = features["displacement_bps"].to_numpy(dtype=float)
    direction_agrees = (
        (np.sign(imbalance) == np.sign(displacement))
        & (np.sign(displacement) != 0)
    )
    return (
        features["valid_start"].to_numpy(dtype=bool)
        & features["boundary_quote_age_ms"].le(
            int(rule["maximum_boundary_quote_age_ms"])
        ).to_numpy()
        & features["maximum_internal_quote_gap_ms"].le(
            int(rule["maximum_internal_quote_gap_ms"])
        ).to_numpy()
        & features["nonzero_mid_updates"].ge(
            int(policy["minimum_nonzero_mid_updates"])
        ).to_numpy()
        & (np.abs(imbalance) >= float(policy["minimum_absolute_update_imbalance"]))
        & (
            np.abs(displacement)
            >= float(policy["minimum_absolute_displacement_bps"])
        )
        & features["spread_bps"].le(
            float(policy["maximum_spread_bps"])
        ).to_numpy()
        & direction_agrees
    )


def generate_candidates(
    features: pd.DataFrame,
    *,
    policy: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    if not features["lookback_ms"].eq(int(policy["lookback_ms"])).all():
        raise ValueError("V87 feature lookback does not match policy")
    gate = _policy_gate(features, policy, rule)
    times = features["decision_timestamp_ms"].to_numpy(dtype=np.int64)
    contiguous = np.r_[
        False,
        np.diff(times) <= int(rule["maximum_internal_quote_gap_ms"]),
    ]
    prior = np.r_[False, gate[:-1]]
    rising = gate & ~(prior & contiguous)
    selected = features.loc[rising & features["is_session"].to_numpy()].head(
        int(rule["maximum_candidates_per_utc_date"])
    ).copy()
    if selected.empty:
        return selected
    selected["direction"] = np.where(
        selected["signed_update_imbalance"] > 0, "LONG", "SHORT"
    )
    selected["family"] = str(rule["family"])
    selected["policy_id"] = policy_id(policy)
    selected.insert(
        0,
        "candidate_id",
        "V87:"
        + selected["policy_id"]
        + ":"
        + selected["decision_timestamp_ms"].astype("int64").astype(str)
        + ":"
        + selected["direction"],
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V87 candidate IDs are not unique")
    return selected.reset_index(drop=True)


def summarize_candidate_facts(
    candidates: pd.DataFrame,
    *,
    eligible_dates: Sequence[str],
    policy: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> dict[str, Any]:
    trades = len(candidates)
    active_days = int(candidates["date_utc"].nunique()) if trades else 0
    longs = int((candidates["direction"] == "LONG").sum()) if trades else 0
    shorts = int((candidates["direction"] == "SHORT").sum()) if trades else 0
    days = len(eligible_dates)
    frequency = trades / days if days else 0.0
    minority = min(longs, shorts) / trades if trades else 0.0
    active_share = active_days / days if days else 0.0
    selectable = bool(
        float(calibration["minimum_candidates_per_full_weekday"])
        <= frequency
        <= float(calibration["maximum_candidates_per_full_weekday"])
        and active_share >= float(calibration["minimum_active_day_share"])
        and minority >= float(calibration["minimum_direction_share"])
    )
    return {
        "policy_id": policy_id(policy),
        **dict(policy),
        "eligible_full_weekdays": days,
        "candidates": trades,
        "candidates_per_full_weekday": frequency,
        "active_days": active_days,
        "active_day_share": active_share,
        "long_candidates": longs,
        "short_candidates": shorts,
        "minority_direction_share": minority,
        "selection_eligible": selectable,
    }


def select_policy(
    rows: Iterable[Mapping[str, Any]], calibration: Mapping[str, Any]
) -> dict[str, Any] | None:
    eligible = [dict(row) for row in rows if bool(row["selection_eligible"])]
    if not eligible:
        return None
    target = float(calibration["target_candidates_per_full_weekday"])
    eligible.sort(
        key=lambda row: (
            abs(float(row["candidates_per_full_weekday"]) - target),
            -float(row["minimum_absolute_displacement_bps"]),
            -float(row["minimum_absolute_update_imbalance"]),
            -int(row["minimum_nonzero_mid_updates"]),
            float(row["maximum_spread_bps"]),
            int(row["lookback_ms"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "lookback_ms",
        "minimum_nonzero_mid_updates",
        "minimum_absolute_update_imbalance",
        "minimum_absolute_displacement_bps",
        "maximum_spread_bps",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}


def label_candidates(
    candidates: pd.DataFrame,
    *,
    quotes: pd.DataFrame,
    config: Mapping[str, Any],
) -> pd.DataFrame:
    columns = [
        "candidate_id",
        "status",
        "direction",
        "decision_time_utc",
        "entry_time_utc",
        "exit_time_utc",
        "observed_move_usd",
        "baseline_net_pnl_usd",
        "stress_net_pnl_usd",
    ]
    if candidates.empty:
        return pd.DataFrame(columns=columns)
    ordered = _ordered_quotes(quotes)
    times = ordered["timestamp_ms"].to_numpy(dtype=np.int64)
    execution = config["execution"]
    hold_ms = int(execution["hold_seconds"]) * 1000
    ounces = float(execution["ounces"])
    ticket = float(execution["ticket_cost_usd"])
    rows: list[dict[str, Any]] = []
    for candidate in candidates.to_dict("records"):
        decision_ms = int(candidate["decision_timestamp_ms"])
        row: dict[str, Any] = {
            "candidate_id": str(candidate["candidate_id"]),
            "status": "NO_ENTRY",
            "direction": str(candidate["direction"]),
            "decision_time_utc": pd.to_datetime(decision_ms, unit="ms", utc=True),
            "entry_time_utc": pd.NaT,
            "exit_time_utc": pd.NaT,
            "observed_move_usd": np.nan,
            "baseline_net_pnl_usd": np.nan,
            "stress_net_pnl_usd": np.nan,
        }
        entry_index = int(np.searchsorted(times, decision_ms, side="right"))
        if entry_index >= len(ordered):
            rows.append(row)
            continue
        entry_ms = int(times[entry_index])
        if entry_ms - decision_ms > int(execution["maximum_entry_delay_ms"]):
            rows.append(row)
            continue
        target_exit_ms = entry_ms + hold_ms
        exit_index = int(np.searchsorted(times, target_exit_ms, side="left"))
        row["entry_time_utc"] = pd.to_datetime(entry_ms, unit="ms", utc=True)
        row["status"] = "NO_EXIT"
        if exit_index >= len(ordered):
            rows.append(row)
            continue
        exit_ms = int(times[exit_index])
        if exit_ms - target_exit_ms > int(execution["maximum_exit_delay_ms"]):
            rows.append(row)
            continue
        entry = ordered.iloc[entry_index]
        exit_quote = ordered.iloc[exit_index]
        if row["direction"] == "LONG":
            observed = float(exit_quote["bid"]) - float(entry["ask"])
        elif row["direction"] == "SHORT":
            observed = float(entry["bid"]) - float(exit_quote["ask"])
        else:
            raise ValueError(f"Unknown V87 direction: {row['direction']}")
        row["status"] = "RESOLVED"
        row["exit_time_utc"] = pd.to_datetime(exit_ms, unit="ms", utc=True)
        row["observed_move_usd"] = observed * ounces
        row["baseline_net_pnl_usd"] = (
            observed * ounces
            - 2.0 * float(execution["base_slippage_per_side_usd"]) * ounces
            - ticket
        )
        row["stress_net_pnl_usd"] = (
            observed * ounces
            - 2.0 * float(execution["stress_slippage_per_side_usd"]) * ounces
            - ticket
        )
        rows.append(row)
    return pd.DataFrame(rows, columns=columns)

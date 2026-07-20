from __future__ import annotations

import itertools
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BASE_SRC = ROOT.parent / "comex-size-segment-flow-v32" / "src"
if str(BASE_SRC) not in sys.path:
    sys.path.insert(0, str(BASE_SRC))

import size_segment_flow as base  # noqa: E402


discover_source_files = base.discover_source_files
load_dbn_trades = base.load_dbn_trades
normalize_trades = base.normalize_trades
session_quality = base.session_quality
session_trades = base.session_trades
sha256_file = base.sha256_file
summarize_stage = base.summarize_stage


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _price_at_or_before(
    times_ns: np.ndarray, prices: np.ndarray, horizon_seconds: int
) -> np.ndarray:
    targets = times_ns - int(horizon_seconds) * 1_000_000_000
    indices = np.searchsorted(times_ns, targets, side="right") - 1
    result = np.full(len(prices), np.nan, dtype=float)
    valid = indices >= 0
    result[valid] = prices[indices[valid]]
    return result


def _add_sequence_state(frame: pd.DataFrame) -> pd.DataFrame:
    groups: list[pd.DataFrame] = []
    for _, raw_group in frame.groupby("instrument_id", sort=False, observed=True):
        group = raw_group.sort_values("ts_event", kind="stable").copy()
        signs = group["aggressor_sign"]
        prior = signs.shift()
        group["known_transition"] = prior.notna().astype("int64")
        group["same_side_transition"] = (prior.notna() & signs.eq(prior)).astype(
            "int64"
        )
        run_id = signs.ne(prior).cumsum()
        group["terminal_run_trades"] = group.groupby(run_id, sort=False).cumcount() + 1
        group["terminal_run_volume"] = group.groupby(run_id, sort=False)[
            "size"
        ].cumsum()
        groups.append(group)
    return pd.concat(groups, ignore_index=True)


def build_sequence_features(
    session: pd.DataFrame, *, rule: Mapping[str, Any]
) -> pd.DataFrame:
    if session.empty:
        return pd.DataFrame()
    frame = normalize_trades(session)
    frame = frame.loc[frame["aggressor_sign"] != 0].copy()
    if frame.empty:
        return pd.DataFrame()
    frame = _add_sequence_state(frame)
    frame["feature_time_utc"] = frame["ts_event"].dt.floor("s") + pd.Timedelta(
        seconds=1
    )
    frame["signed_volume"] = frame["size"] * frame["aggressor_sign"]
    grouped = frame.groupby(
        ["instrument_id", "feature_time_utc"], sort=True, observed=True
    )
    seconds = grouped.agg(
        first_event_utc=("ts_event", "first"),
        last_event_utc=("ts_event", "last"),
        known_trade_count=("size", "size"),
        contract_volume=("size", "sum"),
        signed_volume=("signed_volume", "sum"),
        same_side_transitions=("same_side_transition", "sum"),
        known_transitions=("known_transition", "sum"),
        terminal_run_trades=("terminal_run_trades", "last"),
        terminal_run_volume=("terminal_run_volume", "last"),
        terminal_run_sign=("aggressor_sign", "last"),
        price_last=("price", "last"),
    ).reset_index()
    if not (seconds["last_event_utc"] < seconds["feature_time_utc"]).all():
        raise ValueError(
            "A feature second contains an event at or after decision time."
        )

    current_seconds = int(rule["current_window_seconds"])
    prior_seconds = int(rule["prior_window_seconds"])
    combined_seconds = current_seconds + prior_seconds
    tick_size = float(rule["tick_size"])
    groups: list[pd.DataFrame] = []
    for _, raw_group in seconds.groupby("instrument_id", sort=False, observed=True):
        group = raw_group.sort_values("feature_time_utc", kind="stable").copy()
        indexed = group.set_index("feature_time_utc")

        def rolling(column: str, seconds_count: int) -> np.ndarray:
            return (
                indexed[column]
                .rolling(f"{seconds_count}s", closed="right")
                .sum()
                .to_numpy()
            )

        current_count = rolling("known_trade_count", current_seconds)
        combined_count = rolling("known_trade_count", combined_seconds)
        prior_count = np.maximum(combined_count - current_count, 0.0)
        current_volume = rolling("contract_volume", current_seconds)
        current_signed = rolling("signed_volume", current_seconds)
        same_transitions = rolling("same_side_transitions", current_seconds)
        known_transitions = rolling("known_transitions", current_seconds)
        imbalance = np.divide(
            current_signed,
            current_volume,
            out=np.zeros_like(current_signed, dtype=float),
            where=current_volume > 0,
        )
        transition_share = np.divide(
            same_transitions,
            known_transitions,
            out=np.zeros_like(same_transitions, dtype=float),
            where=known_transitions > 0,
        )
        expected_current_count = np.maximum(
            prior_count * current_seconds / prior_seconds, 1.0
        )
        acceleration = current_count / expected_current_count
        times_ns = (
            group["feature_time_utc"].to_numpy(dtype="datetime64[ns]").astype("int64")
        )
        prices = group["price_last"].to_numpy(dtype=float)
        baseline = _price_at_or_before(times_ns, prices, current_seconds)
        impulse = (prices - baseline) / tick_size
        terminal_sign = group["terminal_run_sign"].to_numpy(dtype=float)
        group["current_trade_count_5s"] = current_count
        group["prior_trade_count_30s"] = prior_count
        group["current_volume_5s"] = current_volume
        group["current_signed_volume_5s"] = current_signed
        group["current_imbalance_5s"] = imbalance
        group["same_side_transition_share_5s"] = transition_share
        group["arrival_acceleration"] = acceleration
        group["current_directional_impulse_ticks"] = terminal_sign * impulse
        group["instrument_age_seconds"] = (
            group["feature_time_utc"] - group["feature_time_utc"].iloc[0]
        ).dt.total_seconds()
        groups.append(group)
    return (
        pd.concat(groups, ignore_index=True)
        .sort_values(["feature_time_utc", "instrument_id"], kind="stable")
        .reset_index(drop=True)
    )


def policy_grid(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    calibration = config["calibration"]
    rows: list[dict[str, Any]] = []
    for values in itertools.product(
        calibration["minimum_current_trade_count_grid"],
        calibration["minimum_terminal_run_trades_grid"],
        calibration["minimum_same_side_transition_share_grid"],
        calibration["minimum_absolute_current_imbalance_grid"],
        calibration["minimum_arrival_acceleration_grid"],
    ):
        count, run, transition, imbalance, acceleration = values
        rows.append(
            {
                "minimum_current_trade_count": int(count),
                "minimum_terminal_run_trades": int(run),
                "minimum_same_side_transition_share": float(transition),
                "minimum_absolute_current_imbalance": float(imbalance),
                "minimum_arrival_acceleration": float(acceleration),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"TC{int(policy['minimum_current_trade_count']):02d}"
        f"__RL{int(policy['minimum_terminal_run_trades']):02d}"
        f"__TS{int(round(float(policy['minimum_same_side_transition_share']) * 100)):02d}"
        f"__IM{int(round(float(policy['minimum_absolute_current_imbalance']) * 100)):02d}"
        f"__AC{int(round(float(policy['minimum_arrival_acceleration']) * 100)):03d}"
    )


def generate_candidates(
    features: pd.DataFrame,
    *,
    policy: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    terminal_sign = np.sign(features["terminal_run_sign"])
    current_sign = np.sign(features["current_imbalance_5s"])
    mask = features["instrument_age_seconds"] >= float(
        rule["instrument_warmup_seconds"]
    )
    mask &= features["current_trade_count_5s"] >= int(
        policy["minimum_current_trade_count"]
    )
    mask &= features["terminal_run_trades"] >= int(
        policy["minimum_terminal_run_trades"]
    )
    mask &= features["same_side_transition_share_5s"] >= float(
        policy["minimum_same_side_transition_share"]
    )
    mask &= features["current_imbalance_5s"].abs() >= float(
        policy["minimum_absolute_current_imbalance"]
    )
    mask &= features["arrival_acceleration"] >= float(
        policy["minimum_arrival_acceleration"]
    )
    mask &= features["current_directional_impulse_ticks"] >= float(
        rule["minimum_current_directional_impulse_ticks"]
    )
    mask &= (terminal_sign != 0) & (terminal_sign == current_sign)
    selected = features.loc[mask].copy()
    if selected.empty:
        return selected
    selected["family"] = str(rule["family"])
    selected["direction"] = np.where(selected["terminal_run_sign"] > 0, "LONG", "SHORT")
    selected = selected.sort_values(
        ["feature_time_utc", "instrument_id"], kind="stable"
    ).reset_index(drop=True)
    cooldown = pd.Timedelta(minutes=int(rule["cooldown_minutes"]))
    retained: list[int] = []
    last_time: pd.Timestamp | None = None
    for index, row in selected.iterrows():
        decision = pd.Timestamp(row["feature_time_utc"])
        if last_time is None or decision - last_time >= cooldown:
            retained.append(index)
            last_time = decision
    result = selected.loc[retained].copy().reset_index(drop=True)
    decision_ms = result["feature_time_utc"].astype("int64") // 1_000_000
    result.insert(
        0,
        "candidate_id",
        result["family"].astype(str)
        + ":"
        + decision_ms.astype(str)
        + ":"
        + result["direction"].astype(str)
        + ":"
        + result["instrument_id"].astype(str),
    )
    if result["candidate_id"].duplicated().any():
        raise ValueError("Candidate generation produced duplicate IDs.")
    return result


def summarize_candidate_facts(
    candidates: pd.DataFrame,
    *,
    eligible_dates: Sequence[str],
    policy: Mapping[str, Any],
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    trades = len(candidates)
    if trades:
        dates = pd.to_datetime(candidates["feature_time_utc"], utc=True).dt.date.astype(
            str
        )
        active_days = int(dates.nunique())
        long_trades = int((candidates["direction"] == "LONG").sum())
        short_trades = int((candidates["direction"] == "SHORT").sum())
    else:
        active_days = long_trades = short_trades = 0
    full_days = len(eligible_dates)
    frequency = trades / full_days if full_days else 0.0
    active_share = active_days / full_days if full_days else 0.0
    minority_share = min(long_trades, short_trades) / trades if trades else 0.0
    eligible = bool(
        float(selection["minimum_candidates_per_full_weekday"])
        <= frequency
        <= float(selection["maximum_candidates_per_full_weekday"])
        and active_share >= float(selection["minimum_active_day_share"])
        and minority_share >= float(selection["minimum_minority_direction_share"])
    )
    return {
        "policy_id": policy_id(policy),
        **dict(policy),
        "eligible_full_weekdays": full_days,
        "candidates": trades,
        "candidates_per_full_weekday": frequency,
        "active_days": active_days,
        "active_day_share": active_share,
        "long_candidates": long_trades,
        "short_candidates": short_trades,
        "minority_direction_share": minority_share,
        "selection_eligible": eligible,
    }


def select_policy(
    rows: Iterable[Mapping[str, Any]], selection: Mapping[str, Any]
) -> dict[str, Any] | None:
    eligible = [dict(row) for row in rows if bool(row["selection_eligible"])]
    if not eligible:
        return None
    target = float(selection["target_candidates_per_full_weekday"])
    eligible.sort(
        key=lambda row: (
            abs(float(row["candidates_per_full_weekday"]) - target),
            -int(row["minimum_current_trade_count"]),
            -int(row["minimum_terminal_run_trades"]),
            -float(row["minimum_same_side_transition_share"]),
            -float(row["minimum_absolute_current_imbalance"]),
            -float(row["minimum_arrival_acceleration"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "minimum_current_trade_count",
        "minimum_terminal_run_trades",
        "minimum_same_side_transition_share",
        "minimum_absolute_current_imbalance",
        "minimum_arrival_acceleration",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}

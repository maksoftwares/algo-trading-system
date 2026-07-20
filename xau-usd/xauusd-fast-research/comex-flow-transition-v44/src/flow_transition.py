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


def build_transition_features(
    session: pd.DataFrame, *, rule: Mapping[str, Any]
) -> pd.DataFrame:
    if session.empty:
        return pd.DataFrame()
    frame = normalize_trades(session)
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
        trade_count=("size", "size"),
        contract_volume=("size", "sum"),
        signed_volume=("signed_volume", "sum"),
        price_open=("price", "first"),
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
        current_volume = (
            indexed["contract_volume"]
            .rolling(f"{current_seconds}s", closed="right")
            .sum()
            .to_numpy()
        )
        current_signed = (
            indexed["signed_volume"]
            .rolling(f"{current_seconds}s", closed="right")
            .sum()
            .to_numpy()
        )
        combined_volume = (
            indexed["contract_volume"]
            .rolling(f"{combined_seconds}s", closed="right")
            .sum()
            .to_numpy()
        )
        combined_signed = (
            indexed["signed_volume"]
            .rolling(f"{combined_seconds}s", closed="right")
            .sum()
            .to_numpy()
        )
        prior_volume = np.maximum(combined_volume - current_volume, 0.0)
        prior_signed = combined_signed - current_signed
        times_ns = (
            group["feature_time_utc"].to_numpy(dtype="datetime64[ns]").astype("int64")
        )
        prices = group["price_last"].to_numpy(dtype=float)
        price_before_current = _price_at_or_before(times_ns, prices, current_seconds)
        price_before_prior = _price_at_or_before(times_ns, prices, combined_seconds)
        current_impulse = (prices - price_before_current) / tick_size
        prior_impulse = (price_before_current - price_before_prior) / tick_size
        current_imbalance = np.divide(
            current_signed,
            current_volume,
            out=np.zeros_like(current_signed, dtype=float),
            where=current_volume > 0,
        )
        prior_imbalance = np.divide(
            prior_signed,
            prior_volume,
            out=np.zeros_like(prior_signed, dtype=float),
            where=prior_volume > 0,
        )
        current_sign = np.sign(current_imbalance)
        prior_sign = np.sign(prior_imbalance)
        prior_efficiency = np.divide(
            prior_sign * prior_impulse,
            np.abs(prior_signed),
            out=np.full_like(prior_impulse, np.nan, dtype=float),
            where=np.abs(prior_signed) > 0,
        )
        expected_current_volume = prior_volume * current_seconds / prior_seconds
        current_acceleration = np.divide(
            current_volume,
            expected_current_volume,
            out=np.full_like(current_volume, np.nan, dtype=float),
            where=expected_current_volume > 0,
        )
        group["current_volume_5s"] = current_volume
        group["current_signed_volume_5s"] = current_signed
        group["current_imbalance_5s"] = current_imbalance
        group["current_directional_impulse_ticks"] = current_sign * current_impulse
        group["current_acceleration"] = current_acceleration
        group["prior_volume_30s"] = prior_volume
        group["prior_signed_volume_30s"] = prior_signed
        group["prior_imbalance_30s"] = prior_imbalance
        group["prior_directional_impact_efficiency"] = prior_efficiency
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
        calibration["minimum_prior_volume_grid"],
        calibration["minimum_absolute_prior_imbalance_grid"],
        calibration["maximum_prior_directional_impact_efficiency_grid"],
        calibration["minimum_current_volume_grid"],
        calibration["minimum_absolute_current_imbalance_grid"],
    ):
        prior_volume, prior_imbalance, impact, current_volume, current_imbalance = (
            values
        )
        rows.append(
            {
                "minimum_prior_volume": int(prior_volume),
                "minimum_absolute_prior_imbalance": float(prior_imbalance),
                "maximum_prior_directional_impact_efficiency": float(impact),
                "minimum_current_volume": int(current_volume),
                "minimum_absolute_current_imbalance": float(current_imbalance),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"PV{int(policy['minimum_prior_volume']):03d}"
        f"__PI{int(round(float(policy['minimum_absolute_prior_imbalance']) * 100)):02d}"
        f"__IE{int(round(float(policy['maximum_prior_directional_impact_efficiency']) * 100)):02d}"
        f"__CV{int(policy['minimum_current_volume']):02d}"
        f"__CI{int(round(float(policy['minimum_absolute_current_imbalance']) * 100)):02d}"
    )


def generate_candidates(
    features: pd.DataFrame,
    *,
    policy: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    prior_sign = np.sign(features["prior_imbalance_30s"])
    current_sign = np.sign(features["current_imbalance_5s"])
    mask = features["instrument_age_seconds"] >= float(
        rule["instrument_warmup_seconds"]
    )
    mask &= features["prior_volume_30s"] >= float(policy["minimum_prior_volume"])
    mask &= features["prior_imbalance_30s"].abs() >= float(
        policy["minimum_absolute_prior_imbalance"]
    )
    mask &= features["prior_directional_impact_efficiency"] <= float(
        policy["maximum_prior_directional_impact_efficiency"]
    )
    mask &= features["current_volume_5s"] >= float(policy["minimum_current_volume"])
    mask &= features["current_imbalance_5s"].abs() >= float(
        policy["minimum_absolute_current_imbalance"]
    )
    mask &= features["current_acceleration"] >= float(
        rule["minimum_current_acceleration"]
    )
    mask &= features["current_directional_impulse_ticks"] >= float(
        rule["minimum_current_directional_impulse_ticks"]
    )
    mask &= (prior_sign != 0) & (current_sign != 0) & (prior_sign == -current_sign)
    selected = features.loc[mask].copy()
    if selected.empty:
        return selected
    selected["family"] = str(rule["family"])
    selected["direction"] = np.where(
        selected["current_imbalance_5s"] > 0, "LONG", "SHORT"
    )
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
            -int(row["minimum_prior_volume"]),
            -float(row["minimum_absolute_prior_imbalance"]),
            float(row["maximum_prior_directional_impact_efficiency"]),
            -int(row["minimum_current_volume"]),
            -float(row["minimum_absolute_current_imbalance"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "minimum_prior_volume",
        "minimum_absolute_prior_imbalance",
        "maximum_prior_directional_impact_efficiency",
        "minimum_current_volume",
        "minimum_absolute_current_imbalance",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}

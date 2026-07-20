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
) -> tuple[np.ndarray, np.ndarray]:
    targets = times_ns - int(horizon_seconds) * 1_000_000_000
    indices = np.searchsorted(times_ns, targets, side="right") - 1
    values = np.full(len(prices), np.nan, dtype=float)
    found_time = np.full(len(prices), -1, dtype=np.int64)
    valid = indices >= 0
    values[valid] = prices[indices[valid]]
    found_time[valid] = times_ns[indices[valid]]
    return values, found_time


def build_barrier_features(
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
        price_open=("price", "first"),
        price_high=("price", "max"),
        price_low=("price", "min"),
        price_last=("price", "last"),
        contract_volume=("size", "sum"),
        signed_volume=("signed_volume", "sum"),
    ).reset_index()
    if not (seconds["last_event_utc"] < seconds["feature_time_utc"]).all():
        raise ValueError("A V71 feature contains a source event at decision time")

    feature_frames: list[pd.DataFrame] = []
    for _, raw_group in seconds.groupby("instrument_id", sort=False, observed=True):
        group = raw_group.sort_values("feature_time_utc", kind="stable").copy()
        indexed = group.set_index("feature_time_utc")
        current_seconds = int(rule["current_flow_seconds"])
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
        current_imbalance = np.divide(
            current_signed,
            current_volume,
            out=np.zeros_like(current_signed, dtype=float),
            where=current_volume > 0,
        )
        times_ns = group["feature_time_utc"].dt.as_unit("ns").astype("int64").to_numpy()
        last_price = group["price_last"].to_numpy(dtype=float)
        instrument_age = (
            group["feature_time_utc"] - group["feature_time_utc"].iloc[0]
        ).dt.total_seconds()
        for lookback in rule["lookback_seconds_grid"]:
            lookback = int(lookback)
            baseline, baseline_time = _price_at_or_before(
                times_ns, last_price, lookback
            )
            rolling_high = (
                indexed["price_high"]
                .rolling(f"{lookback}s", closed="right")
                .max()
                .to_numpy()
            )
            rolling_low = (
                indexed["price_low"]
                .rolling(f"{lookback}s", closed="right")
                .min()
                .to_numpy()
            )
            for spacing_value in rule["level_spacing_usd_grid"]:
                spacing = float(spacing_value)
                upper_level = np.ceil(baseline / spacing) * spacing
                lower_level = np.floor(baseline / spacing) * spacing
                upper_distance = upper_level - baseline
                lower_distance = baseline - lower_level
                upward_probe = rolling_high - upper_level
                upward_rejection = upper_level - last_price
                downward_probe = lower_level - rolling_low
                downward_rejection = last_price - lower_level
                maximum_distance = spacing * float(
                    rule["maximum_initial_level_distance_fraction"]
                )
                upward = np.isfinite(baseline)
                upward &= baseline < upper_level
                upward &= upper_distance <= maximum_distance
                upward &= upward_probe >= float(rule["minimum_materialized_probe_usd"])
                upward &= upward_rejection >= float(
                    rule["minimum_materialized_rejection_usd"]
                )
                upward &= current_imbalance <= -float(
                    rule["minimum_materialized_opposite_flow_imbalance"]
                )
                downward = np.isfinite(baseline)
                downward &= baseline > lower_level
                downward &= lower_distance <= maximum_distance
                downward &= downward_probe >= float(
                    rule["minimum_materialized_probe_usd"]
                )
                downward &= downward_rejection >= float(
                    rule["minimum_materialized_rejection_usd"]
                )
                downward &= current_imbalance >= float(
                    rule["minimum_materialized_opposite_flow_imbalance"]
                )
                material = upward | downward
                if not material.any():
                    continue
                result = group.loc[material].copy()
                indices = np.flatnonzero(material)
                result["lookback_seconds"] = lookback
                result["level_spacing_usd"] = spacing
                result["baseline_price"] = baseline[indices]
                result["baseline_time_ns"] = baseline_time[indices]
                result["barrier_level"] = np.where(
                    upward[indices], upper_level[indices], lower_level[indices]
                )
                result["probe_usd"] = np.where(
                    upward[indices], upward_probe[indices], downward_probe[indices]
                )
                result["rejection_usd"] = np.where(
                    upward[indices],
                    upward_rejection[indices],
                    downward_rejection[indices],
                )
                result["current_flow_imbalance"] = current_imbalance[indices]
                result["current_flow_volume"] = current_volume[indices]
                result["instrument_age_seconds"] = instrument_age.iloc[
                    indices
                ].to_numpy()
                result["direction"] = np.where(upward[indices], "SHORT", "LONG")
                feature_frames.append(result)
    if not feature_frames:
        return pd.DataFrame()
    return (
        pd.concat(feature_frames, ignore_index=True)
        .sort_values(
            [
                "feature_time_utc",
                "instrument_id",
                "lookback_seconds",
                "level_spacing_usd",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def policy_grid(config: Mapping[str, Any]) -> list[dict[str, Any]]:
    calibration = config["calibration"]
    rows: list[dict[str, Any]] = []
    for values in itertools.product(
        calibration["level_spacing_usd_grid"],
        calibration["lookback_seconds_grid"],
        calibration["minimum_probe_usd_grid"],
        calibration["minimum_rejection_usd_grid"],
        calibration["minimum_opposite_flow_imbalance_grid"],
    ):
        spacing, lookback, probe, rejection, flow = values
        rows.append(
            {
                "level_spacing_usd": float(spacing),
                "lookback_seconds": int(lookback),
                "minimum_probe_usd": float(probe),
                "minimum_rejection_usd": float(rejection),
                "minimum_opposite_flow_imbalance": float(flow),
            }
        )
    return rows


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"LS{int(round(float(policy['level_spacing_usd']) * 10)):03d}"
        f"__LB{int(policy['lookback_seconds']):03d}"
        f"__PR{int(round(float(policy['minimum_probe_usd']) * 100)):03d}"
        f"__RJ{int(round(float(policy['minimum_rejection_usd']) * 100)):03d}"
        f"__FI{int(round(float(policy['minimum_opposite_flow_imbalance']) * 100)):02d}"
    )


def generate_candidates(
    features: pd.DataFrame,
    *,
    policy: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    mask = features["level_spacing_usd"].eq(float(policy["level_spacing_usd"]))
    mask &= features["lookback_seconds"].eq(int(policy["lookback_seconds"]))
    mask &= features["probe_usd"] >= float(policy["minimum_probe_usd"])
    mask &= features["rejection_usd"] >= float(policy["minimum_rejection_usd"])
    required_flow = float(policy["minimum_opposite_flow_imbalance"])
    mask &= np.where(
        features["direction"].eq("SHORT"),
        features["current_flow_imbalance"] <= -required_flow,
        features["current_flow_imbalance"] >= required_flow,
    )
    mask &= features["instrument_age_seconds"] >= float(
        rule["instrument_warmup_seconds"]
    )
    selected = features.loc[mask].copy()
    if selected.empty:
        return selected
    selected["date_utc"] = selected["feature_time_utc"].dt.date.astype(str)
    selected = selected.sort_values(
        ["feature_time_utc", "instrument_id", "direction"], kind="stable"
    )
    selected = selected.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected["family"] = str(rule["family"])
    selected["policy_id"] = policy_id(policy)
    decision_ms = selected["feature_time_utc"].dt.as_unit("ms").astype("int64")
    selected.insert(
        0,
        "candidate_id",
        "V71:"
        + selected["policy_id"].astype(str)
        + ":"
        + decision_ms.astype(str)
        + ":"
        + selected["direction"].astype(str),
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V71 candidate IDs are not unique")
    return selected.reset_index(drop=True)


def summarize_candidate_facts(
    candidates: pd.DataFrame,
    *,
    eligible_dates: Sequence[str],
    policy: Mapping[str, Any],
    selection: Mapping[str, Any],
) -> dict[str, Any]:
    trades = len(candidates)
    active_days = int(candidates["date_utc"].nunique()) if trades else 0
    longs = int((candidates["direction"] == "LONG").sum()) if trades else 0
    shorts = int((candidates["direction"] == "SHORT").sum()) if trades else 0
    full_days = len(eligible_dates)
    frequency = trades / full_days if full_days else 0.0
    active_share = active_days / full_days if full_days else 0.0
    minority_share = min(longs, shorts) / trades if trades else 0.0
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
        "long_candidates": longs,
        "short_candidates": shorts,
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
            -float(row["level_spacing_usd"]),
            -int(row["lookback_seconds"]),
            -float(row["minimum_probe_usd"]),
            -float(row["minimum_rejection_usd"]),
            -float(row["minimum_opposite_flow_imbalance"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "level_spacing_usd",
        "lookback_seconds",
        "minimum_probe_usd",
        "minimum_rejection_usd",
        "minimum_opposite_flow_imbalance",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}

from __future__ import annotations

import itertools
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from catchup import clock_ms


def session_quality(
    date: pd.Timestamp,
    dxy: pd.DataFrame,
    bond: pd.DataFrame,
    xag: pd.DataFrame,
    xau: pd.DataFrame,
    rule: Mapping[str, Any],
) -> dict[str, Any]:
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    sessions = {
        "dxy": dxy.loc[
            dxy["timestamp_ms"].between(start_ms, end_ms - 1)
        ],
        "bond": bond.loc[
            bond["timestamp_ms"].between(start_ms, end_ms - 1)
        ],
        "xag": xag.loc[
            xag["timestamp_ms"].between(start_ms, end_ms - 1)
        ],
        "xau": xau.loc[xau["timestamp_ms"].between(start_ms, end_ms - 1)],
    }

    def coverage(frame: pd.DataFrame) -> float:
        if frame.empty:
            return 0.0
        elapsed = int(frame["timestamp_ms"].iloc[-1]) - int(
            frame["timestamp_ms"].iloc[0]
        )
        return elapsed / 60_000

    coverage_minutes = {key: coverage(frame) for key, frame in sessions.items()}
    minimum_quotes = rule["minimum_quotes_by_symbol"]
    eligible = bool(
        date.weekday() < 5
        and all(
            len(frame) >= int(minimum_quotes[key])
            for key, frame in sessions.items()
        )
        and all(
            value >= float(rule["minimum_session_coverage_minutes"])
            for value in coverage_minutes.values()
        )
    )
    result: dict[str, Any] = {
        "date_utc": date.date().isoformat(),
        "weekday": int(date.weekday()),
        "eligible_full_weekday": eligible,
    }
    for key, frame in sessions.items():
        result[f"{key}_quotes"] = int(len(frame))
        result[f"{key}_coverage_minutes"] = coverage_minutes[key]
    return result


def _aligned_indices(
    times: np.ndarray,
    targets: np.ndarray,
    *,
    side: str = "right",
) -> np.ndarray:
    return np.searchsorted(times, targets, side=side) - 1


def build_consensus_features(
    date: pd.Timestamp,
    dxy: pd.DataFrame,
    bond: pd.DataFrame,
    xag: pd.DataFrame,
    xau: pd.DataFrame,
    *,
    horizons_ms: Sequence[int],
    rule: Mapping[str, Any],
    prefilter: Mapping[str, Any],
) -> pd.DataFrame:
    if any(frame.empty for frame in (dxy, bond, xag, xau)):
        return pd.DataFrame()
    start_ms = clock_ms(date, str(rule["session_start_utc"]))
    end_ms = clock_ms(date, str(rule["session_end_utc"]))
    frames = {
        "dxy": dxy,
        "bond": bond,
        "xag": xag,
        "xau": xau,
    }
    times = {
        key: frame["timestamp_ms"].to_numpy(dtype=np.int64)
        for key, frame in frames.items()
    }
    mids = {
        key: frame["mid"].to_numpy(dtype=float) for key, frame in frames.items()
    }
    event_indices = np.flatnonzero(
        (times["dxy"] >= start_ms) & (times["dxy"] < end_ms)
    )
    if event_indices.size == 0:
        return pd.DataFrame()
    event_times = times["dxy"][event_indices]
    event_dxy_mid = mids["dxy"][event_indices]
    baseline_staleness = int(rule["maximum_baseline_staleness_ms"])
    source_staleness = int(rule["maximum_current_source_staleness_ms"])
    xau_staleness = int(rule["maximum_current_xau_staleness_ms"])
    output: list[pd.DataFrame] = []
    for horizon in horizons_ms:
        targets = event_times - int(horizon)
        base_indices = {
            key: _aligned_indices(value, targets) for key, value in times.items()
        }
        current_indices = {
            "bond": _aligned_indices(times["bond"], event_times),
            "xag": _aligned_indices(times["xag"], event_times),
            "xau": _aligned_indices(times["xau"], event_times, side="left"),
        }
        valid = np.ones(len(event_times), dtype=bool)
        for index in base_indices.values():
            valid &= index >= 0
        for index in current_indices.values():
            valid &= index >= 0
        safe_base = {key: np.maximum(value, 0) for key, value in base_indices.items()}
        safe_current = {
            key: np.maximum(value, 0) for key, value in current_indices.items()
        }
        for key in frames:
            valid &= (
                targets - times[key][safe_base[key]] <= baseline_staleness
            )
        for key in ("bond", "xag"):
            valid &= (
                event_times - times[key][safe_current[key]] <= source_staleness
            )
        valid &= (
            event_times - times["xau"][safe_current["xau"]] <= xau_staleness
        )
        dxy_move = (
            event_dxy_mid / mids["dxy"][safe_base["dxy"]] - 1.0
        ) * 10_000.0
        bond_move = (
            mids["bond"][safe_current["bond"]]
            / mids["bond"][safe_base["bond"]]
            - 1.0
        ) * 10_000.0
        xag_move = (
            mids["xag"][safe_current["xag"]]
            / mids["xag"][safe_base["xag"]]
            - 1.0
        ) * 10_000.0
        xau_move = (
            mids["xau"][safe_current["xau"]]
            / mids["xau"][safe_base["xau"]]
            - 1.0
        ) * 10_000.0
        dollar_sign = np.sign(dxy_move)
        expected_xau_sign = -dollar_sign
        consensus = (
            (expected_xau_sign != 0)
            & (np.sign(bond_move) == expected_xau_sign)
            & (np.sign(xag_move) == expected_xau_sign)
        )
        dxy_magnitude = np.abs(dxy_move)
        bond_directional = expected_xau_sign * bond_move
        xag_directional = expected_xau_sign * xag_move
        signed_xau_move = expected_xau_sign * xau_move
        response = np.divide(
            signed_xau_move,
            np.abs(xag_move),
            out=np.full_like(signed_xau_move, -np.inf),
            where=np.abs(xag_move) > 0,
        )
        quote_counts = np.column_stack(
            (
                event_indices - base_indices["dxy"],
                current_indices["bond"] - base_indices["bond"],
                current_indices["xag"] - base_indices["xag"],
            )
        )
        source_quote_count = np.min(quote_counts, axis=1)
        valid &= consensus
        valid &= dxy_magnitude >= float(prefilter["minimum_dxy_move_bps"])
        valid &= bond_directional >= float(prefilter["minimum_bond_move_bps"])
        valid &= xag_directional >= float(prefilter["minimum_xag_move_bps"])
        valid &= response <= float(
            prefilter["maximum_signed_xau_response_ratio"]
        )
        valid &= source_quote_count >= int(
            prefilter["minimum_source_quote_count"]
        )
        if not valid.any():
            continue
        chosen = np.flatnonzero(valid)
        output.append(
            pd.DataFrame(
                {
                    "feature_time_utc": pd.to_datetime(
                        event_times[chosen], unit="ms", utc=True
                    ),
                    "decision_timestamp_ms": event_times[chosen],
                    "horizon_ms": int(horizon),
                    "dxy_baseline_timestamp_ms": times["dxy"][
                        safe_base["dxy"][chosen]
                    ],
                    "bond_baseline_timestamp_ms": times["bond"][
                        safe_base["bond"][chosen]
                    ],
                    "bond_current_timestamp_ms": times["bond"][
                        safe_current["bond"][chosen]
                    ],
                    "xag_baseline_timestamp_ms": times["xag"][
                        safe_base["xag"][chosen]
                    ],
                    "xag_current_timestamp_ms": times["xag"][
                        safe_current["xag"][chosen]
                    ],
                    "xau_baseline_timestamp_ms": times["xau"][
                        safe_base["xau"][chosen]
                    ],
                    "xau_current_timestamp_ms": times["xau"][
                        safe_current["xau"][chosen]
                    ],
                    "dxy_move_bps": dxy_move[chosen],
                    "bond_move_bps": bond_move[chosen],
                    "xag_move_bps": xag_move[chosen],
                    "dxy_magnitude_bps": dxy_magnitude[chosen],
                    "bond_directional_bps": bond_directional[chosen],
                    "xag_directional_bps": xag_directional[chosen],
                    "xau_move_bps": xau_move[chosen],
                    "signed_xau_response_ratio": response[chosen],
                    "source_quote_count": source_quote_count[chosen],
                    "dollar_direction": np.where(
                        dollar_sign[chosen] > 0, "STRENGTH", "WEAKNESS"
                    ),
                    "direction": np.where(
                        expected_xau_sign[chosen] > 0, "LONG", "SHORT"
                    ),
                }
            )
        )
    if not output:
        return pd.DataFrame()
    return (
        pd.concat(output, ignore_index=True)
        .sort_values(["feature_time_utc", "horizon_ms"], kind="stable")
        .reset_index(drop=True)
    )


def policy_grid(calibration: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "horizon_ms": int(horizon),
            "minimum_dxy_move_bps": float(dxy),
            "minimum_bond_move_bps": float(bond),
            "minimum_xag_move_bps": float(xag),
            "maximum_signed_xau_response_ratio": float(response),
        }
        for horizon, dxy, bond, xag, response in itertools.product(
            calibration["horizon_ms_grid"],
            calibration["minimum_dxy_move_bps_grid"],
            calibration["minimum_bond_move_bps_grid"],
            calibration["minimum_xag_move_bps_grid"],
            calibration["maximum_signed_xau_response_ratio_grid"],
        )
    ]


def policy_id(policy: Mapping[str, Any]) -> str:
    return (
        f"H{int(policy['horizon_ms']):05d}"
        f"__DX{int(round(float(policy['minimum_dxy_move_bps']) * 100)):03d}"
        f"__BD{int(round(float(policy['minimum_bond_move_bps']) * 100)):03d}"
        f"__AG{int(round(float(policy['minimum_xag_move_bps']) * 100)):03d}"
        f"__XR{int(round(float(policy['maximum_signed_xau_response_ratio']) * 100)):03d}"
    )


def generate_candidates(
    features: pd.DataFrame, *, policy: Mapping[str, Any], family: str
) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    mask = features["horizon_ms"].eq(int(policy["horizon_ms"]))
    mask &= features["dxy_magnitude_bps"] >= float(
        policy["minimum_dxy_move_bps"]
    )
    mask &= features["bond_directional_bps"] >= float(
        policy["minimum_bond_move_bps"]
    )
    mask &= features["xag_directional_bps"] >= float(
        policy["minimum_xag_move_bps"]
    )
    mask &= features["signed_xau_response_ratio"] <= float(
        policy["maximum_signed_xau_response_ratio"]
    )
    selected = features.loc[mask].copy()
    if selected.empty:
        return selected
    selected["date_utc"] = selected["feature_time_utc"].dt.date.astype(str)
    selected = selected.sort_values(["feature_time_utc", "horizon_ms"], kind="stable")
    selected = selected.groupby("date_utc", sort=True, as_index=False).head(1).copy()
    selected["family"] = family
    selected["policy_id"] = policy_id(policy)
    selected.insert(
        0,
        "candidate_id",
        "V82:"
        + selected["policy_id"]
        + ":"
        + selected["decision_timestamp_ms"].astype("int64").astype(str)
        + ":"
        + selected["direction"],
    )
    if selected["candidate_id"].duplicated().any():
        raise ValueError("V82 candidate IDs are not unique")
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
            -float(row["minimum_dxy_move_bps"]),
            -float(row["minimum_bond_move_bps"]),
            -float(row["minimum_xag_move_bps"]),
            float(row["maximum_signed_xau_response_ratio"]),
            int(row["horizon_ms"]),
            str(row["policy_id"]),
        )
    )
    keys = {
        "policy_id",
        "horizon_ms",
        "minimum_dxy_move_bps",
        "minimum_bond_move_bps",
        "minimum_xag_move_bps",
        "maximum_signed_xau_response_ratio",
    }
    return {key: value for key, value in eligible[0].items() if key in keys}


def calibration_prefilter(calibration: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "minimum_dxy_move_bps": min(calibration["minimum_dxy_move_bps_grid"]),
        "minimum_bond_move_bps": min(
            calibration["minimum_bond_move_bps_grid"]
        ),
        "minimum_xag_move_bps": min(
            calibration["minimum_xag_move_bps_grid"]
        ),
        "maximum_signed_xau_response_ratio": max(
            calibration["maximum_signed_xau_response_ratio_grid"]
        ),
        "minimum_source_quote_count": int(calibration["minimum_source_quote_count"]),
    }

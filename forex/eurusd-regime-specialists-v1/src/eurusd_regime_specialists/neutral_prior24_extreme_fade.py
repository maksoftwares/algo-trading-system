from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

import numpy as np
import pandas as pd

from . import neutral_0608_range_breakout_transfer as ownership
from .research import PACKAGE_ROOT, PIP, load_inputs, serialize, sha256_file


FAMILY = "N49_NEUTRAL_PRIOR24_EXTREME_FADE"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_prior24_extreme_fade.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_PRIOR24_EXTREME_FADE_"
    "PREREG_2026_07_29.sha256.json"
)
PARENT_CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_two_clock_ensemble.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_prior24_extreme_fade"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_parent_config() -> dict[str, Any]:
    return json.loads(
        PARENT_CONFIG_PATH.read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_first_candidate_count") is not True
        or lock.get("locked_before_any_outcome") is not True
        or lock.get("census_forbids_outcome_loading") is not True
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Prior-24-hour fade was not locked in time")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Prior-24-hour fade preregistration drift: {relative}"
            )
        checked[relative] = actual
    return checked


def _default_entry_times(
    cfg: dict[str, Any],
) -> pd.DatetimeIndex:
    starts = [
        pd.Timestamp(bounds[0])
        for bounds in cfg["windows"].values()
    ]
    ends = [
        pd.Timestamp(bounds[1])
        for bounds in cfg["windows"].values()
    ]
    return pd.date_range(
        min(starts).normalize(),
        max(ends).normalize(),
        freq="1D",
        tz="UTC",
    )


def generate_midnight_points(
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    entry_times: Iterable[pd.Timestamp] | None = None,
) -> pd.DataFrame:
    strategy = cfg["strategy"]
    times = (
        _default_entry_times(cfg)
        if entry_times is None
        else pd.DatetimeIndex(entry_times)
    )
    rows: list[dict[str, Any]] = []
    required = int(strategy["required_m5_bars"])
    prior_hours = float(strategy["prior_window_hours"])
    for raw_entry in times:
        entry = pd.Timestamp(raw_entry)
        if entry.tzinfo is None:
            entry = entry.tz_localize("UTC")
        else:
            entry = entry.tz_convert("UTC")
        if (
            bool(strategy["weekdays_only"])
            and entry.weekday() >= 5
        ):
            continue
        if entry not in m5.index:
            continue
        start = entry - pd.Timedelta(hours=prior_hours)
        prior = m5.loc[
            (m5.index >= start) & (m5.index < entry)
        ]
        expected_last = entry - pd.Timedelta(minutes=5)
        if (
            len(prior) != required
            or prior.index[0] != start
            or prior.index[-1] != expected_last
        ):
            continue
        mid_open = (
            float(prior.iloc[0]["bid_open"])
            + float(prior.iloc[0]["ask_open"])
        ) / 2.0
        mid_high = float(
            (
                (
                    prior["bid_high"].astype(float)
                    + prior["ask_high"].astype(float)
                )
                / 2.0
            ).max()
        )
        mid_low = float(
            (
                (
                    prior["bid_low"].astype(float)
                    + prior["ask_low"].astype(float)
                )
                / 2.0
            ).min()
        )
        mid_close = (
            float(prior.iloc[-1]["bid_close"])
            + float(prior.iloc[-1]["ask_close"])
        ) / 2.0
        prior_range = mid_high - mid_low
        if not np.isfinite(prior_range) or prior_range <= 0.0:
            continue
        close_location = (mid_close - mid_low) / prior_range
        body_fraction = abs(mid_close - mid_open) / prior_range
        long_signal = bool(
            close_location
            <= float(strategy["lower_close_location_max"])
            and mid_close < mid_open
            and body_fraction
            >= float(strategy["minimum_body_fraction"])
        )
        short_signal = bool(
            close_location
            >= float(strategy["upper_close_location_min"])
            and mid_close > mid_open
            and body_fraction
            >= float(strategy["minimum_body_fraction"])
        )
        side = (
            "LONG"
            if long_signal
            else "SHORT"
            if short_signal
            else "CASH"
        )
        rows.append(
            {
                "family": FAMILY,
                "signal_time_utc": expected_last,
                "signal_complete_utc": entry,
                "entry_time_utc": entry,
                "state_latest_allowed_utc": (
                    entry - pd.Timedelta(hours=1)
                ),
                "prior_window_start_utc": start,
                "prior_window_end_utc": entry,
                "prior_m5_bars": int(len(prior)),
                "prior_open": mid_open,
                "prior_high": mid_high,
                "prior_low": mid_low,
                "prior_close": mid_close,
                "prior_range": prior_range,
                "prior_range_pips": prior_range / PIP,
                "close_location": close_location,
                "body_fraction": body_fraction,
                "side": side,
                "signal_eligible": side != "CASH",
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        "entry_time_utc"
    ).reset_index(drop=True)


def add_decision_time_risk(
    owned: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    if owned.empty:
        return owned.copy()
    execution = cfg["execution_contract_locked_before_census"]
    ownership_cfg = cfg["neutral_ownership"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    rows: list[dict[str, Any]] = []
    for _, signal in owned.iterrows():
        record = signal.to_dict()
        entry_time = pd.Timestamp(signal["entry_time_utc"])
        record["entry_bar_available"] = False
        record["risk_eligible"] = False
        if entry_time not in m5.index:
            rows.append(record)
            continue
        record["entry_bar_available"] = True
        bar = m5.loc[entry_time]
        side = str(signal["side"])
        if side == "LONG":
            entry = max(
                float(bar["ask_open"]),
                float(bar["bid_open"]) + spread_floor,
            ) + slippage
        else:
            entry = float(bar["bid_open"]) - slippage
        base_distance = max(
            0.25 * float(signal["prior_range"]),
            8.0 * PIP,
        )
        if side == "LONG":
            stop = min(
                float(signal["prior_low"]),
                entry - base_distance,
            )
            risk = entry - stop
        else:
            stop = max(
                float(signal["prior_high"]),
                entry + base_distance,
            )
            risk = stop - entry
        risk_pips = risk / PIP
        state_fresh = bool(
            float(signal["state_known_lag_hours"])
            <= float(
                ownership_cfg[
                    "maximum_state_known_lag_hours"
                ]
            )
        )
        record["state_fresh"] = state_fresh
        record["entry_price_decision_time"] = entry
        record["stop_price_decision_time"] = stop
        record["risk_distance"] = risk
        record["risk_pips"] = risk_pips
        record["risk_eligible"] = bool(
            signal["neutral_owned"]
            and state_fresh
            and np.isfinite(risk_pips)
            and risk_pips > 0.0
            and risk_pips
            <= float(execution["maximum_risk_pips"])
        )
        rows.append(record)
    return pd.DataFrame(rows).sort_values(
        "entry_time_utc"
    ).reset_index(drop=True)


def build_candidates(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    points = generate_midnight_points(m5, cfg)
    if points.empty:
        return points, points.copy()
    signals = points[points["signal_eligible"].astype(bool)].copy()
    if signals.empty:
        return points, signals
    owned = ownership.assign_neutral_ownership(
        signals,
        state,
        cfg,
    )
    candidates = add_decision_time_risk(owned, m5, cfg)
    return points, candidates


def _count_by_window(
    eligible: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name, bounds in cfg["windows"].items():
        start, end = (pd.Timestamp(value) for value in bounds)
        counts[name] = int(
            eligible["entry_time_utc"]
            .between(start, end, inclusive="both")
            .sum()
        )
    return counts


def summarize_census(
    points: pd.DataFrame,
    candidates: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    parent_manifests: dict[str, Any] | None = None,
) -> dict[str, Any]:
    eligible = candidates[
        candidates["risk_eligible"].astype(bool)
    ].copy()
    by_window = _count_by_window(eligible, cfg)
    recent_start, recent_end = (
        pd.Timestamp(value)
        for value in cfg["recent_six_months"]
    )
    recent = eligible["entry_time_utc"].between(
        recent_start,
        recent_end,
        inclusive="both",
    )
    maximum_lag = (
        float(eligible["state_known_lag_hours"].max())
        if len(eligible)
        else 0.0
    )
    gates = cfg["outcome_blind_capacity_gates"]
    gate_results = {
        "minimum_risk_eligible_candidates_total": len(eligible)
        >= int(gates["minimum_risk_eligible_candidates_total"]),
        "minimum_distinct_candidate_dates_total": (
            eligible["entry_time_utc"].dt.date.nunique()
            >= int(gates["minimum_distinct_candidate_dates_total"])
        ),
        "minimum_candidates_development_2019_2022": (
            by_window["development_2019_2022"]
            >= int(gates["minimum_candidates_development_2019_2022"])
        ),
        "minimum_candidates_each_full_oos_year": all(
            by_window[name]
            >= int(gates["minimum_candidates_each_full_oos_year"])
            for name in (
                "validation_2023",
                "validation_2024",
                "pseudo_oos_2025",
            )
        ),
        "minimum_candidates_pseudo_oos_2026h1": (
            by_window["pseudo_oos_2026h1"]
            >= int(gates["minimum_candidates_pseudo_oos_2026h1"])
        ),
        "minimum_candidates_each_side": all(
            int(eligible["side"].eq(side).sum())
            >= int(gates["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
        "minimum_recent_six_month_candidates": int(recent.sum())
        >= int(gates["minimum_recent_six_month_candidates"]),
        "maximum_candidate_state_known_lag_hours": maximum_lag
        <= float(gates["maximum_candidate_state_known_lag_hours"]),
    }
    census_pass = bool(all(gate_results.values()))
    forbidden = {
        "r",
        "pnl",
        "return",
        "exit_time_utc",
        "exit_price",
        "exit_reason",
        "oracle_member",
    }
    if forbidden & set(eligible.columns):
        raise RuntimeError("Outcome field entered candidate census")
    manifest = eligible.to_csv(index=False).encode("utf-8")
    return {
        "schema_version": (
            "eurusd_neutral_prior24_extreme_fade_census_v1"
        ),
        "campaign_id": cfg["campaign_id"],
        "family": FAMILY,
        "status": (
            "CENSUS_PASS_EXECUTION_MAY_BE_SEPARATELY_LOCKED"
            if census_pass
            else "CENSUS_FAIL_NO_PNL_ALLOWED"
        ),
        "complete_prior24_points": int(len(points)),
        "extreme_fade_signals": int(
            points.get(
                "signal_eligible",
                pd.Series(False, index=points.index),
            )
            .astype(bool)
            .sum()
        ),
        "neutral_owned_signals": int(
            candidates.get(
                "neutral_owned",
                pd.Series(False, index=candidates.index),
            )
            .astype(bool)
            .sum()
        ),
        "risk_eligible_candidates_total": int(len(eligible)),
        "distinct_candidate_dates_total": int(
            eligible["entry_time_utc"].dt.date.nunique()
        ),
        "long_candidates": int(eligible["side"].eq("LONG").sum()),
        "short_candidates": int(
            eligible["side"].eq("SHORT").sum()
        ),
        "recent_six_month_candidates": int(recent.sum()),
        "by_window": by_window,
        "state_known_lag_hours": {
            "minimum": (
                float(eligible["state_known_lag_hours"].min())
                if len(eligible)
                else 0.0
            ),
            "median": (
                float(eligible["state_known_lag_hours"].median())
                if len(eligible)
                else 0.0
            ),
            "maximum": maximum_lag,
        },
        "candidate_manifest_sha256": hashlib.sha256(
            manifest
        ).hexdigest(),
        "parent_source_manifests": parent_manifests or {},
        "gate_results": gate_results,
        "census_pass": census_pass,
        "stop_or_target_path_loaded": False,
        "trade_exit_loaded": False,
        "eurusd_return_loaded": False,
        "eurusd_pnl_loaded": False,
        "oracle_rows_loaded": False,
        "performance_gate_evaluated": False,
        "broker_action_allowed": False,
    }


def run_census() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    parent_cfg = load_parent_config()
    if (
        sha256_file(PARENT_CONFIG_PATH)
        != cfg["data_and_classifier"]["sha256"]
    ):
        raise RuntimeError("Parent classifier contract drift")
    m5, state, manifests = load_inputs(parent_cfg)
    points, candidates = build_candidates(m5, state, cfg)
    census = summarize_census(
        points,
        candidates,
        cfg,
        parent_manifests=manifests,
    )
    eligible = candidates[
        candidates["risk_eligible"].astype(bool)
    ].copy()
    return census, {
        "CANDIDATES": eligible,
        "ALL_MIDNIGHT_POINTS": points,
        "ALL_EXTREME_SIGNALS": candidates,
    }


def write_census(
    census: dict[str, Any],
    artifacts: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(
            serialize(census),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    (OUTPUT_ROOT / "CENSUS.json").write_text(
        payload,
        encoding="utf-8",
    )
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)


__all__ = [
    "add_decision_time_risk",
    "build_candidates",
    "generate_midnight_points",
    "load_config",
    "run_census",
    "summarize_census",
    "verify_lock",
    "write_census",
]

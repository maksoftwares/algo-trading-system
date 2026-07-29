from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

import numpy as np
import pandas as pd

from . import neutral_0608_range_breakout_transfer as ownership
from .research import PACKAGE_ROOT, PIP, load_inputs, serialize, sha256_file


FAMILY = "N50_NEUTRAL_MIDNIGHT_AUCTION_REJECTION"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_midnight_auction_rejection.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_MIDNIGHT_AUCTION_REJECTION_"
    "PREREG_2026_07_29.sha256.json"
)
PARENT_CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_two_clock_ensemble.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT
    / "outputs"
    / "neutral_midnight_auction_rejection"
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
        raise RuntimeError("Midnight auction rule was not locked in time")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Midnight auction preregistration drift: {relative}"
            )
        checked[relative] = actual
    return checked


def _default_dates(
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
    )


def generate_auction_points(
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    dates: Iterable[pd.Timestamp] | None = None,
) -> pd.DataFrame:
    strategy = cfg["strategy"]
    candidate_dates = (
        _default_dates(cfg)
        if dates is None
        else pd.DatetimeIndex(dates)
    )
    rows: list[dict[str, Any]] = []
    bars_required = int(strategy["observation_bars_m5"])
    for raw_date in candidate_dates:
        midnight = pd.Timestamp(raw_date).normalize()
        if midnight.tzinfo is None:
            midnight = midnight.tz_localize("UTC")
        else:
            midnight = midnight.tz_convert("UTC")
        if (
            bool(strategy["weekdays_only"])
            and midnight.weekday() >= 5
        ):
            continue
        completion = midnight + pd.Timedelta(minutes=15)
        expected = pd.date_range(
            midnight,
            periods=bars_required,
            freq="5min",
        )
        if (
            completion not in m5.index
            or not expected.isin(m5.index).all()
        ):
            continue
        observed = m5.loc[expected]
        mid_open = (
            float(observed.iloc[0]["bid_open"])
            + float(observed.iloc[0]["ask_open"])
        ) / 2.0
        mid_high = float(
            (
                observed["bid_high"].astype(float)
                + observed["ask_high"].astype(float)
            ).div(2.0).max()
        )
        mid_low = float(
            (
                observed["bid_low"].astype(float)
                + observed["ask_low"].astype(float)
            ).div(2.0).min()
        )
        mid_close = (
            float(observed.iloc[-1]["bid_close"])
            + float(observed.iloc[-1]["ask_close"])
        ) / 2.0
        auction_range = mid_high - mid_low
        if not np.isfinite(auction_range) or auction_range <= 0.0:
            continue
        range_pips = auction_range / PIP
        upward = mid_high - mid_open
        downward = mid_open - mid_low
        upper_wick = mid_high - max(mid_open, mid_close)
        lower_wick = min(mid_open, mid_close) - mid_low
        upper_fraction = max(0.0, upper_wick / auction_range)
        lower_fraction = max(0.0, lower_wick / auction_range)
        minimum_excursion = (
            float(strategy["minimum_failed_excursion_pips"]) * PIP
        )
        maximum_range = float(
            strategy["maximum_opening_range_pips"]
        )
        wick_minimum = float(
            strategy["minimum_rejection_wick_fraction"]
        )
        long_signal = bool(
            range_pips <= maximum_range
            and downward >= minimum_excursion
            and downward > upward
            and mid_close >= mid_open
            and lower_fraction >= wick_minimum
        )
        short_signal = bool(
            range_pips <= maximum_range
            and upward >= minimum_excursion
            and upward > downward
            and mid_close <= mid_open
            and upper_fraction >= wick_minimum
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
                "auction_start_utc": midnight,
                "signal_time_utc": expected[-1],
                "signal_complete_utc": completion,
                "entry_time_utc": completion,
                "state_latest_allowed_utc": (
                    completion.floor("h")
                    - pd.Timedelta(hours=1)
                ),
                "observation_m5_bars": bars_required,
                "auction_open": mid_open,
                "auction_high": mid_high,
                "auction_low": mid_low,
                "auction_close": mid_close,
                "auction_range": auction_range,
                "auction_range_pips": range_pips,
                "upward_excursion_pips": upward / PIP,
                "downward_excursion_pips": downward / PIP,
                "upper_wick_fraction": upper_fraction,
                "lower_wick_fraction": lower_fraction,
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
    minimum_stop = (
        float(execution["minimum_stop_distance_pips"]) * PIP
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
            stop = min(
                float(signal["auction_low"]),
                entry - minimum_stop,
            )
            risk = entry - stop
        else:
            entry = float(bar["bid_open"]) - slippage
            stop = max(
                float(signal["auction_high"]),
                entry + minimum_stop,
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
    result = pd.DataFrame(rows).sort_values(
        "entry_time_utc"
    ).reset_index(drop=True)
    result["window"] = ""
    for name, bounds in cfg["windows"].items():
        start, end = (pd.Timestamp(value) for value in bounds)
        mask = result["entry_time_utc"].between(
            start,
            end,
            inclusive="both",
        )
        result.loc[mask, "window"] = name
    return result


def build_candidates(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    points = generate_auction_points(m5, cfg)
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
    return points, add_decision_time_risk(owned, m5, cfg)


def _count_by_window(
    eligible: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, int]:
    return {
        name: int(eligible["window"].eq(name).sum())
        for name in cfg["windows"]
    }


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
        raise RuntimeError("Outcome field entered auction census")
    manifest = eligible.to_csv(index=False).encode("utf-8")
    return {
        "schema_version": (
            "eurusd_neutral_midnight_auction_rejection_census_v1"
        ),
        "campaign_id": cfg["campaign_id"],
        "family": FAMILY,
        "status": (
            "CENSUS_PASS_EXECUTION_MAY_BE_SEPARATELY_LOCKED"
            if census_pass
            else "CENSUS_FAIL_NO_PNL_ALLOWED"
        ),
        "complete_midnight_auctions": int(len(points)),
        "failed_auction_signals": int(
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
        "ALL_AUCTION_POINTS": points,
        "ALL_FAILED_AUCTION_SIGNALS": candidates,
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
    "generate_auction_points",
    "load_config",
    "run_census",
    "summarize_census",
    "verify_lock",
    "write_census",
]

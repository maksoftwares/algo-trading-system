from __future__ import annotations

import json
from typing import Any, Iterable

import numpy as np
import pandas as pd

from . import neutral_0608_range_breakout_transfer as ownership
from . import neutral_midnight_auction_rejection as auction
from .research import PACKAGE_ROOT, PIP, load_inputs, serialize, sha256_file


FAMILY = "N51_NEUTRAL_LATE_SESSION_INVENTORY_UNWIND"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_late_session_inventory_unwind.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_LATE_SESSION_INVENTORY_UNWIND_"
    "PREREG_2026_07_29.sha256.json"
)
PARENT_CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_two_clock_ensemble.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT
    / "outputs"
    / "neutral_late_session_inventory_unwind"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_parent_config() -> dict[str, Any]:
    return json.loads(PARENT_CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_first_candidate_count") is not True
        or lock.get("locked_before_any_outcome") is not True
        or lock.get("census_forbids_outcome_loading") is not True
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Inventory-unwind rule was not locked in time")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Inventory-unwind preregistration drift: {relative}"
            )
        checked[relative] = actual
    return checked


def _default_dates(cfg: dict[str, Any]) -> pd.DatetimeIndex:
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


def _midpoint(frame: pd.DataFrame, field: str) -> pd.Series:
    return (
        frame[f"bid_{field}"].astype(float)
        + frame[f"ask_{field}"].astype(float)
    ) / 2.0


def generate_inventory_points(
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    threshold_pips: float,
    dates: Iterable[pd.Timestamp] | None = None,
) -> pd.DataFrame:
    strategy = cfg["strategy"]
    candidate_dates = (
        _default_dates(cfg)
        if dates is None
        else pd.DatetimeIndex(dates)
    )
    rows: list[dict[str, Any]] = []
    for raw_date in candidate_dates:
        midnight = pd.Timestamp(raw_date).normalize()
        if midnight.tzinfo is None:
            midnight = midnight.tz_localize("UTC")
        else:
            midnight = midnight.tz_convert("UTC")
        if bool(strategy["weekdays_only"]) and midnight.weekday() >= 5:
            continue
        inventory_expected = pd.date_range(
            midnight - pd.Timedelta(hours=4),
            periods=int(strategy["inventory_bars_m5"]),
            freq="5min",
        )
        confirmation_expected = pd.date_range(
            midnight,
            periods=int(strategy["confirmation_bars_m5"]),
            freq="5min",
        )
        completion = midnight + pd.Timedelta(minutes=15)
        if (
            completion not in m5.index
            or not inventory_expected.isin(m5.index).all()
            or not confirmation_expected.isin(m5.index).all()
        ):
            continue
        inventory = m5.loc[inventory_expected]
        confirmation = m5.loc[confirmation_expected]
        inventory_open = float(_midpoint(inventory, "open").iloc[0])
        inventory_close = float(_midpoint(inventory, "close").iloc[-1])
        inventory_high = float(_midpoint(inventory, "high").max())
        inventory_low = float(_midpoint(inventory, "low").min())
        confirmation_open = float(
            _midpoint(confirmation, "open").iloc[0]
        )
        confirmation_close = float(
            _midpoint(confirmation, "close").iloc[-1]
        )
        confirmation_high = float(_midpoint(confirmation, "high").max())
        confirmation_low = float(_midpoint(confirmation, "low").min())
        inventory_return_pips = (
            inventory_close - inventory_open
        ) / PIP
        confirmation_return_pips = (
            confirmation_close - confirmation_open
        ) / PIP
        displacement = abs(inventory_return_pips)
        retracement = (
            abs(confirmation_return_pips) / displacement
            if displacement > 0.0
            else 0.0
        )
        minimum_confirmation = float(
            strategy["minimum_opposite_confirmation_pips"]
        )
        minimum_retracement = float(
            strategy["minimum_retracement_fraction"]
        )
        long_signal = bool(
            inventory_return_pips <= -float(threshold_pips)
            and confirmation_return_pips >= minimum_confirmation
            and retracement >= minimum_retracement
        )
        short_signal = bool(
            inventory_return_pips >= float(threshold_pips)
            and confirmation_return_pips <= -minimum_confirmation
            and retracement >= minimum_retracement
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
                "inventory_start_utc": inventory_expected[0],
                "inventory_end_bar_utc": inventory_expected[-1],
                "signal_time_utc": confirmation_expected[-1],
                "signal_complete_utc": completion,
                "entry_time_utc": completion,
                "state_latest_allowed_utc": (
                    completion.floor("h") - pd.Timedelta(hours=1)
                ),
                "inventory_open": inventory_open,
                "inventory_high": inventory_high,
                "inventory_low": inventory_low,
                "inventory_close": inventory_close,
                "inventory_return_pips": inventory_return_pips,
                "inventory_displacement_pips": displacement,
                "confirmation_open": confirmation_open,
                "confirmation_high": confirmation_high,
                "confirmation_low": confirmation_low,
                "confirmation_close": confirmation_close,
                "confirmation_return_pips": confirmation_return_pips,
                "retracement_fraction": retracement,
                "displacement_threshold_pips": float(threshold_pips),
                "auction_high": confirmation_high,
                "auction_low": confirmation_low,
                "side": side,
                "signal_eligible": side != "CASH",
            }
        )
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(
        "entry_time_utc"
    ).reset_index(drop=True)


def build_candidates(
    m5: pd.DataFrame,
    state: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    threshold_pips: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    points = generate_inventory_points(
        m5,
        cfg,
        threshold_pips=threshold_pips,
    )
    if points.empty:
        return points, points.copy()
    signals = points[points["signal_eligible"].astype(bool)].copy()
    if signals.empty:
        return points, signals
    owned = ownership.assign_neutral_ownership(signals, state, cfg)
    return points, auction.add_decision_time_risk(owned, m5, cfg)


def summarize_threshold(
    points: pd.DataFrame,
    candidates: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    threshold_pips: float,
    parent_manifests: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = auction.summarize_census(
        points,
        candidates,
        cfg,
        parent_manifests=parent_manifests,
    )
    result["schema_version"] = (
        "eurusd_neutral_late_session_inventory_unwind_census_v1"
    )
    result["family"] = FAMILY
    result["selected_displacement_threshold_pips"] = float(
        threshold_pips
    )
    result["complete_inventory_days"] = result.pop(
        "complete_midnight_auctions"
    )
    result["confirmed_inventory_unwind_signals"] = result.pop(
        "failed_auction_signals"
    )
    return result


def choose_threshold(
    ladder: Iterable[float],
    summaries: dict[float, dict[str, Any]],
) -> tuple[float, bool]:
    ordered = [float(value) for value in ladder]
    for threshold in ordered:
        if bool(summaries[threshold]["census_pass"]):
            return threshold, True
    return ordered[-1], False


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
    ladder = [
        float(value)
        for value in cfg["strategy"][
            "absolute_inventory_displacement_threshold_ladder_pips"
        ]
    ]
    summaries: dict[float, dict[str, Any]] = {}
    artifacts_by_threshold: dict[
        float, tuple[pd.DataFrame, pd.DataFrame]
    ] = {}
    for threshold in ladder:
        points, candidates = build_candidates(
            m5,
            state,
            cfg,
            threshold_pips=threshold,
        )
        summaries[threshold] = summarize_threshold(
            points,
            candidates,
            cfg,
            threshold_pips=threshold,
            parent_manifests=manifests,
        )
        artifacts_by_threshold[threshold] = (points, candidates)
    selected_threshold, passed = choose_threshold(ladder, summaries)
    selected = dict(summaries[selected_threshold])
    selected["threshold_selection_pass"] = passed
    selected["threshold_selection_status"] = (
        "HIGHEST_CAPACITY_COMPLIANT_THRESHOLD_SELECTED"
        if passed
        else "NO_THRESHOLD_PASSED_NO_PNL_ALLOWED"
    )
    selected["threshold_ladder_results"] = [
        {
            "displacement_threshold_pips": threshold,
            "census_pass": bool(summaries[threshold]["census_pass"]),
            "risk_eligible_candidates_total": int(
                summaries[threshold][
                    "risk_eligible_candidates_total"
                ]
            ),
            "distinct_candidate_dates_total": int(
                summaries[threshold][
                    "distinct_candidate_dates_total"
                ]
            ),
            "long_candidates": int(
                summaries[threshold]["long_candidates"]
            ),
            "short_candidates": int(
                summaries[threshold]["short_candidates"]
            ),
            "recent_six_month_candidates": int(
                summaries[threshold]["recent_six_month_candidates"]
            ),
            "by_window": summaries[threshold]["by_window"],
            "gate_results": summaries[threshold]["gate_results"],
        }
        for threshold in ladder
    ]
    points, candidates = artifacts_by_threshold[selected_threshold]
    eligible = candidates[
        candidates["risk_eligible"].astype(bool)
    ].copy()
    return selected, {
        "CANDIDATES": eligible,
        "ALL_INVENTORY_POINTS": points,
        "ALL_CONFIRMED_SIGNALS": candidates,
    }


def write_census(
    census: dict[str, Any],
    artifacts: dict[str, pd.DataFrame],
) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(serialize(census), indent=2, sort_keys=True) + "\n"
    )
    (OUTPUT_ROOT / "CENSUS.json").write_text(
        payload,
        encoding="utf-8",
    )
    for name, frame in artifacts.items():
        frame.to_csv(OUTPUT_ROOT / f"{name}.csv", index=False)


__all__ = [
    "build_candidates",
    "choose_threshold",
    "generate_inventory_points",
    "load_config",
    "run_census",
    "summarize_threshold",
    "verify_lock",
    "write_census",
]

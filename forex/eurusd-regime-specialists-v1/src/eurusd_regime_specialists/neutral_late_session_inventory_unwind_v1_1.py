from __future__ import annotations

import json
from typing import Any, Iterable

import pandas as pd

from . import neutral_0608_range_breakout_transfer as ownership
from . import neutral_late_session_inventory_unwind as parent
from . import neutral_midnight_auction_rejection as auction
from .research import PACKAGE_ROOT, load_inputs, serialize, sha256_file


FAMILY = "N51_1_NEUTRAL_LATE_SESSION_INVENTORY_UNWIND"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_late_session_inventory_unwind_v1_1.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_LATE_SESSION_INVENTORY_UNWIND_"
    "V1_1_PREREG_2026_07_29.sha256.json"
)
PARENT_CONFIG_PATH = (
    PACKAGE_ROOT / "config" / "frozen_two_clock_ensemble.json"
)
OUTPUT_ROOT = (
    PACKAGE_ROOT
    / "outputs"
    / "neutral_late_session_inventory_unwind_v1_1"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if (
        lock.get("locked_before_first_candidate_count") is not True
        or lock.get("locked_before_any_outcome") is not True
        or lock.get("census_forbids_outcome_loading") is not True
        or lock.get("broker_action_allowed") is not False
    ):
        raise RuntimeError("Inventory-unwind V1.1 was not locked in time")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"Inventory-unwind V1.1 preregistration drift: {relative}"
            )
        checked[relative] = actual
    return checked


def derive_threshold_view(
    points: pd.DataFrame,
    candidates: pd.DataFrame,
    threshold_pips: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    threshold = float(threshold_pips)
    view_points = points.copy()
    eligible = (
        view_points["side"].ne("CASH")
        & view_points["inventory_displacement_pips"].ge(threshold)
    )
    view_points["signal_eligible"] = eligible
    view_candidates = candidates[
        candidates["inventory_displacement_pips"].ge(threshold)
    ].copy()
    return view_points, view_candidates


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
    parent_cfg = parent.load_parent_config()
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
    floor = min(ladder)
    base_points = parent.generate_inventory_points(
        m5,
        cfg,
        threshold_pips=floor,
    )
    base_points["family"] = FAMILY
    base_signals = base_points[
        base_points["signal_eligible"].astype(bool)
    ].copy()
    if base_signals.empty:
        base_candidates = base_signals
    else:
        owned = ownership.assign_neutral_ownership(
            base_signals,
            state,
            cfg,
        )
        base_candidates = auction.add_decision_time_risk(
            owned,
            m5,
            cfg,
        )
        base_candidates["family"] = FAMILY
    summaries: dict[float, dict[str, Any]] = {}
    views: dict[float, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for threshold in ladder:
        points, candidates = derive_threshold_view(
            base_points,
            base_candidates,
            threshold,
        )
        summary = parent.summarize_threshold(
            points,
            candidates,
            cfg,
            threshold_pips=threshold,
            parent_manifests=manifests,
        )
        summary["family"] = FAMILY
        summary["schema_version"] = (
            "eurusd_neutral_late_session_inventory_unwind_"
            "census_v1_1"
        )
        summaries[threshold] = summary
        views[threshold] = (points, candidates)
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
    points, candidates = views[selected_threshold]
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
    "choose_threshold",
    "derive_threshold_view",
    "load_config",
    "run_census",
    "verify_lock",
    "write_census",
]

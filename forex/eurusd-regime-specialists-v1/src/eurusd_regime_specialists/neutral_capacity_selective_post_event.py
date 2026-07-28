from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .neutral_midnight_pairs import aggregate_days, write_json
from .neutral_post_event_drive import _oracle
from .neutral_selective_post_event import (
    _model_columns,
    execute_selected,
    fit_and_screen,
    load_source,
    summarize,
)
from .research import PACKAGE_ROOT, sha256_file


FAMILY = "N31_NEUTRAL_CAPACITY_SELECTIVE_POST_EVENT"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_capacity_selective_post_event"
)


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_capacity_selective_post_event.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_CAPACITY_SELECTIVE_POST_EVENT_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get(
            "locked_before_capacity_selective_post_event_forward_outcome_pass"
        )
        is not True
    ):
        raise RuntimeError(
            "Neutral capacity-selective post-event rule is not locked"
        )
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral capacity-selective preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for contract_name in (
        "parent_post_event_contract",
        "parent_selective_screen_contract",
    ):
        contract = cfg[contract_name]
        if sha256_file(PACKAGE_ROOT / contract["path"]) != contract["sha256"]:
            raise RuntimeError(f"{contract_name} config drift")
        if (
            sha256_file(PACKAGE_ROOT / contract["lock_path"])
            != contract["lock_sha256"]
        ):
            raise RuntimeError(f"{contract_name} lock drift")
        if "screen_path" in contract and (
            sha256_file(PACKAGE_ROOT / contract["screen_path"])
            != contract["screen_sha256"]
        ):
            raise RuntimeError(f"{contract_name} screen drift")
    if cfg["pre_forward_selection_census"] is None:
        raise RuntimeError("Capacity-selective candidate manifest is not frozen")
    return checked


def threshold_counts(
    scored: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    ladder = cfg["capacity_calibration"]["threshold_ladder_descending"]
    for threshold in ladder:
        threshold_counts_by_window = {}
        selected = scored[
            scored["model_selection_probability"].ge(float(threshold))
        ]
        for name, bounds in cfg["windows"].items():
            start, end = map(pd.Timestamp, bounds)
            subset = selected[
                selected["entry_time_utc"].between(start, end)
            ]
            threshold_counts_by_window[name] = int(len(subset))
        counts[str(threshold)] = threshold_counts_by_window
    return counts


def choose_capacity_threshold(
    counts: dict[str, dict[str, int]],
    cfg: dict[str, Any],
) -> float | None:
    minimum = int(
        cfg["capacity_calibration"][
            "minimum_candidates_each_forward_window"
        ]
    )
    for threshold in cfg["capacity_calibration"][
        "threshold_ladder_descending"
    ]:
        block = counts[str(threshold)]
        if all(
            int(block[name]) >= minimum
            for name in cfg["forward_windows"]
        ):
            return float(threshold)
    return None


def fit_capacity_screen(
    cfg: dict[str, Any],
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
    dict[str, Any],
    dict[str, int],
]:
    candidates, m5, parent_census, feature_reasons = load_source(cfg)
    selected, scored, coefficients, base_census = fit_and_screen(
        candidates, m5, cfg
    )
    counts = threshold_counts(scored, cfg)
    frozen_counts = cfg["capacity_calibration"]["threshold_counts"]
    if counts != frozen_counts:
        raise RuntimeError(
            f"Outcome-blind threshold-count drift: {counts!r}"
        )
    chosen = choose_capacity_threshold(counts, cfg)
    expected = float(
        cfg["capacity_calibration"]["selected_threshold"]
    )
    if chosen != expected:
        raise RuntimeError(
            f"Capacity threshold drift: {chosen!r} != {expected!r}"
        )
    if float(cfg["model"]["selection_probability_threshold"]) != expected:
        raise RuntimeError("Model threshold differs from capacity selection")
    census = {
        **base_census,
        "capacity_calibration": {
            "threshold_counts": counts,
            "selected_threshold": chosen,
            "minimum_candidates_each_forward_window": int(
                cfg["capacity_calibration"][
                    "minimum_candidates_each_forward_window"
                ]
            ),
            "outcomes_used": False,
        },
    }
    return (
        candidates,
        m5,
        selected,
        scored,
        coefficients,
        census,
        parent_census,
        feature_reasons,
    )


def run_screen() -> tuple[dict[str, Any], dict[str, pd.DataFrame]]:
    cfg = load_config()
    (
        _,
        _,
        selected,
        scored,
        coefficients,
        census,
        parent_census,
        feature_reasons,
    ) = fit_capacity_screen(cfg)
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": "PRE_FORWARD_CAPACITY_SELECTION_SCREEN",
        "forward_outcomes_loaded": False,
        "parent_outcome_blind_census": parent_census,
        "feature_cash_reasons": feature_reasons,
        "pre_forward_selection_census": census,
        "capacity_calibration": cfg["capacity_calibration"],
        "model": {
            "type": cfg["model"]["type"],
            "training_end_utc": cfg["training_window"][1],
            "refit_after_2022": False,
            "threshold": cfg["model"][
                "selection_probability_threshold"
            ],
            "feature_count": len(_model_columns(cfg)),
        },
    }
    return result, {
        "SELECTED_CANDIDATES": selected,
        "SCORED_CANDIDATES": scored,
        "COEFFICIENTS": coefficients,
    }


def run_neutral_capacity_selective_post_event() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    cfg = load_config()
    (
        _,
        m5,
        selected,
        scored,
        _,
        census,
        parent_census,
        feature_reasons,
    ) = fit_capacity_screen(cfg)
    if census != cfg["pre_forward_selection_census"]:
        raise RuntimeError(
            "Capacity-selective candidate manifest drift: "
            f"actual={census!r} "
            f"frozen={cfg['pre_forward_selection_census']!r}"
        )
    trades, diagnostics = execute_selected(selected, m5, cfg)
    if not trades.empty:
        trades["family"] = FAMILY
    oracle, matches = _oracle(trades, cfg)
    strategy, checks = summarize(
        trades, selected, m5, cfg, census, oracle
    )
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    available = int(
        selected["entry_time_utc"].ge(prospective_start).sum()
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "HISTORICAL_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if strategy["admitted"]
            else "REJECTED_NEUTRAL_CAPACITY_SELECTIVE_POST_EVENT_V1"
        ),
        "information_status": cfg["information_status"],
        "parent_post_event_contract": cfg[
            "parent_post_event_contract"
        ],
        "parent_selective_screen_contract": cfg[
            "parent_selective_screen_contract"
        ],
        "causality": {
            "training_end_utc": cfg["training_window"][1],
            "single_fit": True,
            "forward_refit": False,
            "capacity_threshold_uses_outcomes": False,
            "features_complete_at_entry": True,
            "forward_outcome_in_signal": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "parent_outcome_blind_census": parent_census,
        "feature_cash_reasons": feature_reasons,
        "pre_forward_selection_census": census,
        "capacity_calibration": cfg["capacity_calibration"],
        "model": {
            "type": cfg["model"]["type"],
            "threshold": cfg["model"][
                "selection_probability_threshold"
            ],
            "feature_count": len(_model_columns(cfg)),
        },
        "strategy": strategy,
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": prospective_start,
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": available,
            "status": "WAITING_FOR_POST_LOCK_MARKET_DATA",
        },
        "verdict": (
            "The frozen capacity-selective rule passed every historical "
            "gate but remains research-only pending prospective evidence."
            if strategy["admitted"]
            else "The frozen capacity-selective rule failed one or more "
            "gates and is closed without repair."
        ),
    }
    return result, {
        "SELECTED_CANDIDATES": selected,
        "SCORED_CANDIDATES": scored,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "DIAGNOSTICS": diagnostics,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "choose_capacity_threshold",
    "fit_capacity_screen",
    "load_config",
    "run_neutral_capacity_selective_post_event",
    "run_screen",
    "threshold_counts",
    "verify_lock",
    "write_json",
]

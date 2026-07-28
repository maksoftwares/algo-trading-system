from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config
from .neutral_binance_eurusdt_flow import load_parent_points
from .research import (
    PACKAGE_ROOT,
    PIP,
    is_quarantined,
    load_inputs,
    remove_top_winners,
    serialize,
    sha256_file,
)


FAMILY = "N45_NEUTRAL_LONDON_FIX_REVERSAL"
EXPERTS = ("ORDINARY_FIX_REVERSAL", "MONTH_END_FIX_REVERSAL")
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_london_fix_reversal"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_london_fix_reversal.json"
)
PREREG_LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_LONDON_FIX_REVERSAL_PREREG_2026_07_28.sha256.json"
)
SELECTION_LOCK_PATH = (
    OUTPUT_ROOT / "DEVELOPMENT_SELECTION_LOCK.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_prereg_lock() -> dict[str, str]:
    lock = json.loads(PREREG_LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_outcome") is not True:
        raise RuntimeError("London-fix family is not preregistered")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"London-fix preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for key in (
        "parent_neutral_date_contract",
        "data_and_classifier_contract",
    ):
        reference = cfg[key]
        if (
            sha256_file(PACKAGE_ROOT / reference["path"])
            != reference["sha256"]
        ):
            raise RuntimeError(f"{key} drift")
    parent = cfg["parent_neutral_date_contract"]
    if (
        sha256_file(PACKAGE_ROOT / parent["paired_source_path"])
        != parent["paired_source_sha256"]
    ):
        raise RuntimeError("Parent Neutral-date source drift")
    return checked


def verify_selection_lock() -> dict[str, Any]:
    lock = json.loads(SELECTION_LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_forward_outcome") is not True:
        raise RuntimeError("Development selection is not forward-locked")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"Development selection drift: {relative}")
    return lock


def london_fix_utc(date_value: Any) -> pd.Timestamp:
    date = pd.Timestamp(date_value).strftime("%Y-%m-%d")
    return pd.Timestamp(
        f"{date} 16:00:00", tz="Europe/London"
    ).tz_convert("UTC")


def is_calendar_month_end_weekday(date_value: Any) -> bool:
    date = pd.Timestamp(date_value).normalize()
    if date.weekday() >= 5:
        return False
    cursor = date + pd.Timedelta(days=1)
    while cursor.weekday() >= 5:
        cursor += pd.Timedelta(days=1)
    return cursor.month != date.month


def _mid_open(bar: pd.Series) -> float:
    return 0.5 * (
        float(bar["bid_open"]) + float(bar["ask_open"])
    )


def _mid_close(bar: pd.Series) -> float:
    return 0.5 * (
        float(bar["bid_close"]) + float(bar["ask_close"])
    )


def build_candidates(
    neutral_points: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    safe = neutral_points[neutral_points["clock_minute"].eq(0)].copy()
    neutral_dates = sorted(set(safe["eligible_date"].astype(str)))
    lookback = int(cfg["strategy"]["pre_fix_completed_m5_bars"])
    rolling = int(
        cfg["strategy"]["magnitude_lookback_observations"]
    )
    base = load_ensemble_config()
    rows: list[dict[str, Any]] = []
    reasons = {
        "weekend": 0,
        "required_bar_missing": 0,
        "quarantine": 0,
        "insufficient_prior_magnitude_history": 0,
        "below_prior_median_displacement": 0,
        "zero_pre_fix_displacement": 0,
        "zero_or_same_direction_fix_bar": 0,
    }
    raw_observations: list[dict[str, Any]] = []
    for date in neutral_dates:
        day = pd.Timestamp(date)
        if day.weekday() >= 5:
            reasons["weekend"] += 1
            continue
        fix_time = london_fix_utc(day)
        pre_times = pd.date_range(
            fix_time - pd.Timedelta(minutes=5 * lookback),
            periods=lookback,
            freq="5min",
        )
        confirmation_time = fix_time
        entry_time = fix_time + pd.Timedelta(minutes=5)
        required = [*pre_times, confirmation_time, entry_time]
        if any(timestamp not in m5.index for timestamp in required):
            reasons["required_bar_missing"] += 1
            continue
        if is_quarantined(
            entry_time, "EURUSD", base["quarantine"]
        ):
            reasons["quarantine"] += 1
            continue
        pre = m5.loc[pre_times]
        confirmation = m5.loc[confirmation_time]
        pre_displacement = (
            _mid_close(pre.iloc[-1]) - _mid_open(pre.iloc[0])
        )
        confirmation_displacement = (
            _mid_close(confirmation) - _mid_open(confirmation)
        )
        raw_observations.append(
            {
                "eligible_date": date,
                "fix_time_utc": fix_time,
                "confirmation_time_utc": confirmation_time,
                "entry_time_utc": entry_time,
                "pre_fix_displacement_pips": pre_displacement / PIP,
                "absolute_pre_fix_displacement_pips": (
                    abs(pre_displacement) / PIP
                ),
                "confirmation_displacement_pips": (
                    confirmation_displacement / PIP
                ),
                "confirmation_bid_low": float(
                    confirmation["bid_low"]
                ),
                "confirmation_ask_high": float(
                    confirmation["ask_high"]
                ),
                "expert": (
                    "MONTH_END_FIX_REVERSAL"
                    if is_calendar_month_end_weekday(day)
                    else "ORDINARY_FIX_REVERSAL"
                ),
            }
        )
    observations = pd.DataFrame(raw_observations)
    if observations.empty:
        return observations, {
            "neutral_dates": int(len(neutral_dates)),
            "raw_fix_observations": 0,
            "confirmed_candidates": 0,
            "cash_reasons": reasons,
            "passed": False,
        }
    observations = observations.sort_values("fix_time_utc").reset_index(
        drop=True
    )
    observations["prior_20_median_abs_displacement_pips"] = (
        observations["absolute_pre_fix_displacement_pips"]
        .rolling(rolling, min_periods=rolling)
        .median()
        .shift(1)
    )
    for _, observation in observations.iterrows():
        threshold = observation[
            "prior_20_median_abs_displacement_pips"
        ]
        if pd.isna(threshold):
            reasons["insufficient_prior_magnitude_history"] += 1
            continue
        if (
            float(observation["absolute_pre_fix_displacement_pips"])
            + 1e-9
            < float(threshold)
        ):
            reasons["below_prior_median_displacement"] += 1
            continue
        pre = float(observation["pre_fix_displacement_pips"])
        confirmation = float(
            observation["confirmation_displacement_pips"]
        )
        if pre == 0:
            reasons["zero_pre_fix_displacement"] += 1
            continue
        side = "SHORT" if pre > 0 else "LONG"
        confirmation_side = (
            "LONG"
            if confirmation > 0
            else "SHORT"
            if confirmation < 0
            else "CASH"
        )
        if confirmation_side != side:
            reasons["zero_or_same_direction_fix_bar"] += 1
            continue
        rows.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                **observation.to_dict(),
                "side": side,
                "window": window_name(
                    pd.Timestamp(observation["entry_time_utc"]), cfg
                ),
            }
        )
    candidates = pd.DataFrame(rows)
    if candidates.empty:
        candidates = pd.DataFrame(
            columns=[
                "eligible_date",
                "entry_time_utc",
                "expert",
                "side",
                "window",
            ]
        )
    else:
        candidates = candidates.sort_values(
            ["entry_time_utc", "expert"]
        ).reset_index(drop=True)
    census = census_summary(
        candidates, len(neutral_dates), len(observations), reasons, cfg
    )
    return candidates, census


def window_name(
    timestamp: pd.Timestamp, cfg: dict[str, Any]
) -> str:
    for name, (start, end) in cfg["windows"].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE"


def census_summary(
    candidates: pd.DataFrame,
    neutral_dates: int,
    observations: int,
    reasons: dict[str, int],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    by_window = {
        name: int(candidates["window"].eq(name).sum())
        for name in cfg["windows"]
    }
    by_expert = {
        expert: int(candidates["expert"].eq(expert).sum())
        for expert in EXPERTS
    }
    by_side = {
        side: int(candidates["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    gate = cfg["outcome_blind_census"]
    development = (
        by_window["development_a_2019_2020"]
        + by_window["development_b_2021_2022"]
    )
    checks = {
        "total": len(candidates)
        >= int(gate["minimum_candidates_total"]),
        "development": development
        >= int(gate["minimum_candidates_development"]),
        "full_forward_years": all(
            by_window[name]
            >= int(gate["minimum_candidates_each_full_forward_year"])
            for name in (
                "chronological_2023",
                "chronological_2024",
                "chronological_2025",
            )
        ),
        "recent_half_year": (
            by_window["recent_2026_h1"]
            >= int(gate["minimum_candidates_recent_half_year"])
        ),
        "both_sides": all(
            by_side[side] >= int(gate["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
        "month_end": (
            by_expert["MONTH_END_FIX_REVERSAL"]
            >= int(gate["minimum_month_end_candidates_total"])
        ),
    }
    return {
        "neutral_dates": int(neutral_dates),
        "raw_fix_observations": int(observations),
        "confirmed_candidates": int(len(candidates)),
        "candidate_dates": int(
            candidates["eligible_date"].nunique()
            if len(candidates)
            else 0
        ),
        "by_window": by_window,
        "by_expert": by_expert,
        "by_side": by_side,
        "cash_reasons": reasons,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }


def _effective_ask(
    bar: pd.Series, field: str, spread_floor: float
) -> float:
    return max(
        float(bar[f"ask_{field}"]),
        float(bar[f"bid_{field}"]) + spread_floor,
    )


def _walk_exit(
    m5: pd.DataFrame,
    start: int,
    deadline: pd.Timestamp,
    side: str,
    stop: float,
    target: float,
    spread_floor: float,
    slippage: float,
) -> tuple[pd.Timestamp, float, str]:
    end = min(
        max(
            int(m5.index.searchsorted(deadline, side="right")) - 1,
            start,
        ),
        len(m5) - 1,
    )
    for position in range(start, end + 1):
        bar = m5.iloc[position]
        if side == "LONG":
            if float(bar["bid_low"]) <= stop:
                return (
                    m5.index[position],
                    min(float(bar["bid_open"]), stop) - slippage,
                    "STOP",
                )
            if float(bar["bid_high"]) >= target:
                return (
                    m5.index[position],
                    max(float(bar["bid_open"]), target) - slippage,
                    "TARGET",
                )
        else:
            ask_open = _effective_ask(bar, "open", spread_floor)
            ask_high = _effective_ask(bar, "high", spread_floor)
            ask_low = _effective_ask(bar, "low", spread_floor)
            if ask_high >= stop:
                return (
                    m5.index[position],
                    max(ask_open, stop) + slippage,
                    "STOP",
                )
            if ask_low <= target:
                return (
                    m5.index[position],
                    min(ask_open, target) + slippage,
                    "TARGET",
                )
    bar = m5.iloc[end]
    if side == "LONG":
        return (
            m5.index[end],
            float(bar["bid_close"]) - slippage,
            "TIME_12H",
        )
    return (
        m5.index[end],
        _effective_ask(bar, "close", spread_floor) + slippage,
        "TIME_12H",
    )


def simulate(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    execution = cfg["execution"]
    strategy = cfg["strategy"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    stop_buffer = float(strategy["stop_buffer_pips"]) * PIP
    stop_floor = float(strategy["stop_floor_pips"]) * PIP
    stop_ceiling = float(strategy["stop_ceiling_pips"]) * PIP
    target_r = float(strategy["target_r"])
    hold = pd.Timedelta(
        hours=float(strategy["maximum_hold_hours"])
    )
    open_until: pd.Timestamp | None = None
    records: list[dict[str, Any]] = []
    skips = {
        "position_open": 0,
        "entry_bar_missing": 0,
        "risk_ceiling": 0,
    }
    for _, candidate in candidates.sort_values(
        ["entry_time_utc", "expert"]
    ).iterrows():
        entry_time = pd.Timestamp(candidate["entry_time_utc"])
        if open_until is not None and entry_time <= open_until:
            skips["position_open"] += 1
            continue
        position = int(
            m5.index.searchsorted(entry_time, side="left")
        )
        if (
            position >= len(m5)
            or m5.index[position] != entry_time
        ):
            skips["entry_bar_missing"] += 1
            continue
        bar = m5.iloc[position]
        side = str(candidate["side"])
        if side == "LONG":
            entry = (
                _effective_ask(bar, "open", spread_floor)
                + slippage
            )
            raw_risk = entry - (
                float(candidate["confirmation_bid_low"])
                - stop_buffer
            )
            risk = max(raw_risk, stop_floor)
            stop = entry - risk
            target = entry + target_r * risk
        else:
            entry = float(bar["bid_open"]) - slippage
            raw_risk = (
                float(candidate["confirmation_ask_high"])
                + stop_buffer
                - entry
            )
            risk = max(raw_risk, stop_floor)
            stop = entry + risk
            target = entry - target_r * risk
        if risk > stop_ceiling:
            skips["risk_ceiling"] += 1
            continue
        exit_time, exit_price, reason = _walk_exit(
            m5,
            position,
            entry_time + hold,
            side,
            stop,
            target,
            spread_floor,
            slippage,
        )
        pnl = (
            exit_price - entry
            if side == "LONG"
            else entry - exit_price
        )
        result_r = pnl / risk
        records.append(
            {
                "family": FAMILY,
                "expert": candidate["expert"],
                "regime": "NEUTRAL",
                "eligible_date": candidate["eligible_date"],
                "side": side,
                "fix_time_utc": candidate["fix_time_utc"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "r": result_r,
                "extra_half_pip_stress_r": (
                    result_r - 0.5 * PIP / risk
                ),
                "fixed_0p01_lot_usd": pnl * 1000.0,
                "pre_fix_displacement_pips": candidate[
                    "pre_fix_displacement_pips"
                ],
                "confirmation_displacement_pips": candidate[
                    "confirmation_displacement_pips"
                ],
                "prior_20_median_abs_displacement_pips": candidate[
                    "prior_20_median_abs_displacement_pips"
                ],
            }
        )
        open_until = exit_time
    return pd.DataFrame(records), skips


def _window(
    frame: pd.DataFrame, start: str, end: str
) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame[
        frame["entry_time_utc"].between(
            pd.Timestamp(start), pd.Timestamp(end), inclusive="both"
        )
    ]


def development_metrics(
    trades: pd.DataFrame, cfg: dict[str, Any]
) -> dict[str, Any]:
    windows = {
        name: payoff_metrics(_window(trades, *cfg["windows"][name]))
        for name in cfg["development_selection"]["allowed_windows"]
    }
    combined = pd.concat(
        [
            _window(trades, *cfg["windows"][name])
            for name in cfg["development_selection"][
                "allowed_windows"
            ]
        ],
        ignore_index=True,
    )
    overall = payoff_metrics(combined)
    gate = cfg["development_selection"]
    checks = {
        "each_window": all(
            block["trades"]
            >= int(gate["minimum_trades_each_window"])
            and block["profit_factor"]
            >= float(gate["minimum_profit_factor_each_window"])
            and block["expectancy_r"]
            > float(gate["minimum_expectancy_r_each_window"])
            for block in windows.values()
        ),
        "combined_profit_factor": overall["profit_factor"]
        >= float(gate["minimum_combined_profit_factor"]),
    }
    return {
        "windows": windows,
        "combined": overall,
        "selection_checks": checks,
        "selected": bool(all(checks.values())),
    }


def _load_inputs() -> tuple[
    dict[str, Any], pd.DataFrame, pd.DataFrame, dict[str, Any]
]:
    cfg = load_config()
    m5, _, manifests = load_inputs(load_ensemble_config())
    points = load_parent_points(include_outcomes=False)
    safe_columns = {
        "eligible_date",
        "clock_minute",
        "decision_id",
        "entry_time_utc",
    }
    if not safe_columns.issubset(points.columns):
        raise RuntimeError("Parent Neutral points lack safe columns")
    prohibited = (
        "outcome",
        "target_first",
        "oracle_member",
        "exit_time",
        "entry_price",
        "target_price",
        "stop_price",
    )
    if any(
        any(token in column for token in prohibited)
        for column in points.columns
    ):
        raise RuntimeError("Outcome column leaked into Neutral dates")
    return cfg, m5, points, manifests


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    verify_prereg_lock()
    cfg, m5, points, manifests = _load_inputs()
    candidates, census = build_candidates(points, m5, cfg)
    result = {
        "schema_version": (
            "eurusd_neutral_london_fix_reversal_census_v1"
        ),
        "family": FAMILY,
        "status": (
            "CENSUS_PASS_DEVELOPMENT_ALLOWED"
            if census["passed"]
            else "CENSUS_FAIL_NO_PNL_ALLOWED"
        ),
        "census": census,
        "data_manifests": manifests,
        "broker_action_allowed": False,
    }
    return serialize(result), candidates


def run_development() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_prereg_lock()
    cfg, m5, points, manifests = _load_inputs()
    candidates, census = build_candidates(points, m5, cfg)
    if not census["passed"]:
        raise RuntimeError("Outcome-blind census failed; P&L forbidden")
    cutoff = pd.Timestamp("2022-12-31T23:59:59Z")
    development_candidates = candidates[
        candidates["entry_time_utc"].le(cutoff)
    ].copy()
    development_m5 = m5[m5.index <= cutoff].copy()
    trades_by_expert: dict[str, pd.DataFrame] = {}
    metrics: dict[str, Any] = {}
    skips: dict[str, Any] = {}
    for expert in EXPERTS:
        trades, expert_skips = simulate(
            development_candidates[
                development_candidates["expert"].eq(expert)
            ],
            development_m5,
            cfg,
        )
        trades_by_expert[expert] = trades
        metrics[expert] = development_metrics(trades, cfg)
        skips[expert] = expert_skips
    selected = [
        expert for expert in EXPERTS if metrics[expert]["selected"]
    ]
    selection = {
        "schema_version": (
            "eurusd_neutral_london_fix_development_selection_v1"
        ),
        "selected_experts": selected,
        "selection_rule": cfg["development_selection"][
            "selection_rule"
        ],
        "outcome_source_max_timestamp_utc": cutoff,
        "forward_outcomes_loaded": False,
    }
    status = (
        "DEVELOPMENT_PASS_SELECTION_LOCK_REQUIRED"
        if selected
        else "REJECTED_IN_DEVELOPMENT_FORWARD_FORBIDDEN"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_london_fix_reversal_development_v1"
        ),
        "family": FAMILY,
        "status": status,
        "census": census,
        "development": metrics,
        "execution_skips": skips,
        "selection": selection,
        "data_manifests": manifests,
        "broker_action_allowed": False,
    }
    artifacts = {
        "CANDIDATES_OUTCOME_BLIND": candidates,
        "DEVELOPMENT_CANDIDATES": development_candidates,
        **{
            f"{expert}_DEVELOPMENT_TRADES": trades
            for expert, trades in trades_by_expert.items()
        },
        "SELECTION": pd.DataFrame(
            [{"selected_experts": json.dumps(selected)}]
        ),
    }
    return serialize(result), artifacts


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "OUTPUT_ROOT",
    "build_candidates",
    "development_metrics",
    "is_calendar_month_end_weekday",
    "load_config",
    "london_fix_utc",
    "run_census",
    "run_development",
    "simulate",
    "verify_prereg_lock",
    "verify_selection_lock",
    "write_json",
]

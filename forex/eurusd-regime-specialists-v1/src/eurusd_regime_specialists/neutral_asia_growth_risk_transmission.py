from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .asymmetric import payoff_metrics
from .neutral_growth_risk_consensus import (
    build_candidates as build_external_candidates,
    load_config as load_parent_config,
    load_eurusd_stage,
    load_growth_risk,
    load_oracle_forward,
    safe_neutral_dates,
    same_day_same_side_oracle_metrics,
    simulate,
    verify_prereg_lock as verify_parent_prereg_lock,
    write_json,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    remove_top_winners,
    serialize,
    sha256_file,
)


FAMILY = "N48_NEUTRAL_ASIA_GROWTH_RISK_TRANSMISSION"
OUTPUT_ROOT = (
    PACKAGE_ROOT
    / "outputs"
    / "neutral_asia_growth_risk_transmission"
)
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_asia_growth_risk_transmission.json"
)
PREREG_LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_ASIA_GROWTH_RISK_TRANSMISSION_PREREG_2026_07_28.sha256.json"
)
DEVELOPMENT_LOCK_PATH = (
    OUTPUT_ROOT / "DEVELOPMENT_GATE_LOCK.sha256.json"
)
CONFIRMATION_LOCK_PATH = (
    OUTPUT_ROOT / "CONFIRMATION_GATE_LOCK.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_prereg_lock() -> dict[str, str]:
    verify_parent_prereg_lock()
    lock = json.loads(PREREG_LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_transmission_subgroup_outcome") is not True:
        raise RuntimeError("N48 is not preregistered")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"N48 preregistration drift: {relative}")
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_mechanics"]
    for relative, expected in (
        (parent["config_path"], parent["config_sha256"]),
        (
            parent["prereg_lock_path"],
            parent["prereg_lock_sha256"],
        ),
        (
            cfg["prior_attempt_closure"]["path"],
            cfg["prior_attempt_closure"]["sha256"],
        ),
    ):
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"N48 evidence drift: {relative}")
    return checked


def _verify_stage_lock(
    path: Path,
    flag: str,
    result_path_key: str,
    expected_status: str,
) -> dict[str, Any]:
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get(flag) is not True:
        raise RuntimeError(f"N48 stage lock lacks {flag}")
    for relative, expected in lock["files"].items():
        if sha256_file(PACKAGE_ROOT / relative) != expected:
            raise RuntimeError(f"N48 stage drift: {relative}")
    result = json.loads(
        (
            PACKAGE_ROOT / lock[result_path_key]
        ).read_text(encoding="utf-8")
    )
    if result.get("status") != expected_status:
        raise RuntimeError("N48 stage lock is not a pass")
    return lock


def verify_development_lock() -> dict[str, Any]:
    verify_prereg_lock()
    return _verify_stage_lock(
        DEVELOPMENT_LOCK_PATH,
        "locked_before_2024_eurusd_outcome",
        "development_result_path",
        "DEVELOPMENT_PASS_2024_LOCK_REQUIRED",
    )


def verify_confirmation_lock() -> dict[str, Any]:
    verify_development_lock()
    return _verify_stage_lock(
        CONFIRMATION_LOCK_PATH,
        "locked_before_2025_2026_eurusd_outcome",
        "confirmation_result_path",
        "CONFIRMATION_PASS_FORWARD_LOCK_REQUIRED",
    )


def add_transmission_confirmation(
    external_candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, int]]:
    bars = int(
        cfg["strategy"][
            "eurusd_confirmation_completed_m5_bars"
        ]
    )
    if bars != 3:
        raise RuntimeError("N48 requires exactly three M5 bars")
    rows: list[dict[str, Any]] = []
    reasons = {
        "non_asia_external_candidate": 0,
        "required_eurusd_bar_missing": 0,
        "opposite_or_zero_transmission": 0,
    }
    for _, candidate in external_candidates.sort_values(
        "entry_time_utc"
    ).iterrows():
        if candidate["expert"] != cfg["expert"]:
            reasons["non_asia_external_candidate"] += 1
            continue
        entry = pd.Timestamp(candidate["entry_time_utc"])
        required = pd.date_range(
            entry - pd.Timedelta(minutes=5 * bars),
            periods=bars,
            freq="5min",
        )
        if any(timestamp not in m5.index for timestamp in required):
            reasons["required_eurusd_bar_missing"] += 1
            continue
        prior = m5.loc[required]
        first_mid_open = 0.5 * (
            float(prior.iloc[0]["bid_open"])
            + float(prior.iloc[0]["ask_open"])
        )
        last_mid_close = 0.5 * (
            float(prior.iloc[-1]["bid_close"])
            + float(prior.iloc[-1]["ask_close"])
        )
        displacement = last_mid_close - first_mid_open
        aligned = (
            candidate["side"] == "LONG" and displacement > 0
        ) or (
            candidate["side"] == "SHORT" and displacement < 0
        )
        if not aligned:
            reasons["opposite_or_zero_transmission"] += 1
            continue
        row = candidate.to_dict()
        row["family"] = FAMILY
        row["eurusd_confirmation_first_bar_utc"] = required[0]
        row["eurusd_confirmation_last_bar_utc"] = required[-1]
        row["eurusd_confirmation_displacement_pips"] = (
            displacement / PIP
        )
        rows.append(row)
    if rows:
        result = pd.DataFrame(rows).sort_values(
            "entry_time_utc"
        ).reset_index(drop=True)
    else:
        result = pd.DataFrame(
            columns=[
                "family",
                "eligible_date",
                "expert",
                "side",
                "entry_time_utc",
                "eurusd_confirmation_displacement_pips",
            ]
        )
    return result, reasons


def _base_candidates(
    parent_cfg: dict[str, Any],
) -> pd.DataFrame:
    candidates, census = build_external_candidates(
        safe_neutral_dates(),
        load_growth_risk(parent_cfg),
        parent_cfg,
    )
    if not census["passed"]:
        raise RuntimeError("Parent external census drifted to failure")
    return candidates


def _stage_candidates(
    base: pd.DataFrame,
    parent_cfg: dict[str, Any],
    cfg: dict[str, Any],
    bounds: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int], dict[str, Any]]:
    start, end = map(pd.Timestamp, bounds)
    m5, bounded_load = load_eurusd_stage(
        parent_cfg, start, end
    )
    subset = base[
        base["entry_time_utc"].between(
            start, end, inclusive="both"
        )
    ].copy()
    candidates, reasons = add_transmission_confirmation(
        subset, m5, cfg
    )
    return candidates, m5, reasons, bounded_load


def census_summary(
    candidates: pd.DataFrame,
    cfg: dict[str, Any],
    reasons: dict[str, dict[str, int]],
) -> dict[str, Any]:
    by_window = {
        name: int(
            candidates["entry_time_utc"]
            .between(
                pd.Timestamp(bounds[0]),
                pd.Timestamp(bounds[1]),
                inclusive="both",
            )
            .sum()
        )
        for name, bounds in cfg["windows"].items()
    }
    by_side = {
        side: int(candidates["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    gate = cfg["outcome_blind_census_gate"]
    checks = {
        "total": len(candidates)
        >= int(gate["minimum_candidates_total"]),
        "development_years": all(
            by_window[name]
            >= int(gate["minimum_candidates_each_development_year"])
            for name in ("development_2022", "development_2023")
        ),
        "confirmation": by_window["confirmation_2024"]
        >= int(gate["minimum_candidates_confirmation"]),
        "forward_2025": by_window["forward_2025"]
        >= int(gate["minimum_candidates_forward_2025"]),
        "recent_half_year": by_window["recent_2026_h1"]
        >= int(gate["minimum_candidates_recent_half_year"]),
        "both_sides": all(
            by_side[side]
            >= int(gate["minimum_candidates_each_side"])
            for side in ("LONG", "SHORT")
        ),
    }
    return {
        "candidates": int(len(candidates)),
        "candidate_dates": int(candidates["eligible_date"].nunique()),
        "by_window": by_window,
        "by_side": by_side,
        "cash_reasons_by_window": reasons,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }


def build_all_census_candidates() -> tuple[
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
]:
    cfg = load_config()
    parent_cfg = load_parent_config()
    base = _base_candidates(parent_cfg)
    frames: list[pd.DataFrame] = []
    reasons: dict[str, dict[str, int]] = {}
    loads: dict[str, Any] = {}
    for name, bounds in cfg["windows"].items():
        candidates, _, stage_reasons, bounded_load = (
            _stage_candidates(
                base, parent_cfg, cfg, bounds
            )
        )
        frames.append(candidates)
        reasons[name] = stage_reasons
        loads[name] = bounded_load
    combined = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame()
    )
    return (
        census_summary(combined, cfg, reasons),
        loads,
        combined,
    )


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    verify_prereg_lock()
    census, loads, candidates = build_all_census_candidates()
    result = {
        "schema_version": (
            "eurusd_neutral_asia_growth_risk_transmission_census_v1"
        ),
        "family": FAMILY,
        "status": (
            "CENSUS_PASS_DEVELOPMENT_ALLOWED"
            if census["passed"]
            else "CENSUS_FAIL_NO_PNL_ALLOWED"
        ),
        "census": census,
        "feature_only_bounded_loads": loads,
        "trade_outcomes_loaded": False,
        "broker_action_allowed": False,
    }
    return serialize(result), candidates


def development_metrics(
    trades: pd.DataFrame,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    gate = cfg["development_gate"]
    windows = {
        name: payoff_metrics(
            trades[
                trades["entry_time_utc"].between(
                    pd.Timestamp(cfg["windows"][name][0]),
                    pd.Timestamp(cfg["windows"][name][1]),
                    inclusive="both",
                )
            ]
        )
        for name in gate["allowed_windows"]
    }
    overall = payoff_metrics(trades)
    by_side = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
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
        "combined_trades": overall["trades"]
        >= int(gate["minimum_combined_trades"]),
        "combined_win_rate_band": (
            overall["win_rate"]
            >= float(gate["minimum_combined_win_rate"])
            and overall["win_rate"]
            <= float(gate["maximum_combined_win_rate"])
        ),
        "combined_payoff_band": (
            overall["realized_payoff_ratio"]
            >= float(
                gate[
                    "minimum_combined_realized_payoff_ratio"
                ]
            )
            and overall["realized_payoff_ratio"]
            <= float(
                gate[
                    "maximum_combined_realized_payoff_ratio"
                ]
            )
        ),
        "combined_profit_factor": overall["profit_factor"]
        >= float(gate["minimum_combined_profit_factor"]),
        "combined_expectancy": overall["expectancy_r"]
        > float(gate["minimum_combined_expectancy_r"]),
        "side_capacity": all(
            block["trades"] >= int(gate["minimum_each_side_trades"])
            for block in by_side.values()
        ),
        "side_profit_factor": all(
            block["profit_factor"]
            >= float(gate["minimum_each_side_profit_factor"])
            for block in by_side.values()
        ),
        "drawdown": overall["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r"]),
    }
    return {
        "windows": windows,
        "combined": overall,
        "by_side": by_side,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }


def run_development() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_prereg_lock()
    census, _, all_candidates = build_all_census_candidates()
    if not census["passed"]:
        raise RuntimeError("N48 census failed; P&L forbidden")
    cfg = load_config()
    parent_cfg = load_parent_config()
    bounds = [
        cfg["windows"]["development_2022"][0],
        cfg["windows"]["development_2023"][1],
    ]
    m5, bounded_load = load_eurusd_stage(
        parent_cfg,
        pd.Timestamp(bounds[0]),
        pd.Timestamp(bounds[1]),
    )
    candidates = all_candidates[
        all_candidates["entry_time_utc"].between(
            pd.Timestamp(bounds[0]),
            pd.Timestamp(bounds[1]),
            inclusive="both",
        )
    ].copy()
    trades, skips = simulate(candidates, m5, parent_cfg)
    metrics = development_metrics(trades, cfg)
    status = (
        "DEVELOPMENT_PASS_2024_LOCK_REQUIRED"
        if metrics["passed"]
        else "REJECTED_IN_DEVELOPMENT_2024_2026_FORBIDDEN"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_asia_growth_risk_transmission_development_v1"
        ),
        "family": FAMILY,
        "status": status,
        "census": census,
        "development": metrics,
        "execution_skips": skips,
        "eurusd_bounded_load": bounded_load,
        "later_trade_outcomes_loaded": False,
        "broker_action_allowed": False,
    }
    return serialize(result), {
        "DEVELOPMENT_CANDIDATES": candidates,
        "DEVELOPMENT_TRADES": trades,
    }


def confirmation_metrics(
    trades: pd.DataFrame,
    gate: dict[str, Any],
) -> dict[str, Any]:
    overall = payoff_metrics(trades)
    by_side = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    checks = {
        "trades": overall["trades"] >= int(gate["minimum_trades"]),
        "win_rate_band": (
            overall["win_rate"] >= float(gate["minimum_win_rate"])
            and overall["win_rate"] <= float(gate["maximum_win_rate"])
        ),
        "payoff_band": (
            overall["realized_payoff_ratio"]
            >= float(gate["minimum_realized_payoff_ratio"])
            and overall["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
        ),
        "profit_factor": overall["profit_factor"]
        >= float(gate["minimum_profit_factor"]),
        "expectancy": overall["expectancy_r"]
        > float(gate["minimum_expectancy_r"]),
        "side_capacity": all(
            block["trades"] >= int(gate["minimum_each_side_trades"])
            for block in by_side.values()
        ),
        "side_profit_factor": all(
            block["profit_factor"]
            >= float(gate["minimum_each_side_profit_factor"])
            for block in by_side.values()
        ),
        "drawdown": overall["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r"]),
    }
    return {
        "overall": overall,
        "by_side": by_side,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }


def _load_stage_candidates(
    window: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    cfg = load_config()
    parent_cfg = load_parent_config()
    base = _base_candidates(parent_cfg)
    candidates, m5, _, bounded_load = _stage_candidates(
        base, parent_cfg, cfg, cfg["windows"][window]
    )
    return cfg, parent_cfg, candidates, m5, bounded_load


def run_confirmation() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_development_lock()
    frozen = load_config()
    cfg_name = frozen["confirmation_gate"]["allowed_window"]
    cfg, parent_cfg, candidates, m5, bounded_load = (
        _load_stage_candidates(cfg_name)
    )
    trades, skips = simulate(candidates, m5, parent_cfg)
    metrics = confirmation_metrics(
        trades, cfg["confirmation_gate"]
    )
    status = (
        "CONFIRMATION_PASS_FORWARD_LOCK_REQUIRED"
        if metrics["passed"]
        else "REJECTED_IN_CONFIRMATION_2025_2026_FORBIDDEN"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_asia_growth_risk_transmission_confirmation_v1"
        ),
        "family": FAMILY,
        "status": status,
        "stage": cfg_name,
        "confirmation": metrics,
        "execution_skips": skips,
        "eurusd_bounded_load": bounded_load,
        "later_trade_outcomes_loaded": False,
        "broker_action_allowed": False,
    }
    return serialize(result), {
        "CONFIRMATION_CANDIDATES": candidates,
        "CONFIRMATION_TRADES": trades,
    }


def final_metrics(
    trades: pd.DataFrame,
    oracle: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    gate = cfg["forward_admission"]
    windows = {
        name: payoff_metrics(
            trades[
                trades["entry_time_utc"].between(
                    pd.Timestamp(cfg["windows"][name][0]),
                    pd.Timestamp(cfg["windows"][name][1]),
                    inclusive="both",
                )
            ]
        )
        for name in ("forward_2025", "recent_2026_h1")
    }
    overall = payoff_metrics(trades)
    by_side = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    top_removed = payoff_metrics(remove_top_winners(trades))
    stressed = payoff_metrics(
        trades, value_column="extra_half_pip_stress_r"
    )
    oracle_metrics, matches = same_day_same_side_oracle_metrics(
        trades, oracle
    )
    checks = {
        "window_capacity": (
            windows["forward_2025"]["trades"]
            >= int(gate["minimum_trades_2025"])
            and windows["recent_2026_h1"]["trades"]
            >= int(gate["minimum_trades_recent_half_year"])
        ),
        "win_rate_band": (
            overall["win_rate"]
            >= float(gate["minimum_overall_win_rate"])
            and overall["win_rate"]
            <= float(gate["maximum_overall_win_rate"])
        ),
        "payoff_band": (
            overall["realized_payoff_ratio"]
            >= float(
                gate["minimum_overall_realized_payoff_ratio"]
            )
            and overall["realized_payoff_ratio"]
            <= float(
                gate["maximum_overall_realized_payoff_ratio"]
            )
        ),
        "profit_factor": overall["profit_factor"]
        >= float(gate["minimum_overall_profit_factor"]),
        "window_profit_factor": all(
            block["profit_factor"]
            >= float(gate["minimum_profit_factor_each_window"])
            for block in windows.values()
        ),
        "side_capacity": all(
            block["trades"] >= int(gate["minimum_each_side_trades"])
            for block in by_side.values()
        ),
        "side_profit_factor": all(
            block["profit_factor"]
            >= float(gate["minimum_each_side_profit_factor"])
            for block in by_side.values()
        ),
        "drawdown": overall["max_drawdown_r"]
        <= float(gate["maximum_drawdown_r"]),
        "top_removed": top_removed["profit_factor"]
        >= float(
            gate["minimum_top_5pct_removed_profit_factor"]
        ),
        "stressed": stressed["profit_factor"]
        >= float(gate["minimum_extra_half_pip_profit_factor"]),
        "oracle_precision": oracle_metrics["precision"]
        >= float(
            gate["minimum_same_day_same_side_oracle_precision"]
        ),
    }
    return {
        "overall": overall,
        "windows": windows,
        "by_side": by_side,
        "top_5_percent_winners_removed": top_removed,
        "extra_half_pip_round_trip": stressed,
        "same_day_same_side_oracle": oracle_metrics,
        "gate_results": checks,
        "passed": bool(all(checks.values())),
    }, matches


def run_forward() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    verify_confirmation_lock()
    cfg = load_config()
    parent_cfg = load_parent_config()
    base = _base_candidates(parent_cfg)
    start = pd.Timestamp(cfg["windows"]["forward_2025"][0])
    end = pd.Timestamp(cfg["windows"]["recent_2026_h1"][1])
    m5, bounded_load = load_eurusd_stage(
        parent_cfg, start, end
    )
    external = base[
        base["entry_time_utc"].between(
            start, end, inclusive="both"
        )
    ]
    candidates, _ = add_transmission_confirmation(
        external, m5, cfg
    )
    trades, skips = simulate(candidates, m5, parent_cfg)
    oracle = load_oracle_forward(cfg, start, end)
    metrics, matches = final_metrics(trades, oracle, cfg)
    status = (
        "HISTORICAL_FORWARD_PASS_PROSPECTIVE_SHADOW_REQUIRED"
        if metrics["passed"]
        else "REJECTED_IN_CHRONOLOGICAL_FORWARD_NO_RETUNING"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_asia_growth_risk_transmission_forward_v1"
        ),
        "family": FAMILY,
        "status": status,
        "forward": metrics,
        "last_six_months": metrics["windows"][
            "recent_2026_h1"
        ],
        "execution_skips": skips,
        "eurusd_bounded_load": bounded_load,
        "broker_action_allowed": False,
    }
    return serialize(result), {
        "FORWARD_CANDIDATES": candidates,
        "FORWARD_TRADES": trades,
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "CONFIRMATION_LOCK_PATH",
    "DEVELOPMENT_LOCK_PATH",
    "OUTPUT_ROOT",
    "add_transmission_confirmation",
    "build_all_census_candidates",
    "confirmation_metrics",
    "development_metrics",
    "final_metrics",
    "load_config",
    "run_census",
    "run_confirmation",
    "run_development",
    "run_forward",
    "verify_confirmation_lock",
    "verify_development_lock",
    "verify_prereg_lock",
    "write_json",
]

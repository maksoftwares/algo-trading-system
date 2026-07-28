from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config
from .neutral_binance_eurusdt_flow import load_parent_points
from .neutral_bls_release_acceleration import (
    build_release_signals,
    load_release_source,
)
from .neutral_symmetric_rsi_1p5r import (
    _effective_ask,
    _walk_exit,
    oracle_metrics,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    load_inputs,
    serialize,
    sha256_file,
)


FAMILY = "N37_NEUTRAL_BLS_FIRST_HOUR_CARRY"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_bls_first_hour_carry"
CONFIG_PATH = (
    PACKAGE_ROOT
    / "config"
    / "frozen_neutral_bls_first_hour_carry.json"
)
LOCK_PATH = (
    PACKAGE_ROOT
    / "EURUSD_NEUTRAL_BLS_FIRST_HOUR_CARRY_PREREG_2026_07_28.sha256.json"
)


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def verify_lock() -> dict[str, str]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock.get("locked_before_census_and_outcome") is not True:
        raise RuntimeError("BLS first-hour contract is not outcome-locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                f"BLS first-hour preregistration mismatch: {relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for key in (
        "parent_neutral_clock_contract",
        "data_and_classifier_contract",
    ):
        reference = cfg[key]
        if (
            sha256_file(PACKAGE_ROOT / reference["path"])
            != reference["sha256"]
        ):
            raise RuntimeError(f"{key} drift")
    parent = cfg["parent_neutral_clock_contract"]
    if (
        sha256_file(PACKAGE_ROOT / parent["paired_source_path"])
        != parent["paired_source_sha256"]
    ):
        raise RuntimeError("Parent outcome-blind paired source drift")
    source = cfg["initial_release_source"]
    if sha256_file(Path(source["path"])) != source["sha256"]:
        raise RuntimeError("BLS normalized source drift")
    if (
        sha256_file(Path(source["manifest_path"]))
        != source["manifest_sha256"]
    ):
        raise RuntimeError("BLS manifest drift")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    if manifest["raw_pdf_chain_sha256"] != source["raw_pdf_chain_sha256"]:
        raise RuntimeError("BLS raw PDF chain drift")
    oracle = cfg["oracle_source"]
    if sha256_file(PACKAGE_ROOT / oracle["path"]) != oracle["sha256"]:
        raise RuntimeError("Oracle evaluation source drift")
    return checked


def _window_name(timestamp: pd.Timestamp, cfg: dict[str, Any]) -> str:
    for name, (start, end) in cfg["windows"].items():
        if pd.Timestamp(start) <= timestamp <= pd.Timestamp(end):
            return name
    return "OUTSIDE_FROZEN_WINDOWS"


def attach_latest_release(
    points: pd.DataFrame,
    releases: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    signals, source_census = build_release_signals(releases, cfg)
    macro = signals[
        [
            "family",
            "event_time_utc",
            "initial_value",
            "previous_initial_value",
            "acceleration",
            "side",
            "source_pdf_sha256",
        ]
    ].rename(
        columns={
            "family": "macro_family",
            "event_time_utc": "macro_signal_time_utc",
            "side": "macro_side",
        }
    )
    left = points.sort_values("entry_time_utc").copy()
    right = macro.sort_values("macro_signal_time_utc").copy()
    for column in ("entry_time_utc", "macro_signal_time_utc"):
        target = left if column == "entry_time_utc" else right
        target[column] = pd.to_datetime(
            target[column], utc=True
        ).dt.as_unit("ns")
    joined = pd.merge_asof(
        left,
        right,
        left_on="entry_time_utc",
        right_on="macro_signal_time_utc",
        direction="backward",
        allow_exact_matches=False,
    )
    joined["macro_age_hours"] = (
        joined["entry_time_utc"] - joined["macro_signal_time_utc"]
    ).dt.total_seconds() / 3600.0
    maximum = float(cfg["strategy"]["maximum_release_age_hours"])
    recent = (
        joined["macro_signal_time_utc"].notna()
        & joined["macro_age_hours"].gt(
            float(
                cfg["strategy"][
                    "minimum_release_age_hours_exclusive"
                ]
            )
        )
        & joined["macro_age_hours"].le(maximum)
    )
    candidates = joined[recent].copy()
    candidates["family"] = FAMILY
    candidates["regime"] = "NEUTRAL"
    candidates["side"] = candidates["macro_side"]
    candidates["window"] = candidates["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    candidates = candidates.sort_values(
        ["entry_time_utc", "decision_id"]
    ).reset_index(drop=True)
    by_window = {
        name: int(candidates["window"].eq(name).sum())
        for name in cfg["windows"]
    }
    by_side = {
        side: int(candidates["side"].eq(side).sum())
        for side in ("LONG", "SHORT")
    }
    by_family = {
        family: int(candidates["macro_family"].eq(family).sum())
        for family in cfg["strategy"]["families"]
    }
    census = {
        **source_census,
        "neutral_clock_points": int(len(points)),
        "recent_macro_candidates": int(len(candidates)),
        "cash_no_release_within_72h": int((~recent).sum()),
        "candidate_days": int(candidates["eligible_date"].nunique()),
        "by_window": by_window,
        "by_side": by_side,
        "by_macro_family": by_family,
        "by_clock_minute": {
            str(minute): int(
                candidates["clock_minute"].eq(minute).sum()
            )
            for minute in cfg["strategy"]["entry_minutes_utc"]
        },
    }
    gate = cfg["outcome_blind_census"]
    checks = {
        "total": (
            census["recent_macro_candidates"]
            >= int(gate["minimum_candidates_total"])
        ),
        "development": (
            by_window["development_2019_2022"]
            >= int(gate["minimum_candidates_development"])
        ),
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
        "families": (
            sum(value > 0 for value in by_family.values())
            >= int(gate["minimum_families_represented"])
        ),
    }
    census["gate_results"] = checks
    census["passed"] = bool(all(checks.values()))
    return candidates, census


def execute(
    candidates: pd.DataFrame,
    eurusd: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    execution = cfg["execution"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    risk = float(execution["risk_pips"]) * PIP
    target_distance = float(execution["target_r"]) * risk
    ticket_weight = float(execution["risk_per_trade_portfolio_r"])
    hold = pd.Timedelta(
        hours=float(execution["maximum_hold_hours"])
    )
    records: list[dict[str, Any]] = []
    for _, candidate in candidates.sort_values(
        ["entry_time_utc", "decision_id"]
    ).iterrows():
        entry_time = pd.Timestamp(candidate["entry_time_utc"])
        position = int(eurusd.index.get_loc(entry_time))
        bar = eurusd.iloc[position]
        side = str(candidate["side"])
        if side == "LONG":
            entry = _effective_ask(bar, "open", spread_floor) + slippage
            stop = entry - risk
            target = entry + target_distance
        else:
            entry = float(bar["bid_open"]) - slippage
            stop = entry + risk
            target = entry - target_distance
        exit_time, exit_price, reason = _walk_exit(
            eurusd,
            position,
            entry_time + hold,
            side,
            stop,
            target,
            spread_floor,
            slippage,
        )
        signed_move = (
            exit_price - entry
            if side == "LONG"
            else entry - exit_price
        )
        outcome_r = signed_move / risk
        stressed_r = (
            outcome_r
            - float(execution["extra_round_trip_stress_pips"])
            / float(execution["risk_pips"])
        )
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "eligible_date": candidate["eligible_date"],
                "decision_id": candidate["decision_id"],
                "clock_minute": int(candidate["clock_minute"]),
                "macro_family": candidate["macro_family"],
                "macro_signal_time_utc": candidate[
                    "macro_signal_time_utc"
                ],
                "macro_age_hours": candidate["macro_age_hours"],
                "initial_value": candidate["initial_value"],
                "previous_initial_value": candidate[
                    "previous_initial_value"
                ],
                "acceleration": candidate["acceleration"],
                "side": side,
                "window": candidate["window"],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "risk_pips": float(execution["risk_pips"]),
                "r": outcome_r,
                "portfolio_r": outcome_r * ticket_weight,
                "extra_half_pip_stress_r": stressed_r,
                "extra_half_pip_stress_portfolio_r": (
                    stressed_r * ticket_weight
                ),
                "fixed_0p01_lot_usd": (
                    signed_move / PIP * 0.10
                ),
            }
        )
    return pd.DataFrame(records)


def _top_removed(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return trades
    remove = int(math.ceil(len(trades) * 0.05))
    return trades.sort_values("r").iloc[:-remove].copy()


def aggregate_days(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=["eligible_date", "entry_time_utc", "r"])
    return (
        trades.groupby("eligible_date", sort=True)
        .agg(
            entry_time_utc=("entry_time_utc", "first"),
            tickets=("decision_id", "size"),
            r=("portfolio_r", "sum"),
            extra_half_pip_stress_r=(
                "extra_half_pip_stress_portfolio_r",
                "sum",
            ),
        )
        .reset_index()
    )


def summarize(
    trades: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    overall = payoff_metrics(trades)
    windows = {
        name: payoff_metrics(trades[trades["window"].eq(name)])
        for name in cfg["windows"]
    }
    sides = {
        side: payoff_metrics(trades[trades["side"].eq(side)])
        for side in ("LONG", "SHORT")
    }
    families = {
        family: payoff_metrics(
            trades[trades["macro_family"].eq(family)]
        )
        for family in cfg["strategy"]["families"]
    }
    clocks = {
        str(minute): payoff_metrics(
            trades[trades["clock_minute"].eq(minute)]
        )
        for minute in cfg["strategy"]["entry_minutes_utc"]
    }
    daily = aggregate_days(trades)
    daily_metrics = payoff_metrics(daily)
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(_top_removed(trades))
    oracle, matches = oracle_metrics(trades)
    recent = trades[trades["window"].eq("recent_2026_h1")].copy()
    if recent.empty:
        recent_monthly: dict[str, Any] = {}
    else:
        recent["month"] = recent["entry_time_utc"].dt.strftime("%Y-%m")
        recent_monthly = {
            str(month): payoff_metrics(group)
            for month, group in recent.groupby("month", sort=True)
        }
    gate = cfg["admission"]
    checks = {
        "total_trades": (
            overall["trades"]
            >= int(gate["minimum_executed_trades_total"])
        ),
        "development_sample": (
            windows["development_2019_2022"]["trades"]
            >= int(gate["minimum_executed_trades_development"])
        ),
        "forward_samples": (
            all(
                windows[name]["trades"]
                >= int(
                    gate[
                        "minimum_executed_trades_each_full_forward_year"
                    ]
                )
                for name in (
                    "chronological_2023",
                    "chronological_2024",
                    "chronological_2025",
                )
            )
            and windows["recent_2026_h1"]["trades"]
            >= int(gate["minimum_executed_trades_recent_half_year"])
        ),
        "win_rate": (
            float(gate["minimum_overall_win_rate"])
            <= overall["win_rate"]
            <= float(gate["maximum_overall_win_rate"])
        ),
        "payoff": (
            float(gate["minimum_overall_realized_payoff_ratio"])
            <= overall["realized_payoff_ratio"]
            <= float(gate["maximum_overall_realized_payoff_ratio"])
        ),
        "overall_profit_factor": (
            overall["profit_factor"]
            >= float(gate["minimum_overall_profit_factor"])
        ),
        "every_window_profitable": all(
            value["profit_factor"]
            >= float(gate["minimum_profit_factor_each_window"])
            for value in windows.values()
        ),
        "both_sides": all(
            sides[side]["trades"]
            >= int(gate["minimum_each_side_trades"])
            and sides[side]["profit_factor"]
            >= float(gate["minimum_each_side_profit_factor"])
            for side in ("LONG", "SHORT")
        ),
        "daily_drawdown": (
            daily_metrics["max_drawdown_r"]
            <= float(gate["maximum_daily_portfolio_drawdown_r"])
        ),
        "top_winner_removal": (
            top_removed["profit_factor"]
            >= float(gate["minimum_top_5pct_removed_profit_factor"])
        ),
        "extra_half_pip": (
            stressed["profit_factor"]
            >= float(gate["minimum_extra_half_pip_profit_factor"])
        ),
        "exact_oracle_precision": (
            oracle["exact_precision"]
            >= float(gate["minimum_exact_oracle_precision"])
        ),
        "tolerant_oracle_precision": (
            oracle["same_side_15m_precision"]
            >= float(gate["minimum_15m_oracle_precision"])
        ),
    }
    return (
        {
            "overall": overall,
            "windows": windows,
            "by_side": sides,
            "by_macro_family": families,
            "by_clock_minute": clocks,
            "daily_portfolio": daily_metrics,
            "recent_2026_h1_monthly": recent_monthly,
            "top_5pct_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
            "oracle_resemblance": oracle,
            "fixed_0p01_lot_usd": {
                "net": float(trades["fixed_0p01_lot_usd"].sum()),
                "recent_2026_h1": float(
                    recent["fixed_0p01_lot_usd"].sum()
                ),
            },
            "gate_results": checks,
            "passed": bool(all(checks.values())),
        },
        matches,
    )


def _load_all() -> tuple[
    dict[str, Any],
    pd.DataFrame,
    pd.DataFrame,
    dict[str, Any],
]:
    cfg = load_config()
    eurusd, _, manifests = load_inputs(load_ensemble_config())
    releases, release_manifest = load_release_source(cfg)
    points = load_parent_points(include_outcomes=False)
    safe_columns = {
        "eligible_date",
        "clock_minute",
        "decision_id",
        "entry_time_utc",
    }
    if not safe_columns.issubset(points.columns):
        raise RuntimeError("Parent clock points missing safe columns")
    prohibited = {
        "outcome_r",
        "target_first",
        "oracle_member",
        "exit_time_utc",
    }
    if any(
        any(token in column for token in prohibited)
        for column in points.columns
    ):
        raise RuntimeError("Outcome column leaked into census clock source")
    return (
        cfg,
        eurusd,
        releases,
        {
            **manifests,
            "BLS_INITIAL_RELEASES": release_manifest,
            "NEUTRAL_CLOCK_POINTS": {
                "rows": int(len(points)),
                "paired_source_path": cfg[
                    "parent_neutral_clock_contract"
                ]["paired_source_path"],
                "paired_source_sha256": cfg[
                    "parent_neutral_clock_contract"
                ]["paired_source_sha256"],
            },
            "_points": points,
        },
    )


def run_census() -> tuple[dict[str, Any], pd.DataFrame]:
    cfg, _, releases, manifests = _load_all()
    points = manifests.pop("_points")
    candidates, census = attach_latest_release(points, releases, cfg)
    return (
        serialize(
            {
                "schema_version": (
                    "eurusd_neutral_bls_first_hour_carry_census_v1"
                ),
                "family": FAMILY,
                "status": (
                    "CENSUS_PASS_BACKTEST_ALLOWED"
                    if census["passed"]
                    else "CENSUS_FAIL_NO_PNL_ALLOWED"
                ),
                "census": census,
                "data_manifests": manifests,
            }
        ),
        candidates,
    )


def run_backtest() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    cfg, eurusd, releases, manifests = _load_all()
    points = manifests.pop("_points")
    candidates, census = attach_latest_release(points, releases, cfg)
    if not census["passed"]:
        raise RuntimeError("Outcome-blind census failed; P&L is forbidden")
    trades = execute(candidates, eurusd, cfg)
    summary, matches = summarize(trades, cfg)
    status = (
        "QUALIFIED_NEUTRAL_RESEARCH_CANDIDATE_FORWARD_REQUIRED"
        if summary["passed"]
        else "REJECTED_NEUTRAL_BLS_FIRST_HOUR_CARRY_V1"
    )
    result = {
        "schema_version": (
            "eurusd_neutral_bls_first_hour_carry_result_v1"
        ),
        "family": FAMILY,
        "status": status,
        "demo_ready": False,
        "live_ready": False,
        "information_status": cfg["information_status"],
        "research_boundary": (
            "All archived windows are adaptive historical development data. "
            "Chronological labels do not make them pristine holdouts."
        ),
        "mechanism": (
            "Most recent directional BLS initial-release acceleration "
            "within 72 hours, carried to the Neutral oracle's fixed "
            "first-hour decision clocks."
        ),
        "census": census,
        "summary": summary,
        "data_manifests": manifests,
        "decision_policy": cfg["decision_policy"],
    }
    return (
        serialize(result),
        {
            "CANDIDATES": candidates,
            "TRADES": trades,
            "DAILY_PORTFOLIO": aggregate_days(trades),
            "ORACLE_MATCHES_15M": matches,
        },
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serialize(payload), indent=2) + "\n",
        encoding="utf-8",
    )


__all__ = [
    "OUTPUT_ROOT",
    "aggregate_days",
    "attach_latest_release",
    "execute",
    "load_config",
    "run_backtest",
    "run_census",
    "summarize",
    "verify_lock",
    "write_json",
]

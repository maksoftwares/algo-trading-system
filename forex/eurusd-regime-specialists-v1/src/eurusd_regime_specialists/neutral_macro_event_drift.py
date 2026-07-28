from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_binance_eurusdt_flow import (
    _direction_metrics,
    _period,
    load_parent_points,
)
from .neutral_four_clock_ranker import route_predictions
from .neutral_midnight_pairs import (
    aggregate_days,
    oracle_match_metrics,
    write_json,
)
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N28_NEUTRAL_MACRO_EVENT_DRIFT"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_macro_event_drift"
BRANCHES = ("MOMENTUM", "REVERSAL")


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_macro_event_drift.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_MACRO_EVENT_DRIFT_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_macro_event_drift_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral macro-event contract is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral macro-event preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_four_clock_contract"]
    if sha256_file(PACKAGE_ROOT / parent["path"]) != parent["sha256"]:
        raise RuntimeError("Parent four-clock contract drift")
    source = cfg["event_source"]
    if sha256_file(Path(source["path"])) != source["sha256"]:
        raise RuntimeError("Dukascopy event source drift")
    if (
        sha256_file(Path(source["manifest_path"]))
        != source["manifest_sha256"]
    ):
        raise RuntimeError("Dukascopy event manifest drift")
    manifest = json.loads(
        Path(source["manifest_path"]).read_text(encoding="utf-8")
    )
    if (
        manifest["raw_response_chain_sha256"]
        != source["raw_response_chain_sha256"]
    ):
        raise RuntimeError("Dukascopy raw response chain drift")
    if cfg["outcome_blind_census"] is None:
        raise RuntimeError("Macro-event outcome-blind census is not frozen")
    return checked


def load_event_source(cfg: dict[str, Any]) -> pd.DataFrame:
    frame = pd.read_parquet(Path(cfg["event_source"]["path"]))
    frame["event_time_utc"] = pd.to_datetime(
        frame["event_time_utc"], utc=True
    )
    return frame.sort_values(
        ["event_time_utc", "event_id"]
    ).reset_index(drop=True)


def qualifying_events(
    source: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    allowed = set(cfg["event_filter"]["currencies"])
    fragments = cfg["event_filter"][
        "case_insensitive_title_fragments"
    ]
    pieces: list[pd.DataFrame] = []
    for currency in sorted(allowed):
        pattern = "|".join(
            re.escape(value) for value in fragments[currency]
        )
        subset = source[source["currency"].eq(currency)].copy()
        title = subset["title"].fillna("").astype(str)
        subset = subset[
            title.str.contains(pattern, case=False, regex=True)
        ]
        pieces.append(subset)
    result = pd.concat(pieces, ignore_index=True)
    prohibited = set(cfg["event_source"]["prohibited_strategy_fields"])
    if prohibited.intersection(
        {
            "event_id",
            "event_time_utc",
            "currency",
            "title",
            "tag",
        }
    ):
        raise RuntimeError("A required event field is prohibited")
    return result.sort_values(
        ["event_time_utc", "event_id"]
    ).reset_index(drop=True)


def _window_name(
    timestamp: pd.Timestamp,
    cfg: dict[str, Any],
) -> str:
    for name, (start_raw, end_raw) in cfg["windows"].items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def _expected_pre_event_bar(
    timestamp: pd.Timestamp,
) -> pd.Timestamp:
    return timestamp.floor("5min") - pd.Timedelta(minutes=5)


def _mid_close(m5: pd.DataFrame, timestamp: pd.Timestamp) -> float:
    bar = m5.loc[timestamp]
    return 0.5 * (
        float(bar["bid_close"]) + float(bar["ask_close"])
    )


def _distribution(
    candidate_dates: set[str],
    source_dates: list[str],
) -> dict[str, int]:
    return {
        "0": len(set(source_dates) - candidate_dates),
        "1": len(candidate_dates),
    }


def _census_block(
    parent: pd.DataFrame,
    decisions: pd.DataFrame,
) -> dict[str, Any]:
    source_dates = sorted(parent["eligible_date"].astype(str).unique())
    candidate_dates = set(
        decisions["eligible_date"].astype(str).unique()
    )
    candidates = int(len(decisions))
    active = int(len(candidate_dates))
    source_days = int(len(source_dates))
    return {
        "source_eligible_days": source_days,
        "source_decision_points": int(len(parent)),
        "event_candidates": candidates,
        "active_candidate_days": active,
        "no_trade_days": source_days - active,
        "momentum_long_rate": (
            float(decisions["momentum_side"].eq("LONG").mean())
            if candidates
            else 0.0
        ),
        "reversal_long_rate": (
            float(decisions["reversal_side"].eq("LONG").mean())
            if candidates
            else 0.0
        ),
        "trades_per_source_eligible_day": (
            candidates / source_days if source_days else 0.0
        ),
        "trades_per_active_candidate_day": (
            candidates / active if active else 0.0
        ),
        "candidate_count_distribution": _distribution(
            candidate_dates, source_dates
        ),
    }


def build_event_decisions(
    parent: pd.DataFrame,
    m5: pd.DataFrame,
    events: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    points = parent[parent["clock_minute"].eq(0)].copy()
    points["window"] = points["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    points = points[points["window"].ne("OUTSIDE")].sort_values(
        "entry_time_utc"
    )
    lookback = pd.Timedelta(
        hours=int(cfg["strategy"]["lookback_hours"])
    )
    event_times = events["event_time_utc"]
    records: list[dict[str, Any]] = []
    missing_pre_event_bar = 0
    missing_pre_entry_bar = 0
    zero_impulses = 0
    no_event = 0
    for _, point in points.iterrows():
        entry = pd.Timestamp(point["entry_time_utc"])
        eligible = events[
            event_times.ge(entry - lookback) & event_times.lt(entry)
        ]
        if eligible.empty:
            no_event += 1
            continue
        latest_time = eligible["event_time_utc"].max()
        cluster = eligible[
            eligible["event_time_utc"].eq(latest_time)
        ].sort_values("event_id")
        pre_event_bar = _expected_pre_event_bar(latest_time)
        pre_entry_bar = entry - pd.Timedelta(minutes=5)
        if pre_event_bar not in m5.index:
            missing_pre_event_bar += 1
            continue
        if pre_entry_bar not in m5.index:
            missing_pre_entry_bar += 1
            continue
        start_price = _mid_close(m5, pre_event_bar)
        end_price = _mid_close(m5, pre_entry_bar)
        impulse_pips = (end_price - start_price) / PIP
        if impulse_pips == 0.0:
            zero_impulses += 1
            continue
        momentum = "LONG" if impulse_pips > 0.0 else "SHORT"
        reversal = "SHORT" if momentum == "LONG" else "LONG"
        row = point.to_dict()
        row.update(
            {
                "event_time_utc": latest_time,
                "event_age_minutes": (
                    entry - latest_time
                ).total_seconds()
                / 60.0,
                "event_cluster_size": int(len(cluster)),
                "event_currencies": "|".join(
                    sorted(cluster["currency"].astype(str).unique())
                ),
                "event_ids": "|".join(
                    cluster["event_id"].astype(str)
                ),
                "event_tags": "|".join(
                    cluster["tag"].fillna("").astype(str)
                ),
                "event_titles": " | ".join(
                    cluster["title"].fillna("").astype(str)
                ),
                "pre_event_bar_time_utc": pre_event_bar,
                "pre_entry_bar_time_utc": pre_entry_bar,
                "pre_event_mid_close": start_price,
                "pre_entry_mid_close": end_price,
                "event_to_entry_impulse_pips": impulse_pips,
                "momentum_side": momentum,
                "reversal_side": reversal,
            }
        )
        records.append(row)
    if records:
        decisions = pd.DataFrame(records)
        decisions = decisions.sort_values(
            "entry_time_utc"
        ).reset_index(drop=True)
    else:
        decisions = pd.DataFrame(
            columns=[
                *points.columns,
                "event_time_utc",
                "event_age_minutes",
                "event_cluster_size",
                "event_currencies",
                "event_ids",
                "event_tags",
                "event_titles",
                "pre_event_bar_time_utc",
                "pre_entry_bar_time_utc",
                "pre_event_mid_close",
                "pre_entry_mid_close",
                "event_to_entry_impulse_pips",
                "momentum_side",
                "reversal_side",
            ]
        )

    by_window: dict[str, Any] = {}
    for name in cfg["windows"]:
        by_window[name] = _census_block(
            points[points["window"].eq(name)],
            decisions[decisions["window"].eq(name)],
        )
    census = {
        **_census_block(points, decisions),
        "qualifying_event_rows": int(len(events)),
        "qualifying_event_clusters": int(
            events["event_time_utc"].nunique()
        ),
        "parent_points_without_event_in_prior_24h": no_event,
        "missing_pre_event_completed_bar": missing_pre_event_bar,
        "missing_pre_entry_completed_bar": missing_pre_entry_bar,
        "zero_impulse_cash_points": zero_impulses,
        "event_currency_clusters": (
            {
                str(key): int(value)
                for key, value in decisions[
                    "event_currencies"
                ].value_counts().items()
            }
            if not decisions.empty
            else {}
        ),
        "event_age_minutes": (
            {
                "minimum": float(decisions["event_age_minutes"].min()),
                "median": float(decisions["event_age_minutes"].median()),
                "maximum": float(decisions["event_age_minutes"].max()),
            }
            if not decisions.empty
            else {"minimum": None, "median": None, "maximum": None}
        ),
        "by_window": by_window,
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Macro-event outcome-blind census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return decisions, census


def execute_branch(
    decisions: pd.DataFrame,
    branch: str,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if branch not in BRANCHES:
        raise ValueError(f"Unknown macro-event branch {branch!r}")
    side_column = f"{branch.lower()}_side"
    probabilities = np.where(
        decisions[side_column].eq("LONG"), 1.0, 0.0
    )
    trades, predictions = route_predictions(
        decisions, probabilities, cfg
    )
    trades["family"] = FAMILY
    predictions["family"] = FAMILY
    trades["selected_branch"] = branch
    predictions["selected_branch"] = branch
    metadata = [
        "event_time_utc",
        "event_age_minutes",
        "event_cluster_size",
        "event_currencies",
        "event_ids",
        "event_tags",
        "event_titles",
        "pre_event_bar_time_utc",
        "pre_entry_bar_time_utc",
        "pre_event_mid_close",
        "pre_entry_mid_close",
        "event_to_entry_impulse_pips",
        "momentum_side",
        "reversal_side",
    ]
    for column in metadata:
        trades[column] = decisions[column].to_numpy()
        predictions[column] = decisions[column].to_numpy()
    return trades, predictions


def _selection_metrics(
    decisions: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, pd.DataFrame]]:
    start, end = map(
        pd.Timestamp, cfg["branch_selection"]["window"]
    )
    development = _period(decisions, start, end)
    metrics: dict[str, Any] = {}
    ledgers: dict[str, pd.DataFrame] = {}
    for branch in BRANCHES:
        trades, _ = execute_branch(development, branch, cfg)
        ledgers[branch] = trades
        metrics[branch] = payoff_metrics(trades)
    ranking = sorted(
        BRANCHES,
        key=lambda branch: (
            metrics[branch]["profit_factor"],
            metrics[branch]["net_r"],
            branch == cfg["branch_selection"][
                "deterministic_tie_break"
            ],
        ),
        reverse=True,
    )
    return ranking[0], metrics, ledgers


def _window_metrics(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
    m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    selected_trades = _period(trades, start, end)
    selected_predictions = _period(predictions, start, end)
    daily = aggregate_days(selected_trades)
    active_days = active_weekday_fx_days(m5, start, end)
    return {
        "tickets": payoff_metrics(selected_trades),
        "daily_portfolio": payoff_metrics(daily),
        "direction_selection": _direction_metrics(
            selected_predictions
        ),
        "active_weekdays": active_days,
        "executed_neutral_days": int(
            selected_trades["eligible_date"].nunique()
        ),
        "trades_per_active_weekday": (
            len(selected_trades) / active_days
            if active_days
            else 0.0
        ),
    }


def _oracle_evaluation(
    trades: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    oracle = pd.read_csv(PACKAGE_ROOT / cfg["oracle_source"])
    for column in ("entry_time_utc", "exit_time_utc"):
        oracle[column] = pd.to_datetime(oracle[column], utc=True)
    oracle = oracle[oracle["regime"].eq(cfg["oracle_regime"])]
    tolerance = int(
        cfg["oracle_matching"]["secondary_tolerance_minutes"]
    )
    forward_bounds = [
        cfg["windows"][name] for name in cfg["forward_windows"]
    ]
    start = min(pd.Timestamp(bounds[0]) for bounds in forward_bounds)
    end = max(pd.Timestamp(bounds[1]) for bounds in forward_bounds)
    overall, matches = oracle_match_metrics(
        trades, oracle, start, end, tolerance
    )
    windows = {}
    for name in cfg["forward_windows"]:
        lower, upper = map(pd.Timestamp, cfg["windows"][name])
        windows[name], _ = oracle_match_metrics(
            trades, oracle, lower, upper, tolerance
        )
    return {"overall": overall, "windows": windows}, matches


def summarize(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
    selected_branch: str,
    development_metrics: dict[str, Any],
    oracle: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool]]:
    windows = {
        name: _window_metrics(
            trades,
            predictions,
            m5,
            pd.Timestamp(bounds[0]),
            pd.Timestamp(bounds[1]),
        )
        for name, bounds in cfg["windows"].items()
    }
    forward_start = min(
        pd.Timestamp(cfg["windows"][name][0])
        for name in cfg["forward_windows"]
    )
    forward_end = max(
        pd.Timestamp(cfg["windows"][name][1])
        for name in cfg["forward_windows"]
    )
    forward = _period(trades, forward_start, forward_end)
    forward_predictions = _period(
        predictions, forward_start, forward_end
    )
    forward_daily = aggregate_days(forward)
    stressed = payoff_metrics(
        forward, "extra_half_pip_stress_r"
    )
    top_removed = payoff_metrics(remove_top_winners(forward))
    recent_start, recent_end = map(
        pd.Timestamp, cfg["recent_six_months"]
    )
    recent = _period(trades, recent_start, recent_end)
    recent_predictions = _period(
        predictions, recent_start, recent_end
    )
    recent_daily = aggregate_days(recent)
    gate = cfg["admission"]
    selection = development_metrics[selected_branch]
    selection_pass = (
        selection["trades"]
        >= int(gate["minimum_development_trades"])
        and selection["net_r"] > 0.0
        and selection["profit_factor"]
        > float(
            cfg["branch_selection"][
                "selection_pass_requires_profit_factor_exclusive"
            ]
        )
    )
    forward_window_checks = {}
    for name in cfg["forward_windows"]:
        tickets = windows[name]["tickets"]
        daily = windows[name]["daily_portfolio"]
        forward_window_checks[name] = (
            tickets["trades"]
            >= int(gate["minimum_forward_trades_each_window"])
            and float(gate["minimum_forward_win_rate_each_window"])
            <= tickets["win_rate"]
            <= float(gate["maximum_forward_win_rate_each_window"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= tickets["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and tickets["profit_factor"]
            > float(
                gate[
                    "minimum_forward_profit_factor_each_window_exclusive"
                ]
            )
            and tickets["net_r"] > 0.0
            and daily["profit_factor"]
            > float(
                gate[
                    "minimum_forward_daily_profit_factor_each_window_exclusive"
                ]
            )
        )
    forward_metrics = payoff_metrics(forward)
    forward_daily_metrics = payoff_metrics(forward_daily)
    oracle_overall = oracle["overall"]
    checks = {
        "development_branch_selection": selection_pass,
        "every_forward_window": all(forward_window_checks.values()),
        "forward_overall_profit_factor": (
            forward_metrics["profit_factor"]
            >= float(gate["minimum_forward_overall_profit_factor"])
        ),
        "forward_overall_win_rate": (
            float(gate["minimum_forward_overall_win_rate"])
            <= forward_metrics["win_rate"]
            <= float(gate["maximum_forward_overall_win_rate"])
        ),
        "stressed": (
            stressed["net_r"] > 0.0
            and stressed["profit_factor"]
            > float(gate["minimum_stressed_profit_factor_exclusive"])
        ),
        "top_winners_removed": top_removed["net_r"] > 0.0,
        "daily_drawdown": (
            forward_daily_metrics["max_drawdown_r"]
            <= float(gate["maximum_daily_portfolio_drawdown_r"])
        ),
        "recent_six_months": (
            len(recent)
            >= int(gate["minimum_recent_six_month_trades"])
            and payoff_metrics(recent)["net_r"] > 0.0
            and payoff_metrics(recent)["profit_factor"]
            > float(
                gate[
                    "minimum_recent_six_month_profit_factor_exclusive"
                ]
            )
            and payoff_metrics(recent_daily)["profit_factor"] > 1.0
        ),
        "oracle_exact_precision": (
            oracle_overall["exact_precision"]
            >= float(gate["minimum_overall_exact_oracle_precision"])
        ),
        "oracle_15m_precision": (
            oracle_overall["tolerant_precision"]
            >= float(gate["minimum_overall_15m_oracle_precision"])
        ),
        "frequency_not_a_gate": (
            gate["exact_daily_frequency_gate"] is False
        ),
    }
    recent_active = active_weekday_fx_days(
        m5, recent_start, recent_end
    )
    strategy = {
        "selected_branch": selected_branch,
        "development_branch_metrics": development_metrics,
        "development_selection_pass": selection_pass,
        "forward_window_checks": forward_window_checks,
        "windows": windows,
        "forward_only": {
            "tickets": forward_metrics,
            "daily_portfolio": forward_daily_metrics,
            "direction_selection": _direction_metrics(
                forward_predictions
            ),
            "robustness": {
                "top_5_percent_winners_removed": top_removed,
                "extra_half_pip_round_trip": stressed,
            },
        },
        "frequency": {
            "source_eligible_days": census["source_eligible_days"],
            "executed_days": census["active_candidate_days"],
            "cash_only_days": census["no_trade_days"],
            "trades": census["event_candidates"],
            "trades_per_source_eligible_day": census[
                "trades_per_source_eligible_day"
            ],
            "frequency_gate": False,
        },
        "recent_six_months": {
            "tickets": payoff_metrics(recent),
            "daily_portfolio": payoff_metrics(recent_daily),
            "direction_selection": _direction_metrics(
                recent_predictions
            ),
            "active_weekdays": recent_active,
            "executed_neutral_days": int(
                recent["eligible_date"].nunique()
            ),
            "trades_per_active_weekday": (
                len(recent) / recent_active if recent_active else 0.0
            ),
        },
    }
    return strategy, checks


def run_census() -> dict[str, Any]:
    cfg = load_config()
    parent = load_parent_points(include_outcomes=False)
    base = load_ensemble_config()
    m5, _, _ = load_inputs(base)
    events = qualifying_events(load_event_source(cfg), cfg)
    _, census = build_event_decisions(
        parent,
        m5,
        events,
        cfg,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_macro_event_drift() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_points(include_outcomes=True)
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    events = qualifying_events(load_event_source(cfg), cfg)
    decisions, census = build_event_decisions(
        parent,
        m5,
        events,
        cfg,
        enforce_frozen_census=True,
    )
    selected, development_metrics, development_ledgers = (
        _selection_metrics(decisions, cfg)
    )
    trades, predictions = execute_branch(decisions, selected, cfg)
    oracle, matches = _oracle_evaluation(trades, cfg)
    strategy, checks = summarize(
        trades,
        predictions,
        m5,
        cfg,
        census,
        selected,
        development_metrics,
        oracle,
    )
    admitted = all(checks.values())
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    prospective = decisions[
        decisions["entry_time_utc"] >= prospective_start
    ]
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_MACRO_EVENT_DRIFT_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "event_source": cfg["event_source"],
        "causality": {
            "event_fields_used": (
                "timestamp, currency, title, tag only"
            ),
            "event_numeric_fields_used": False,
            "direction": (
                "selected once between fixed event-to-entry momentum "
                "and reversal branches on 2019-2022 only"
            ),
            "event_to_entry_impulse_uses_only_completed_m5_bars": True,
            "impulse_magnitude_threshold": None,
            "future_information_in_signal": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "outcome_blind_census": census,
        "strategy": {
            "admitted": admitted,
            "admission_checks": checks,
            **strategy,
        },
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": cfg["prospective"]["start_utc"],
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": int(len(prospective)),
            "status": (
                "WAITING_FOR_POST_LOCK_MARKET_DATA"
                if prospective.empty
                else "POST_LOCK_POINTS_AVAILABLE"
            ),
        },
        "verdict": (
            "The frozen event-timing rule passed every historical gate; "
            "only post-lock observations may confirm it."
            if admitted
            else "The frozen event-timing rule failed one or more gates "
            "and is closed without repair."
        ),
    }
    artifacts = {
        "QUALIFYING_EVENTS": events,
        "DECISIONS": decisions,
        "PREDICTIONS": predictions,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "ORACLE_MATCHES": matches,
    }
    for branch, frame in development_ledgers.items():
        artifacts[f"DEVELOPMENT_{branch}_TRADES"] = frame
    return result, artifacts


__all__ = [
    "BRANCHES",
    "FAMILY",
    "OUTPUT_ROOT",
    "build_event_decisions",
    "execute_branch",
    "load_config",
    "load_event_source",
    "qualifying_events",
    "run_census",
    "run_neutral_macro_event_drift",
    "verify_lock",
    "write_json",
]

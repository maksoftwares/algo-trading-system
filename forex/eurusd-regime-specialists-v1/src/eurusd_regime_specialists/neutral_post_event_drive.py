from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_binance_eurusdt_flow import _period, load_parent_points
from .neutral_macro_event_drift import (
    load_config as load_event_config,
    load_event_source,
    qualifying_events,
)
from .neutral_midnight_pairs import (
    aggregate_days,
    oracle_match_metrics,
    write_json,
)
from .neutral_session_oco import _effective_ask, _walk_exit
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    is_quarantined,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N29_NEUTRAL_POST_EVENT_DRIVE"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_post_event_drive"
BRANCHES = ("MOMENTUM", "REVERSAL")


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_post_event_drive.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_POST_EVENT_DRIVE_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_post_event_drive_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral post-event drive is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral post-event preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_event_clock_contract"]
    if sha256_file(PACKAGE_ROOT / parent["path"]) != parent["sha256"]:
        raise RuntimeError("Parent event-clock contract drift")
    if (
        sha256_file(PACKAGE_ROOT / parent["lock_path"])
        != parent["lock_sha256"]
    ):
        raise RuntimeError("Parent event-clock lock drift")
    if cfg["outcome_blind_census"] is None:
        raise RuntimeError("Post-event outcome-blind census is not frozen")
    return checked


def _window_name(
    timestamp: pd.Timestamp,
    cfg: dict[str, Any],
) -> str:
    for name, (start_raw, end_raw) in cfg["windows"].items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def _mid_open(frame: pd.DataFrame) -> float:
    first = frame.iloc[0]
    return 0.5 * (
        float(first["bid_open"]) + float(first["ask_open"])
    )


def _mid_close(frame: pd.DataFrame) -> float:
    last = frame.iloc[-1]
    return 0.5 * (
        float(last["bid_close"]) + float(last["ask_close"])
    )


def _candidate_block(
    points: pd.DataFrame,
    candidates: pd.DataFrame,
) -> dict[str, Any]:
    source_days = int(points["eligible_date"].nunique())
    active = int(candidates["eligible_date"].nunique())
    trades = int(len(candidates))
    return {
        "source_eligible_days": source_days,
        "event_candidates": trades,
        "active_candidate_days": active,
        "no_trade_days": source_days - active,
        "momentum_long_rate": (
            float(candidates["momentum_side"].eq("LONG").mean())
            if trades
            else 0.0
        ),
        "reversal_long_rate": (
            float(candidates["reversal_side"].eq("LONG").mean())
            if trades
            else 0.0
        ),
        "trades_per_source_eligible_day": (
            trades / source_days if source_days else 0.0
        ),
        "trades_per_active_candidate_day": (
            trades / active if active else 0.0
        ),
        "candidate_count_distribution": {
            "0": source_days - active,
            "1": active,
        },
    }


def build_candidates(
    parent: pd.DataFrame,
    m5: pd.DataFrame,
    events: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    points = parent[parent["clock_minute"].eq(0)].copy()
    points["neutral_date"] = points["eligible_date"].astype(str)
    points["window"] = points["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    points = points[points["window"].ne("OUTSIDE")].copy()
    neutral_dates = set(points["neutral_date"])
    event_frame = events.copy()
    event_frame["event_date"] = event_frame[
        "event_time_utc"
    ].dt.strftime("%Y-%m-%d")
    event_frame = event_frame[
        event_frame["event_date"].isin(neutral_dates)
    ]
    latest_times = (
        event_frame.groupby("event_date")["event_time_utc"].max().to_dict()
    )
    execution = cfg["execution"]
    risk_cfg = cfg["structure_risk"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    stop_buffer = float(risk_cfg["stop_buffer_pips"]) * PIP
    risk_floor_pips = float(risk_cfg["minimum_risk_pips"])
    risk_ceiling_pips = float(risk_cfg["maximum_risk_pips"])
    observation_bars = int(cfg["strategy"]["observation_bars"])
    base = load_ensemble_config()
    records: list[dict[str, Any]] = []
    reasons = {
        "no_qualifying_event_on_neutral_date": 0,
        "observation_or_entry_bar_missing": 0,
        "entry_crosses_utc_date": 0,
        "quarantine": 0,
        "zero_impulse": 0,
        "risk_ceiling": 0,
    }
    for _, point in points.sort_values("entry_time_utc").iterrows():
        date = str(point["neutral_date"])
        if date not in latest_times:
            reasons["no_qualifying_event_on_neutral_date"] += 1
            continue
        event_time = latest_times[date]
        cluster = event_frame[
            event_frame["event_time_utc"].eq(event_time)
        ].sort_values("event_id")
        observation_start = event_time.ceil("5min")
        entry_time = observation_start + pd.Timedelta(
            minutes=int(cfg["strategy"]["observation_minutes"])
        )
        if entry_time.strftime("%Y-%m-%d") != date:
            reasons["entry_crosses_utc_date"] += 1
            continue
        expected = pd.date_range(
            observation_start,
            periods=observation_bars,
            freq="5min",
        )
        if (
            any(timestamp not in m5.index for timestamp in expected)
            or entry_time not in m5.index
        ):
            reasons["observation_or_entry_bar_missing"] += 1
            continue
        if is_quarantined(
            entry_time, "EURUSD", base["quarantine"]
        ):
            reasons["quarantine"] += 1
            continue
        observation = m5.loc[expected]
        impulse_pips = (
            _mid_close(observation) - _mid_open(observation)
        ) / PIP
        if impulse_pips == 0.0:
            reasons["zero_impulse"] += 1
            continue
        position = int(m5.index.get_loc(entry_time))
        entry_bar = m5.iloc[position]
        long_entry = (
            _effective_ask(entry_bar, "open", spread_floor) + slippage
        )
        short_entry = float(entry_bar["bid_open"]) - slippage
        long_structure_stop = (
            float(observation["bid_low"].min()) - stop_buffer
        )
        short_structure_stop = (
            max(
                _effective_ask(bar, "high", spread_floor)
                for _, bar in observation.iterrows()
            )
            + stop_buffer
        )
        long_risk_pips = max(
            (long_entry - long_structure_stop) / PIP,
            risk_floor_pips,
        )
        short_risk_pips = max(
            (short_structure_stop - short_entry) / PIP,
            risk_floor_pips,
        )
        long_risk = long_risk_pips * PIP
        short_risk = short_risk_pips * PIP
        long_stop = long_entry - long_risk
        short_stop = short_entry + short_risk
        if (
            long_risk_pips > risk_ceiling_pips
            or short_risk_pips > risk_ceiling_pips
        ):
            reasons["risk_ceiling"] += 1
            continue
        momentum = "LONG" if impulse_pips > 0 else "SHORT"
        reversal = "SHORT" if momentum == "LONG" else "LONG"
        target_r = float(execution["target_r"])
        row = point.to_dict()
        row.update(
            {
                "pair_id": f"{date}:EVENT",
                "event_time_utc": event_time,
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
                "observation_start_utc": observation_start,
                "observation_end_utc": entry_time,
                "entry_time_utc": entry_time,
                "entry_position": position,
                "impulse_pips": impulse_pips,
                "observation_range_pips": (
                    float(observation["ask_high"].max())
                    - float(observation["bid_low"].min())
                )
                / PIP,
                "momentum_side": momentum,
                "reversal_side": reversal,
                "entry_price_long": long_entry,
                "stop_price_long": long_stop,
                "target_price_long": long_entry
                + target_r * long_risk,
                "risk_distance_long": long_risk,
                "risk_pips_long": long_risk_pips,
                "entry_price_short": short_entry,
                "stop_price_short": short_stop,
                "target_price_short": short_entry
                - target_r * short_risk,
                "risk_distance_short": short_risk,
                "risk_pips_short": short_risk_pips,
            }
        )
        row["window"] = _window_name(entry_time, cfg)
        records.append(row)
    candidates = pd.DataFrame(records)
    if not candidates.empty:
        candidates = candidates.sort_values(
            "entry_time_utc"
        ).reset_index(drop=True)
    else:
        candidates = pd.DataFrame(
            columns=[
                *points.columns,
                "momentum_side",
                "reversal_side",
                "entry_time_utc",
            ]
        )
    by_window = {}
    for name in cfg["windows"]:
        by_window[name] = _candidate_block(
            points[points["window"].eq(name)],
            candidates[candidates["window"].eq(name)],
        )
    census = {
        **_candidate_block(points, candidates),
        "neutral_dates_with_qualifying_events": int(
            len(latest_times)
        ),
        "cash_reasons": reasons,
        "risk_pips": (
            {
                "long_minimum": float(
                    candidates["risk_pips_long"].min()
                ),
                "long_median": float(
                    candidates["risk_pips_long"].median()
                ),
                "long_maximum": float(
                    candidates["risk_pips_long"].max()
                ),
                "short_minimum": float(
                    candidates["risk_pips_short"].min()
                ),
                "short_median": float(
                    candidates["risk_pips_short"].median()
                ),
                "short_maximum": float(
                    candidates["risk_pips_short"].max()
                ),
            }
            if not candidates.empty
            else {}
        ),
        "event_currency_clusters": (
            {
                str(key): int(value)
                for key, value in candidates[
                    "event_currencies"
                ].value_counts().items()
            }
            if not candidates.empty
            else {}
        ),
        "by_window": by_window,
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Post-event outcome-blind census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return candidates, census


def execute_branch(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    branch: str,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if branch not in BRANCHES:
        raise ValueError(f"Unknown post-event branch {branch!r}")
    execution = cfg["execution"]
    spread_floor = (
        float(execution["minimum_retail_spread_pips"]) * PIP
    )
    slippage = (
        float(execution["extra_slippage_pips_per_side"]) * PIP
    )
    hold = pd.Timedelta(
        hours=float(execution["maximum_hold_hours"])
    )
    ticket_weight = float(
        execution["risk_per_trade_portfolio_r"]
    )
    records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    open_until: pd.Timestamp | None = None
    for _, candidate in candidates.iterrows():
        entry_time = pd.Timestamp(candidate["entry_time_utc"])
        if open_until is not None and entry_time <= open_until:
            diagnostics.append(
                {
                    "pair_id": candidate["pair_id"],
                    "entry_time_utc": entry_time,
                    "branch": branch,
                    "status": "SKIP_POSITION_OPEN",
                }
            )
            continue
        side = str(candidate[f"{branch.lower()}_side"])
        suffix = side.lower()
        entry = float(candidate[f"entry_price_{suffix}"])
        stop = float(candidate[f"stop_price_{suffix}"])
        target = float(candidate[f"target_price_{suffix}"])
        risk = float(candidate[f"risk_distance_{suffix}"])
        exit_time, exit_price, reason = _walk_exit(
            m5,
            int(candidate["entry_position"]),
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
        stressed_r = result_r - 0.5 * PIP / risk
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "eligible_date": candidate["eligible_date"],
                "pair_id": candidate["pair_id"],
                "trade_id": f"{candidate['pair_id']}:{side}",
                "selected_branch": branch,
                "side": side,
                "event_time_utc": candidate["event_time_utc"],
                "event_cluster_size": candidate["event_cluster_size"],
                "event_currencies": candidate["event_currencies"],
                "event_ids": candidate["event_ids"],
                "event_tags": candidate["event_tags"],
                "event_titles": candidate["event_titles"],
                "observation_start_utc": candidate[
                    "observation_start_utc"
                ],
                "observation_end_utc": candidate[
                    "observation_end_utc"
                ],
                "impulse_pips": candidate["impulse_pips"],
                "observation_range_pips": candidate[
                    "observation_range_pips"
                ],
                "entry_time_utc": entry_time,
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "risk_pips": risk / PIP,
                "r": result_r,
                "portfolio_r": result_r * ticket_weight,
                "extra_half_pip_stress_r": stressed_r,
                "extra_half_pip_stress_portfolio_r": (
                    stressed_r * ticket_weight
                ),
                "fixed_0p01_lot_usd": pnl * 1000.0,
            }
        )
        diagnostics.append(
            {
                "pair_id": candidate["pair_id"],
                "entry_time_utc": entry_time,
                "branch": branch,
                "side": side,
                "status": "EXECUTED",
                "exit_time_utc": exit_time,
                "exit_reason": reason,
            }
        )
        open_until = exit_time
    return pd.DataFrame(records), pd.DataFrame(diagnostics)


def _selection(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[str, dict[str, Any], dict[str, pd.DataFrame]]:
    start, end = map(
        pd.Timestamp, cfg["branch_selection"]["window"]
    )
    development = _period(candidates, start, end)
    metrics: dict[str, Any] = {}
    ledgers: dict[str, pd.DataFrame] = {}
    for branch in BRANCHES:
        trades, _ = execute_branch(
            development, m5, branch, cfg
        )
        ledgers[branch] = trades
        metrics[branch] = payoff_metrics(trades)
    tie = cfg["branch_selection"]["deterministic_tie_break"]
    selected = max(
        BRANCHES,
        key=lambda branch: (
            metrics[branch]["profit_factor"],
            metrics[branch]["net_r"],
            branch == tie,
        ),
    )
    return selected, metrics, ledgers


def _window_metrics(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    subset = _period(trades, start, end)
    daily = aggregate_days(subset)
    active = active_weekday_fx_days(m5, start, end)
    return {
        "tickets": payoff_metrics(subset),
        "daily_portfolio": payoff_metrics(daily),
        "active_weekdays": active,
        "executed_neutral_days": int(
            subset["eligible_date"].nunique()
        ),
        "trades_per_active_weekday": (
            len(subset) / active if active else 0.0
        ),
    }


def _oracle(
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
    start = min(
        pd.Timestamp(cfg["windows"][name][0])
        for name in cfg["forward_windows"]
    )
    end = max(
        pd.Timestamp(cfg["windows"][name][1])
        for name in cfg["forward_windows"]
    )
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
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
    selected: str,
    development_metrics: dict[str, Any],
    oracle: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool]]:
    windows = {
        name: _window_metrics(
            trades,
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
    forward_daily = aggregate_days(forward)
    forward_metrics = payoff_metrics(forward)
    forward_daily_metrics = payoff_metrics(forward_daily)
    stressed = payoff_metrics(
        forward, "extra_half_pip_stress_r"
    )
    top_removed = payoff_metrics(remove_top_winners(forward))
    recent_start, recent_end = map(
        pd.Timestamp, cfg["recent_six_months"]
    )
    recent = _period(trades, recent_start, recent_end)
    recent_daily = aggregate_days(recent)
    gate = cfg["admission"]
    development = development_metrics[selected]
    development_pass = (
        development["trades"]
        >= int(gate["minimum_development_trades"])
        and development["net_r"] > 0.0
        and development["profit_factor"] > 1.0
    )
    forward_checks = {}
    for name in cfg["forward_windows"]:
        tickets = windows[name]["tickets"]
        daily = windows[name]["daily_portfolio"]
        forward_checks[name] = (
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
    oracle_overall = oracle["overall"]
    recent_metrics = payoff_metrics(recent)
    recent_daily_metrics = payoff_metrics(recent_daily)
    checks = {
        "development_branch_selection": development_pass,
        "every_forward_window": all(forward_checks.values()),
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
            recent_metrics["trades"]
            >= int(gate["minimum_recent_six_month_trades"])
            and recent_metrics["net_r"] > 0.0
            and recent_metrics["profit_factor"]
            > float(
                gate[
                    "minimum_recent_six_month_profit_factor_exclusive"
                ]
            )
            and recent_daily_metrics["profit_factor"] > 1.0
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
        "selected_branch": selected,
        "development_branch_metrics": development_metrics,
        "development_selection_pass": development_pass,
        "forward_window_checks": forward_checks,
        "windows": windows,
        "forward_only": {
            "tickets": forward_metrics,
            "daily_portfolio": forward_daily_metrics,
            "robustness": {
                "top_5_percent_winners_removed": top_removed,
                "extra_half_pip_round_trip": stressed,
            },
        },
        "frequency": {
            "source_eligible_days": census["source_eligible_days"],
            "candidates": census["event_candidates"],
            "candidate_days": census["active_candidate_days"],
            "cash_only_days": census["no_trade_days"],
            "trades_per_source_eligible_day": census[
                "trades_per_source_eligible_day"
            ],
            "frequency_gate": False,
        },
        "recent_six_months": {
            "tickets": recent_metrics,
            "daily_portfolio": recent_daily_metrics,
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
    event_cfg = load_event_config()
    parent = load_parent_points(include_outcomes=False)
    base = load_ensemble_config()
    m5, _, _ = load_inputs(base)
    events = qualifying_events(
        load_event_source(event_cfg), event_cfg
    )
    _, census = build_candidates(
        parent,
        m5,
        events,
        cfg,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_post_event_drive() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    event_cfg = load_event_config()
    parent = load_parent_points(include_outcomes=False)
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    events = qualifying_events(
        load_event_source(event_cfg), event_cfg
    )
    candidates, census = build_candidates(
        parent,
        m5,
        events,
        cfg,
        enforce_frozen_census=True,
    )
    selected, development_metrics, development_ledgers = _selection(
        candidates, m5, cfg
    )
    trades, diagnostics = execute_branch(
        candidates, m5, selected, cfg
    )
    oracle, matches = _oracle(trades, cfg)
    strategy, checks = summarize(
        trades,
        m5,
        cfg,
        census,
        selected,
        development_metrics,
        oracle,
    )
    admitted = all(checks.values())
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_POST_EVENT_DRIVE_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "parent_event_clock_contract": cfg[
            "parent_event_clock_contract"
        ],
        "causality": {
            "event_numeric_fields_used": False,
            "event_selection": (
                "latest frozen-taxonomy event cluster on Neutral UTC date"
            ),
            "direction": (
                "selected once between fixed first-15m momentum and "
                "reversal branches on 2019-2022 only"
            ),
            "observation_uses_only_completed_m5_bars": True,
            "structure_risk_known_before_entry": True,
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
            "available_points_after_start": 0,
            "status": "WAITING_FOR_POST_LOCK_MARKET_DATA",
        },
        "verdict": (
            "The frozen post-event drive passed every historical gate; "
            "only post-lock observations may confirm it."
            if admitted
            else "The frozen post-event drive failed one or more gates "
            "and is closed without repair."
        ),
    }
    artifacts = {
        "CANDIDATES": candidates,
        "DIAGNOSTICS": diagnostics,
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
    "build_candidates",
    "execute_branch",
    "load_config",
    "run_census",
    "run_neutral_post_event_drive",
    "verify_lock",
    "write_json",
]

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_midnight_pairs import (
    load_oracle,
    oracle_match_metrics,
    write_json,
)
from .neutral_session_oco import _effective_ask
from .research import (
    PACKAGE_ROOT,
    PIP,
    active_weekday_fx_days,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N33_NEUTRAL_FIVE_SESSION_REVERSAL"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_five_session_reversal"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_five_session_reversal.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_FIVE_SESSION_REVERSAL_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_five_session_reversal_forward_outcomes")
        is not True
    ):
        raise RuntimeError("Neutral five-session reversal is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral five-session reversal preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    for source_name in (
        "data_and_classifier_contract",
        "neutral_timestamp_source",
    ):
        source = cfg[source_name]
        if sha256_file(PACKAGE_ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(
                f"Neutral five-session reversal {source_name} drift"
            )
    return checked


def _window_name(
    timestamp: pd.Timestamp, cfg: dict[str, Any]
) -> str:
    for name, (start_raw, end_raw) in cfg["windows"].items():
        if (
            pd.Timestamp(start_raw)
            <= timestamp
            <= pd.Timestamp(end_raw)
        ):
            return name
    return "OUTSIDE"


def _neutral_midnights(cfg: dict[str, Any]) -> pd.DatetimeIndex:
    source = pd.read_parquet(
        PACKAGE_ROOT / cfg["neutral_timestamp_source"]["path"],
        columns=["entry_time_utc", "side"],
    )
    source["entry_time_utc"] = pd.to_datetime(
        source["entry_time_utc"], utc=True
    )
    counts = source.groupby("entry_time_utc").size()
    paired = counts[
        counts.eq(2)
        & (
            counts.index.hour
            == int(cfg["strategy"]["entry_hour_utc"])
        )
        & (
            counts.index.minute
            == int(cfg["strategy"]["entry_minute_utc"])
        )
        & (counts.index.weekday < 5)
    ]
    return pd.DatetimeIndex(paired.index).sort_values()


def build_candidates(
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    strategy = cfg["strategy"]
    lookback = int(strategy["completed_m5_lookback_bars"])
    cooldown = pd.Timedelta(
        hours=float(strategy["cooldown_hours_from_entry"])
    )
    mid_close = (m5["bid_close"] + m5["ask_close"]) / 2.0
    source_times = _neutral_midnights(cfg)
    records: list[dict[str, Any]] = []
    history_complete = 0
    zero_moves = 0
    cooldown_cash = 0
    next_allowed = pd.Timestamp.min.tz_localize("UTC")
    for entry_time in source_times:
        position = int(m5.index.searchsorted(entry_time, side="left"))
        if (
            position >= len(m5)
            or m5.index[position] != entry_time
            or position <= lookback
        ):
            continue
        history_complete += 1
        signal_end_position = position - 1
        signal_start_position = signal_end_position - lookback
        move = float(
            mid_close.iloc[signal_end_position]
            - mid_close.iloc[signal_start_position]
        )
        if move == 0.0:
            zero_moves += 1
            continue
        if entry_time < next_allowed:
            cooldown_cash += 1
            continue
        side = "SHORT" if move > 0.0 else "LONG"
        records.append(
            {
                "family": FAMILY,
                "regime": "NEUTRAL",
                "eligible_date": entry_time.strftime("%Y-%m-%d"),
                "trade_id": (
                    f"{entry_time.strftime('%Y-%m-%dT%H%M')}:{side}"
                ),
                "entry_time_utc": entry_time,
                "entry_position": position,
                "side": side,
                "signal_start_time_utc": m5.index[
                    signal_start_position
                ],
                "signal_end_time_utc": m5.index[
                    signal_end_position
                ],
                "completed_m5_bars": lookback,
                "five_session_move_pips": move / PIP,
                "window": _window_name(entry_time, cfg),
            }
        )
        next_allowed = entry_time + cooldown
    candidates = pd.DataFrame(records)
    if not candidates.empty:
        candidates = candidates.sort_values(
            "entry_time_utc"
        ).reset_index(drop=True)
    by_window: dict[str, Any] = {}
    for name in cfg["windows"]:
        subset = candidates[candidates["window"].eq(name)]
        by_window[name] = {
            "candidates": int(len(subset)),
            "active_days": int(subset["eligible_date"].nunique()),
            "long_candidates": int(subset["side"].eq("LONG").sum()),
            "short_candidates": int(subset["side"].eq("SHORT").sum()),
            "long_rate": (
                float(subset["side"].eq("LONG").mean())
                if len(subset)
                else 0.0
            ),
        }
    census = {
        "neutral_midnight_source_points": int(len(source_times)),
        "history_complete_points": history_complete,
        "zero_move_cash_points": zero_moves,
        "cooldown_cash_points": cooldown_cash,
        "selected_candidates": int(len(candidates)),
        "active_candidate_days": int(
            candidates["eligible_date"].nunique()
        )
        if not candidates.empty
        else 0,
        "long_candidates": int(candidates["side"].eq("LONG").sum())
        if not candidates.empty
        else 0,
        "short_candidates": int(candidates["side"].eq("SHORT").sum())
        if not candidates.empty
        else 0,
        "long_rate": (
            float(candidates["side"].eq("LONG").mean())
            if not candidates.empty
            else 0.0
        ),
        "by_window": by_window,
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Five-session reversal census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return candidates, census


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
            "TIME_72H",
        )
    return (
        m5.index[end],
        _effective_ask(bar, "close", spread_floor) + slippage,
        "TIME_72H",
    )


def execute(
    candidates: pd.DataFrame,
    m5: pd.DataFrame,
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
    hold = pd.Timedelta(
        hours=float(execution["maximum_hold_hours"])
    )
    ticket_weight = float(
        execution["risk_per_trade_portfolio_r"]
    )
    rows: list[dict[str, Any]] = []
    for _, candidate in candidates.iterrows():
        position = int(candidate["entry_position"])
        entry_time = candidate["entry_time_utc"]
        bar = m5.iloc[position]
        side = candidate["side"]
        if side == "LONG":
            entry = (
                _effective_ask(bar, "open", spread_floor) + slippage
            )
            stop = entry - risk
            target = entry + target_distance
        else:
            entry = float(bar["bid_open"]) - slippage
            stop = entry + risk
            target = entry - target_distance
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
        stressed_r = result_r - 0.5 * PIP / risk
        rows.append(
            {
                **candidate.to_dict(),
                "exit_time_utc": exit_time,
                "entry_price": entry,
                "stop_price": stop,
                "target_price": target,
                "exit_price": exit_price,
                "exit_reason": reason,
                "risk_distance": risk,
                "risk_pips": float(execution["risk_pips"]),
                "r": result_r,
                "portfolio_r": result_r * ticket_weight,
                "extra_half_pip_stress_r": stressed_r,
                "extra_half_pip_stress_portfolio_r": (
                    stressed_r * ticket_weight
                ),
                "fixed_0p01_lot_usd": pnl * 1000.0,
            }
        )
    return pd.DataFrame(rows)


def aggregate_days(trades: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    return (
        trades.groupby("eligible_date", sort=True)
        .agg(
            entry_time_utc=("entry_time_utc", "first"),
            tickets=("trade_id", "size"),
            raw_ticket_r=("r", "sum"),
            r=("portfolio_r", "sum"),
            extra_half_pip_stress_r=(
                "extra_half_pip_stress_portfolio_r",
                "sum",
            ),
        )
        .reset_index()
    )


def _period(
    frame: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DataFrame:
    return frame[
        frame["entry_time_utc"].between(
            start, end, inclusive="both"
        )
    ].copy()


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
    trades: pd.DataFrame, cfg: dict[str, Any]
) -> tuple[dict[str, Any], pd.DataFrame]:
    oracle = load_oracle(cfg)
    tolerance = int(
        cfg["oracle_matching"]["secondary_tolerance_minutes"]
    )
    overall_start = min(
        pd.Timestamp(cfg["windows"][name][0])
        for name in cfg["forward_windows"]
    )
    overall_end = max(
        pd.Timestamp(cfg["windows"][name][1])
        for name in cfg["forward_windows"]
    )
    overall, matches = oracle_match_metrics(
        trades, oracle, overall_start, overall_end, tolerance
    )
    windows = {}
    for name in cfg["forward_windows"]:
        start, end = map(pd.Timestamp, cfg["windows"][name])
        metrics, _ = oracle_match_metrics(
            trades, oracle, start, end, tolerance
        )
        windows[name] = metrics
    return {"overall": overall, "windows": windows}, matches


def summarize(
    trades: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
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
    development_start, development_end = map(
        pd.Timestamp, cfg["windows"]["development_2019_2022"]
    )
    development = _period(
        trades, development_start, development_end
    )
    development_metrics = payoff_metrics(development)
    development_years = {
        str(year): payoff_metrics(
            development[
                development["entry_time_utc"].dt.year.eq(year)
            ]
        )
        for year in range(2019, 2023)
    }
    development_stress = payoff_metrics(
        development, "extra_half_pip_stress_r"
    )
    development_top_removed = payoff_metrics(
        remove_top_winners(development)
    )
    forward_start = min(
        pd.Timestamp(cfg["windows"][name][0])
        for name in cfg["forward_windows"]
    )
    forward_end = max(
        pd.Timestamp(cfg["windows"][name][1])
        for name in cfg["forward_windows"]
    )
    forward = _period(trades, forward_start, forward_end)
    forward_metrics = payoff_metrics(forward)
    forward_daily = payoff_metrics(aggregate_days(forward))
    stressed = payoff_metrics(
        forward, "extra_half_pip_stress_r"
    )
    top_removed = payoff_metrics(remove_top_winners(forward))
    recent_start, recent_end = map(
        pd.Timestamp, cfg["recent_six_months"]
    )
    recent = _period(trades, recent_start, recent_end)
    recent_metrics = payoff_metrics(recent)
    recent_daily = payoff_metrics(aggregate_days(recent))
    gate = cfg["admission"]
    development_year_checks = {
        year: (
            metrics["trades"]
            >= int(gate["minimum_development_trades_each_year"])
            and metrics["profit_factor"]
            > float(
                gate[
                    "minimum_development_year_profit_factor_exclusive"
                ]
            )
            and metrics["net_r"] > 0.0
        )
        for year, metrics in development_years.items()
    }
    development_pass = (
        development_metrics["trades"]
        >= int(gate["minimum_development_trades"])
        and float(gate["minimum_development_win_rate"])
        <= development_metrics["win_rate"]
        <= float(gate["maximum_development_win_rate"])
        and float(gate["minimum_realized_payoff_ratio"])
        <= development_metrics["realized_payoff_ratio"]
        <= float(gate["maximum_realized_payoff_ratio"])
        and development_metrics["profit_factor"]
        >= float(gate["minimum_development_profit_factor"])
        and development_stress["net_r"] > 0.0
        and development_top_removed["net_r"] > 0.0
        and all(development_year_checks.values())
    )
    forward_window_checks: dict[str, bool] = {}
    for name in cfg["forward_windows"]:
        metrics = windows[name]["tickets"]
        daily = windows[name]["daily_portfolio"]
        forward_window_checks[name] = (
            metrics["trades"]
            >= int(gate["minimum_forward_trades_by_window"][name])
            and float(gate["minimum_forward_win_rate_each_window"])
            <= metrics["win_rate"]
            <= float(gate["maximum_forward_win_rate_each_window"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= metrics["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and metrics["profit_factor"]
            > float(
                gate["minimum_profit_factor_each_window_exclusive"]
            )
            and metrics["net_r"] > 0.0
            and daily["profit_factor"] > 1.0
        )
    checks = {
        "development": development_pass,
        "every_forward_window": all(
            forward_window_checks.values()
        ),
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
        "drawdown": (
            forward_metrics["max_drawdown_r"]
            <= float(gate["maximum_ticket_drawdown_r"])
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
            and recent_daily["profit_factor"] > 1.0
        ),
        "oracle_diagnostic_only": bool(
            gate["oracle_resemblance_is_diagnostic_only"]
        ),
        "frequency_not_a_gate": (
            gate["exact_daily_frequency_gate"] is False
        ),
    }
    strategy = {
        "admitted": all(checks.values()),
        "admission_checks": checks,
        "development_pass": development_pass,
        "development": {
            "tickets": development_metrics,
            "yearly": development_years,
            "year_checks": development_year_checks,
            "robustness": {
                "extra_half_pip_round_trip": development_stress,
                "top_5_percent_winners_removed": (
                    development_top_removed
                ),
            },
        },
        "forward_window_checks": forward_window_checks,
        "windows": windows,
        "forward_only": {
            "tickets": forward_metrics,
            "daily_portfolio": forward_daily,
            "robustness": {
                "extra_half_pip_round_trip": stressed,
                "top_5_percent_winners_removed": top_removed,
            },
        },
        "frequency": {
            "source_eligible_points": census[
                "neutral_midnight_source_points"
            ],
            "selected_candidates": census["selected_candidates"],
            "active_candidate_days": census[
                "active_candidate_days"
            ],
            "frequency_gate": False,
        },
        "recent_six_months": {
            "tickets": recent_metrics,
            "daily_portfolio": recent_daily,
            "active_weekdays": active_weekday_fx_days(
                m5, recent_start, recent_end
            ),
            "executed_neutral_days": int(
                recent["eligible_date"].nunique()
            ),
        },
    }
    return strategy, checks


def run_census() -> dict[str, Any]:
    cfg = load_config()
    m5, _, _ = load_inputs(load_ensemble_config())
    _, census = build_candidates(
        m5, cfg, enforce_frozen_census=False
    )
    return census


def run_neutral_five_session_reversal() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    cfg = load_config()
    m5, _, source_manifests = load_inputs(load_ensemble_config())
    candidates, census = build_candidates(
        m5, cfg, enforce_frozen_census=True
    )
    trades = execute(candidates, m5, cfg)
    oracle, matches = _oracle(trades, cfg)
    strategy, checks = summarize(
        trades, m5, cfg, census, oracle
    )
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "HISTORICAL_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if strategy["admitted"]
            else "REJECTED_NEUTRAL_FIVE_SESSION_REVERSAL_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": source_manifests,
        "causality": {
            "signal_uses_completed_m5_closes_only": True,
            "signal_lookback_bars": cfg["strategy"][
                "completed_m5_lookback_bars"
            ],
            "fixed_time_cooldown": True,
            "fitting": False,
            "threshold_search_in_frozen_rule": False,
            "future_information_in_signal": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "outcome_blind_census": census,
        "strategy": strategy,
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": prospective_start,
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": int(
                candidates["entry_time_utc"]
                .ge(prospective_start)
                .sum()
            ),
            "status": "WAITING_FOR_POST_LOCK_MARKET_DATA",
        },
        "verdict": (
            "The frozen five-session reversal passed every historical "
            "gate but remains research-only pending prospective evidence."
            if all(checks.values())
            else "The frozen five-session reversal failed one or more "
            "gates and is closed without repair."
        ),
    }
    return result, {
        "CANDIDATES": candidates,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "aggregate_days",
    "build_candidates",
    "execute",
    "load_config",
    "run_census",
    "run_neutral_five_session_reversal",
    "verify_lock",
    "write_json",
]

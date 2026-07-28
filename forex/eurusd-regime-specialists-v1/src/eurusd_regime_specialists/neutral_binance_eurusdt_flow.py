from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_four_clock_ranker import (
    build_paired_points,
    load_config as load_parent_config,
    load_source as load_parent_source,
    route_predictions,
)
from .neutral_midnight_pairs import (
    aggregate_days,
    oracle_match_metrics,
    write_json,
)
from .research import (
    PACKAGE_ROOT,
    active_weekday_fx_days,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N22_NEUTRAL_BINANCE_EURUSDT_EXECUTED_FLOW"
OUTPUT_ROOT = PACKAGE_ROOT / "outputs" / "neutral_binance_eurusdt_flow"


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_binance_eurusdt_flow.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_BINANCE_EURUSDT_FLOW_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get("locked_before_binance_eurusdt_flow_outcome_pass")
        is not True
    ):
        raise RuntimeError("Neutral Binance EURUSDT flow is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral Binance EURUSDT flow preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_four_clock_contract"]
    if sha256_file(PACKAGE_ROOT / parent["path"]) != parent["sha256"]:
        raise RuntimeError("Four-clock parent contract drift")
    paired = cfg["paired_trade_source"]
    if sha256_file(PACKAGE_ROOT / paired["path"]) != paired["sha256"]:
        raise RuntimeError("Paired trade source drift")
    flow = cfg["executed_flow_source"]
    if sha256_file(Path(flow["path"])) != flow["sha256"]:
        raise RuntimeError("EURUSDT normalized flow source drift")
    if (
        sha256_file(Path(flow["manifest_path"]))
        != flow["manifest_sha256"]
    ):
        raise RuntimeError("EURUSDT source manifest drift")
    return checked


def load_flow(cfg: dict[str, Any]) -> pd.DataFrame:
    path = Path(cfg["executed_flow_source"]["path"])
    frame = pd.read_parquet(path)
    for column in ("open_time_utc", "close_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame.sort_values("open_time_utc").reset_index(drop=True)


def build_flow_signals(
    flow: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    bars = int(cfg["flow_rule"]["completed_m5_bars"])
    if bars != 3:
        raise RuntimeError("Frozen EURUSDT flow rule requires three bars")
    frame = flow.sort_values("open_time_utc").copy()
    difference = frame["open_time_utc"].diff()
    consecutive = difference.eq(pd.Timedelta(minutes=5))
    fully_consecutive = consecutive.copy()
    for lag in range(1, bars - 1):
        fully_consecutive &= consecutive.shift(lag).fillna(False)
    quote = frame["quote_volume"].rolling(
        bars, min_periods=bars
    ).sum()
    taker_buy = frame["taker_buy_quote_volume"].rolling(
        bars, min_periods=bars
    ).sum()
    trades = frame["trade_count"].rolling(
        bars, min_periods=bars
    ).sum()
    first_open = frame["open"].shift(bars - 1)
    valid = fully_consecutive & quote.gt(0)
    signal = pd.DataFrame(
        {
            "entry_time_utc": (
                frame["open_time_utc"] + pd.Timedelta(minutes=5)
            ),
            "flow_consecutive": fully_consecutive,
            "flow_quote_volume_15m": quote,
            "flow_taker_buy_quote_volume_15m": taker_buy,
            "flow_trade_count_15m": trades,
            "flow_return_15m": frame["close"] / first_open - 1.0,
            "flow_feature_valid": valid,
        }
    )
    signal["flow_taker_imbalance_15m"] = np.where(
        valid,
        (2.0 * taker_buy - quote) / quote,
        np.nan,
    )
    return signal


def _window_name(
    timestamp: pd.Timestamp,
    cfg: dict[str, Any],
) -> str:
    for name, (start_raw, end_raw) in cfg["windows"].items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def load_parent_points(
    *,
    include_outcomes: bool,
) -> pd.DataFrame:
    parent_cfg = load_parent_config()
    source = load_parent_source(
        parent_cfg, include_outcomes=include_outcomes
    )
    points, _ = build_paired_points(
        source,
        parent_cfg,
        include_outcomes=include_outcomes,
        enforce_frozen_census=True,
    )
    return points


def build_decisions(
    points: pd.DataFrame,
    flow_signals: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    joined = points.merge(
        flow_signals,
        on="entry_time_utc",
        how="left",
        validate="one_to_one",
    )
    matched = joined["flow_feature_valid"].fillna(False).astype(bool)
    valid = joined[matched].copy()
    valid["flow_side"] = np.where(
        valid["flow_taker_imbalance_15m"].ge(
            float(cfg["flow_rule"]["long_threshold"])
        ),
        "LONG",
        "SHORT",
    )
    valid["window"] = valid["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    expected = int(
        cfg["strategy"]["required_trades_per_eligible_day"]
    )
    day_counts_before = valid.groupby("eligible_date").size()
    complete_dates = set(
        day_counts_before[day_counts_before == expected].index
    )
    decisions = valid[
        valid["eligible_date"].isin(complete_dates)
        & valid["window"].ne("OUTSIDE")
    ].copy()
    decisions = decisions.sort_values(
        "entry_time_utc"
    ).reset_index(drop=True)
    day_counts = decisions.groupby("eligible_date").size()
    by_window: dict[str, Any] = {}
    for name in cfg["windows"]:
        subset = decisions[decisions["window"].eq(name)]
        by_window[name] = {
            "eligible_days": int(subset["eligible_date"].nunique()),
            "decision_points": int(len(subset)),
            "forced_trade_candidates": int(len(subset)),
        }
    eligible_days = int(decisions["eligible_date"].nunique())
    exact_days = int((day_counts == expected).sum())
    census = {
        "parent_paired_decision_points": int(len(points)),
        "flow_feature_matched_points": int(matched.sum()),
        "flow_feature_missing_or_invalid_points": int((~matched).sum()),
        "complete_days_before_window_filter": int(len(complete_dates)),
        "eligible_complete_days": eligible_days,
        "paired_decision_points": int(len(decisions)),
        "forced_trade_candidates": int(len(decisions)),
        "days_exactly_four_candidates": exact_days,
        "eligible_day_exact_four_coverage": (
            exact_days / eligible_days if eligible_days else 0.0
        ),
        "by_window": by_window,
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Binance EURUSDT flow census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return decisions, census


def _period(
    frame: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    return frame[
        frame["entry_time_utc"].between(start, end, inclusive="both")
    ]


def _direction_metrics(predictions: pd.DataFrame) -> dict[str, Any]:
    available = predictions[predictions["one_winner_label"]]
    correct = int(
        available["direction_correct_when_available"].sum()
    )
    return {
        "decision_points": int(len(predictions)),
        "one_winner_points": int(len(available)),
        "no_winner_points": int(
            (~predictions["one_winner_label"]).sum()
        ),
        "correct_side_when_one_winner": correct,
        "conditional_direction_accuracy": (
            correct / len(available) if len(available) else 0.0
        ),
        "unconditional_target_first_rate": (
            float(predictions["chosen_target_first"].mean())
            if len(predictions)
            else 0.0
        ),
        "predicted_long_rate": (
            float(predictions["chosen_side"].eq("LONG").mean())
            if len(predictions)
            else 0.0
        ),
    }


def execute(
    decisions: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    probabilities = np.where(
        decisions["flow_side"].eq("LONG"), 1.0, 0.0
    )
    trades, predictions = route_predictions(
        decisions, probabilities, cfg
    )
    predictions["flow_side"] = decisions["flow_side"].to_numpy()
    predictions["flow_taker_imbalance_15m"] = decisions[
        "flow_taker_imbalance_15m"
    ].to_numpy()
    predictions["flow_quote_volume_15m"] = decisions[
        "flow_quote_volume_15m"
    ].to_numpy()
    predictions["flow_trade_count_15m"] = decisions[
        "flow_trade_count_15m"
    ].to_numpy()
    predictions["flow_return_15m"] = decisions[
        "flow_return_15m"
    ].to_numpy()
    return trades, predictions


def summarize(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
) -> dict[str, Any]:
    windows: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg["windows"].items():
        start = pd.Timestamp(start_raw)
        end = pd.Timestamp(end_raw)
        window_trades = _period(trades, start, end)
        window_predictions = _period(predictions, start, end)
        daily = aggregate_days(window_trades)
        ticket_metrics = payoff_metrics(window_trades)
        active_days = active_weekday_fx_days(m5, start, end)
        eligible_days = int(
            window_trades["eligible_date"].nunique()
        )
        ticket_metrics["active_weekdays"] = active_days
        ticket_metrics["eligible_neutral_days"] = eligible_days
        ticket_metrics["trades_per_active_weekday"] = (
            len(window_trades) / active_days if active_days else 0.0
        )
        ticket_metrics["trades_per_eligible_neutral_day"] = (
            len(window_trades) / eligible_days if eligible_days else 0.0
        )
        windows[name] = {
            "tickets": ticket_metrics,
            "daily_portfolio": payoff_metrics(daily),
            "direction_selection": _direction_metrics(
                window_predictions
            ),
        }
    overall = payoff_metrics(trades)
    daily = aggregate_days(trades)
    daily_overall = payoff_metrics(daily)
    direction_overall = _direction_metrics(predictions)
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(remove_top_winners(trades))
    expected = int(
        cfg["strategy"]["required_trades_per_eligible_day"]
    )
    counts = trades.groupby("eligible_date").size()
    exact_days = int((counts == expected).sum())
    eligible_days = int(census["eligible_complete_days"])
    gate = cfg["admission"]
    window_checks = {
        name: (
            block["tickets"]["trades"]
            >= int(gate["minimum_trades_each_window"])
            and float(gate["minimum_win_rate"])
            <= block["tickets"]["win_rate"]
            <= float(gate["maximum_win_rate"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= block["tickets"]["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and block["tickets"]["profit_factor"]
            >= float(gate["minimum_profit_factor_each_window"])
            and block["tickets"]["expectancy_r"]
            > float(gate["minimum_expectancy_r_each_window"])
            and block["direction_selection"][
                "conditional_direction_accuracy"
            ]
            >= float(
                gate[
                    "minimum_conditional_direction_accuracy_each_window"
                ]
            )
            and block["daily_portfolio"]["profit_factor"]
            >= float(gate["minimum_daily_profit_factor_each_window"])
        )
        for name, block in windows.items()
    }
    recent_start, recent_end = map(
        pd.Timestamp, cfg["recent_six_months"]
    )
    recent_trades = _period(trades, recent_start, recent_end)
    recent_predictions = _period(
        predictions, recent_start, recent_end
    )
    recent_daily = aggregate_days(recent_trades)
    active_days = active_weekday_fx_days(
        m5, recent_start, recent_end
    )
    recent_eligible = int(
        recent_trades["eligible_date"].nunique()
    )
    return {
        "window_checks": window_checks,
        "overall_tickets": overall,
        "overall_daily_portfolio": daily_overall,
        "overall_direction_selection": direction_overall,
        "windows": windows,
        "frequency": {
            "eligible_days": eligible_days,
            "executed_days": int(len(counts)),
            "days_exactly_four_executed_trades": exact_days,
            "eligible_day_exact_four_execution_coverage": (
                exact_days / eligible_days if eligible_days else 0.0
            ),
            "trades_per_eligible_day": (
                len(trades) / eligible_days if eligible_days else 0.0
            ),
        },
        "robustness": {
            "top_5_percent_winners_removed": top_removed,
            "extra_half_pip_round_trip": stressed,
        },
        "recent_six_months": {
            "tickets": payoff_metrics(recent_trades),
            "daily_portfolio": payoff_metrics(recent_daily),
            "direction_selection": _direction_metrics(
                recent_predictions
            ),
            "active_weekdays": active_days,
            "eligible_neutral_days": recent_eligible,
            "trades_per_active_weekday": (
                len(recent_trades) / active_days
                if active_days
                else 0.0
            ),
            "trades_per_eligible_neutral_day": (
                len(recent_trades) / recent_eligible
                if recent_eligible
                else 0.0
            ),
        },
    }


def load_oracle(cfg: dict[str, Any]) -> pd.DataFrame:
    frame = pd.read_csv(PACKAGE_ROOT / cfg["oracle_source"])
    for column in ("entry_time_utc", "exit_time_utc"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return (
        frame[frame["regime"].eq(cfg["oracle_regime"])]
        .sort_values(["entry_time_utc", "oracle_trade_number"])
        .reset_index(drop=True)
    )


def evaluate_oracle(
    trades: pd.DataFrame,
    cfg: dict[str, Any],
) -> tuple[dict[str, Any], pd.DataFrame]:
    oracle = load_oracle(cfg)
    tolerance = int(
        cfg["oracle_matching"]["secondary_tolerance_minutes"]
    )
    starts = [
        pd.Timestamp(values[0]) for values in cfg["windows"].values()
    ]
    ends = [
        pd.Timestamp(values[1]) for values in cfg["windows"].values()
    ]
    overall, matches = oracle_match_metrics(
        trades, oracle, min(starts), max(ends), tolerance
    )
    by_window: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg["windows"].items():
        metrics, _ = oracle_match_metrics(
            trades,
            oracle,
            pd.Timestamp(start_raw),
            pd.Timestamp(end_raw),
            tolerance,
        )
        by_window[name] = metrics
    return {"overall": overall, "windows": by_window}, matches


def admission(
    strategy: dict[str, Any],
    oracle: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[bool, dict[str, bool]]:
    gate = cfg["admission"]
    oracle_overall = oracle["overall"]
    checks = {
        "every_window": all(strategy["window_checks"].values()),
        "overall_profit_factor": (
            strategy["overall_tickets"]["profit_factor"]
            >= float(gate["minimum_overall_profit_factor"])
        ),
        "overall_exact_oracle_precision": (
            oracle_overall["exact_precision"]
            >= float(gate["minimum_overall_exact_oracle_precision"])
        ),
        "overall_15m_oracle_precision": (
            oracle_overall["tolerant_precision"]
            >= float(gate["minimum_overall_15m_oracle_precision"])
        ),
        "stressed": (
            strategy["robustness"]["extra_half_pip_round_trip"][
                "net_r"
            ]
            > 0
            and strategy["robustness"][
                "extra_half_pip_round_trip"
            ]["profit_factor"]
            >= float(gate["minimum_stressed_profit_factor"])
        ),
        "top_winners_removed": (
            strategy["robustness"][
                "top_5_percent_winners_removed"
            ]["net_r"]
            > 0
        ),
        "daily_drawdown": (
            strategy["overall_daily_portfolio"][
                "max_drawdown_r"
            ]
            <= float(gate["maximum_daily_portfolio_drawdown_r"])
        ),
        "exact_four_frequency": (
            strategy["frequency"][
                "eligible_day_exact_four_execution_coverage"
            ]
            == 1.0
        ),
    }
    return all(checks.values()), checks


def run_census() -> dict[str, Any]:
    cfg = load_config()
    parent = load_parent_points(include_outcomes=False)
    flow = load_flow(cfg)
    signals = build_flow_signals(flow, cfg)
    _, census = build_decisions(
        parent,
        signals,
        cfg,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_binance_eurusdt_flow() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_points(include_outcomes=True)
    flow = load_flow(cfg)
    signals = build_flow_signals(flow, cfg)
    decisions, census = build_decisions(
        parent,
        signals,
        cfg,
        enforce_frozen_census=True,
    )
    trades, predictions = execute(decisions, cfg)
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    strategy = summarize(
        trades, predictions, m5, cfg, census
    )
    oracle, matches = evaluate_oracle(trades, cfg)
    admitted, checks = admission(strategy, oracle, cfg)
    prospective_start = pd.Timestamp(
        cfg["prospective"]["start_utc"]
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_BINANCE_EURUSDT_FLOW_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "executed_flow_source": cfg["executed_flow_source"],
        "causality": {
            "direction": (
                "sign of prior three completed EURUSDT M5 bars' "
                "taker-quote imbalance"
            ),
            "future_information_in_signal": False,
            "model_or_threshold_fit": False,
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
            "available_points_after_start": int(
                (
                    decisions["entry_time_utc"] >= prospective_start
                ).sum()
            ),
            "status": "WAITING_FOR_POST_LOCK_MARKET_DATA",
        },
        "verdict": (
            "The fixed executed-flow sign passed every historical gate; "
            "only post-lock rows may confirm it."
            if admitted
            else "The fixed executed-flow sign failed one or more frozen "
            "gates and is closed without repair."
        ),
    }
    return result, {
        "FLOW_SIGNALS": signals,
        "DECISIONS": decisions,
        "PREDICTIONS": predictions,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "build_decisions",
    "build_flow_signals",
    "execute",
    "load_config",
    "load_flow",
    "run_census",
    "run_neutral_binance_eurusdt_flow",
    "verify_lock",
    "write_json",
]

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .asymmetric import payoff_metrics
from .ensemble import load_ensemble_config, load_inputs
from .neutral_binance_eurusdt_flow import (
    _direction_metrics,
    _period,
    evaluate_oracle,
    load_parent_points,
)
from .neutral_four_clock_ranker import route_predictions
from .neutral_kraken_multivenue_flow import (
    _signals,
    build_decisions as build_parent_decisions,
    load_config as load_parent_config,
    verify_lock as verify_parent_lock,
)
from .neutral_midnight_pairs import aggregate_days, write_json
from .research import (
    PACKAGE_ROOT,
    active_weekday_fx_days,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N25_NEUTRAL_SELECTIVE_MULTIVENUE_AGREEMENT"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_selective_multivenue_agreement"
)


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_selective_multivenue_agreement.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_SELECTIVE_MULTIVENUE_AGREEMENT_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get(
            "locked_before_selective_multivenue_agreement_outcome_pass"
        )
        is not True
    ):
        raise RuntimeError(
            "Neutral selective multivenue agreement is not locked"
        )
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Neutral selective multivenue preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_multivenue_contract"]
    if sha256_file(PACKAGE_ROOT / parent["path"]) != parent["sha256"]:
        raise RuntimeError("Parent multivenue contract drift")
    if (
        sha256_file(PACKAGE_ROOT / parent["lock_path"])
        != parent["lock_sha256"]
    ):
        raise RuntimeError("Parent multivenue lock drift")
    verify_parent_lock()
    return checked


def load_parent_decisions(*, include_outcomes: bool) -> pd.DataFrame:
    cfg = load_parent_config()
    parent = load_parent_points(include_outcomes=include_outcomes)
    kraken_signals, binance_signals = _signals(cfg)
    decisions, _ = build_parent_decisions(
        parent,
        kraken_signals,
        binance_signals,
        cfg,
        enforce_frozen_census=True,
    )
    return decisions


def _distribution(
    frame: pd.DataFrame,
    source_dates: pd.Index,
) -> dict[str, int]:
    counts = (
        frame.groupby("eligible_date").size().reindex(source_dates, fill_value=0)
    )
    return {
        str(candidate_count): int((counts == candidate_count).sum())
        for candidate_count in range(5)
    }


def _census_block(
    parent: pd.DataFrame,
    selected: pd.DataFrame,
) -> dict[str, Any]:
    source_dates = pd.Index(
        sorted(parent["eligible_date"].astype(str).unique())
    )
    active_days = int(selected["eligible_date"].nunique())
    source_days = int(len(source_dates))
    candidates = int(len(selected))
    return {
        "source_eligible_days": source_days,
        "agreement_candidates": candidates,
        "active_candidate_days": active_days,
        "no_trade_days": source_days - active_days,
        "predicted_long_rate": (
            float(selected["flow_side"].eq("LONG").mean())
            if candidates
            else 0.0
        ),
        "trades_per_source_eligible_day": (
            candidates / source_days if source_days else 0.0
        ),
        "trades_per_active_candidate_day": (
            candidates / active_days if active_days else 0.0
        ),
        "candidate_count_distribution": _distribution(
            selected, source_dates
        ),
    }


def build_selective_decisions(
    parent: pd.DataFrame,
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    kraken_long = parent[
        "kraken_reported_side_imbalance_15m"
    ].ge(0.0)
    binance_long = parent["binance_taker_imbalance_15m"].ge(0.0)
    agreement = kraken_long.eq(binance_long)
    selected = parent[agreement].copy()
    selected["flow_side"] = np.where(
        kraken_long[agreement], "LONG", "SHORT"
    )
    selected["venue_sign_agreement"] = True
    selected = selected.sort_values("entry_time_utc").reset_index(drop=True)

    overall = _census_block(parent, selected)
    by_window: dict[str, Any] = {}
    for name in cfg["windows"]:
        parent_window = parent[parent["window"].eq(name)]
        selected_window = selected[selected["window"].eq(name)]
        by_window[name] = _census_block(
            parent_window, selected_window
        )
    census = {
        "parent_decision_points": int(len(parent)),
        "source_eligible_days": overall["source_eligible_days"],
        "agreement_candidates": overall["agreement_candidates"],
        "disagreement_points": int((~agreement).sum()),
        "active_candidate_days": overall["active_candidate_days"],
        "no_trade_days": overall["no_trade_days"],
        "predicted_long_rate": overall["predicted_long_rate"],
        "trades_per_source_eligible_day": overall[
            "trades_per_source_eligible_day"
        ],
        "trades_per_active_candidate_day": overall[
            "trades_per_active_candidate_day"
        ],
        "candidate_count_distribution": overall[
            "candidate_count_distribution"
        ],
        "by_window": by_window,
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Selective multivenue census drift: "
            f"actual={census!r} "
            f"frozen={cfg['outcome_blind_census']!r}"
        )
    return selected, census


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
    trades["family"] = FAMILY
    predictions["family"] = FAMILY
    feature_columns = [
        "flow_side",
        "venue_sign_agreement",
        "kraken_reported_side_imbalance_15m",
        "binance_taker_imbalance_15m",
        "kraken_return_15m",
        "binance_return_15m",
    ]
    for column in feature_columns:
        trades[column] = decisions[column].to_numpy()
        predictions[column] = decisions[column].to_numpy()
    return trades, predictions


def _window_summary(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
    m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    census: dict[str, Any],
) -> dict[str, Any]:
    window_trades = _period(trades, start, end)
    window_predictions = _period(predictions, start, end)
    ticket_metrics = payoff_metrics(window_trades)
    daily_metrics = payoff_metrics(aggregate_days(window_trades))
    active_weekdays = active_weekday_fx_days(m5, start, end)
    ticket_metrics.update(
        {
            "active_weekdays": active_weekdays,
            "source_eligible_neutral_days": census[
                "source_eligible_days"
            ],
            "executed_neutral_days": census["active_candidate_days"],
            "cash_only_source_eligible_days": census["no_trade_days"],
            "trades_per_active_weekday": (
                len(window_trades) / active_weekdays
                if active_weekdays
                else 0.0
            ),
            "trades_per_source_eligible_neutral_day": census[
                "trades_per_source_eligible_day"
            ],
            "trades_per_executed_neutral_day": census[
                "trades_per_active_candidate_day"
            ],
        }
    )
    return {
        "tickets": ticket_metrics,
        "daily_portfolio": daily_metrics,
        "direction_selection": _direction_metrics(window_predictions),
        "candidate_count_distribution": census[
            "candidate_count_distribution"
        ],
    }


def summarize_selective(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
) -> dict[str, Any]:
    windows: dict[str, Any] = {}
    for name, (start_raw, end_raw) in cfg["windows"].items():
        windows[name] = _window_summary(
            trades,
            predictions,
            m5,
            pd.Timestamp(start_raw),
            pd.Timestamp(end_raw),
            census["by_window"][name],
        )

    gate = cfg["admission"]
    window_checks = {
        name: {
            "minimum_trades": (
                block["tickets"]["trades"]
                >= int(gate["minimum_trades_each_window"])
            ),
            "payoff_ratio": (
                float(gate["minimum_realized_payoff_ratio"])
                <= block["tickets"]["realized_payoff_ratio"]
                <= float(gate["maximum_realized_payoff_ratio"])
            ),
            "ticket_profit_factor": (
                block["tickets"]["profit_factor"]
                > float(
                    gate[
                        "minimum_profit_factor_each_window_exclusive"
                    ]
                )
            ),
            "positive_expectancy": (
                block["tickets"]["expectancy_r"]
                > float(
                    gate[
                        "minimum_expectancy_r_each_window_exclusive"
                    ]
                )
            ),
            "conditional_direction_accuracy": (
                block["direction_selection"][
                    "conditional_direction_accuracy"
                ]
                > float(
                    gate[
                        "minimum_conditional_direction_accuracy_each_window_exclusive"
                    ]
                )
            ),
            "daily_profit_factor": (
                block["daily_portfolio"]["profit_factor"]
                > float(
                    gate[
                        "minimum_daily_profit_factor_each_window_exclusive"
                    ]
                )
            ),
        }
        for name, block in windows.items()
    }
    window_pass = {
        name: all(checks.values())
        for name, checks in window_checks.items()
    }

    overall = payoff_metrics(trades)
    overall_daily = payoff_metrics(aggregate_days(trades))
    stressed = payoff_metrics(trades, "extra_half_pip_stress_r")
    top_removed = payoff_metrics(remove_top_winners(trades))
    recent_start, recent_end = map(
        pd.Timestamp, cfg["recent_six_months"]
    )
    recent_trades = _period(trades, recent_start, recent_end)
    recent_predictions = _period(
        predictions, recent_start, recent_end
    )
    recent_daily = aggregate_days(recent_trades)
    recent_name = next(
        name
        for name, bounds in cfg["windows"].items()
        if list(bounds) == list(cfg["recent_six_months"])
    )
    recent_census = census["by_window"][recent_name]
    recent_active_weekdays = active_weekday_fx_days(
        m5, recent_start, recent_end
    )
    return {
        "window_checks": window_checks,
        "window_pass": window_pass,
        "overall_tickets": overall,
        "overall_daily_portfolio": overall_daily,
        "overall_direction_selection": _direction_metrics(predictions),
        "windows": windows,
        "frequency": {
            "source_eligible_days": census["source_eligible_days"],
            "executed_days": census["active_candidate_days"],
            "cash_only_days": census["no_trade_days"],
            "trades": census["agreement_candidates"],
            "trades_per_source_eligible_day": census[
                "trades_per_source_eligible_day"
            ],
            "trades_per_executed_day": census[
                "trades_per_active_candidate_day"
            ],
            "candidate_count_distribution": census[
                "candidate_count_distribution"
            ],
            "exact_daily_frequency_gate": False,
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
            "active_weekdays": recent_active_weekdays,
            "source_eligible_neutral_days": recent_census[
                "source_eligible_days"
            ],
            "executed_neutral_days": recent_census[
                "active_candidate_days"
            ],
            "cash_only_source_eligible_days": recent_census[
                "no_trade_days"
            ],
            "trades_per_active_weekday": (
                len(recent_trades) / recent_active_weekdays
                if recent_active_weekdays
                else 0.0
            ),
            "trades_per_source_eligible_neutral_day": recent_census[
                "trades_per_source_eligible_day"
            ],
            "trades_per_executed_neutral_day": recent_census[
                "trades_per_active_candidate_day"
            ],
        },
    }


def admission(
    strategy: dict[str, Any],
    oracle: dict[str, Any],
    cfg: dict[str, Any],
) -> tuple[bool, dict[str, bool]]:
    gate = cfg["admission"]
    recent = strategy["recent_six_months"]
    oracle_overall = oracle["overall"]
    checks = {
        "every_window": all(strategy["window_pass"].values()),
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
            strategy["robustness"]["extra_half_pip_round_trip"]["net_r"]
            > 0.0
            and strategy["robustness"][
                "extra_half_pip_round_trip"
            ]["profit_factor"]
            > float(gate["minimum_stressed_profit_factor_exclusive"])
        ),
        "top_winners_removed": (
            strategy["robustness"][
                "top_5_percent_winners_removed"
            ]["net_r"]
            > 0.0
        ),
        "daily_drawdown": (
            strategy["overall_daily_portfolio"]["max_drawdown_r"]
            <= float(gate["maximum_daily_portfolio_drawdown_r"])
        ),
        "recent_six_months": (
            recent["tickets"]["trades"]
            >= int(gate["minimum_recent_six_month_trades"])
            and recent["tickets"]["net_r"] > 0.0
            and recent["tickets"]["profit_factor"]
            > float(
                gate[
                    "minimum_recent_six_month_profit_factor_exclusive"
                ]
            )
            and recent["daily_portfolio"]["profit_factor"]
            > float(
                gate[
                    "minimum_recent_six_month_daily_profit_factor_exclusive"
                ]
            )
        ),
        "frequency_not_a_gate": (
            gate["exact_daily_frequency_gate"] is False
        ),
    }
    return all(checks.values()), checks


def run_census() -> dict[str, Any]:
    cfg = load_config()
    parent = load_parent_decisions(include_outcomes=False)
    _, census = build_selective_decisions(
        parent, cfg, enforce_frozen_census=False
    )
    return census


def run_neutral_selective_multivenue_agreement() -> tuple[
    dict[str, Any],
    dict[str, pd.DataFrame],
]:
    verify_lock()
    cfg = load_config()
    parent = load_parent_decisions(include_outcomes=True)
    decisions, census = build_selective_decisions(
        parent, cfg, enforce_frozen_census=True
    )
    trades, predictions = execute(decisions, cfg)
    base = load_ensemble_config()
    m5, _, manifests = load_inputs(base)
    strategy = summarize_selective(
        trades, predictions, m5, cfg, census
    )
    oracle, matches = evaluate_oracle(trades, cfg)
    admitted, checks = admission(strategy, oracle, cfg)
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    prospective_points = decisions[
        decisions["entry_time_utc"] >= prospective_start
    ]
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "CAUSAL_RESEARCH_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if admitted
            else "REJECTED_NEUTRAL_SELECTIVE_MULTIVENUE_AGREEMENT_V1"
        ),
        "information_status": cfg["information_status"],
        "source_manifests": manifests,
        "parent_multivenue_contract": cfg[
            "parent_multivenue_contract"
        ],
        "causality": {
            "direction": (
                "agreed sign of prior-15-minute normalized executed-flow "
                "imbalance from Kraken EUR/USD and Binance EURUSDT"
            ),
            "abstention": "CASH when venue signs disagree",
            "magnitude_threshold_or_weight_fit": False,
            "clock_or_subgroup_selection": False,
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
            "available_points_after_start": int(
                len(prospective_points)
            ),
            "status": (
                "WAITING_FOR_POST_LOCK_MARKET_DATA"
                if prospective_points.empty
                else "POST_LOCK_POINTS_AVAILABLE"
            ),
        },
        "verdict": (
            "The frozen selective agreement rule passed every historical "
            "gate; only post-lock rows may confirm it."
            if admitted
            else "The frozen selective agreement rule failed one or more "
            "gates and is closed without repair."
        ),
    }
    return result, {
        "DECISIONS": decisions,
        "PREDICTIONS": predictions,
        "TRADES": trades,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "FAMILY",
    "OUTPUT_ROOT",
    "admission",
    "build_selective_decisions",
    "execute",
    "load_config",
    "run_census",
    "run_neutral_selective_multivenue_agreement",
    "summarize_selective",
    "verify_lock",
    "write_json",
]

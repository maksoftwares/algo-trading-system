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
    load_parent_points,
)
from .neutral_four_clock_ranker import route_predictions
from .neutral_midnight_pairs import aggregate_days, write_json
from .neutral_post_event_drive import _oracle
from .research import (
    PACKAGE_ROOT,
    active_weekday_fx_days,
    remove_top_winners,
    sha256_file,
)


FAMILY = "N32_NEUTRAL_PRECIOUS_METALS_CONSENSUS"
OUTPUT_ROOT = (
    PACKAGE_ROOT / "outputs" / "neutral_precious_metals_consensus"
)
SYMBOLS = ("XAUUSD", "XAGUSD")


def load_config() -> dict[str, Any]:
    return json.loads(
        (
            PACKAGE_ROOT
            / "config"
            / "frozen_neutral_precious_metals_consensus.json"
        ).read_text(encoding="utf-8")
    )


def verify_lock() -> dict[str, str]:
    lock = json.loads(
        (
            PACKAGE_ROOT
            / "EURUSD_NEUTRAL_PRECIOUS_METALS_CONSENSUS_PREREG_2026_07_28.sha256.json"
        ).read_text(encoding="utf-8")
    )
    if (
        lock.get(
            "locked_before_precious_metals_consensus_outcome_pass"
        )
        is not True
    ):
        raise RuntimeError("Precious-metals consensus is not locked")
    checked: dict[str, str] = {}
    for relative, expected in lock["files"].items():
        actual = sha256_file(PACKAGE_ROOT / relative)
        if actual != expected:
            raise RuntimeError(
                "Precious-metals consensus preregistration mismatch: "
                f"{relative}"
            )
        checked[relative] = actual
    cfg = load_config()
    parent = cfg["parent_four_clock_contract"]
    if sha256_file(PACKAGE_ROOT / parent["path"]) != parent["sha256"]:
        raise RuntimeError("Parent four-clock config drift")
    if (
        sha256_file(PACKAGE_ROOT / parent["lock_path"])
        != parent["lock_sha256"]
    ):
        raise RuntimeError("Parent four-clock lock drift")
    source = cfg["source"]
    if sha256_file(Path(source["path"])) != source["sha256"]:
        raise RuntimeError("Precious-metals parquet drift")
    if (
        sha256_file(Path(source["manifest_path"]))
        != source["manifest_sha256"]
    ):
        raise RuntimeError("Precious-metals manifest drift")
    if cfg["outcome_blind_census"] is None:
        raise RuntimeError("Precious-metals census is not frozen")
    return checked


def _mid_close(frame: pd.DataFrame) -> pd.Series:
    return 0.5 * (
        frame["bid_close"].astype(float)
        + frame["ask_close"].astype(float)
    )


def completed_return_vote(
    close: pd.Series, horizon_minutes: int
) -> tuple[pd.Series, pd.Series]:
    bars = int(horizon_minutes // 5)
    if bars <= 0 or bars * 5 != horizon_minutes:
        raise ValueError("Return horizon must be a positive M5 multiple")
    lag = close.shift(bars)
    elapsed = (
        close.index.to_series()
        - close.index.to_series().shift(bars)
    )
    contiguous = elapsed.eq(pd.Timedelta(minutes=horizon_minutes))
    returns = (
        close.astype(float) / lag.astype(float) - 1.0
    ).where(contiguous)
    return returns, np.sign(returns)


def load_metals(cfg: dict[str, Any]) -> dict[str, pd.DataFrame]:
    frame = pd.read_parquet(Path(cfg["source"]["path"]))
    frame["timestamp_utc"] = pd.to_datetime(
        frame["timestamp_utc"], utc=True
    )
    result = {}
    for symbol in SYMBOLS:
        subset = (
            frame[frame["symbol"].eq(symbol)]
            .drop(columns=["symbol"])
            .sort_values("timestamp_utc")
            .drop_duplicates("timestamp_utc", keep="last")
            .set_index("timestamp_utc")
        )
        if subset.empty or not subset.index.is_monotonic_increasing:
            raise RuntimeError(f"Invalid {symbol} M5 source")
        result[symbol] = subset
    return result


def _window_name(
    timestamp: pd.Timestamp, cfg: dict[str, Any]
) -> str:
    for name, (start_raw, end_raw) in cfg["windows"].items():
        if pd.Timestamp(start_raw) <= timestamp <= pd.Timestamp(end_raw):
            return name
    return "OUTSIDE"


def build_decisions(
    points: pd.DataFrame,
    metals: dict[str, pd.DataFrame],
    cfg: dict[str, Any],
    *,
    enforce_frozen_census: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    horizon = int(cfg["strategy"]["return_horizon_minutes"])
    attached = points.copy()
    attached["signal_time_metals_utc"] = (
        attached["entry_time_utc"] - pd.Timedelta(minutes=5)
    )
    for symbol in SYMBOLS:
        returns, votes = completed_return_vote(
            _mid_close(metals[symbol]), horizon
        )
        signal_index = pd.DatetimeIndex(
            attached["signal_time_metals_utc"]
        )
        attached[f"{symbol.lower()}_return_60m"] = returns.reindex(
            signal_index
        ).to_numpy()
        attached[f"{symbol.lower()}_vote"] = votes.reindex(
            signal_index
        ).to_numpy()
    vote_columns = [f"{symbol.lower()}_vote" for symbol in SYMBOLS]
    attached["both_valid_nonzero"] = (
        attached[vote_columns].abs().eq(1.0).all(axis=1)
    )
    attached["metals_agree"] = (
        attached["both_valid_nonzero"]
        & attached["xauusd_vote"].eq(attached["xagusd_vote"])
    )
    attached["trade_candidate"] = attached["metals_agree"]
    attached["metals_side"] = np.select(
        [
            attached["metals_agree"]
            & attached["xauusd_vote"].eq(1.0),
            attached["metals_agree"]
            & attached["xauusd_vote"].eq(-1.0),
        ],
        ["LONG", "SHORT"],
        default="CASH",
    )
    attached["window"] = attached["entry_time_utc"].map(
        lambda value: _window_name(value, cfg)
    )
    decisions = attached[
        attached["trade_candidate"] & attached["window"].ne("OUTSIDE")
    ].copy()
    decisions["flow_side"] = decisions["metals_side"]
    decisions = decisions.sort_values("entry_time_utc").reset_index(
        drop=True
    )

    def block(
        source: pd.DataFrame, selected: pd.DataFrame
    ) -> dict[str, Any]:
        counts = selected.groupby("eligible_date").size()
        distribution = (
            counts.reindex(
                sorted(source["eligible_date"].unique()), fill_value=0
            )
            .value_counts()
            .sort_index()
        )
        return {
            "source_decision_points": int(len(source)),
            "trade_candidates": int(len(selected)),
            "active_candidate_days": int(
                selected["eligible_date"].nunique()
            ),
            "cash_decision_points": int(len(source) - len(selected)),
            "predicted_long_rate": (
                float(selected["metals_side"].eq("LONG").mean())
                if len(selected)
                else 0.0
            ),
            "candidate_count_distribution_per_source_day": {
                str(int(key)): int(value)
                for key, value in distribution.items()
            },
        }

    by_window = {}
    for name in cfg["windows"]:
        by_window[name] = block(
            attached[attached["window"].eq(name)],
            decisions[decisions["window"].eq(name)],
        )
    source_dates = sorted(attached["eligible_date"].unique())
    day_counts = decisions.groupby("eligible_date").size().reindex(
        source_dates, fill_value=0
    )
    census = {
        "parent_paired_decision_points": int(len(points)),
        "both_metals_valid_nonzero_points": int(
            attached["both_valid_nonzero"].sum()
        ),
        "agreement_trade_candidates": int(len(decisions)),
        "active_candidate_days": int(
            decisions["eligible_date"].nunique()
        ),
        "cash_decision_points": int(len(points) - len(decisions)),
        "predicted_long_rate": (
            float(decisions["metals_side"].eq("LONG").mean())
            if len(decisions)
            else 0.0
        ),
        "trades_per_source_eligible_day": (
            len(decisions) / len(source_dates) if source_dates else 0.0
        ),
        "candidate_count_distribution_per_source_day": {
            str(int(key)): int(value)
            for key, value in day_counts.value_counts()
            .sort_index()
            .items()
        },
        "by_window": by_window,
    }
    if (
        enforce_frozen_census
        and census != cfg["outcome_blind_census"]
    ):
        raise RuntimeError(
            "Precious-metals consensus census drift: "
            f"actual={census!r} frozen={cfg['outcome_blind_census']!r}"
        )
    return attached, decisions, census


def execute(
    decisions: pd.DataFrame, cfg: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    probabilities = np.where(
        decisions["metals_side"].eq("LONG"), 1.0, 0.0
    )
    trades, predictions = route_predictions(
        decisions, probabilities, cfg
    )
    trades["family"] = FAMILY
    for column in (
        "signal_time_metals_utc",
        "xauusd_return_60m",
        "xagusd_return_60m",
        "xauusd_vote",
        "xagusd_vote",
        "metals_side",
    ):
        trades[column] = decisions[column].to_numpy()
        predictions[column] = decisions[column].to_numpy()
    return trades, predictions


def _window_metrics(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
    m5: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
) -> dict[str, Any]:
    subset = _period(trades, start, end)
    predicted = _period(predictions, start, end)
    daily = aggregate_days(subset)
    active = active_weekday_fx_days(m5, start, end)
    return {
        "tickets": payoff_metrics(subset),
        "daily_portfolio": payoff_metrics(daily),
        "direction_selection": _direction_metrics(predicted),
        "active_weekdays": active,
        "executed_neutral_days": int(
            subset["eligible_date"].nunique()
        ),
        "trades_per_active_weekday": (
            len(subset) / active if active else 0.0
        ),
    }


def summarize(
    trades: pd.DataFrame,
    predictions: pd.DataFrame,
    m5: pd.DataFrame,
    cfg: dict[str, Any],
    census: dict[str, Any],
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
    development = windows["development_2019_2022"]["tickets"]
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
    recent_predictions = _period(
        predictions, recent_start, recent_end
    )
    recent_daily = aggregate_days(recent)
    recent_metrics = payoff_metrics(recent)
    recent_daily_metrics = payoff_metrics(recent_daily)
    gate = cfg["admission"]
    development_pass = (
        development["trades"]
        >= int(gate["minimum_development_trades"])
        and development["net_r"] > 0.0
        and development["profit_factor"] > 1.0
    )
    window_checks = {}
    for name in cfg["forward_windows"]:
        tickets = windows[name]["tickets"]
        daily = windows[name]["daily_portfolio"]
        window_checks[name] = (
            tickets["trades"]
            >= int(gate["minimum_forward_trades_by_window"][name])
            and float(gate["minimum_forward_win_rate_each_window"])
            <= tickets["win_rate"]
            <= float(gate["maximum_forward_win_rate_each_window"])
            and float(gate["minimum_realized_payoff_ratio"])
            <= tickets["realized_payoff_ratio"]
            <= float(gate["maximum_realized_payoff_ratio"])
            and tickets["profit_factor"]
            > float(
                gate["minimum_profit_factor_each_window_exclusive"]
            )
            and tickets["net_r"] > 0.0
            and daily["profit_factor"]
            > float(
                gate[
                    "minimum_daily_profit_factor_each_window_exclusive"
                ]
            )
        )
    overall_oracle = oracle["overall"]
    checks = {
        "development": development_pass,
        "every_forward_window": all(window_checks.values()),
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
            overall_oracle["exact_precision"]
            >= float(gate["minimum_overall_exact_oracle_precision"])
        ),
        "oracle_15m_precision": (
            overall_oracle["tolerant_precision"]
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
        "admitted": all(checks.values()),
        "admission_checks": checks,
        "development_pass": development_pass,
        "forward_window_checks": window_checks,
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
            "source_eligible_days": 642,
            "selected_candidates": census[
                "agreement_trade_candidates"
            ],
            "active_candidate_days": census["active_candidate_days"],
            "trades_per_source_eligible_day": census[
                "trades_per_source_eligible_day"
            ],
            "frequency_gate": False,
        },
        "recent_six_months": {
            "tickets": recent_metrics,
            "daily_portfolio": recent_daily_metrics,
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
    points = load_parent_points(include_outcomes=False)
    metals = load_metals(cfg)
    _, _, census = build_decisions(
        points,
        metals,
        cfg,
        enforce_frozen_census=False,
    )
    return census


def run_neutral_precious_metals_consensus() -> tuple[
    dict[str, Any], dict[str, pd.DataFrame]
]:
    cfg = load_config()
    base = load_ensemble_config()
    m5, _, source_manifests = load_inputs(base)
    points = load_parent_points(include_outcomes=True)
    metals = load_metals(cfg)
    attached, decisions, census = build_decisions(
        points,
        metals,
        cfg,
        enforce_frozen_census=True,
    )
    trades, predictions = execute(decisions, cfg)
    oracle, matches = _oracle(trades, cfg)
    strategy, checks = summarize(
        trades, predictions, m5, cfg, census, oracle
    )
    prospective_start = pd.Timestamp(cfg["prospective"]["start_utc"])
    available = int(
        decisions["entry_time_utc"].ge(prospective_start).sum()
    )
    result = {
        "campaign_id": cfg["campaign_id"],
        "status": (
            "HISTORICAL_PASS_REQUIRES_PROSPECTIVE_CONFIRMATION"
            if strategy["admitted"]
            else "REJECTED_NEUTRAL_PRECIOUS_METALS_CONSENSUS_V1"
        ),
        "information_status": cfg["information_status"],
        "source": cfg["source"],
        "source_manifests": source_manifests,
        "causality": {
            "signal_bar_complete_at_entry": True,
            "return_endpoints_exact": True,
            "fitting": False,
            "threshold_search": False,
            "future_information_in_signal": False,
            "oracle_usage": "evaluation only after trade ledger",
        },
        "outcome_blind_census": census,
        "strategy": strategy,
        "oracle_resemblance": oracle,
        "prospective": {
            "start_utc": prospective_start,
            "historical_rows_before_start_are_research_only": True,
            "available_points_after_start": available,
            "status": "WAITING_FOR_POST_LOCK_MARKET_DATA",
        },
        "verdict": (
            "The frozen metals-consensus rule passed every historical "
            "gate but remains research-only pending prospective evidence."
            if strategy["admitted"]
            else "The frozen metals-consensus rule failed one or more "
            "gates and is closed without repair."
        ),
    }
    return result, {
        "ALL_POINTS": attached,
        "DECISIONS": decisions,
        "TRADES": trades,
        "PREDICTIONS": predictions,
        "DAILY_PORTFOLIO": aggregate_days(trades),
        "ORACLE_MATCHES": matches,
    }


__all__ = [
    "OUTPUT_ROOT",
    "build_decisions",
    "completed_return_vote",
    "load_config",
    "load_metals",
    "run_census",
    "run_neutral_precious_metals_consensus",
    "verify_lock",
    "write_json",
]

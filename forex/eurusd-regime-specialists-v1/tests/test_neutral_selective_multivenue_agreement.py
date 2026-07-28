from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from eurusd_regime_specialists.neutral_selective_multivenue_agreement import (  # noqa: E402
    admission,
    build_selective_decisions,
)


def config() -> dict:
    return {
        "windows": {
            "test": [
                "2025-01-01T00:00:00Z",
                "2025-12-31T23:59:59Z",
            ]
        },
        "outcome_blind_census": {},
        "admission": {
            "minimum_overall_profit_factor": 1.1,
            "minimum_overall_exact_oracle_precision": 0.2,
            "minimum_overall_15m_oracle_precision": 0.4,
            "minimum_stressed_profit_factor_exclusive": 1.0,
            "maximum_daily_portfolio_drawdown_r": 20.0,
            "minimum_recent_six_month_trades": 50,
            "minimum_recent_six_month_profit_factor_exclusive": 1.0,
            "minimum_recent_six_month_daily_profit_factor_exclusive": 1.0,
            "exact_daily_frequency_gate": False,
        },
    }


def parent() -> pd.DataFrame:
    entries = pd.to_datetime(
        [
            "2025-01-02T00:00:00Z",
            "2025-01-02T00:15:00Z",
            "2025-01-02T00:30:00Z",
            "2025-01-02T00:45:00Z",
        ],
        utc=True,
    )
    return pd.DataFrame(
        {
            "entry_time_utc": entries,
            "eligible_date": ["2025-01-02"] * 4,
            "window": ["test"] * 4,
            "kraken_reported_side_imbalance_15m": [
                0.7,
                -0.4,
                0.2,
                -0.8,
            ],
            "binance_taker_imbalance_15m": [
                0.1,
                -0.2,
                -0.3,
                0.6,
            ],
        }
    )


def test_agreement_trades_and_disagreement_is_cash() -> None:
    decisions, census = build_selective_decisions(
        parent(), config(), enforce_frozen_census=False
    )
    assert decisions["flow_side"].tolist() == ["LONG", "SHORT"]
    assert len(decisions) == 2
    assert census["agreement_candidates"] == 2
    assert census["disagreement_points"] == 2
    assert census["candidate_count_distribution"] == {
        "0": 0,
        "1": 0,
        "2": 1,
        "3": 0,
        "4": 0,
    }


def test_no_daily_quota_or_exact_four_requirement() -> None:
    source = parent().iloc[:3].copy()
    source.loc[
        :,
        "binance_taker_imbalance_15m",
    ] = [0.1, -0.2, 0.3]
    decisions, census = build_selective_decisions(
        source, config(), enforce_frozen_census=False
    )
    assert len(decisions) == 3
    assert census["active_candidate_days"] == 1
    assert census["candidate_count_distribution"]["3"] == 1


def test_admission_does_not_require_four_trades_per_day() -> None:
    metrics = {
        "profit_factor": 1.2,
        "net_r": 1.0,
        "trades": 60,
    }
    strategy = {
        "window_pass": {"test": True},
        "overall_tickets": {"profit_factor": 1.2},
        "overall_daily_portfolio": {"max_drawdown_r": 2.0},
        "robustness": {
            "extra_half_pip_round_trip": metrics,
            "top_5_percent_winners_removed": {"net_r": 0.5},
        },
        "recent_six_months": {
            "tickets": metrics,
            "daily_portfolio": {"profit_factor": 1.1},
        },
    }
    oracle = {
        "overall": {
            "exact_precision": 0.25,
            "tolerant_precision": 0.45,
        }
    }
    admitted, checks = admission(strategy, oracle, config())
    assert admitted
    assert checks["frequency_not_a_gate"]

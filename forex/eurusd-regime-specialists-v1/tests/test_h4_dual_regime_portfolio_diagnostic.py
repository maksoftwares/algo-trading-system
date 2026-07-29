from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eurusd_regime_specialists.h4_dual_regime_portfolio_diagnostic import (
    apply_portfolio_weight,
    apply_weighted_cost,
    circular_calendar_month_bootstrap,
    concurrency_audit,
)


def _trades() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "entry_time_utc": pd.to_datetime(
                ["2026-01-05T07:00Z", "2026-01-05T08:00Z"], utc=True
            ),
            "exit_time_utc": pd.to_datetime(
                ["2026-01-05T09:00Z", "2026-01-05T10:00Z"], utc=True
            ),
            "stop_pips": [10.0, 20.0],
            "r": [1.0, -1.0],
            "stress_r": [0.95, -1.05],
            "pnl_usd_001_lot": [1.0, -2.0],
        }
    )


def test_weight_and_cost_scale_position_risk_consistently() -> None:
    weighted = apply_portfolio_weight(_trades(), 0.5)
    assert weighted["r"].tolist() == [0.5, -0.5]
    stressed = apply_weighted_cost(weighted, 1.0)
    assert stressed["r"].tolist() == [0.45, -0.525]
    assert stressed["pnl_usd_001_lot"].tolist() == [0.45, -1.05]


def test_concurrency_reports_positions_and_weighted_risk() -> None:
    weighted = apply_portfolio_weight(_trades(), 0.5)
    result = concurrency_audit(weighted)
    assert result["maximum_concurrent_positions"] == 2
    assert result["maximum_concurrent_initial_risk_units"] == 1.0


def test_calendar_bootstrap_is_deterministic() -> None:
    trades = apply_portfolio_weight(_trades(), 1.0)
    args = {
        "start": pd.Timestamp("2026-01-01T00:00Z"),
        "end": pd.Timestamp("2026-04-01T00:00Z"),
        "samples": 100,
        "block_months": 2,
        "seed": 11,
        "lower_quantile": 0.05,
    }
    assert circular_calendar_month_bootstrap(
        trades, **args
    ) == circular_calendar_month_bootstrap(trades, **args)

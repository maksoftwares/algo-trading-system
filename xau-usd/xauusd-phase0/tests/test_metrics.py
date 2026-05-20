from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from phase0.data_contracts import Trade
from phase0.metrics import (
    REQUIRED_PER_CELL_METRICS,
    add_cost_sensitivity_ratios,
    metrics_row,
    monthly_metrics,
)


def test_metrics_row_includes_required_fields():
    trades = [
        _trade("2020-01-10T00:00:00Z", 100.0, 2.0),
        _trade("2020-03-10T00:00:00Z", -50.0, -1.0),
        _trade("2020-03-20T00:00:00Z", 25.0, 0.5),
    ]

    row = metrics_row(
        trades,
        starting_equity=10000.0,
        period_start="2020-01-01T00:00:00Z",
        period_end="2020-03-31T23:59:59Z",
        extra={
            "cell_id": 1,
            "time_window": "2020-Q1",
            "tick_source": "capital_com",
            "cost_model": "median",
            "expert": "trend_pullback",
            "symbol": "XAUUSD",
        },
    )

    for column in REQUIRED_PER_CELL_METRICS:
        assert column in row
    assert row["trade_count"] == 3
    assert row["profit_factor"] == pytest.approx(2.5)
    assert row["total_pnl_usd"] == pytest.approx(75.0)
    assert row["avg_trade_R"] == pytest.approx(0.5)
    assert row["median_trade_R"] == pytest.approx(0.5)
    assert row["max_consecutive_zero_trade_months"] == 1
    assert row["losing_month_pct"] == pytest.approx(100.0 / 3.0)


def test_monthly_metrics_with_empty_months():
    trades = [_trade("2020-01-10T00:00:00Z", 100.0, 1.0)]

    monthly = monthly_metrics(trades, "2020-01-01T00:00:00Z", "2020-04-30T23:59:59Z")

    assert monthly["best_month_usd"] == pytest.approx(100.0)
    assert monthly["worst_month_usd"] == pytest.approx(0.0)
    assert monthly["max_consecutive_zero_trade_months"] == 3


def test_add_cost_sensitivity_ratios():
    matrix = pd.DataFrame(
        {
            "cell_id": [1, 2, 3, 4, 5, 6, 7, 8, 9],
            "profit_factor": [2.0, 1.5, 1.0, 4.0, 2.0, 1.0, 1.0, 1.0, 1.0],
        }
    )

    result = add_cost_sensitivity_ratios(matrix)

    assert result.loc[result["cell_id"] == 3, "p95_to_best_pf_ratio"].iloc[0] == pytest.approx(0.5)
    assert result.loc[result["cell_id"] == 6, "p95_to_best_pf_ratio"].iloc[0] == pytest.approx(0.25)


def _trade(exit_time: str, net_pnl: float, r_value: float) -> Trade:
    timestamp = datetime.fromisoformat(exit_time.replace("Z", "+00:00"))
    return Trade(
        expert="trend_pullback",
        symbol="XAUUSD",
        direction="LONG",
        entry_time_utc=datetime(2020, 1, 1, tzinfo=timezone.utc),
        exit_time_utc=timestamp,
        entry_price=100.0,
        exit_price=101.0,
        stop_loss=99.0,
        take_profit=101.0,
        lots=0.1,
        gross_pnl_usd=net_pnl,
        costs_usd=0.0,
        net_pnl_usd=net_pnl,
        r_multiple=r_value,
        exit_reason="take_profit" if net_pnl > 0 else "stop_loss",
    )

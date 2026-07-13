from __future__ import annotations

import pandas as pd

from metrics import floating_drawdown, profit_factor, rolling_results, standalone_family_gate, summary


def _trades() -> pd.DataFrame:
    return pd.DataFrame({
        "entry_time": pd.to_datetime(["2020-01-15", "2020-03-15", "2020-03-16"], utc=True),
        "net_r": [2.0, -1.0, -0.5],
        "stress_net_r": [1.5, -1.2, -0.8],
        "mae_r": [0.5, 1.5, 0.8],
    })


def test_profit_factor_and_floating_drawdown_use_ordered_trade_path() -> None:
    trades = _trades()
    assert profit_factor(trades["net_r"]) == 2.0 / 1.5
    assert floating_drawdown(trades) == 1.8


def test_summary_counts_zero_trade_calendar_months_and_latest_windows() -> None:
    result = summary(
        _trades(),
        pd.Timestamp("2020-01-01", tz="UTC"),
        pd.Timestamp("2021-01-01", tz="UTC"),
    )
    assert result["trades"] == 3
    assert result["wins"] == 1
    assert result["losses"] == 2
    assert result["median_trades_per_calendar_month"] == 0.0
    assert result["latest_12_month_trades"] == 3
    assert result["latest_6_month_trades"] == 0


def test_family_is_not_admitted_when_any_standalone_gate_fails() -> None:
    metrics = {
        "trades": 250,
        "profit_factor": 1.20,
        "expectancy_r": 0.08,
        "stress_profit_factor": 1.05,
        "stress_expectancy_r": 0.01,
        "stress_net_r": 2.0,
        "floating_drawdown_r": 16.0,
        "top_ten_winner_share": 0.30,
    }
    result = standalone_family_gate(metrics)
    assert result["passed"] is False
    assert result["checks"]["floating_dd_lte_15"] is False


def test_empty_unadmitted_portfolio_still_emits_all_rolling_windows() -> None:
    result = rolling_results(
        pd.DataFrame(),
        pd.Timestamp("2020-01-01", tz="UTC"),
        pd.Timestamp("2022-01-01", tz="UTC"),
    )
    assert set(result["window_months"]) == {12, 24}
    assert (result["trades"] == 0).all()

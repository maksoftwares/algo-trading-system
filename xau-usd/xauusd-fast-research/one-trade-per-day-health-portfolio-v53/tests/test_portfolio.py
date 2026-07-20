import numpy as np
import pandas as pd

from portfolio import (
    causal_shadow_health_gate,
    govern_addons,
    profit_factor,
    window_metrics,
)


def _trades(values: list[float]) -> pd.DataFrame:
    signal = pd.date_range("2020-01-01", periods=len(values), freq="2D", tz="UTC")
    return pd.DataFrame(
        {
            "trade_id": [f"T{index}" for index in range(len(values))],
            "signal_time": signal,
            "entry_time": signal,
            "exit_time": signal + pd.Timedelta(days=1),
            "pnl_usd": values,
        }
    )


def test_health_gate_uses_only_strictly_completed_shadow_trades() -> None:
    trades = _trades([2.0, -1.0, 2.0, -1.0, 3.0])
    accepted = causal_shadow_health_gate(trades, 3, 1.0)
    assert accepted["trade_id"].tolist() == ["T3"]
    assert accepted["shadow_completed_count"].eq(3).all()


def test_health_gate_rejects_negative_trailing_net() -> None:
    trades = _trades([-2.0, 1.0, -2.0, 10.0])
    accepted = causal_shadow_health_gate(trades, 3, 1.0)
    assert accepted.empty


def test_governor_suspends_addons_after_core_drawdown() -> None:
    core = pd.DataFrame(
        {
            "trade_id": ["C1", "C2"],
            "entry_time": pd.to_datetime(["2020-01-01", "2020-01-02"], utc=True),
            "exit_time": pd.to_datetime(["2020-01-02", "2020-01-03"], utc=True),
            "pnl_usd": [100.0, -250.0],
        }
    )
    candidates = pd.DataFrame(
        {
            "trade_id": ["A1"],
            "sleeve_id": ["S"],
            "signal_time": pd.to_datetime(["2020-01-04"], utc=True),
            "entry_time": pd.to_datetime(["2020-01-04"], utc=True),
            "exit_time": pd.to_datetime(["2020-01-05"], utc=True),
            "direction": ["LONG"],
            "pnl_usd": [10.0],
            "risk_usd": [10.0],
        }
    )
    account = {
        "maximum_addon_open_positions": 2,
        "maximum_addon_concurrent_initial_risk_usd": 45.0,
        "maximum_addon_entries_per_utc_date": 2,
        "drawdown_suspend_usd": 240.0,
        "drawdown_resume_usd": 200.0,
    }
    accepted, decisions = govern_addons(candidates, core, account)
    assert accepted.empty
    assert decisions.loc[0, "decision_reason"] == "ACCOUNT_DRAWDOWN_SUSPENDED"


def test_window_metrics_reports_closed_drawdown_and_winner_removal() -> None:
    trades = _trades([10.0, -4.0, -3.0, 2.0])
    value = window_metrics(
        trades,
        pd.Timestamp("2020-01-01", tz="UTC"),
        pd.Timestamp("2020-02-01", tz="UTC"),
        1,
    )
    assert value["closed_drawdown_usd"] == 7.0
    assert value["winner_removed_net_usd"] == -5.0
    assert np.isclose(profit_factor(trades["pnl_usd"]), 12.0 / 7.0)

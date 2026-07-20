from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.research import (
    drawdown,
    evaluate_gates,
    overlap_metrics,
    price_regime_features,
    profit_factor,
)


def test_drawdown_includes_zero_equity_baseline() -> None:
    assert drawdown(pd.Series([-5.0, 2.0, -4.0])) == pytest.approx(7.0)


def test_profit_factor_uses_dollar_pnl() -> None:
    assert profit_factor(pd.Series([4.0, -2.0, 2.0, -1.0])) == pytest.approx(2.0)


def test_price_regime_features_exclude_micro_and_identity_columns() -> None:
    features = price_regime_features()
    assert "dir_return_4h_atr" in features
    assert "action_target_r" in features
    assert "dir_tick_imbalance_5m" not in features
    assert "event_id" not in features
    assert "stress_net_r" not in features
    assert "exit_time" not in features


def test_overlap_metrics_counts_cross_lane_overlap() -> None:
    frame = pd.DataFrame(
        {
            "trade_id": ["core", "addon"],
            "lane": ["CORE", "ADDON"],
            "entry_time": pd.to_datetime(
                ["2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z"], utc=True
            ),
            "exit_time": pd.to_datetime(
                ["2026-01-01T02:00:00Z", "2026-01-01T03:00:00Z"], utc=True
            ),
            "risk_usd": [5.0, 3.0],
        }
    )
    value = overlap_metrics(frame)
    assert value["maximum_concurrent_positions"] == 2
    assert value["maximum_open_initial_risk_dollars"] == pytest.approx(8.0)
    assert value["addon_entries_while_core_open"] == 1


def test_gate_requires_one_trade_per_weekday_and_buffered_drawdown() -> None:
    addon = {
        "trades": 300,
        "trades_per_weekday": 0.7,
        "profit_factor": 1.2,
        "net_pnl_dollars": 20.0,
        "closed_drawdown_dollars": 100.0,
        "maximum_risk_usd": 8.0,
        "top_winners_removed_net_dollars": 1.0,
    }
    combined = {
        "trades": 500,
        "trades_per_weekday": 1.01,
        "profit_factor": 1.6,
        "net_pnl_dollars": 100.0,
        "positive_month_share": 0.6,
        "first_half_net_dollars": 40.0,
        "second_half_net_dollars": 60.0,
        "top_winners_removed_net_dollars": 10.0,
        "closed_drawdown_dollars": 300.0,
    }
    gate = {
        "minimum_addon_trades": 250,
        "minimum_addon_trades_per_weekday": 0.6,
        "minimum_addon_profit_factor": 1.1,
        "minimum_addon_net_dollars": 0.0,
        "maximum_addon_closed_drawdown_dollars": 175.0,
        "minimum_combined_trades": 450,
        "minimum_combined_trades_per_weekday": 1.0,
        "minimum_combined_profit_factor": 1.5,
        "minimum_combined_net_dollars": 0.0,
        "minimum_combined_positive_month_share": 0.55,
        "minimum_each_half_combined_net_dollars": 0.0,
    }
    account = {
        "equity_dollars": 3000.0,
        "maximum_equity_drawdown_fraction": 0.15,
        "capital_safety_buffer_multiple": 1.25,
        "maximum_combined_closed_drawdown_dollars": 300.0,
        "maximum_addon_risk_usd": 8.165487,
    }
    passed, checks = evaluate_gates(addon, combined, gate, account)
    assert passed is True
    assert checks["minimum_combined_frequency"] is True
    combined["trades_per_weekday"] = 0.99
    passed, checks = evaluate_gates(addon, combined, gate, account)
    assert passed is False
    assert checks["minimum_combined_frequency"] is False


def test_config_freezes_account_feasibility_and_no_execution() -> None:
    root = Path(__file__).resolve().parents[1]
    config = json.loads(
        (root / "config" / "one_trade_per_day_portfolio_v51.json").read_text(
            encoding="utf-8"
        )
    )
    assert config["addon_policy"]["require_current_account_feasible"] is True
    assert config["addon_policy"]["maximum_concurrent_positions"] == 1
    assert config["gates"]["final_exam"]["minimum_combined_trades_per_weekday"] == 1.0
    assert config["research_controls"]["broker_action_authorized"] is False


def test_preregistration_disclaims_pristine_holdout_and_floating_drawdown() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "PREREGISTRATION.md").read_text(encoding="utf-8")
    assert "pristine-holdout" in text
    assert "floating equity drawdown" in text

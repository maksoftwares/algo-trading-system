from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from phase0.config import load_project_config
from phase0.data_contracts import TradePlan
from phase0.execution import ExecutionError, find_entry_fill, load_cost_model, simulate_trade


def test_market_entry_uses_next_bar_open_ask(project_root):
    config = load_project_config(project_root)
    bars = _execution_bars()
    model = load_cost_model(config, "XAUUSD", "capital_com", "median")
    plan = _market_plan("LONG")

    fill = find_entry_fill(bars, plan, model)

    assert fill.time_utc == pd.Timestamp("2016-01-04T10:00:00Z")
    assert fill.price == pytest.approx(100.10)


def test_long_trade_take_profit(project_root):
    config = load_project_config(project_root)
    trade = simulate_trade(
        config,
        bars=_execution_bars(),
        plan=_market_plan("LONG"),
        broker="capital_com",
        cost_model_name="median",
        current_equity=10000.0,
        risk_per_trade_pct=0.005,
    )

    assert trade.entry_price == pytest.approx(100.10)
    assert trade.exit_price == pytest.approx(101.20)
    assert trade.exit_reason == "take_profit"
    assert trade.lots == pytest.approx(0.45)
    assert trade.net_pnl_usd > 0
    assert trade.metadata["ambiguous_exit"] is False


def test_ambiguous_same_bar_exit_uses_stop_loss(project_root):
    config = load_project_config(project_root)
    bars = _execution_bars()
    bars.loc[1, "low"] = 98.0
    bars.loc[1, "high"] = 102.0

    trade = simulate_trade(
        config,
        bars=bars,
        plan=_market_plan("LONG"),
        broker="capital_com",
        cost_model_name="median",
        current_equity=10000.0,
        risk_per_trade_pct=0.005,
    )

    assert trade.exit_reason == "stop_loss"
    assert trade.exit_price == pytest.approx(99.0)
    assert trade.metadata["ambiguous_exit"] is True


def test_short_pending_stop_trade(project_root):
    config = load_project_config(project_root)
    bars = _execution_bars()
    plan = TradePlan(
        expert="breakout_retest",
        symbol="XAUUSD",
        direction="SHORT",
        signal_time_utc=datetime(2016, 1, 4, 10, 0, tzinfo=timezone.utc),
        entry_type="STOP",
        entry_price=99.0,
        stop_loss=100.0,
        take_profit=98.0,
        invalidation_level=100.0,
        risk_reward=1.0,
        reason_code="TEST_SHORT_STOP",
    )

    trade = simulate_trade(
        config,
        bars=bars,
        plan=plan,
        broker="capital_com",
        cost_model_name="median",
        current_equity=10000.0,
        risk_per_trade_pct=0.005,
    )

    assert trade.entry_price == pytest.approx(99.0)
    assert trade.exit_reason == "take_profit"
    assert trade.exit_price == pytest.approx(98.0)
    assert trade.net_pnl_usd > 0


def test_pending_order_expiry_blocks_late_fill(project_root):
    config = load_project_config(project_root)
    bars = _execution_bars()
    plan = TradePlan(
        expert="breakout_retest",
        symbol="XAUUSD",
        direction="SHORT",
        signal_time_utc=datetime(2016, 1, 4, 10, 0, tzinfo=timezone.utc),
        entry_type="STOP",
        entry_price=99.0,
        stop_loss=100.0,
        take_profit=98.0,
        invalidation_level=100.0,
        risk_reward=1.0,
        reason_code="TEST_SHORT_STOP",
        metadata={"expires_after_bars": 2},
    )

    with pytest.raises(ExecutionError, match="expired after 2 bar"):
        simulate_trade(
            config,
            bars=bars,
            plan=plan,
            broker="capital_com",
            cost_model_name="median",
            current_equity=10000.0,
            risk_per_trade_pct=0.005,
        )


def test_end_of_period_close(project_root):
    config = load_project_config(project_root)
    bars = _execution_bars()
    plan = TradePlan(
        expert="trend_pullback",
        symbol="XAUUSD",
        direction="LONG",
        signal_time_utc=datetime(2016, 1, 4, 10, 0, tzinfo=timezone.utc),
        entry_type="MARKET",
        entry_price=None,
        stop_loss=90.0,
        take_profit=120.0,
        invalidation_level=90.0,
        risk_reward=2.0,
        reason_code="NO_EXIT",
    )

    trade = simulate_trade(
        config,
        bars=bars,
        plan=plan,
        broker="capital_com",
        cost_model_name="median",
        current_equity=10000.0,
        risk_per_trade_pct=0.005,
    )

    assert trade.exit_reason == "end_of_test_period"
    assert trade.exit_time_utc == pd.Timestamp("2016-01-04T10:20:00Z")


def test_max_holding_bars_exits_at_time_stop(project_root):
    config = load_project_config(project_root)
    plan = TradePlan(
        expert="trend_pullback",
        symbol="XAUUSD",
        direction="LONG",
        signal_time_utc=datetime(2016, 1, 4, 10, 0, tzinfo=timezone.utc),
        entry_type="MARKET",
        entry_price=None,
        stop_loss=90.0,
        take_profit=120.0,
        invalidation_level=90.0,
        risk_reward=2.0,
        reason_code="TIME_STOP",
        metadata={"max_holding_bars": 2},
    )

    trade = simulate_trade(
        config,
        bars=_execution_bars(),
        plan=plan,
        broker="capital_com",
        cost_model_name="median",
        current_equity=10000.0,
        risk_per_trade_pct=0.005,
    )

    assert trade.exit_reason == "time_stop"
    assert trade.exit_time_utc == pd.Timestamp("2016-01-04T10:10:00Z")


def _market_plan(direction: str) -> TradePlan:
    return TradePlan(
        expert="trend_pullback",
        symbol="XAUUSD",
        direction=direction,
        signal_time_utc=datetime(2016, 1, 4, 10, 0, tzinfo=timezone.utc),
        entry_type="MARKET",
        entry_price=None,
        stop_loss=99.0 if direction == "LONG" else 101.0,
        take_profit=101.2 if direction == "LONG" else 99.0,
        invalidation_level=99.0,
        risk_reward=1.0,
        reason_code="TEST_MARKET",
    )


def _execution_bars() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp_utc": [
                "2016-01-04T10:05:00Z",
                "2016-01-04T10:10:00Z",
                "2016-01-04T10:15:00Z",
                "2016-01-04T10:20:00Z",
            ],
            "bar_start_utc": [
                "2016-01-04T10:00:00Z",
                "2016-01-04T10:05:00Z",
                "2016-01-04T10:10:00Z",
                "2016-01-04T10:15:00Z",
            ],
            "open": [100.0, 100.1, 99.5, 98.5],
            "high": [100.2, 101.3, 99.7, 98.7],
            "low": [99.8, 99.4, 98.0, 97.8],
            "close": [100.1, 99.6, 98.6, 98.2],
            "mid_open": [100.0, 100.1, 99.5, 98.5],
            "mid_close": [100.1, 99.6, 98.6, 98.2],
            "bid_open": [99.9, 100.0, 99.4, 98.4],
            "ask_open": [100.1, 100.2, 99.6, 98.6],
            "bid_close": [100.0, 99.5, 98.5, 98.1],
            "ask_close": [100.2, 99.7, 98.7, 98.3],
        }
    )

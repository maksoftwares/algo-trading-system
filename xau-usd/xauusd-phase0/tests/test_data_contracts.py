from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from phase0.data_contracts import Signal, TradePlan
from phase0.trades import TRADE_COLUMNS, trades_to_dataframe


def test_signal_is_frozen():
    signal = Signal(
        expert="trend_pullback",
        timestamp_utc=datetime(2025, 1, 1, tzinfo=timezone.utc),
        symbol="XAUUSD",
        direction="LONG",
        reason_code="TEST",
    )

    with pytest.raises(FrozenInstanceError):
        signal.symbol = "EURUSD"


def test_trade_plan_accepts_market_without_entry_price():
    plan = TradePlan(
        expert="trend_pullback",
        symbol="XAUUSD",
        direction="LONG",
        signal_time_utc=datetime(2025, 1, 1, tzinfo=timezone.utc),
        entry_type="MARKET",
        entry_price=None,
        stop_loss=100.0,
        take_profit=103.0,
        invalidation_level=99.5,
        risk_reward=1.5,
        reason_code="TEST",
    )

    assert plan.entry_price is None
    assert plan.risk_reward == 1.5


def test_empty_trade_dataframe_keeps_stable_schema():
    frame = trades_to_dataframe([])

    assert list(frame.columns) == list(TRADE_COLUMNS)
    assert frame.empty

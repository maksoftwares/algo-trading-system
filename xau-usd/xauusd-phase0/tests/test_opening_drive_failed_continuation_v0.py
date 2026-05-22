from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.opening_drive_failed_continuation_v0 import (
    OpeningDriveFailedContinuationV0Strategy,
)


def test_opening_drive_failed_continuation_v0_generates_short_market_plan():
    strategy = OpeningDriveFailedContinuationV0Strategy()
    context = _opening_drive_context("SHORT")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "SHORT"
    assert signals[-1].metadata["opening_drive_window_utc"] == "13:30-14:00"
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_opening_drive_failed_continuation_v0_generates_long_market_plan():
    strategy = OpeningDriveFailedContinuationV0Strategy()
    context = _opening_drive_context("LONG")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_opening_drive_failed_continuation_v0_ignores_before_failure_window():
    strategy = OpeningDriveFailedContinuationV0Strategy()
    context = _opening_drive_context("SHORT")
    context["M5"]["bar_start_utc"] = context["M5"]["bar_start_utc"] - pd.Timedelta(hours=2)
    context["M5"]["timestamp_utc"] = context["M5"]["timestamp_utc"] - pd.Timedelta(hours=2)

    assert strategy.generate_signals(context) == []


def _opening_drive_context(direction: str) -> dict:
    m5_times = pd.date_range("2024-10-01T13:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.2] * 120,
            "low": [99.8] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    if direction == "SHORT":
        bars = {
            6: (100.00, 100.45, 99.95, 100.35),
            7: (100.35, 100.85, 100.30, 100.75),
            8: (100.75, 101.10, 100.70, 101.00),
            9: (101.00, 101.20, 100.92, 101.05),
            10: (101.05, 101.25, 100.95, 101.10),
            11: (101.10, 101.30, 101.00, 101.15),
            16: (101.55, 101.62, 100.80, 100.95),
        }
    else:
        bars = {
            6: (100.00, 100.05, 99.55, 99.65),
            7: (99.65, 99.70, 99.15, 99.25),
            8: (99.25, 99.30, 98.90, 99.00),
            9: (99.00, 99.08, 98.80, 98.95),
            10: (98.95, 99.05, 98.75, 98.90),
            11: (98.90, 99.00, 98.70, 98.85),
            16: (98.45, 99.20, 98.38, 99.05),
        }
    for idx, values in bars.items():
        m5.loc[idx, ["open", "high", "low", "close"]] = values
        m5.loc[idx, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
            values[0],
            values[3],
            values[0] - 0.1,
            values[0] + 0.1,
            values[3] - 0.1,
            values[3] + 0.1,
        ]
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T13:15:00Z", periods=50, freq="15min"),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T10:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}

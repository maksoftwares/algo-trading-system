from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.squeeze_breakout_long_v0 import SqueezeBreakoutLongV0Strategy


def test_squeeze_breakout_long_v0_generates_long_market_plan():
    strategy = SqueezeBreakoutLongV0Strategy()
    context = _squeeze_context()

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["compression_high"] == pytest.approx(100.1)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_squeeze_breakout_long_v0_ignores_when_h1_context_fails():
    strategy = SqueezeBreakoutLongV0Strategy()
    context = _squeeze_context()
    context["H1"]["close"] = 98.0

    assert strategy.generate_signals(context) == []


def _squeeze_context() -> dict:
    m15_times = pd.date_range("2024-01-01T00:15:00Z", periods=140, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 140,
            "high": [102.0] * 120 + [100.1] * 20,
            "low": [98.0] * 120 + [99.9] * 20,
            "close": [100.0] * 140,
        }
    )

    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=430, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "open": [100.0] * 430,
            "high": [100.15] * 430,
            "low": [99.95] * 430,
            "close": [100.0] * 430,
            "atr14": [1.0] * 409 + [0.4] * 21,
        }
    )
    m5.loc[410, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.7, 99.95, 100.55, 0.4]

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T01:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [99.0] * 40,
            "close": [101.0] * 40,
            "ema50": [100.0] * 40,
            "ema50_slope12": [0.1] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}

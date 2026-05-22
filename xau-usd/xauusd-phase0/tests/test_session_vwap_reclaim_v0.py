from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.session_vwap_reclaim_v0 import SessionVwapReclaimV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_session_vwap_reclaim_v0_generates_long_market_plan():
    strategy = SessionVwapReclaimV0Strategy()
    context = synthetic_context_for_expert("session_vwap_reclaim_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["session_vwap"] == pytest.approx(100.0, abs=0.05)
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_session_vwap_reclaim_v0_ignores_without_vwap_reclaim():
    strategy = SessionVwapReclaimV0Strategy()
    context = synthetic_context_for_expert("session_vwap_reclaim_v0")
    m5 = context["M5"].copy()
    m5.loc[50, "close"] = 99.95
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_session_vwap_reclaim_v0_ignores_without_sweep_distance():
    strategy = SessionVwapReclaimV0Strategy()
    context = synthetic_context_for_expert("session_vwap_reclaim_v0")
    m5 = context["M5"].copy()
    m5.loc[50, "low"] = 99.70
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_session_vwap_reclaim_v0_uses_volume_when_available():
    strategy = SessionVwapReclaimV0Strategy()
    context = synthetic_context_for_expert("session_vwap_reclaim_v0")
    m5 = context["M5"].copy()
    m5["tick_volume"] = 1
    m5.loc[49, "tick_volume"] = 100
    context["M5"] = m5

    signals = strategy.generate_signals(context)

    assert signals


def test_session_vwap_reclaim_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("session_vwap_reclaim_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

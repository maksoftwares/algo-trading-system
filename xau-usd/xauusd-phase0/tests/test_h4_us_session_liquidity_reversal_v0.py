from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h4_us_session_liquidity_reversal_v0_generates_short_market_plan():
    strategy = get_strategy("h4_us_session_liquidity_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_us_session_liquidity_reversal_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].expert == "h4_us_session_liquidity_reversal_v0"
    assert signals[-1].direction == "SHORT"
    assert signals[-1].metadata["sweep_direction"] == "UP"
    assert signals[-1].metadata["range_atr"] >= strategy.min_range_atr
    assert signals[-1].metadata["close_position"] <= strategy.close_back_fraction
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.35)
    assert plan.metadata["planned_time_stop_h4_bars"] == 12
    assert plan.metadata["max_holding_bars"] == 576


def test_h4_us_session_liquidity_reversal_v0_ignores_non_us_session_candle():
    strategy = get_strategy("h4_us_session_liquidity_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_us_session_liquidity_reversal_v0")
    h4 = context["H4"].copy()
    h4.loc[40, "timestamp_utc"] = pd.Timestamp("2024-05-07T12:00:00Z")
    context["H4"] = h4

    assert strategy.generate_signals(context) == []


def test_h4_us_session_liquidity_reversal_v0_ignores_without_close_back_inside():
    strategy = get_strategy("h4_us_session_liquidity_reversal_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h4_us_session_liquidity_reversal_v0")
    h4 = context["H4"].copy()
    h4.loc[40, ["open", "high", "low", "close"]] = [102.0, 105.0, 99.7, 103.8]
    context["H4"] = h4

    assert strategy.generate_signals(context) == []


def test_h4_us_session_liquidity_reversal_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("h4_us_session_liquidity_reversal_v0")

    assert pd.to_datetime(context["H4"]["timestamp_utc"], utc=True).is_monotonic_increasing
    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

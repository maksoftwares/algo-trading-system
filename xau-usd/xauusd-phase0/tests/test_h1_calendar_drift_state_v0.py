from __future__ import annotations

import pytest

from phase0.strategies.h1_calendar_drift_state_v0 import H1CalendarDriftStateV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_h1_calendar_drift_state_v0_generates_long_market_plan():
    strategy = H1CalendarDriftStateV0Strategy()
    context = synthetic_context_for_expert("h1_calendar_drift_state_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["calendar_drift_score"] >= strategy.score_threshold
    assert signals[-1].metadata["calendar_drift_mean_atr"] >= strategy.mean_threshold_atr
    assert signals[-1].metadata["calendar_bucket_observations"] >= strategy.min_bucket_observations
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.35)
    assert plan.metadata["max_holding_bars"] == 144


def test_h1_calendar_drift_state_v0_requires_bucket_history():
    strategy = H1CalendarDriftStateV0Strategy()
    context = synthetic_context_for_expert("h1_calendar_drift_state_v0")
    context["H1"] = context["H1"].iloc[: 7 * 24].copy()

    assert strategy.generate_signals(context) == []

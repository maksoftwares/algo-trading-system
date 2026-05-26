from __future__ import annotations

from phase0.macro_event_calendar import build_standard_us_macro_event_calendar
from phase0.strategies.registry import get_strategy
from phase0.synthetic import synthetic_context_for_expert


def test_macro_event_calendar_generates_standard_event_slots():
    calendar = build_standard_us_macro_event_calendar("2022-01-01", "2022-03-31")

    assert {"NFP_FIRST_FRIDAY", "CPI_SECOND_WEDNESDAY", "FOMC_THIRD_WEDNESDAY"}.issubset(
        set(calendar["event_type"])
    )
    assert calendar["timestamp_utc"].is_monotonic_increasing


def test_h1_macro_event_aftershock_synthetic_smoke():
    strategy = get_strategy("h1_macro_event_aftershock_v0", allow_research_candidate=True)
    context = synthetic_context_for_expert("h1_macro_event_aftershock_v0")

    signals = strategy.generate_signals(context)

    assert signals
    assert signals[-1].expert == "h1_macro_event_aftershock_v0"
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["event_move_atr"] >= strategy.min_event_move_atr

    plan = strategy.build_trade_plan(signals[-1], context)

    assert plan.entry_type == "MARKET"
    assert plan.stop_loss < signals[-1].metadata["estimated_entry_price"]
    assert plan.take_profit > signals[-1].metadata["estimated_entry_price"]
    assert plan.risk_reward == 1.35
    assert plan.metadata["planned_time_stop_h1_bars"] == 12

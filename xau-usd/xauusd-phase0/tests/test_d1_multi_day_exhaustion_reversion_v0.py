from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.d1_multi_day_exhaustion_reversion_v0 import (
    D1MultiDayExhaustionReversionV0Strategy,
)
from phase0.synthetic import synthetic_context_for_expert


def test_d1_multi_day_exhaustion_reversion_v0_generates_short_market_plan():
    strategy = D1MultiDayExhaustionReversionV0Strategy()
    context = synthetic_context_for_expert("d1_multi_day_exhaustion_reversion_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "SHORT"
    assert signals[-1].metadata["extension_direction"] == "UP"
    assert signals[-1].metadata["d1_momentum5"] > 0
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss > plan.metadata["estimated_entry_price"]
    assert plan.take_profit < plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.75)


def test_d1_multi_day_exhaustion_reversion_v0_ignores_without_d1_extension():
    strategy = D1MultiDayExhaustionReversionV0Strategy()
    context = synthetic_context_for_expert("d1_multi_day_exhaustion_reversion_v0")
    d1 = context["D1"].copy()
    d1["close"] = [100.0] * len(d1)
    d1["open"] = [100.0] * len(d1)
    d1["high"] = [101.0] * len(d1)
    d1["low"] = [99.0] * len(d1)
    context["D1"] = d1

    assert strategy.generate_signals(context) == []


def test_d1_multi_day_exhaustion_reversion_v0_ignores_without_h4_reversal():
    strategy = D1MultiDayExhaustionReversionV0Strategy()
    context = synthetic_context_for_expert("d1_multi_day_exhaustion_reversion_v0")
    h4 = context["H4"].copy()
    h4.loc[31, ["open", "high", "low", "close"]] = [130.0, 130.6, 129.4, 130.2]
    context["H4"] = h4

    assert strategy.generate_signals(context) == []


def test_d1_multi_day_exhaustion_reversion_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("d1_multi_day_exhaustion_reversion_v0")

    assert pd.to_datetime(context["D1"]["timestamp_utc"], utc=True).is_monotonic_increasing
    assert pd.to_datetime(context["H4"]["timestamp_utc"], utc=True).is_monotonic_increasing

from __future__ import annotations

import pytest
import pandas as pd

from phase0.strategies.swing_breakout_retest_v0 import SwingBreakoutRetestV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_swing_breakout_retest_v0_generates_stop_plan_from_swing_level():
    strategy = SwingBreakoutRetestV0Strategy()
    context = synthetic_context_for_expert("swing_breakout_retest_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["level_kind"] == "latest_swing_high"
    assert signals[-1].metadata["level_price"] == pytest.approx(100.0)
    assert plan.entry_type == "STOP"
    assert plan.entry_price is not None
    assert plan.stop_loss < plan.entry_price
    assert plan.take_profit > plan.entry_price
    assert plan.risk_reward == pytest.approx(1.5)


def test_swing_breakout_retest_v0_ignores_non_swing_levels():
    strategy = SwingBreakoutRetestV0Strategy()
    context = synthetic_context_for_expert("swing_breakout_retest_v0")
    m5 = context["M5"].copy()
    m5["latest_swing_high"] = [pd.NA] * len(m5)
    m5["latest_swing_high_time_utc"] = [None] * len(m5)
    context["M5"] = m5

    assert strategy.generate_signals(context) == []

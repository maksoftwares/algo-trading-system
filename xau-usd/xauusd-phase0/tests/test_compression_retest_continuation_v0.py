from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.compression_retest_continuation_v0 import CompressionRetestContinuationV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_compression_retest_continuation_v0_generates_long_market_plan():
    strategy = CompressionRetestContinuationV0Strategy()
    context = synthetic_context_for_expert("compression_retest_continuation_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["compression_high"] == pytest.approx(100.10)
    assert signals[-1].metadata["breakout_index"] == 410
    assert signals[-1].metadata["retest_index"] == 413
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.5)


def test_compression_retest_continuation_v0_ignores_without_retest():
    strategy = CompressionRetestContinuationV0Strategy()
    context = synthetic_context_for_expert("compression_retest_continuation_v0")
    m5 = context["M5"].copy()
    m5.loc[413, "low"] = 100.40
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_compression_retest_continuation_v0_ignores_without_confirmation():
    strategy = CompressionRetestContinuationV0Strategy()
    context = synthetic_context_for_expert("compression_retest_continuation_v0")
    m5 = context["M5"].copy()
    m5.loc[415, ["open", "close"]] = [100.60, 100.20]
    context["M5"] = m5

    assert strategy.generate_signals(context) == []


def test_compression_retest_continuation_v0_ignores_without_compression():
    strategy = CompressionRetestContinuationV0Strategy()
    context = synthetic_context_for_expert("compression_retest_continuation_v0")
    m15 = context["M15"].copy()
    m15.loc[130:, "high"] = 102.0
    m15.loc[130:, "low"] = 98.0
    context["M15"] = m15

    assert strategy.generate_signals(context) == []


def test_compression_retest_continuation_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("compression_retest_continuation_v0")

    assert pd.to_datetime(context["M5"]["timestamp_utc"], utc=True).is_monotonic_increasing

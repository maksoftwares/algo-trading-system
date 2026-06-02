from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.h4_d1_contraction_trend_continuation_v0 import (
    H4D1ContractionTrendContinuationV0Strategy,
)
from phase0.synthetic import synthetic_context_for_expert


def test_h4_d1_contraction_trend_continuation_v0_generates_long_market_plan():
    strategy = H4D1ContractionTrendContinuationV0Strategy()
    context = synthetic_context_for_expert("h4_d1_contraction_trend_continuation_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["d1_atr14"] <= signals[-1].metadata["d1_prior60_atr40"]
    assert signals[-1].metadata["d1_range3_width"] < signals[-1].metadata["d1_prior40_range3_median"]
    assert signals[-1].metadata["h4_ema50_slope6"] > 0
    assert signals[-1].metadata["h4_adx14"] >= 18.0
    assert signals[-1].metadata["pullback_close_position"] >= 0.60
    assert signals[-1].metadata["stop_distance_points"] >= 325.0
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.70)


def test_h4_d1_contraction_trend_continuation_v0_ignores_without_d1_contraction():
    strategy = H4D1ContractionTrendContinuationV0Strategy()
    context = synthetic_context_for_expert("h4_d1_contraction_trend_continuation_v0")
    d1 = context["D1"].copy()
    for idx in range(60, len(d1)):
        d1.loc[idx, ["open", "high", "low", "close"]] = [100.0, 104.0, 96.0, 100.0]
    context["D1"] = d1

    assert strategy.generate_signals(context) == []


def test_h4_d1_contraction_trend_continuation_v0_ignores_without_h4_trend():
    strategy = H4D1ContractionTrendContinuationV0Strategy()
    context = synthetic_context_for_expert("h4_d1_contraction_trend_continuation_v0")
    h4 = context["H4"].copy()
    h4["close"] = [100.0] * len(h4)
    h4["open"] = [100.0] * len(h4)
    h4["high"] = [100.5] * len(h4)
    h4["low"] = [99.5] * len(h4)
    context["H4"] = h4

    assert strategy.generate_signals(context) == []


def test_h4_d1_contraction_trend_continuation_v0_ignores_tight_stops():
    strategy = H4D1ContractionTrendContinuationV0Strategy()
    context = synthetic_context_for_expert("h4_d1_contraction_trend_continuation_v0")
    h4 = context["H4"].copy()
    h4.loc[120, ["open", "high", "low", "close"]] = [109.0, 110.0, 108.8, 109.9]
    context["H4"] = h4

    assert strategy.generate_signals(context) == []


def test_h4_d1_contraction_trend_continuation_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("h4_d1_contraction_trend_continuation_v0")

    assert pd.to_datetime(context["D1"]["timestamp_utc"], utc=True).is_monotonic_increasing
    assert pd.to_datetime(context["H4"]["timestamp_utc"], utc=True).is_monotonic_increasing

from __future__ import annotations

import pandas as pd
import pytest

from phase0.strategies.d1_compression_h4_expansion_v0 import D1CompressionH4ExpansionV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_d1_compression_h4_expansion_v0_generates_long_market_plan():
    strategy = D1CompressionH4ExpansionV0Strategy()
    context = synthetic_context_for_expert("d1_compression_h4_expansion_v0")

    signals = strategy.generate_signals(context)
    plan = strategy.build_trade_plan(signals[-1], context)

    assert signals
    assert signals[-1].direction == "LONG"
    assert signals[-1].metadata["d1_compression_ratio"] < 0.85
    assert signals[-1].metadata["expansion_body_ratio"] > 0.55
    assert plan.entry_type == "MARKET"
    assert plan.entry_price is None
    assert plan.stop_loss < plan.metadata["estimated_entry_price"]
    assert plan.take_profit > plan.metadata["estimated_entry_price"]
    assert plan.risk_reward == pytest.approx(1.75)


def test_d1_compression_h4_expansion_v0_ignores_without_d1_compression():
    strategy = D1CompressionH4ExpansionV0Strategy()
    context = synthetic_context_for_expert("d1_compression_h4_expansion_v0")
    d1 = context["D1"].copy()
    for idx in range(60, len(d1)):
        d1.loc[idx, ["open", "high", "low", "close"]] = [100.0, 103.0, 97.0, 100.0]
    context["D1"] = d1

    assert strategy.generate_signals(context) == []


def test_d1_compression_h4_expansion_v0_ignores_without_h4_expansion():
    strategy = D1CompressionH4ExpansionV0Strategy()
    context = synthetic_context_for_expert("d1_compression_h4_expansion_v0")
    h4 = context["H4"].copy()
    h4.loc[33, ["open", "high", "low", "close"]] = [100.0, 100.5, 99.5, 100.2]
    context["H4"] = h4

    assert strategy.generate_signals(context) == []


def test_d1_compression_h4_expansion_v0_requires_h4_and_d1_context():
    strategy = D1CompressionH4ExpansionV0Strategy()
    context = synthetic_context_for_expert("d1_compression_h4_expansion_v0")
    del context["D1"]

    with pytest.raises(Exception):
        strategy.generate_signals(context)


def test_d1_compression_h4_expansion_v0_synthetic_timestamps_are_complete():
    context = synthetic_context_for_expert("d1_compression_h4_expansion_v0")

    assert pd.to_datetime(context["D1"]["timestamp_utc"], utc=True).is_monotonic_increasing
    assert pd.to_datetime(context["H4"]["timestamp_utc"], utc=True).is_monotonic_increasing

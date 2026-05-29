from __future__ import annotations

from phase0.strategies.quarter_round_retest_v0 import QuarterRoundRetestV0Strategy
from phase0.synthetic import synthetic_context_for_expert


def test_quarter_round_retest_smoke_signal() -> None:
    strategy = QuarterRoundRetestV0Strategy()

    signals = strategy.generate_signals(synthetic_context_for_expert("quarter_round_retest_v0"))

    assert len(signals) >= 1
    assert signals[0].expert == "quarter_round_retest_v0"
    assert signals[0].metadata["level_kind"].startswith("quarter_round_")


def test_quarter_round_retest_xau_increments_include_five() -> None:
    strategy = QuarterRoundRetestV0Strategy()

    assert strategy._increments_for_point_size(0.01) == (5.0, 10.0, 25.0, 50.0)
    assert strategy._increments_for_point_size(0.00001) == (0.0025, 0.005, 0.01, 0.025)

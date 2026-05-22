from __future__ import annotations

import pytest

from phase0.config import ConfigError
from phase0.strategies.registry import enabled_strategy_names, get_strategy


def test_research_candidate_is_explicit_only():
    for expert in (
        "compression_retest_continuation_v0",
        "emr_inactivity_long_v0",
        "extreme_activity_mean_reversion_v0",
        "london_fix_continuation_v0",
        "ny_failed_london_reversal_v0",
        "post_spike_short_v0",
        "squeeze_breakout_long_v0",
    ):
        with pytest.raises(ConfigError):
            enabled_strategy_names(expert)

        assert enabled_strategy_names(
            expert,
            allow_research_candidate=True,
        ) == [expert]
    assert "squeeze_breakout_long_v0" not in enabled_strategy_names(
        "all",
        allow_research_candidate=True,
    )
    for expert in (
        "compression_retest_continuation_v0",
        "emr_inactivity_long_v0",
        "extreme_activity_mean_reversion_v0",
        "london_fix_continuation_v0",
        "ny_failed_london_reversal_v0",
        "post_spike_short_v0",
    ):
        assert expert not in enabled_strategy_names(
            "all",
            allow_research_candidate=True,
        )


def test_research_strategy_requires_explicit_permission():
    for expert in (
        "compression_retest_continuation_v0",
        "emr_inactivity_long_v0",
        "extreme_activity_mean_reversion_v0",
        "london_fix_continuation_v0",
        "ny_failed_london_reversal_v0",
        "post_spike_short_v0",
        "squeeze_breakout_long_v0",
    ):
        with pytest.raises(ConfigError):
            get_strategy(expert)

        strategy = get_strategy(expert, allow_research_candidate=True)

        assert strategy.name == expert

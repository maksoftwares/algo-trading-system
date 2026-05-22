from __future__ import annotations

import pytest

from phase0.config import ConfigError
from phase0.strategies.registry import enabled_strategy_names, get_strategy


def test_research_candidate_is_explicit_only():
    with pytest.raises(ConfigError):
        enabled_strategy_names("squeeze_breakout_long_v0")

    assert enabled_strategy_names(
        "squeeze_breakout_long_v0",
        allow_research_candidate=True,
    ) == ["squeeze_breakout_long_v0"]
    assert "squeeze_breakout_long_v0" not in enabled_strategy_names(
        "all",
        allow_research_candidate=True,
    )


def test_research_strategy_requires_explicit_permission():
    with pytest.raises(ConfigError):
        get_strategy("squeeze_breakout_long_v0")

    strategy = get_strategy("squeeze_breakout_long_v0", allow_research_candidate=True)

    assert strategy.name == "squeeze_breakout_long_v0"

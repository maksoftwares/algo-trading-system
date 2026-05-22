from __future__ import annotations

from phase0.config import ConfigError
from phase0.strategies.base import StrategyBase
from phase0.strategies.breakout_retest import BreakoutRetestStrategy
from phase0.strategies.range_mr import RangeMeanReversionStrategy
from phase0.strategies.squeeze_breakout_long_v0 import SqueezeBreakoutLongV0Strategy
from phase0.strategies.trend_pullback import TrendPullbackStrategy


STRATEGY_CLASSES: dict[str, type[StrategyBase]] = {
    TrendPullbackStrategy.name: TrendPullbackStrategy,
    BreakoutRetestStrategy.name: BreakoutRetestStrategy,
    RangeMeanReversionStrategy.name: RangeMeanReversionStrategy,
}

RESEARCH_STRATEGY_CLASSES: dict[str, type[StrategyBase]] = {
    SqueezeBreakoutLongV0Strategy.name: SqueezeBreakoutLongV0Strategy,
}


def get_strategy(name: str) -> StrategyBase:
    if name not in STRATEGY_CLASSES:
        raise ConfigError(f"Unknown strategy {name!r}. Available: {', '.join(STRATEGY_CLASSES)}.")
    return STRATEGY_CLASSES[name]()


def get_research_strategy(name: str) -> StrategyBase:
    if name not in RESEARCH_STRATEGY_CLASSES:
        raise ConfigError(
            f"Unknown research strategy {name!r}. Available: {', '.join(RESEARCH_STRATEGY_CLASSES)}."
        )
    return RESEARCH_STRATEGY_CLASSES[name]()


def research_strategy_names() -> list[str]:
    return list(RESEARCH_STRATEGY_CLASSES)


def enabled_strategy_names(expert: str) -> list[str]:
    if expert == "all":
        return list(STRATEGY_CLASSES)
    if expert not in STRATEGY_CLASSES:
        raise ConfigError(f"Unknown expert {expert!r}.")
    return [expert]

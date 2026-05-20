from __future__ import annotations

from phase0.config import ConfigError
from phase0.strategies.base import StrategyBase
from phase0.strategies.breakout_retest import BreakoutRetestStrategy
from phase0.strategies.range_mr import RangeMeanReversionStrategy
from phase0.strategies.trend_pullback import TrendPullbackStrategy


STRATEGY_CLASSES: dict[str, type[StrategyBase]] = {
    TrendPullbackStrategy.name: TrendPullbackStrategy,
    BreakoutRetestStrategy.name: BreakoutRetestStrategy,
    RangeMeanReversionStrategy.name: RangeMeanReversionStrategy,
}


def get_strategy(name: str) -> StrategyBase:
    if name not in STRATEGY_CLASSES:
        raise ConfigError(f"Unknown strategy {name!r}. Available: {', '.join(STRATEGY_CLASSES)}.")
    return STRATEGY_CLASSES[name]()


def enabled_strategy_names(expert: str) -> list[str]:
    if expert == "all":
        return list(STRATEGY_CLASSES)
    if expert not in STRATEGY_CLASSES:
        raise ConfigError(f"Unknown expert {expert!r}.")
    return [expert]

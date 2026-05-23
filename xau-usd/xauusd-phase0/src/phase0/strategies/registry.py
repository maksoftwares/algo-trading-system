from __future__ import annotations

from phase0.config import ConfigError
from phase0.strategies.asia_range_london_breakout_v0 import AsiaRangeLondonBreakoutV0Strategy
from phase0.strategies.asia_range_london_failed_break_reversal_v0 import (
    AsiaRangeLondonFailedBreakReversalV0Strategy,
)
from phase0.strategies.base import StrategyBase
from phase0.strategies.breakout_retest import BreakoutRetestStrategy
from phase0.strategies.compression_retest_continuation_v0 import CompressionRetestContinuationV0Strategy
from phase0.strategies.d1_compression_h4_expansion_v0 import D1CompressionH4ExpansionV0Strategy
from phase0.strategies.d1_momentum_h4_pullback_v0 import D1MomentumH4PullbackV0Strategy
from phase0.strategies.d1_multi_day_exhaustion_reversion_v0 import D1MultiDayExhaustionReversionV0Strategy
from phase0.strategies.d1_volatility_expansion_reversal_v0 import D1VolatilityExpansionReversalV0Strategy
from phase0.strategies.daily_pivot_reclaim_v0 import DailyPivotReclaimV0Strategy
from phase0.strategies.emr_inactivity_long_v0 import EmrInactivityLongV0Strategy
from phase0.strategies.extreme_activity_mean_reversion_v0 import ExtremeActivityMeanReversionV0Strategy
from phase0.strategies.h4_d1_momentum_expansion_continuation_v0 import (
    H4D1MomentumExpansionContinuationV0Strategy,
)
from phase0.strategies.h4_inside_bar_d1_momentum_breakout_v0 import H4InsideBarD1MomentumBreakoutV0Strategy
from phase0.strategies.london_fix_continuation_v0 import LondonFixContinuationV0Strategy
from phase0.strategies.liquidity_sweep_continuation_v0 import LiquiditySweepContinuationV0Strategy
from phase0.strategies.liquidity_sweep_reversal_v0 import LiquiditySweepReversalV0Strategy
from phase0.strategies.m15_inside_bar_breakout_v0 import M15InsideBarBreakoutV0Strategy
from phase0.strategies.m5_impulse_continuation_v0 import M5ImpulseContinuationV0Strategy
from phase0.strategies.ny_failed_london_reversal_v0 import NyFailedLondonReversalV0Strategy
from phase0.strategies.ny_am_pullback_continuation_v0 import NyAmPullbackContinuationV0Strategy
from phase0.strategies.ny_london_overlap_compression_break_v0 import (
    NyLondonOverlapCompressionBreakV0Strategy,
)
from phase0.strategies.opening_drive_failed_continuation_v0 import (
    OpeningDriveFailedContinuationV0Strategy,
)
from phase0.strategies.post_spike_short_v0 import PostSpikeShortV0Strategy
from phase0.strategies.previous_day_extreme_retest_v0 import PreviousDayExtremeRetestV0Strategy
from phase0.strategies.range_mr import RangeMeanReversionStrategy
from phase0.strategies.round_number_retest_v0 import RoundNumberRetestV0Strategy
from phase0.strategies.session_vwap_reclaim_v0 import SessionVwapReclaimV0Strategy
from phase0.strategies.session_extreme_retest_v0 import SessionExtremeRetestV0Strategy
from phase0.strategies.squeeze_breakout_long_v0 import SqueezeBreakoutLongV0Strategy
from phase0.strategies.swing_breakout_retest_v0 import SwingBreakoutRetestV0Strategy
from phase0.strategies.symbol_normalized_round_retest_v0 import SymbolNormalizedRoundRetestV0Strategy
from phase0.strategies.symbol_round_sweep_reversal_v0 import SymbolRoundSweepReversalV0Strategy
from phase0.strategies.trend_pullback import TrendPullbackStrategy
from phase0.strategies.w1_d1_momentum_continuation_v0 import W1D1MomentumContinuationV0Strategy
from phase0.strategies.weekly_level_reclaim_v0 import WeeklyLevelReclaimV0Strategy


STRATEGY_CLASSES: dict[str, type[StrategyBase]] = {
    TrendPullbackStrategy.name: TrendPullbackStrategy,
    BreakoutRetestStrategy.name: BreakoutRetestStrategy,
    RangeMeanReversionStrategy.name: RangeMeanReversionStrategy,
}

RESEARCH_STRATEGY_CLASSES: dict[str, type[StrategyBase]] = {
    AsiaRangeLondonBreakoutV0Strategy.name: AsiaRangeLondonBreakoutV0Strategy,
    AsiaRangeLondonFailedBreakReversalV0Strategy.name: AsiaRangeLondonFailedBreakReversalV0Strategy,
    CompressionRetestContinuationV0Strategy.name: CompressionRetestContinuationV0Strategy,
    D1CompressionH4ExpansionV0Strategy.name: D1CompressionH4ExpansionV0Strategy,
    D1MomentumH4PullbackV0Strategy.name: D1MomentumH4PullbackV0Strategy,
    D1MultiDayExhaustionReversionV0Strategy.name: D1MultiDayExhaustionReversionV0Strategy,
    D1VolatilityExpansionReversalV0Strategy.name: D1VolatilityExpansionReversalV0Strategy,
    DailyPivotReclaimV0Strategy.name: DailyPivotReclaimV0Strategy,
    EmrInactivityLongV0Strategy.name: EmrInactivityLongV0Strategy,
    ExtremeActivityMeanReversionV0Strategy.name: ExtremeActivityMeanReversionV0Strategy,
    H4D1MomentumExpansionContinuationV0Strategy.name: H4D1MomentumExpansionContinuationV0Strategy,
    H4InsideBarD1MomentumBreakoutV0Strategy.name: H4InsideBarD1MomentumBreakoutV0Strategy,
    LondonFixContinuationV0Strategy.name: LondonFixContinuationV0Strategy,
    LiquiditySweepContinuationV0Strategy.name: LiquiditySweepContinuationV0Strategy,
    LiquiditySweepReversalV0Strategy.name: LiquiditySweepReversalV0Strategy,
    M15InsideBarBreakoutV0Strategy.name: M15InsideBarBreakoutV0Strategy,
    M5ImpulseContinuationV0Strategy.name: M5ImpulseContinuationV0Strategy,
    NyFailedLondonReversalV0Strategy.name: NyFailedLondonReversalV0Strategy,
    NyAmPullbackContinuationV0Strategy.name: NyAmPullbackContinuationV0Strategy,
    NyLondonOverlapCompressionBreakV0Strategy.name: NyLondonOverlapCompressionBreakV0Strategy,
    OpeningDriveFailedContinuationV0Strategy.name: OpeningDriveFailedContinuationV0Strategy,
    PostSpikeShortV0Strategy.name: PostSpikeShortV0Strategy,
    PreviousDayExtremeRetestV0Strategy.name: PreviousDayExtremeRetestV0Strategy,
    RoundNumberRetestV0Strategy.name: RoundNumberRetestV0Strategy,
    SessionExtremeRetestV0Strategy.name: SessionExtremeRetestV0Strategy,
    SessionVwapReclaimV0Strategy.name: SessionVwapReclaimV0Strategy,
    SqueezeBreakoutLongV0Strategy.name: SqueezeBreakoutLongV0Strategy,
    SwingBreakoutRetestV0Strategy.name: SwingBreakoutRetestV0Strategy,
    SymbolNormalizedRoundRetestV0Strategy.name: SymbolNormalizedRoundRetestV0Strategy,
    SymbolRoundSweepReversalV0Strategy.name: SymbolRoundSweepReversalV0Strategy,
    W1D1MomentumContinuationV0Strategy.name: W1D1MomentumContinuationV0Strategy,
    WeeklyLevelReclaimV0Strategy.name: WeeklyLevelReclaimV0Strategy,
}


def get_strategy(name: str, allow_research_candidate: bool = False) -> StrategyBase:
    if name in STRATEGY_CLASSES:
        return STRATEGY_CLASSES[name]()
    if allow_research_candidate and name in RESEARCH_STRATEGY_CLASSES:
        return RESEARCH_STRATEGY_CLASSES[name]()
    available = list(STRATEGY_CLASSES)
    if allow_research_candidate:
        available.extend(RESEARCH_STRATEGY_CLASSES)
    raise ConfigError(f"Unknown strategy {name!r}. Available: {', '.join(available)}.")


def get_research_strategy(name: str) -> StrategyBase:
    if name not in RESEARCH_STRATEGY_CLASSES:
        raise ConfigError(
            f"Unknown research strategy {name!r}. Available: {', '.join(RESEARCH_STRATEGY_CLASSES)}."
        )
    return RESEARCH_STRATEGY_CLASSES[name]()


def research_strategy_names() -> list[str]:
    return list(RESEARCH_STRATEGY_CLASSES)


def enabled_strategy_names(expert: str, allow_research_candidate: bool = False) -> list[str]:
    if expert == "all":
        return list(STRATEGY_CLASSES)
    if expert not in STRATEGY_CLASSES:
        if allow_research_candidate and expert in RESEARCH_STRATEGY_CLASSES:
            return [expert]
        raise ConfigError(f"Unknown expert {expert!r}.")
    return [expert]

from __future__ import annotations

from phase0.config import ConfigError
from phase0.strategies.asia_range_london_breakout_v0 import AsiaRangeLondonBreakoutV0Strategy
from phase0.strategies.asia_range_london_failed_break_reversal_v0 import (
    AsiaRangeLondonFailedBreakReversalV0Strategy,
)
from phase0.strategies.base import StrategyBase
from phase0.strategies.breakout_retest import BreakoutRetestStrategy
from phase0.strategies.compression_retest_continuation_v0 import CompressionRetestContinuationV0Strategy
from phase0.strategies.cot_gold_positioning_reversal_v0 import CotGoldPositioningReversalV0Strategy
from phase0.strategies.h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0 import (
    H1AudjpyUsdjpyFxCarryRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_breakeven_inflation_shock_reversal_v0 import (
    H1BreakevenInflationShockReversalV0Strategy,
)
from phase0.strategies.h1_credit_spread_shock_reversal_v0 import (
    H1CreditSpreadShockReversalV0Strategy,
)
from phase0.strategies.h1_credit_spread_shock_followthrough_v0 import (
    H1CreditSpreadShockFollowthroughV0Strategy,
)
from phase0.strategies.h1_financial_conditions_shock_reversal_v0 import (
    H1FinancialConditionsShockReversalV0Strategy,
)
from phase0.strategies.h1_financial_conditions_shock_followthrough_v0 import (
    H1FinancialConditionsShockFollowthroughV0Strategy,
)
from phase0.strategies.h1_dbc_uup_commodity_dollar_followthrough_v0 import (
    H1DbcUupCommodityDollarFollowthroughV0Strategy,
)
from phase0.strategies.h1_dbb_uup_industrial_metals_followthrough_v0 import (
    H1DbbUupIndustrialMetalsFollowthroughV0Strategy,
)
from phase0.strategies.h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_v0 import (
    H1EurjpyUsdjpyFxRiskRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_broker_fx_usd_pressure_followthrough_v0 import (
    H1BrokerFxUsdPressureFollowthroughV0Strategy,
)
from phase0.strategies.h1_broker_fx_usd_pressure_conflict_reversion_v0 import (
    H1BrokerFxUsdPressureConflictReversionV0Strategy,
)
from phase0.strategies.h1_btc_risk_pressure_gold_followthrough_v0 import (
    H1BtcRiskPressureGoldFollowthroughV0Strategy,
)
from phase0.strategies.h1_qqq_spy_growth_risk_rotation_followthrough_v0 import (
    H1QqqSpyGrowthRiskRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_iwm_spy_size_risk_rotation_followthrough_v0 import (
    H1IwmSpySizeRiskRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_slv_gld_precious_beta_rotation_followthrough_v0 import (
    H1SlvGldPreciousBetaRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_xle_xlu_energy_defensive_rotation_followthrough_v0 import (
    H1XleXluEnergyDefensiveRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_eem_spy_em_risk_rotation_followthrough_v0 import (
    H1EemSpyEmRiskRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_acwx_spy_global_ex_us_rotation_followthrough_v0 import (
    H1AcwxSpyGlobalExUsRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_xme_spy_metals_mining_rotation_followthrough_v0 import (
    H1XmeSpyMetalsMiningRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0 import (
    H1FxyUupSafeHavenFxRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0 import (
    H1FxfUupSafeHavenFxRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0 import (
    H1FxeUupEuroDollarFxRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0 import (
    H1CybUupYuanDollarFxRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_cny_dollar_pressure_followthrough_v0 import (
    H1CnyDollarPressureFollowthroughV0Strategy,
)
from phase0.strategies.h1_cny_dollar_pressure_reversion_v0 import (
    H1CnyDollarPressureReversionV0Strategy,
)
from phase0.strategies.h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0 import (
    H1FxaUupAussieDollarFxRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_cot_positioning_continuation_v0 import (
    H1CotPositioningContinuationV0Strategy,
)
from phase0.strategies.h4_credit_spread_stress_momentum_v0 import (
    H4CreditSpreadStressMomentumV0Strategy,
)
from phase0.strategies.d1_compression_h4_expansion_v0 import D1CompressionH4ExpansionV0Strategy
from phase0.strategies.d1_inside_day_breakout_v0 import D1InsideDayBreakoutV0Strategy
from phase0.strategies.d1_momentum_h4_pullback_v0 import D1MomentumH4PullbackV0Strategy
from phase0.strategies.d1_multi_day_exhaustion_reversion_v0 import D1MultiDayExhaustionReversionV0Strategy
from phase0.strategies.d1_outside_day_followthrough_v0 import D1OutsideDayFollowthroughV0Strategy
from phase0.strategies.d1_volatility_expansion_reversal_v0 import D1VolatilityExpansionReversalV0Strategy
from phase0.strategies.d1_w1_momentum_h4_pullback_v0 import D1W1MomentumH4PullbackV0Strategy
from phase0.strategies.daily_pivot_reclaim_v0 import DailyPivotReclaimV0Strategy
from phase0.strategies.emr_inactivity_long_v0 import EmrInactivityLongV0Strategy
from phase0.strategies.extreme_activity_mean_reversion_v0 import ExtremeActivityMeanReversionV0Strategy
from phase0.strategies.gold_fx_proxy_divergence_v0 import GoldFxProxyDivergenceV0Strategy
from phase0.strategies.h4_breakeven_inflation_momentum_v0 import (
    H4BreakevenInflationMomentumV0Strategy,
)
from phase0.strategies.h1_calendar_drift_state_v0 import H1CalendarDriftStateV0Strategy
from phase0.strategies.h1_friday_position_squaring_reversion_v0 import (
    H1FridayPositionSquaringReversionV0Strategy,
)
from phase0.strategies.h1_gc_momentum_pullback_v0 import H1GcMomentumPullbackV0Strategy
from phase0.strategies.h1_gdx_gld_trend_confirmation_v0 import H1GdxGldTrendConfirmationV0Strategy
from phase0.strategies.h1_gc_xau_basis_reversion_v0 import H1GcXauBasisReversionV0Strategy
from phase0.strategies.h1_gvz_vix_vol_premium_reversal_v0 import (
    H1GvzVixVolPremiumReversalV0Strategy,
)
from phase0.strategies.h1_gvz_vix_vol_premium_followthrough_v0 import (
    H1GvzVixVolPremiumFollowthroughV0Strategy,
)
from phase0.strategies.h1_gvz_realized_vol_spread_reversal_v0 import (
    H1GvzRealizedVolSpreadReversalV0Strategy,
)
from phase0.strategies.h1_gvz_realized_vol_spread_followthrough_v0 import (
    H1GvzRealizedVolSpreadFollowthroughV0Strategy,
)
from phase0.strategies.h1_move_vix_bond_vol_shock_reversal_v0 import (
    H1MoveVixBondVolShockReversalV0Strategy,
)
from phase0.strategies.h1_hyg_ief_credit_risk_rotation_followthrough_v0 import (
    H1HygIefCreditRiskRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_hg_gc_copper_gold_rotation_followthrough_v0 import (
    H1HgGcCopperGoldRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_xlp_xly_consumer_rotation_followthrough_v0 import (
    H1XlpXlyConsumerRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_xlf_xlu_financials_defensive_rotation_followthrough_v0 import (
    H1XlfXluFinancialsDefensiveRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0 import (
    H1XliXluCyclicalDefensiveRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_macro_composite_pullback_v0 import H1MacroCompositePullbackV0Strategy
from phase0.strategies.h1_macro_composite_state_reversion_v0 import (
    H1MacroCompositeStateReversionV0Strategy,
)
from phase0.strategies.h1_macro_composite_trend_continuation_v0 import (
    H1MacroCompositeTrendContinuationV0Strategy,
)
from phase0.strategies.h1_macro_event_aftershock_v0 import H1MacroEventAftershockV0Strategy
from phase0.strategies.h1_smooth_trend_exhaustion_reversal_v0 import (
    H1SmoothTrendExhaustionReversalV0Strategy,
)
from phase0.strategies.h1_return_autocorrelation_state_v0 import (
    H1ReturnAutocorrelationStateV0Strategy,
)
from phase0.strategies.h1_m5_path_skew_reversal_v0 import H1M5PathSkewReversalV0Strategy
from phase0.strategies.h1_month_turn_flow_continuation_v0 import H1MonthTurnFlowContinuationV0Strategy
from phase0.strategies.h1_month_turn_flow_reversion_v0 import H1MonthTurnFlowReversionV0Strategy
from phase0.strategies.h1_policy_uncertainty_intraday_reversal_v0 import (
    H1PolicyUncertaintyIntradayReversalV0Strategy,
)
from phase0.strategies.h1_real_yield_dollar_shock_followthrough_v0 import (
    H1RealYieldDollarShockFollowthroughV0Strategy,
)
from phase0.strategies.h1_real_yield_dollar_shock_reversal_v0 import (
    H1RealYieldDollarShockReversalV0Strategy,
)
from phase0.strategies.h1_real_yield_inflation_mix_reversal_v0 import (
    H1RealYieldInflationMixReversalV0Strategy,
)
from phase0.strategies.h1_real_yield_inflation_mix_followthrough_v0 import (
    H1RealYieldInflationMixFollowthroughV0Strategy,
)
from phase0.strategies.h1_session_impulse_reversion_v0 import H1SessionImpulseReversionV0Strategy
from phase0.strategies.h1_tick_volume_climax_continuation_v0 import (
    H1TickVolumeClimaxContinuationV0Strategy,
)
from phase0.strategies.h1_tick_volume_climax_reversal_v0 import (
    H1TickVolumeClimaxReversalV0Strategy,
)
from phase0.strategies.h1_spy_tlt_risk_rotation_followthrough_v0 import (
    H1SpyTltRiskRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_tip_ief_real_yield_rotation_followthrough_v0 import (
    H1TipIefRealYieldRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_tlt_uup_pressure_reversion_v0 import H1TltUupPressureReversionV0Strategy
from phase0.strategies.h1_tlt_uup_pressure_followthrough_v0 import (
    H1TltUupPressureFollowthroughV0Strategy,
)
from phase0.strategies.h1_tlt_shy_duration_rotation_followthrough_v0 import (
    H1TltShyDurationRotationFollowthroughV0Strategy,
)
from phase0.strategies.h1_treasury_curve_shock_followthrough_v0 import (
    H1TreasuryCurveShockFollowthroughV0Strategy,
)
from phase0.strategies.h1_treasury_curve_shock_reversal_v0 import (
    H1TreasuryCurveShockReversalV0Strategy,
)
from phase0.strategies.h1_uso_uup_oil_dollar_followthrough_v0 import (
    H1UsoUupOilDollarFollowthroughV0Strategy,
)
from phase0.strategies.h1_vix_term_structure_inversion_followthrough_v0 import (
    H1VixTermStructureInversionFollowthroughV0Strategy,
)
from phase0.strategies.h1_vix_term_structure_inversion_reversal_v0 import (
    H1VixTermStructureInversionReversalV0Strategy,
)
from phase0.strategies.h1_volatility_squeeze_breakout_v0 import (
    H1VolatilitySqueezeBreakoutV0Strategy,
)
from phase0.strategies.h1_walk_forward_linear_state_v0 import H1WalkForwardLinearStateV0Strategy
from phase0.strategies.h1_xlu_xlk_defensive_rotation_followthrough_v0 import (
    H1XluXlkDefensiveRotationFollowthroughV0Strategy,
)
from phase0.strategies.h4_d1_momentum_expansion_continuation_v0 import (
    H4D1MomentumExpansionContinuationV0Strategy,
)
from phase0.strategies.h4_financial_conditions_stress_reversal_v0 import (
    H4FinancialConditionsStressReversalV0Strategy,
)
from phase0.strategies.h4_gdx_gld_miner_divergence_v0 import H4GdxGldMinerDivergenceV0Strategy
from phase0.strategies.h4_gld_etf_flow_reversal_v0 import H4GldEtfFlowReversalV0Strategy
from phase0.strategies.h4_gld_etf_flow_reversal_v1 import H4GldEtfFlowReversalV1Strategy
from phase0.strategies.h4_gld_etf_flow_reversal_v2 import H4GldEtfFlowReversalV2Strategy
from phase0.strategies.h1_gld_flow_momentum_pullback_v0 import H1GldFlowMomentumPullbackV0Strategy
from phase0.strategies.h1_gld_flow_stress_followthrough_v0 import H1GldFlowStressFollowthroughV0Strategy
from phase0.strategies.h1_gld_flow_stress_reversal_v0 import H1GldFlowStressReversalV0Strategy
from phase0.strategies.h1_gld_spy_safe_haven_rotation_followthrough_v0 import (
    H1GldSpySafeHavenRotationFollowthroughV0Strategy,
)
from phase0.strategies.h4_gold_futures_volume_climax_v0 import H4GoldFuturesVolumeClimaxV0Strategy
from phase0.strategies.h4_gvz_volatility_panic_reversal_v0 import (
    H4GvzVolatilityPanicReversalV0Strategy,
)
from phase0.strategies.h4_inside_bar_d1_momentum_breakout_v0 import H4InsideBarD1MomentumBreakoutV0Strategy
from phase0.strategies.h4_macro_composite_risk_state_v0 import H4MacroCompositeRiskStateV0Strategy
from phase0.strategies.h4_macro_composite_risk_state_v1 import H4MacroCompositeRiskStateV1Strategy
from phase0.strategies.h4_policy_uncertainty_safe_haven_v0 import (
    H4PolicyUncertaintySafeHavenV0Strategy,
)
from phase0.strategies.h4_real_yield_proxy_momentum_v0 import H4RealYieldProxyMomentumV0Strategy
from phase0.strategies.h4_treasury_curve_stress_momentum_v0 import (
    H4TreasuryCurveStressMomentumV0Strategy,
)
from phase0.strategies.h4_us_session_liquidity_reversal_v0 import (
    H4UsSessionLiquidityReversalV0Strategy,
)
from phase0.strategies.h4_vix_risk_off_followthrough_v0 import H4VixRiskOffFollowthroughV0Strategy
from phase0.strategies.h4_vix_risk_off_reversal_v0 import H4VixRiskOffReversalV0Strategy
from phase0.strategies.h4_walk_forward_knn_momentum_state_v0 import H4WalkForwardKnnMomentumStateV0Strategy
from phase0.strategies.london_fix_continuation_v0 import LondonFixContinuationV0Strategy
from phase0.strategies.liquidity_sweep_continuation_v0 import LiquiditySweepContinuationV0Strategy
from phase0.strategies.liquidity_sweep_reversal_v0 import LiquiditySweepReversalV0Strategy
from phase0.strategies.m15_inside_bar_breakout_v0 import M15InsideBarBreakoutV0Strategy
from phase0.strategies.m15_two_bar_impulse_continuation_v0 import (
    M15TwoBarImpulseContinuationV0Strategy,
)
from phase0.strategies.m15_two_bar_exhaustion_reversal_v0 import (
    M15TwoBarExhaustionReversalV0Strategy,
)
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
from phase0.strategies.quarter_round_retest_v0 import QuarterRoundRetestV0Strategy
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
from phase0.strategies.weekly_open_reversion_v0 import WeeklyOpenReversionV0Strategy
from phase0.strategies.xag_lead_xau_followthrough_v0 import XagLeadXauFollowthroughV0Strategy
from phase0.strategies.xau_xag_fx_composite_reversion_v0 import (
    XauXagFxCompositeReversionV0Strategy,
)
from phase0.strategies.xau_xag_relative_value_v0 import XauXagRelativeValueV0Strategy


STRATEGY_CLASSES: dict[str, type[StrategyBase]] = {
    TrendPullbackStrategy.name: TrendPullbackStrategy,
    BreakoutRetestStrategy.name: BreakoutRetestStrategy,
    RangeMeanReversionStrategy.name: RangeMeanReversionStrategy,
}

RESEARCH_STRATEGY_CLASSES: dict[str, type[StrategyBase]] = {
    AsiaRangeLondonBreakoutV0Strategy.name: AsiaRangeLondonBreakoutV0Strategy,
    AsiaRangeLondonFailedBreakReversalV0Strategy.name: AsiaRangeLondonFailedBreakReversalV0Strategy,
    CompressionRetestContinuationV0Strategy.name: CompressionRetestContinuationV0Strategy,
    CotGoldPositioningReversalV0Strategy.name: CotGoldPositioningReversalV0Strategy,
    H1AudjpyUsdjpyFxCarryRotationFollowthroughV0Strategy.name: H1AudjpyUsdjpyFxCarryRotationFollowthroughV0Strategy,
    H1BreakevenInflationShockReversalV0Strategy.name: H1BreakevenInflationShockReversalV0Strategy,
    H1CreditSpreadShockFollowthroughV0Strategy.name: H1CreditSpreadShockFollowthroughV0Strategy,
    H1CreditSpreadShockReversalV0Strategy.name: H1CreditSpreadShockReversalV0Strategy,
    H1FinancialConditionsShockFollowthroughV0Strategy.name: H1FinancialConditionsShockFollowthroughV0Strategy,
    H1FinancialConditionsShockReversalV0Strategy.name: H1FinancialConditionsShockReversalV0Strategy,
    H1DbbUupIndustrialMetalsFollowthroughV0Strategy.name: H1DbbUupIndustrialMetalsFollowthroughV0Strategy,
    H1DbcUupCommodityDollarFollowthroughV0Strategy.name: H1DbcUupCommodityDollarFollowthroughV0Strategy,
    H1EurjpyUsdjpyFxRiskRotationFollowthroughV0Strategy.name: H1EurjpyUsdjpyFxRiskRotationFollowthroughV0Strategy,
    H1BrokerFxUsdPressureFollowthroughV0Strategy.name: H1BrokerFxUsdPressureFollowthroughV0Strategy,
    H1BrokerFxUsdPressureConflictReversionV0Strategy.name: H1BrokerFxUsdPressureConflictReversionV0Strategy,
    H1BtcRiskPressureGoldFollowthroughV0Strategy.name: H1BtcRiskPressureGoldFollowthroughV0Strategy,
    H1QqqSpyGrowthRiskRotationFollowthroughV0Strategy.name: H1QqqSpyGrowthRiskRotationFollowthroughV0Strategy,
    H1IwmSpySizeRiskRotationFollowthroughV0Strategy.name: H1IwmSpySizeRiskRotationFollowthroughV0Strategy,
    H1SlvGldPreciousBetaRotationFollowthroughV0Strategy.name: H1SlvGldPreciousBetaRotationFollowthroughV0Strategy,
    H1XleXluEnergyDefensiveRotationFollowthroughV0Strategy.name: H1XleXluEnergyDefensiveRotationFollowthroughV0Strategy,
    H1EemSpyEmRiskRotationFollowthroughV0Strategy.name: H1EemSpyEmRiskRotationFollowthroughV0Strategy,
    H1AcwxSpyGlobalExUsRotationFollowthroughV0Strategy.name: H1AcwxSpyGlobalExUsRotationFollowthroughV0Strategy,
    H1XmeSpyMetalsMiningRotationFollowthroughV0Strategy.name: H1XmeSpyMetalsMiningRotationFollowthroughV0Strategy,
    H1FxyUupSafeHavenFxRotationFollowthroughV0Strategy.name: H1FxyUupSafeHavenFxRotationFollowthroughV0Strategy,
    H1FxfUupSafeHavenFxRotationFollowthroughV0Strategy.name: H1FxfUupSafeHavenFxRotationFollowthroughV0Strategy,
    H1FxeUupEuroDollarFxRotationFollowthroughV0Strategy.name: H1FxeUupEuroDollarFxRotationFollowthroughV0Strategy,
    H1CybUupYuanDollarFxRotationFollowthroughV0Strategy.name: H1CybUupYuanDollarFxRotationFollowthroughV0Strategy,
    H1CnyDollarPressureFollowthroughV0Strategy.name: H1CnyDollarPressureFollowthroughV0Strategy,
    H1CnyDollarPressureReversionV0Strategy.name: H1CnyDollarPressureReversionV0Strategy,
    H1FxaUupAussieDollarFxRotationFollowthroughV0Strategy.name: H1FxaUupAussieDollarFxRotationFollowthroughV0Strategy,
    H4CreditSpreadStressMomentumV0Strategy.name: H4CreditSpreadStressMomentumV0Strategy,
    D1CompressionH4ExpansionV0Strategy.name: D1CompressionH4ExpansionV0Strategy,
    D1InsideDayBreakoutV0Strategy.name: D1InsideDayBreakoutV0Strategy,
    D1MomentumH4PullbackV0Strategy.name: D1MomentumH4PullbackV0Strategy,
    D1MultiDayExhaustionReversionV0Strategy.name: D1MultiDayExhaustionReversionV0Strategy,
    D1OutsideDayFollowthroughV0Strategy.name: D1OutsideDayFollowthroughV0Strategy,
    D1VolatilityExpansionReversalV0Strategy.name: D1VolatilityExpansionReversalV0Strategy,
    D1W1MomentumH4PullbackV0Strategy.name: D1W1MomentumH4PullbackV0Strategy,
    DailyPivotReclaimV0Strategy.name: DailyPivotReclaimV0Strategy,
    EmrInactivityLongV0Strategy.name: EmrInactivityLongV0Strategy,
    ExtremeActivityMeanReversionV0Strategy.name: ExtremeActivityMeanReversionV0Strategy,
    GoldFxProxyDivergenceV0Strategy.name: GoldFxProxyDivergenceV0Strategy,
    H4BreakevenInflationMomentumV0Strategy.name: H4BreakevenInflationMomentumV0Strategy,
    H1CalendarDriftStateV0Strategy.name: H1CalendarDriftStateV0Strategy,
    H1CotPositioningContinuationV0Strategy.name: H1CotPositioningContinuationV0Strategy,
    H1FridayPositionSquaringReversionV0Strategy.name: H1FridayPositionSquaringReversionV0Strategy,
    H1GcMomentumPullbackV0Strategy.name: H1GcMomentumPullbackV0Strategy,
    H1GcXauBasisReversionV0Strategy.name: H1GcXauBasisReversionV0Strategy,
    H1GdxGldTrendConfirmationV0Strategy.name: H1GdxGldTrendConfirmationV0Strategy,
    H1GvzRealizedVolSpreadFollowthroughV0Strategy.name: H1GvzRealizedVolSpreadFollowthroughV0Strategy,
    H1GvzRealizedVolSpreadReversalV0Strategy.name: H1GvzRealizedVolSpreadReversalV0Strategy,
    H1GvzVixVolPremiumFollowthroughV0Strategy.name: H1GvzVixVolPremiumFollowthroughV0Strategy,
    H1GvzVixVolPremiumReversalV0Strategy.name: H1GvzVixVolPremiumReversalV0Strategy,
    H1HgGcCopperGoldRotationFollowthroughV0Strategy.name: H1HgGcCopperGoldRotationFollowthroughV0Strategy,
    H1MoveVixBondVolShockReversalV0Strategy.name: H1MoveVixBondVolShockReversalV0Strategy,
    H1HygIefCreditRiskRotationFollowthroughV0Strategy.name: H1HygIefCreditRiskRotationFollowthroughV0Strategy,
    H1XliXluCyclicalDefensiveRotationFollowthroughV0Strategy.name: H1XliXluCyclicalDefensiveRotationFollowthroughV0Strategy,
    H1XlfXluFinancialsDefensiveRotationFollowthroughV0Strategy.name: H1XlfXluFinancialsDefensiveRotationFollowthroughV0Strategy,
    H1XlpXlyConsumerRotationFollowthroughV0Strategy.name: H1XlpXlyConsumerRotationFollowthroughV0Strategy,
    H1MacroCompositePullbackV0Strategy.name: H1MacroCompositePullbackV0Strategy,
    H1MacroCompositeStateReversionV0Strategy.name: H1MacroCompositeStateReversionV0Strategy,
    H1MacroCompositeTrendContinuationV0Strategy.name: H1MacroCompositeTrendContinuationV0Strategy,
    H1MacroEventAftershockV0Strategy.name: H1MacroEventAftershockV0Strategy,
    H1M5PathSkewReversalV0Strategy.name: H1M5PathSkewReversalV0Strategy,
    H1MonthTurnFlowContinuationV0Strategy.name: H1MonthTurnFlowContinuationV0Strategy,
    H1MonthTurnFlowReversionV0Strategy.name: H1MonthTurnFlowReversionV0Strategy,
    H1PolicyUncertaintyIntradayReversalV0Strategy.name: H1PolicyUncertaintyIntradayReversalV0Strategy,
    H1RealYieldDollarShockFollowthroughV0Strategy.name: H1RealYieldDollarShockFollowthroughV0Strategy,
    H1RealYieldInflationMixFollowthroughV0Strategy.name: H1RealYieldInflationMixFollowthroughV0Strategy,
    H1RealYieldInflationMixReversalV0Strategy.name: H1RealYieldInflationMixReversalV0Strategy,
    H1RealYieldDollarShockReversalV0Strategy.name: H1RealYieldDollarShockReversalV0Strategy,
    H1ReturnAutocorrelationStateV0Strategy.name: H1ReturnAutocorrelationStateV0Strategy,
    H1SessionImpulseReversionV0Strategy.name: H1SessionImpulseReversionV0Strategy,
    H1TickVolumeClimaxContinuationV0Strategy.name: H1TickVolumeClimaxContinuationV0Strategy,
    H1SpyTltRiskRotationFollowthroughV0Strategy.name: H1SpyTltRiskRotationFollowthroughV0Strategy,
    H1TipIefRealYieldRotationFollowthroughV0Strategy.name: H1TipIefRealYieldRotationFollowthroughV0Strategy,
    H1TickVolumeClimaxReversalV0Strategy.name: H1TickVolumeClimaxReversalV0Strategy,
    H1TltShyDurationRotationFollowthroughV0Strategy.name: H1TltShyDurationRotationFollowthroughV0Strategy,
    H1TltUupPressureFollowthroughV0Strategy.name: H1TltUupPressureFollowthroughV0Strategy,
    H1TltUupPressureReversionV0Strategy.name: H1TltUupPressureReversionV0Strategy,
    H1TreasuryCurveShockFollowthroughV0Strategy.name: H1TreasuryCurveShockFollowthroughV0Strategy,
    H1TreasuryCurveShockReversalV0Strategy.name: H1TreasuryCurveShockReversalV0Strategy,
    H1UsoUupOilDollarFollowthroughV0Strategy.name: H1UsoUupOilDollarFollowthroughV0Strategy,
    H1VixTermStructureInversionFollowthroughV0Strategy.name: H1VixTermStructureInversionFollowthroughV0Strategy,
    H1VixTermStructureInversionReversalV0Strategy.name: H1VixTermStructureInversionReversalV0Strategy,
    H1VolatilitySqueezeBreakoutV0Strategy.name: H1VolatilitySqueezeBreakoutV0Strategy,
    H1WalkForwardLinearStateV0Strategy.name: H1WalkForwardLinearStateV0Strategy,
    H1XluXlkDefensiveRotationFollowthroughV0Strategy.name: H1XluXlkDefensiveRotationFollowthroughV0Strategy,
    H1SmoothTrendExhaustionReversalV0Strategy.name: H1SmoothTrendExhaustionReversalV0Strategy,
    H4D1MomentumExpansionContinuationV0Strategy.name: H4D1MomentumExpansionContinuationV0Strategy,
    H4FinancialConditionsStressReversalV0Strategy.name: H4FinancialConditionsStressReversalV0Strategy,
    H4GdxGldMinerDivergenceV0Strategy.name: H4GdxGldMinerDivergenceV0Strategy,
    H4GldEtfFlowReversalV0Strategy.name: H4GldEtfFlowReversalV0Strategy,
    H4GldEtfFlowReversalV1Strategy.name: H4GldEtfFlowReversalV1Strategy,
    H4GldEtfFlowReversalV2Strategy.name: H4GldEtfFlowReversalV2Strategy,
    H1GldFlowMomentumPullbackV0Strategy.name: H1GldFlowMomentumPullbackV0Strategy,
    H1GldFlowStressFollowthroughV0Strategy.name: H1GldFlowStressFollowthroughV0Strategy,
    H1GldFlowStressReversalV0Strategy.name: H1GldFlowStressReversalV0Strategy,
    H1GldSpySafeHavenRotationFollowthroughV0Strategy.name: H1GldSpySafeHavenRotationFollowthroughV0Strategy,
    H4GoldFuturesVolumeClimaxV0Strategy.name: H4GoldFuturesVolumeClimaxV0Strategy,
    H4GvzVolatilityPanicReversalV0Strategy.name: H4GvzVolatilityPanicReversalV0Strategy,
    H4InsideBarD1MomentumBreakoutV0Strategy.name: H4InsideBarD1MomentumBreakoutV0Strategy,
    H4MacroCompositeRiskStateV0Strategy.name: H4MacroCompositeRiskStateV0Strategy,
    H4MacroCompositeRiskStateV1Strategy.name: H4MacroCompositeRiskStateV1Strategy,
    H4PolicyUncertaintySafeHavenV0Strategy.name: H4PolicyUncertaintySafeHavenV0Strategy,
    H4RealYieldProxyMomentumV0Strategy.name: H4RealYieldProxyMomentumV0Strategy,
    H4TreasuryCurveStressMomentumV0Strategy.name: H4TreasuryCurveStressMomentumV0Strategy,
    H4UsSessionLiquidityReversalV0Strategy.name: H4UsSessionLiquidityReversalV0Strategy,
    H4VixRiskOffFollowthroughV0Strategy.name: H4VixRiskOffFollowthroughV0Strategy,
    H4VixRiskOffReversalV0Strategy.name: H4VixRiskOffReversalV0Strategy,
    H4WalkForwardKnnMomentumStateV0Strategy.name: H4WalkForwardKnnMomentumStateV0Strategy,
    LondonFixContinuationV0Strategy.name: LondonFixContinuationV0Strategy,
    LiquiditySweepContinuationV0Strategy.name: LiquiditySweepContinuationV0Strategy,
    LiquiditySweepReversalV0Strategy.name: LiquiditySweepReversalV0Strategy,
    M15InsideBarBreakoutV0Strategy.name: M15InsideBarBreakoutV0Strategy,
    M15TwoBarImpulseContinuationV0Strategy.name: M15TwoBarImpulseContinuationV0Strategy,
    M15TwoBarExhaustionReversalV0Strategy.name: M15TwoBarExhaustionReversalV0Strategy,
    M5ImpulseContinuationV0Strategy.name: M5ImpulseContinuationV0Strategy,
    NyFailedLondonReversalV0Strategy.name: NyFailedLondonReversalV0Strategy,
    NyAmPullbackContinuationV0Strategy.name: NyAmPullbackContinuationV0Strategy,
    NyLondonOverlapCompressionBreakV0Strategy.name: NyLondonOverlapCompressionBreakV0Strategy,
    OpeningDriveFailedContinuationV0Strategy.name: OpeningDriveFailedContinuationV0Strategy,
    PostSpikeShortV0Strategy.name: PostSpikeShortV0Strategy,
    PreviousDayExtremeRetestV0Strategy.name: PreviousDayExtremeRetestV0Strategy,
    QuarterRoundRetestV0Strategy.name: QuarterRoundRetestV0Strategy,
    RoundNumberRetestV0Strategy.name: RoundNumberRetestV0Strategy,
    SessionExtremeRetestV0Strategy.name: SessionExtremeRetestV0Strategy,
    SessionVwapReclaimV0Strategy.name: SessionVwapReclaimV0Strategy,
    SqueezeBreakoutLongV0Strategy.name: SqueezeBreakoutLongV0Strategy,
    SwingBreakoutRetestV0Strategy.name: SwingBreakoutRetestV0Strategy,
    SymbolNormalizedRoundRetestV0Strategy.name: SymbolNormalizedRoundRetestV0Strategy,
    SymbolRoundSweepReversalV0Strategy.name: SymbolRoundSweepReversalV0Strategy,
    W1D1MomentumContinuationV0Strategy.name: W1D1MomentumContinuationV0Strategy,
    WeeklyLevelReclaimV0Strategy.name: WeeklyLevelReclaimV0Strategy,
    WeeklyOpenReversionV0Strategy.name: WeeklyOpenReversionV0Strategy,
    XagLeadXauFollowthroughV0Strategy.name: XagLeadXauFollowthroughV0Strategy,
    XauXagFxCompositeReversionV0Strategy.name: XauXagFxCompositeReversionV0Strategy,
    XauXagRelativeValueV0Strategy.name: XauXagRelativeValueV0Strategy,
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

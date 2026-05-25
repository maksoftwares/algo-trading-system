from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PACKAGE_ROOT / "config"
DEFAULT_PHASE0_CONFIG = CONFIG_DIR / "phase0.yaml"
DEFAULT_TRUE_HOLDOUT_CONFIG = CONFIG_DIR / "true_holdout_period.yaml"

EXPERTS = ("trend_pullback", "breakout_retest", "range_mr")
RESEARCH_EXPERTS = (
    "asia_range_london_breakout_v0",
    "asia_range_london_failed_break_reversal_v0",
    "compression_retest_continuation_v0",
    "cot_gold_positioning_reversal_v0",
    "d1_compression_h4_expansion_v0",
    "d1_inside_day_breakout_v0",
    "d1_momentum_h4_pullback_v0",
    "d1_multi_day_exhaustion_reversion_v0",
    "d1_outside_day_followthrough_v0",
    "d1_volatility_expansion_reversal_v0",
    "d1_w1_momentum_h4_pullback_v0",
    "daily_pivot_reclaim_v0",
    "emr_inactivity_long_v0",
    "extreme_activity_mean_reversion_v0",
    "gold_fx_proxy_divergence_v0",
    "h1_calendar_drift_state_v0",
    "h1_m5_path_skew_reversal_v0",
    "h1_return_autocorrelation_state_v0",
    "h1_smooth_trend_exhaustion_reversal_v0",
    "h1_tick_volume_climax_reversal_v0",
    "h1_volatility_squeeze_breakout_v0",
    "h1_walk_forward_linear_state_v0",
    "h4_d1_momentum_expansion_continuation_v0",
    "h4_inside_bar_d1_momentum_breakout_v0",
    "h4_real_yield_proxy_momentum_v0",
    "h4_walk_forward_knn_momentum_state_v0",
    "london_fix_continuation_v0",
    "liquidity_sweep_continuation_v0",
    "liquidity_sweep_reversal_v0",
    "m15_inside_bar_breakout_v0",
    "m15_two_bar_impulse_continuation_v0",
    "m15_two_bar_exhaustion_reversal_v0",
    "m5_impulse_continuation_v0",
    "ny_failed_london_reversal_v0",
    "ny_am_pullback_continuation_v0",
    "ny_london_overlap_compression_break_v0",
    "opening_drive_failed_continuation_v0",
    "post_spike_short_v0",
    "previous_day_extreme_retest_v0",
    "round_number_retest_v0",
    "session_extreme_retest_v0",
    "session_vwap_reclaim_v0",
    "symbol_normalized_round_retest_v0",
    "symbol_round_sweep_reversal_v0",
    "squeeze_breakout_long_v0",
    "swing_breakout_retest_v0",
    "w1_d1_momentum_continuation_v0",
    "weekly_level_reclaim_v0",
    "weekly_open_reversion_v0",
    "xag_lead_xau_followthrough_v0",
    "xau_xag_fx_composite_reversion_v0",
    "xau_xag_relative_value_v0",
)
COST_MODELS = ("best_case", "median", "p95")
BROKERS = ("capital_com", "pepperstone", "dukascopy")
PRIMARY_SYMBOL = "XAUUSD"
COMPARISON_SYMBOLS = ("EURUSD", "USDJPY")

TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4", "D1")
BAR_TIMESTAMP_CONVENTION = "timestamp_utc_equals_bar_end_utc"

CELL_WINDOWS = {
    1: ("cell_1_3_start", "cell_1_3_end", "capital_com"),
    2: ("cell_1_3_start", "cell_1_3_end", "capital_com"),
    3: ("cell_1_3_start", "cell_1_3_end", "capital_com"),
    4: ("cell_4_6_start", "cell_4_6_end", "pepperstone"),
    5: ("cell_4_6_start", "cell_4_6_end", "pepperstone"),
    6: ("cell_4_6_start", "cell_4_6_end", "pepperstone"),
    7: ("cell_7_9_start", "cell_7_9_end", "dukascopy"),
    8: ("cell_7_9_start", "cell_7_9_end", "dukascopy"),
    9: ("cell_7_9_start", "cell_7_9_end", "dukascopy"),
}

CELL_COST_MODELS = {
    1: "best_case",
    2: "median",
    3: "p95",
    4: "best_case",
    5: "median",
    6: "p95",
    7: "best_case",
    8: "median",
    9: "p95",
}

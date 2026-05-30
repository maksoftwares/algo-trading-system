from __future__ import annotations

import pandas as pd

from phase0.audjpy_usdjpy_fx_carry_rotation_data import AUDJPY_USDJPY_FX_CARRY_ROTATION_FRAME_KEY
from phase0.btc_risk_pressure_data import BTC_RISK_PRESSURE_FRAME_KEY
from phase0.dbc_uup_commodity_dollar_data import DBC_UUP_COMMODITY_DOLLAR_FRAME_KEY
from phase0.dbb_uup_industrial_metals_data import DBB_UUP_INDUSTRIAL_METALS_FRAME_KEY
from phase0.eurjpy_usdjpy_fx_risk_rotation_data import EURJPY_USDJPY_FX_RISK_ROTATION_FRAME_KEY
from phase0.eem_spy_em_risk_rotation_data import EEM_SPY_EM_RISK_ROTATION_FRAME_KEY
from phase0.acwx_spy_global_ex_us_rotation_data import ACWX_SPY_GLOBAL_EX_US_ROTATION_FRAME_KEY
from phase0.xme_spy_metals_mining_rotation_data import XME_SPY_METALS_MINING_ROTATION_FRAME_KEY
from phase0.fxy_uup_safe_haven_fx_rotation_data import FXY_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY
from phase0.fxf_uup_safe_haven_fx_rotation_data import FXF_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY
from phase0.fxe_uup_euro_dollar_fx_rotation_data import FXE_UUP_EURO_DOLLAR_FX_ROTATION_FRAME_KEY
from phase0.cyb_uup_yuan_dollar_fx_rotation_data import CYB_UUP_YUAN_DOLLAR_FX_ROTATION_FRAME_KEY
from phase0.cny_dollar_pressure_data import CNY_DOLLAR_PRESSURE_FRAME_KEY
from phase0.fxa_uup_aussie_dollar_fx_rotation_data import FXA_UUP_AUSSIE_DOLLAR_FX_ROTATION_FRAME_KEY
from phase0.gc_futures_volume_data import GC_FUTURES_VOLUME_FRAME_KEY
from phase0.gdx_gld_relative_data import GDX_GLD_RELATIVE_FRAME_KEY
from phase0.gld_etf_flow_data import GLD_ETF_FLOW_FRAME_KEY
from phase0.hyg_ief_credit_risk_rotation_data import HYG_IEF_CREDIT_RISK_ROTATION_FRAME_KEY
from phase0.iwm_spy_size_rotation_data import IWM_SPY_SIZE_ROTATION_FRAME_KEY
from phase0.macro_real_yield_data import MACRO_FRAME_KEY
from phase0.macro_event_calendar import MACRO_EVENT_FRAME_KEY
from phase0.move_bond_vol_data import MOVE_BOND_VOL_FRAME_KEY
from phase0.qqq_spy_growth_rotation_data import QQQ_SPY_GROWTH_ROTATION_FRAME_KEY
from phase0.slv_gld_precious_rotation_data import SLV_GLD_PRECIOUS_ROTATION_FRAME_KEY
from phase0.spy_tlt_risk_rotation_data import SPY_TLT_RISK_ROTATION_FRAME_KEY
from phase0.tip_ief_real_yield_rotation_data import TIP_IEF_REAL_YIELD_ROTATION_FRAME_KEY
from phase0.tlt_uup_macro_pressure_data import TLT_UUP_PRESSURE_FRAME_KEY
from phase0.tlt_shy_duration_rotation_data import TLT_SHY_DURATION_ROTATION_FRAME_KEY
from phase0.uso_uup_oil_dollar_data import USO_UUP_OIL_DOLLAR_FRAME_KEY
from phase0.xlu_xlk_defensive_rotation_data import XLU_XLK_DEFENSIVE_ROTATION_FRAME_KEY
from phase0.xlp_xly_consumer_rotation_data import XLP_XLY_CONSUMER_ROTATION_FRAME_KEY
from phase0.xlf_xlu_financials_defensive_rotation_data import (
    XLF_XLU_FINANCIALS_DEFENSIVE_ROTATION_FRAME_KEY,
)
from phase0.xli_xlu_cyclical_defensive_rotation_data import (
    XLI_XLU_CYCLICAL_DEFENSIVE_ROTATION_FRAME_KEY,
)
from phase0.xle_xlu_energy_defensive_rotation_data import XLE_XLU_ENERGY_DEFENSIVE_ROTATION_FRAME_KEY


def synthetic_context_for_expert(expert: str) -> dict:
    if expert == "asia_range_london_breakout_v0":
        return _asia_range_london_breakout_context()
    if expert == "asia_range_london_failed_break_reversal_v0":
        return _asia_range_london_failed_break_reversal_context()
    if expert == "compression_retest_continuation_v0":
        return _compression_retest_continuation_context()
    if expert == "cot_gold_positioning_reversal_v0":
        return _cot_gold_positioning_reversal_context()
    if expert == "h1_dbc_uup_commodity_dollar_followthrough_v0":
        return _h1_dbc_uup_commodity_dollar_followthrough_context()
    if expert == "h1_dbb_uup_industrial_metals_followthrough_v0":
        return _h1_dbb_uup_industrial_metals_followthrough_context()
    if expert == "h1_cot_positioning_continuation_v0":
        return _h1_cot_positioning_continuation_context()
    if expert == "h1_friday_position_squaring_reversion_v0":
        return _h1_friday_position_squaring_reversion_context()
    if expert == "h4_credit_spread_stress_momentum_v0":
        return _h4_credit_spread_stress_momentum_context()
    if expert == "d1_compression_h4_expansion_v0":
        return _d1_compression_h4_expansion_context()
    if expert == "d1_inside_day_breakout_v0":
        return _d1_inside_day_breakout_context()
    if expert == "d1_momentum_h4_pullback_v0":
        return _d1_momentum_h4_pullback_context()
    if expert == "d1_multi_day_exhaustion_reversion_v0":
        return _d1_multi_day_exhaustion_reversion_context()
    if expert == "d1_outside_day_followthrough_v0":
        return _d1_outside_day_followthrough_context()
    if expert == "d1_volatility_expansion_reversal_v0":
        return _d1_volatility_expansion_reversal_context()
    if expert == "d1_w1_momentum_h4_pullback_v0":
        return _d1_momentum_h4_pullback_context()
    if expert == "daily_pivot_reclaim_v0":
        return _daily_pivot_reclaim_context()
    if expert == "trend_pullback":
        return _trend_context()
    if expert == "breakout_retest":
        return _breakout_context()
    if expert == "range_mr":
        return _range_context()
    if expert == "emr_inactivity_long_v0":
        return _emr_inactivity_long_context()
    if expert == "extreme_activity_mean_reversion_v0":
        return _extreme_activity_mean_reversion_context()
    if expert == "gold_fx_proxy_divergence_v0":
        return _gold_fx_proxy_divergence_context()
    if expert == "h4_breakeven_inflation_momentum_v0":
        return _h4_breakeven_inflation_momentum_context()
    if expert == "h1_calendar_drift_state_v0":
        return _h1_calendar_drift_state_context()
    if expert == "h1_gdx_gld_trend_confirmation_v0":
        return _h1_gdx_gld_trend_confirmation_context()
    if expert == "h1_gc_momentum_pullback_v0":
        return _h1_gc_momentum_pullback_context()
    if expert == "h1_gc_xau_basis_reversion_v0":
        return _h1_gc_xau_basis_reversion_context()
    if expert == "h1_gvz_vix_vol_premium_reversal_v0":
        return _h1_gvz_vix_vol_premium_reversal_context()
    if expert == "h1_move_vix_bond_vol_shock_reversal_v0":
        return _h1_move_vix_bond_vol_shock_reversal_context()
    if expert == "h1_hyg_ief_credit_risk_rotation_followthrough_v0":
        return _h1_hyg_ief_credit_risk_rotation_followthrough_context()
    if expert == "h1_macro_event_aftershock_v0":
        return _h1_macro_event_aftershock_context()
    if expert == "h1_macro_composite_pullback_v0":
        return _h1_macro_composite_pullback_context()
    if expert == "h1_macro_composite_state_reversion_v0":
        return _h1_macro_composite_state_reversion_context()
    if expert == "h1_macro_composite_trend_continuation_v0":
        return _h1_macro_composite_pullback_context()
    if expert == "h1_m5_path_skew_reversal_v0":
        return _h1_m5_path_skew_reversal_context()
    if expert == "h1_month_turn_flow_continuation_v0":
        return _h1_month_turn_flow_continuation_context()
    if expert == "h1_month_turn_flow_reversion_v0":
        return _h1_month_turn_flow_reversion_context()
    if expert == "h1_return_autocorrelation_state_v0":
        return _h1_return_autocorrelation_state_context()
    if expert == "h1_session_impulse_reversion_v0":
        return _h1_session_impulse_reversion_context()
    if expert == "h1_smooth_trend_exhaustion_reversal_v0":
        return _h1_smooth_trend_exhaustion_reversal_context()
    if expert == "h1_spy_tlt_risk_rotation_followthrough_v0":
        return _h1_spy_tlt_risk_rotation_followthrough_context()
    if expert == "h1_tip_ief_real_yield_rotation_followthrough_v0":
        return _h1_tip_ief_real_yield_rotation_followthrough_context()
    if expert == "h1_tick_volume_climax_continuation_v0":
        return _h1_tick_volume_climax_continuation_context()
    if expert == "h1_tick_volume_climax_reversal_v0":
        return _h1_tick_volume_climax_reversal_context()
    if expert == "h1_tlt_uup_pressure_followthrough_v0":
        return _h1_tlt_uup_pressure_followthrough_context()
    if expert == "h1_tlt_uup_pressure_reversion_v0":
        return _h1_tlt_uup_pressure_reversion_context()
    if expert == "h1_tlt_shy_duration_rotation_followthrough_v0":
        return _h1_tlt_shy_duration_rotation_followthrough_context()
    if expert == "h1_uso_uup_oil_dollar_followthrough_v0":
        return _h1_uso_uup_oil_dollar_followthrough_context()
    if expert == "h1_volatility_squeeze_breakout_v0":
        return _h1_volatility_squeeze_breakout_context()
    if expert == "h1_walk_forward_linear_state_v0":
        return _h1_walk_forward_linear_state_context()
    if expert == "h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0":
        return _h1_audjpy_usdjpy_fx_carry_rotation_followthrough_context()
    if expert == "h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_v0":
        return _h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_context()
    if expert == "h1_eem_spy_em_risk_rotation_followthrough_v0":
        return _h1_eem_spy_em_risk_rotation_followthrough_context()
    if expert == "h1_acwx_spy_global_ex_us_rotation_followthrough_v0":
        return _h1_acwx_spy_global_ex_us_rotation_followthrough_context()
    if expert == "h1_xme_spy_metals_mining_rotation_followthrough_v0":
        return _h1_xme_spy_metals_mining_rotation_followthrough_context()
    if expert == "h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0":
        return _h1_fxy_uup_safe_haven_fx_rotation_followthrough_context()
    if expert == "h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0":
        return _h1_fxf_uup_safe_haven_fx_rotation_followthrough_context()
    if expert == "h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0":
        return _h1_fxe_uup_euro_dollar_fx_rotation_followthrough_context()
    if expert == "h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0":
        return _h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_context()
    if expert == "h1_cny_dollar_pressure_followthrough_v0":
        return _h1_cny_dollar_pressure_followthrough_context()
    if expert == "h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0":
        return _h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_context()
    if expert == "h1_broker_fx_usd_pressure_followthrough_v0":
        return _h1_broker_fx_usd_pressure_followthrough_context()
    if expert == "h1_broker_fx_usd_pressure_conflict_reversion_v0":
        return _h1_broker_fx_usd_pressure_conflict_reversion_context()
    if expert == "h1_btc_risk_pressure_gold_followthrough_v0":
        return _h1_btc_risk_pressure_gold_followthrough_context()
    if expert == "h1_qqq_spy_growth_risk_rotation_followthrough_v0":
        return _h1_qqq_spy_growth_risk_rotation_followthrough_context()
    if expert == "h1_iwm_spy_size_risk_rotation_followthrough_v0":
        return _h1_iwm_spy_size_risk_rotation_followthrough_context()
    if expert == "h1_slv_gld_precious_beta_rotation_followthrough_v0":
        return _h1_slv_gld_precious_beta_rotation_followthrough_context()
    if expert == "h1_xlu_xlk_defensive_rotation_followthrough_v0":
        return _h1_xlu_xlk_defensive_rotation_followthrough_context()
    if expert == "h1_xlp_xly_consumer_rotation_followthrough_v0":
        return _h1_xlp_xly_consumer_rotation_followthrough_context()
    if expert == "h1_xlf_xlu_financials_defensive_rotation_followthrough_v0":
        return _h1_xlf_xlu_financials_defensive_rotation_followthrough_context()
    if expert == "h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0":
        return _h1_xli_xlu_cyclical_defensive_rotation_followthrough_context()
    if expert == "h1_xle_xlu_energy_defensive_rotation_followthrough_v0":
        return _h1_xle_xlu_energy_defensive_rotation_followthrough_context()
    if expert == "xau_xag_relative_value_v0":
        return _xau_xag_relative_value_context()
    if expert == "h4_d1_momentum_expansion_continuation_v0":
        return _h4_d1_momentum_expansion_continuation_context()
    if expert == "h4_financial_conditions_stress_reversal_v0":
        return _h4_financial_conditions_stress_reversal_context()
    if expert == "h4_gdx_gld_miner_divergence_v0":
        return _h4_gdx_gld_miner_divergence_context()
    if expert == "h4_gld_etf_flow_reversal_v0":
        return _h4_gld_etf_flow_reversal_context()
    if expert == "h4_gld_etf_flow_reversal_v1":
        return _h4_gld_etf_flow_reversal_context()
    if expert == "h4_gld_etf_flow_reversal_v2":
        return _h4_gld_etf_flow_reversal_context()
    if expert == "h1_gld_flow_momentum_pullback_v0":
        return _h1_gld_flow_momentum_pullback_context()
    if expert == "h1_gld_flow_stress_followthrough_v0":
        return _h1_gld_flow_stress_followthrough_context()
    if expert == "h1_gld_flow_stress_reversal_v0":
        return _h1_gld_flow_stress_reversal_context()
    if expert == "h1_gld_spy_safe_haven_rotation_followthrough_v0":
        return _h1_gld_spy_safe_haven_rotation_followthrough_context()
    if expert == "h4_gold_futures_volume_climax_v0":
        return _h4_gold_futures_volume_climax_context()
    if expert == "h4_gvz_volatility_panic_reversal_v0":
        return _h4_gvz_volatility_panic_reversal_context()
    if expert == "h4_inside_bar_d1_momentum_breakout_v0":
        return _h4_inside_bar_d1_momentum_breakout_context()
    if expert == "h4_macro_composite_risk_state_v0":
        return _h4_macro_composite_risk_state_context()
    if expert == "h4_macro_composite_risk_state_v1":
        return _h4_macro_composite_risk_state_context()
    if expert == "h4_policy_uncertainty_safe_haven_v0":
        return _h4_policy_uncertainty_safe_haven_context()
    if expert == "h4_real_yield_proxy_momentum_v0":
        return _h4_real_yield_proxy_momentum_context()
    if expert == "h1_real_yield_dollar_shock_reversal_v0":
        return _h1_real_yield_dollar_shock_reversal_context()
    if expert == "h1_real_yield_dollar_shock_followthrough_v0":
        return _h1_real_yield_dollar_shock_followthrough_context()
    if expert == "h4_treasury_curve_stress_momentum_v0":
        return _h4_treasury_curve_stress_momentum_context()
    if expert == "h4_us_session_liquidity_reversal_v0":
        return _h4_us_session_liquidity_reversal_context()
    if expert == "h4_vix_risk_off_reversal_v0":
        return _h4_vix_risk_off_reversal_context()
    if expert == "h4_walk_forward_knn_momentum_state_v0":
        return _h4_walk_forward_knn_momentum_state_context()
    if expert == "xag_lead_xau_followthrough_v0":
        return _xag_lead_xau_followthrough_context()
    if expert == "xau_xag_fx_composite_reversion_v0":
        return _xau_xag_fx_composite_reversion_context()
    if expert == "london_fix_continuation_v0":
        return _london_fix_continuation_context()
    if expert == "liquidity_sweep_continuation_v0":
        return _liquidity_sweep_continuation_context()
    if expert == "liquidity_sweep_reversal_v0":
        return _liquidity_sweep_reversal_context()
    if expert == "m15_inside_bar_breakout_v0":
        return _m15_inside_bar_breakout_context()
    if expert == "m15_two_bar_impulse_continuation_v0":
        return _m15_two_bar_impulse_continuation_context()
    if expert == "m15_two_bar_exhaustion_reversal_v0":
        return _m15_two_bar_exhaustion_reversal_context()
    if expert == "m5_impulse_continuation_v0":
        return _m5_impulse_continuation_context()
    if expert == "ny_failed_london_reversal_v0":
        return _ny_failed_london_reversal_context()
    if expert == "ny_am_pullback_continuation_v0":
        return _ny_am_pullback_continuation_context()
    if expert == "ny_london_overlap_compression_break_v0":
        return _ny_london_overlap_compression_break_context()
    if expert == "opening_drive_failed_continuation_v0":
        return _opening_drive_failed_continuation_context()
    if expert == "post_spike_short_v0":
        return _post_spike_short_context()
    if expert == "previous_day_extreme_retest_v0":
        return _previous_day_extreme_retest_context()
    if expert == "quarter_round_retest_v0":
        return _round_number_retest_context()
    if expert == "round_number_retest_v0":
        return _round_number_retest_context()
    if expert == "session_extreme_retest_v0":
        return _session_extreme_retest_context()
    if expert == "session_vwap_reclaim_v0":
        return _session_vwap_reclaim_context()
    if expert == "symbol_normalized_round_retest_v0":
        return _round_number_retest_context()
    if expert == "symbol_round_sweep_reversal_v0":
        return _symbol_round_sweep_reversal_context()
    if expert == "squeeze_breakout_long_v0":
        return _squeeze_breakout_long_context()
    if expert == "swing_breakout_retest_v0":
        return _swing_breakout_retest_context()
    if expert == "w1_d1_momentum_continuation_v0":
        return _w1_d1_momentum_continuation_context()
    if expert == "weekly_level_reclaim_v0":
        return _weekly_level_reclaim_context()
    if expert == "weekly_open_reversion_v0":
        return _weekly_open_reversion_context()
    raise ValueError(f"Unknown synthetic expert {expert!r}.")


def _base_m5(start: str, periods: int) -> pd.DataFrame:
    times = pd.date_range(start, periods=periods, freq="5min")
    return pd.DataFrame(
        {
            "timestamp_utc": times + pd.Timedelta(minutes=5),
            "bar_start_utc": times,
            "open": [100.0] * periods,
            "high": [100.2] * periods,
            "low": [99.8] * periods,
            "close": [100.0] * periods,
            "mid_open": [100.0] * periods,
            "mid_close": [100.0] * periods,
            "bid_open": [99.9] * periods,
            "ask_open": [100.1] * periods,
            "bid_close": [99.9] * periods,
            "ask_close": [100.1] * periods,
        }
    )


def _trend_context() -> dict:
    m5 = _base_m5("2016-01-04T10:00:00Z", 13)
    m5["low"] = [99.8] * 9 + [99.4, 100.0, 100.0, 100.0]
    m5["open"] = [100.0] * 13
    m5["close"] = [100.0] * 9 + [100.2, 101.8, 101.8, 101.8]
    m5["high"] = [100.2] * 9 + [100.3, 102.2, 102.2, 102.2]
    m5["mid_open"] = m5["open"]
    m5["mid_close"] = m5["close"]
    m5["bid_open"] = m5["open"] - 0.1
    m5["ask_open"] = m5["open"] + 0.1
    m5["bid_close"] = m5["close"] - 0.1
    m5["ask_close"] = m5["close"] + 0.1
    m5["bullish_engulfing"] = [False] * 13
    m5["bearish_engulfing"] = [False] * 13
    m5["bullish_pin_bar"] = [False] * 9 + [True] + [False] * 3
    m5["bearish_pin_bar"] = [False] * 13

    m15 = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-04T10:50:00Z"],
            "open": [100.0],
            "high": [101.0],
            "low": [99.0],
            "close": [100.2],
            "ema21": [100.0],
            "atr14": [2.0],
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": ["2016-01-04T10:00:00Z"],
            "open": [100.0],
            "high": [102.0],
            "low": [98.0],
            "close": [101.0],
            "ema50": [110.0],
            "ema200": [100.0],
            "ema50_slope20": [1.0],
            "atr14": [2.0],
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _breakout_context() -> dict:
    times = pd.date_range("2016-01-05T10:00:00Z", periods=24, freq="5min")
    m5 = _base_m5("2016-01-05T10:00:00Z", 24)
    m5["timestamp_utc"] = times + pd.Timedelta(minutes=5)
    m5["atr14"] = [1.0] * 24
    m5["previous_daily_high"] = [100.0] * 24
    m5["previous_daily_low"] = [90.0] * 24
    m5["previous_weekly_high"] = [pd.NA] * 24
    m5["previous_weekly_low"] = [pd.NA] * 24
    m5["latest_swing_high"] = [pd.NA] * 24
    m5["latest_swing_high_time_utc"] = [pd.NaT] * 24
    m5["latest_swing_low"] = [pd.NA] * 24
    m5["latest_swing_low_time_utc"] = [pd.NaT] * 24
    m5.loc[18, ["open", "high", "low", "close"]] = [100.0, 100.8, 99.8, 100.4]
    m5.loc[20, ["open", "high", "low", "close"]] = [100.2, 100.4, 100.03, 100.1]
    m5.loc[21, ["open", "high", "low", "close"]] = [100.1, 100.5, 100.0, 100.3]
    m5.loc[22, ["open", "high", "low", "close"]] = [100.3, 101.3, 100.3, 101.1]
    for column in ("mid_open", "bid_open", "ask_open"):
        m5[column] = m5["open"]
    for column in ("mid_close", "bid_close", "ask_close"):
        m5[column] = m5["close"]
    m5["bid_open"] = m5["open"] - 0.1
    m5["ask_open"] = m5["open"] + 0.1
    m5["bid_close"] = m5["close"] - 0.1
    m5["ask_close"] = m5["close"] + 0.1
    return {"M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


def _swing_breakout_retest_context() -> dict:
    context = _breakout_context()
    m5 = context["M5"].copy()
    m5["previous_daily_high"] = [pd.NA] * len(m5)
    m5["previous_daily_low"] = [pd.NA] * len(m5)
    m5["previous_weekly_high"] = [pd.NA] * len(m5)
    m5["previous_weekly_low"] = [pd.NA] * len(m5)
    m5["latest_swing_high"] = [100.0] * len(m5)
    m5["latest_swing_high_time_utc"] = [pd.Timestamp("2016-01-05T08:00:00Z")] * len(m5)
    m5["latest_swing_low"] = [90.0] * len(m5)
    m5["latest_swing_low_time_utc"] = [pd.Timestamp("2016-01-05T08:00:00Z")] * len(m5)
    context["M5"] = m5
    return context


def _range_context() -> dict:
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2016-01-04T00:00:00Z", periods=30, freq="1h"),
            "open": [105.0] * 30,
            "high": [106.0] * 30,
            "low": [104.0] * 30,
            "close": [105.0] * 30,
            "adx14": [10.0] * 30,
        }
    )
    highs = [106.0] * 50
    lows = [104.0] * 50
    for index in (0, 10, 20):
        highs[index] = 110.0
    for index in (5, 15, 25):
        lows[index] = 100.0
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2016-01-04T00:00:00Z", periods=50, freq="15min"),
            "open": [105.0] * 50,
            "high": highs,
            "low": lows,
            "close": [105.0] * 50,
            "atr14": [2.0] * 50,
        }
    )
    m5 = _base_m5("2016-01-05T05:00:00Z", 4)
    m5.loc[0, ["open", "high", "low", "close"]] = [100.2, 100.4, 100.1, 100.3]
    m5.loc[1, ["open", "high", "low", "close"]] = [100.2, 100.3, 99.8, 100.1]
    m5.loc[2, ["open", "high", "low", "close"]] = [100.0, 110.5, 100.0, 110.0]
    m5["bullish_pin_bar"] = [True, False, False, False]
    m5["bearish_pin_bar"] = [False, False, False, False]
    return {"H1": h1, "M15": m15, "M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


def _squeeze_breakout_long_context() -> dict:
    m15_times = pd.date_range("2024-01-01T00:15:00Z", periods=140, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 140,
            "high": [102.0] * 120 + [100.1] * 20,
            "low": [98.0] * 120 + [99.9] * 20,
            "close": [100.0] * 140,
        }
    )

    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=430, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 430,
            "high": [100.15] * 430,
            "low": [99.95] * 430,
            "close": [100.0] * 430,
            "atr14": [1.0] * 409 + [0.4] * 21,
            "mid_open": [100.0] * 430,
            "mid_close": [100.0] * 430,
            "bid_open": [99.9] * 430,
            "ask_open": [100.1] * 430,
            "bid_close": [99.9] * 430,
            "ask_close": [100.1] * 430,
        }
    )
    m5.loc[410, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.7, 99.95, 100.55, 0.4]
    m5.loc[410, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.0,
        100.55,
        99.9,
        100.1,
        100.45,
        100.65,
    ]

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T01:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [99.0] * 40,
            "close": [101.0] * 40,
            "ema50": [100.0] * 40,
            "ema50_slope12": [0.1] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _post_spike_short_context() -> dict:
    m5_times = pd.date_range("2024-02-01T00:05:00Z", periods=150, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 150,
            "high": [100.2] * 150,
            "low": [99.8] * 150,
            "close": [100.0] * 150,
            "atr14": [0.5] * 150,
            "mid_open": [100.0] * 150,
            "mid_close": [100.0] * 150,
            "bid_open": [99.9] * 150,
            "ask_open": [100.1] * 150,
            "bid_close": [99.9] * 150,
            "ask_close": [100.1] * 150,
        }
    )
    m5.loc[120, ["open", "high", "low", "close"]] = [100.0, 100.8, 99.95, 100.7]
    m5.loc[121, ["open", "high", "low", "close"]] = [100.7, 101.35, 100.6, 101.2]
    m5.loc[122, ["open", "high", "low", "close"]] = [101.2, 101.55, 101.0, 101.35]
    m5.loc[123, ["open", "high", "low", "close"]] = [101.4, 101.60, 100.75, 100.85]
    for idx in (120, 121, 122, 123):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-02-01T00:15:00Z", periods=60, freq="15min"),
            "open": [100.0] * 60,
            "high": [100.5] * 60,
            "low": [99.4] * 60,
            "close": [100.0] * 60,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-31T00:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [101.0] * 60,
            "low": [99.0] * 60,
            "close": [99.6] * 60,
            "ema50": [100.0] * 60,
            "ema50_slope12": [-0.1] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _emr_inactivity_long_context() -> dict:
    m15_times = pd.date_range("2024-03-01T00:15:00Z", periods=150, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 150,
            "high": [102.0] * 120 + [100.08] * 30,
            "low": [98.0] * 120 + [99.92] * 30,
            "close": [100.0] * 150,
        }
    )

    m5_times = pd.date_range("2024-03-01T00:05:00Z", periods=440, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 440,
            "high": [100.10] * 440,
            "low": [99.90] * 440,
            "close": [100.0] * 440,
            "atr14": [1.0] * 408 + [0.35] * 32,
            "mid_open": [100.0] * 440,
            "mid_close": [100.0] * 440,
            "bid_open": [99.9] * 440,
            "ask_open": [100.1] * 440,
            "bid_close": [99.9] * 440,
            "ask_close": [100.1] * 440,
        }
    )
    m5.loc[410, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.05, 99.20, 99.35, 0.35]
    m5.loc[411, ["open", "high", "low", "close", "atr14"]] = [99.35, 99.45, 98.95, 99.05, 0.35]
    m5.loc[412, ["open", "high", "low", "close", "atr14"]] = [99.05, 99.10, 98.80, 98.90, 0.35]
    m5.loc[413, ["open", "high", "low", "close", "atr14"]] = [98.90, 100.15, 98.75, 100.05, 0.35]
    for idx in (410, 411, 412, 413):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T01:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [101.0] * 60,
            "low": [99.0] * 60,
            "close": [99.8] * 60,
            "ema50": [100.0] * 60,
            "ema50_slope12": [-0.05] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _ny_failed_london_reversal_context() -> dict:
    m5_times = pd.date_range("2024-04-01T06:05:00Z", periods=160, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 160,
            "high": [100.3] * 160,
            "low": [99.7] * 160,
            "close": [100.0] * 160,
            "atr14": [0.5] * 160,
            "mid_open": [100.0] * 160,
            "mid_close": [100.0] * 160,
            "bid_open": [99.9] * 160,
            "ask_open": [100.1] * 160,
            "bid_close": [99.9] * 160,
            "ask_close": [100.1] * 160,
        }
    )
    london_mask = (m5["bar_start_utc"].dt.hour >= 7) & (m5["bar_start_utc"].dt.hour < 11)
    m5.loc[london_mask, ["high", "low"]] = [101.0, 99.0]
    m5.loc[90, ["open", "high", "low", "close"]] = [101.50, 101.60, 100.40, 100.60]
    m5.loc[90, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        101.50,
        100.60,
        101.40,
        101.60,
        100.50,
        100.70,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T06:15:00Z", periods=60, freq="15min"),
            "open": [100.0] * 60,
            "high": [101.0] * 60,
            "low": [99.0] * 60,
            "close": [100.0] * 60,
            "atr14": [1.2] * 60,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T01:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _liquidity_sweep_reversal_context() -> dict:
    m5_times = pd.date_range("2024-04-01T00:05:00Z", periods=440, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 440,
            "high": [100.2] * 440,
            "low": [99.8] * 440,
            "close": [100.0] * 440,
            "atr14": [0.5] * 440,
            "mid_open": [100.0] * 440,
            "mid_close": [100.0] * 440,
            "bid_open": [99.9] * 440,
            "ask_open": [100.1] * 440,
            "bid_close": [99.9] * 440,
            "ask_close": [100.1] * 440,
        }
    )
    first_day = m5["bar_start_utc"].dt.strftime("%Y-%m-%d") == "2024-04-01"
    m5.loc[first_day, ["high", "low"]] = [101.0, 99.0]
    m5.loc[390, ["open", "high", "low", "close"]] = [101.15, 102.00, 100.30, 100.55]
    m5.loc[390, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        101.15,
        100.55,
        101.05,
        101.25,
        100.45,
        100.65,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T00:15:00Z", periods=120, freq="15min"),
            "open": [100.0] * 120,
            "high": [101.0] * 120,
            "low": [99.0] * 120,
            "close": [100.0] * 120,
            "atr14": [1.2] * 120,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T00:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [98.0] * 40,
            "close": [100.0] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _liquidity_sweep_continuation_context() -> dict:
    context = _liquidity_sweep_reversal_context()
    m5 = context["M5"].copy()
    m5.loc[390, ["open", "high", "low", "close"]] = [100.95, 101.70, 100.85, 101.45]
    m5.loc[390, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.95,
        101.45,
        100.85,
        101.05,
        101.35,
        101.55,
    ]
    context["M5"] = m5
    return context


def _daily_pivot_reclaim_context() -> dict:
    m5_times = pd.date_range("2024-04-01T00:05:00Z", periods=440, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 440,
            "high": [100.2] * 440,
            "low": [99.8] * 440,
            "close": [100.0] * 440,
            "atr14": [0.5] * 440,
            "mid_open": [100.0] * 440,
            "mid_close": [100.0] * 440,
            "bid_open": [99.9] * 440,
            "ask_open": [100.1] * 440,
            "bid_close": [99.9] * 440,
            "ask_close": [100.1] * 440,
        }
    )
    first_day = m5["bar_start_utc"].dt.strftime("%Y-%m-%d") == "2024-04-01"
    m5.loc[first_day, ["high", "low", "close"]] = [101.0, 99.0, 100.0]
    m5.loc[390, ["open", "high", "low", "close"]] = [99.65, 100.45, 99.35, 100.30]
    m5.loc[390, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        99.65,
        100.30,
        99.55,
        99.75,
        100.20,
        100.40,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T00:15:00Z", periods=120, freq="15min"),
            "open": [100.0] * 120,
            "high": [101.0] * 120,
            "low": [99.0] * 120,
            "close": [100.0] * 120,
            "atr14": [1.0] * 120,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-04-01T00:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [98.0] * 40,
            "close": [100.0] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_momentum_h4_pullback_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=90, freq="1D")
    d1_closes = [100.0 + 0.55 * index for index in range(90)]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.2 for close in d1_closes],
            "high": [close + 1.0 for close in d1_closes],
            "low": [close - 1.0 for close in d1_closes],
            "close": d1_closes,
        }
    )

    h4_times = pd.date_range("2024-03-01T00:00:00Z", periods=180, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [130.0] * 180,
            "high": [130.35] * 180,
            "low": [129.65] * 180,
            "close": [130.0] * 180,
        }
    )
    h4.loc[120, ["open", "high", "low", "close"]] = [129.85, 131.35, 129.45, 130.85]

    m5_times = pd.date_range("2024-03-01T00:05:00Z", periods=9000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [130.0] * 9000,
            "high": [130.5] * 9000,
            "low": [129.5] * 9000,
            "close": [130.0] * 9000,
            "mid_open": [130.0] * 9000,
            "mid_close": [130.0] * 9000,
            "bid_open": [129.9] * 9000,
            "ask_open": [130.1] * 9000,
            "bid_close": [129.9] * 9000,
            "ask_close": [130.1] * 9000,
        }
    )

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:15:00Z", periods=3000, freq="15min"),
            "open": [130.0] * 3000,
            "high": [130.5] * 3000,
            "low": [129.5] * 3000,
            "close": [130.0] * 3000,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:00:00Z", periods=760, freq="1h"),
            "open": [130.0] * 760,
            "high": [130.5] * 760,
            "low": [129.5] * 760,
            "close": [130.0] * 760,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_compression_h4_expansion_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=82, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * 82,
            "high": [102.0] * 82,
            "low": [98.0] * 82,
            "close": [100.0] * 82,
        }
    )
    for idx in range(60, 82):
        d1.loc[idx, ["open", "high", "low", "close"]] = [100.0, 100.4, 99.6, 100.0]

    h4_times = pd.date_range("2024-03-05T00:00:00Z", periods=110, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 110,
            "high": [100.5] * 110,
            "low": [99.5] * 110,
            "close": [100.0] * 110,
        }
    )
    h4.loc[33, ["open", "high", "low", "close"]] = [100.0, 102.0, 99.6, 101.8]

    m5_times = pd.date_range("2024-03-05T00:05:00Z", periods=8000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [101.8] * 8000,
            "high": [102.4] * 8000,
            "low": [101.2] * 8000,
            "close": [101.8] * 8000,
            "mid_open": [101.8] * 8000,
            "mid_close": [101.8] * 8000,
            "bid_open": [101.7] * 8000,
            "ask_open": [101.9] * 8000,
            "bid_close": [101.7] * 8000,
            "ask_close": [101.9] * 8000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-05T00:15:00Z", periods=2700, freq="15min"),
            "open": [101.8] * 2700,
            "high": [102.4] * 2700,
            "low": [101.2] * 2700,
            "close": [101.8] * 2700,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-05T00:00:00Z", periods=680, freq="1h"),
            "open": [101.8] * 680,
            "high": [102.4] * 680,
            "low": [101.2] * 680,
            "close": [101.8] * 680,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_multi_day_exhaustion_reversion_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=80, freq="1D")
    d1_closes = [100.0] * 80
    for idx in range(55, 80):
        d1_closes[idx] = d1_closes[idx - 1] + 1.2
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.3 for close in d1_closes],
            "high": [close + 0.8 for close in d1_closes],
            "low": [close - 0.8 for close in d1_closes],
            "close": d1_closes,
        }
    )

    h4_times = pd.date_range("2024-03-10T00:00:00Z", periods=120, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [128.0] * 120,
            "high": [128.7] * 120,
            "low": [127.3] * 120,
            "close": [128.0] * 120,
        }
    )
    h4.loc[31, ["open", "high", "low", "close"]] = [130.4, 131.2, 128.6, 129.0]

    m5_times = pd.date_range("2024-03-10T00:05:00Z", periods=8000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [129.0] * 8000,
            "high": [129.6] * 8000,
            "low": [128.4] * 8000,
            "close": [129.0] * 8000,
            "mid_open": [129.0] * 8000,
            "mid_close": [129.0] * 8000,
            "bid_open": [128.9] * 8000,
            "ask_open": [129.1] * 8000,
            "bid_close": [128.9] * 8000,
            "ask_close": [129.1] * 8000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-10T00:15:00Z", periods=2700, freq="15min"),
            "open": [129.0] * 2700,
            "high": [129.6] * 2700,
            "low": [128.4] * 2700,
            "close": [129.0] * 2700,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-10T00:00:00Z", periods=680, freq="1h"),
            "open": [129.0] * 680,
            "high": [129.6] * 680,
            "low": [128.4] * 680,
            "close": [129.0] * 680,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _h4_d1_momentum_expansion_continuation_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=90, freq="1D")
    d1_closes = [100.0 + 0.45 * index for index in range(90)]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.2 for close in d1_closes],
            "high": [close + 0.9 for close in d1_closes],
            "low": [close - 0.9 for close in d1_closes],
            "close": d1_closes,
        }
    )

    h4_times = pd.date_range("2024-03-01T00:00:00Z", periods=180, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [130.0] * 180,
            "high": [130.45] * 180,
            "low": [129.55] * 180,
            "close": [130.0] * 180,
        }
    )
    h4.loc[120, ["open", "high", "low", "close"]] = [130.0, 131.8, 129.8, 131.55]

    m5_times = pd.date_range("2024-03-01T00:05:00Z", periods=9000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [131.55] * 9000,
            "high": [132.2] * 9000,
            "low": [130.9] * 9000,
            "close": [131.55] * 9000,
            "mid_open": [131.55] * 9000,
            "mid_close": [131.55] * 9000,
            "bid_open": [131.45] * 9000,
            "ask_open": [131.65] * 9000,
            "bid_close": [131.45] * 9000,
            "ask_close": [131.65] * 9000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:15:00Z", periods=3000, freq="15min"),
            "open": [131.55] * 3000,
            "high": [132.2] * 3000,
            "low": [130.9] * 3000,
            "close": [131.55] * 3000,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:00:00Z", periods=760, freq="1h"),
            "open": [131.55] * 760,
            "high": [132.2] * 760,
            "low": [130.9] * 760,
            "close": [131.55] * 760,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _h4_inside_bar_d1_momentum_breakout_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=90, freq="1D")
    d1_closes = [100.0 + 0.35 * index for index in range(90)]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.2 for close in d1_closes],
            "high": [close + 0.9 for close in d1_closes],
            "low": [close - 0.9 for close in d1_closes],
            "close": d1_closes,
        }
    )

    h4_times = pd.date_range("2024-03-01T00:00:00Z", periods=180, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [130.0] * 180,
            "high": [130.7] * 180,
            "low": [129.3] * 180,
            "close": [130.0] * 180,
        }
    )
    h4.loc[118, ["open", "high", "low", "close"]] = [130.0, 131.2, 128.8, 130.4]
    h4.loc[119, ["open", "high", "low", "close"]] = [130.3, 130.8, 129.7, 130.2]
    h4.loc[120, ["open", "high", "low", "close"]] = [130.4, 132.0, 130.1, 131.8]

    m5_times = pd.date_range("2024-03-01T00:05:00Z", periods=9000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [131.8] * 9000,
            "high": [132.4] * 9000,
            "low": [131.2] * 9000,
            "close": [131.8] * 9000,
            "mid_open": [131.8] * 9000,
            "mid_close": [131.8] * 9000,
            "bid_open": [131.7] * 9000,
            "ask_open": [131.9] * 9000,
            "bid_close": [131.7] * 9000,
            "ask_close": [131.9] * 9000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:15:00Z", periods=3000, freq="15min"),
            "open": [131.8] * 3000,
            "high": [132.4] * 3000,
            "low": [131.2] * 3000,
            "close": [131.8] * 3000,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-03-01T00:00:00Z", periods=760, freq="1h"),
            "open": [131.8] * 760,
            "high": [132.4] * 760,
            "low": [131.2] * 760,
            "close": [131.8] * 760,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _h4_real_yield_proxy_momentum_context() -> dict:
    macro_dates = pd.bdate_range("2022-01-03", periods=360, tz="UTC")
    real_yield: list[float] = []
    dollar_index: list[float] = []
    for index in range(360):
        if index < 240:
            real_yield.append(2.50 + (0.01 if index % 2 else -0.01))
            dollar_index.append(110.0 + (0.05 if index % 2 else -0.04))
        else:
            real_yield.append(2.50 - 0.015 * (index - 239))
            dollar_index.append(110.0 - 0.075 * (index - 239))
    macro = pd.DataFrame(
        {
            "timestamp_utc": macro_dates,
            "real_yield_10y": real_yield,
            "dollar_index_broad": dollar_index,
        }
    )

    h4_periods = 240
    h4_times = pd.date_range(macro_dates[270] + pd.Timedelta(hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.24 if index % 5 else -0.03
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=60, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 60,
            "high": [2005.0] * 60,
            "low": [1995.0] * 60,
            "close": [2001.0] * 60,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h4_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "macro_proxy": macro,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_real_yield_dollar_shock_reversal_context() -> dict:
    macro_dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    real_yield: list[float] = []
    dollar_index: list[float] = []
    for index in range(560):
        if index < 430:
            real_yield.append(1.60 + (0.006 if index % 2 else -0.006))
            dollar_index.append(110.0 + (0.025 if index % 2 else -0.020))
        else:
            real_yield.append(1.60 + 0.014 * (index - 429))
            dollar_index.append(110.0 + 0.030 * (index - 429))
    macro = pd.DataFrame(
        {
            "timestamp_utc": macro_dates,
            "real_yield_10y": real_yield,
            "dollar_index_broad": dollar_index,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(macro_dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.04 if index % 5 else -0.02
        elif index < signal_index:
            current -= 0.45
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.05 if index % 4 else -0.03
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 2.0)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.03 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        MACRO_FRAME_KEY: macro,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_real_yield_dollar_shock_followthrough_context() -> dict:
    macro_dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    real_yield: list[float] = []
    dollar_index: list[float] = []
    for index in range(560):
        if index < 430:
            real_yield.append(1.60 + (0.006 if index % 2 else -0.006))
            dollar_index.append(110.0 + (0.025 if index % 2 else -0.020))
        else:
            real_yield.append(1.60 + 0.014 * (index - 429))
            dollar_index.append(110.0 + 0.030 * (index - 429))
    macro = pd.DataFrame(
        {
            "timestamp_utc": macro_dates,
            "real_yield_10y": real_yield,
            "dollar_index_broad": dollar_index,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(macro_dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current -= 0.36
        elif index == signal_index:
            current -= 0.95
        else:
            current -= 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.20)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 - 0.03 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [1999.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close - 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close - 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close - 0.6] * 1200,
            "ask_close": [last_close - 0.4] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        MACRO_FRAME_KEY: macro,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_tlt_uup_pressure_reversion_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    tlt_close: list[float] = []
    uup_close: list[float] = []
    tlt_volume: list[float] = []
    uup_volume: list[float] = []
    for index in range(560):
        if index < 430:
            tlt_close.append(100.0 + (0.04 if index % 2 else -0.03))
            uup_close.append(28.0 + (0.01 if index % 2 else -0.01))
        else:
            step = index - 429
            tlt_close.append(100.0 + 0.18 * step)
            uup_close.append(28.0 - 0.035 * step)
        tlt_volume.append(12_000_000.0 + 20_000.0 * (index % 13))
        uup_volume.append(2_000_000.0 + 10_000.0 * (index % 11))
    pressure = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "tlt_close": tlt_close,
            "tlt_volume": tlt_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.04 if index % 5 else -0.02
        elif index < signal_index:
            current -= 0.42
        elif index == signal_index:
            current += 0.95
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 2.0)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        TLT_UUP_PRESSURE_FRAME_KEY: pressure,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_tlt_uup_pressure_followthrough_context() -> dict:
    context = _h1_tlt_uup_pressure_reversion_context()
    pressure = context[TLT_UUP_PRESSURE_FRAME_KEY]
    h1_periods = 420
    signal_index = 300
    dates = pd.to_datetime(pressure["timestamp_utc"], utc=True)
    h1_times = pd.date_range(dates.iloc[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.03 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.34
        elif index == signal_index:
            current += 0.85
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)
    context["H1"] = h1

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    context["M5"] = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return context


def _h1_tlt_shy_duration_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    tlt_close: list[float] = []
    shy_close: list[float] = []
    tlt_volume: list[float] = []
    shy_volume: list[float] = []
    for index in range(560):
        if index < 430:
            tlt_close.append(100.0 + (0.04 if index % 2 else -0.03))
            shy_close.append(82.0 + (0.005 if index % 2 else -0.005))
        else:
            step = index - 429
            tlt_close.append(100.0 + 0.18 * step)
            shy_close.append(82.0 - 0.004 * step)
        tlt_volume.append(12_000_000.0 + 20_000.0 * (index % 13))
        shy_volume.append(4_000_000.0 + 8_000.0 * (index % 11))
    pressure = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "tlt_close": tlt_close,
            "tlt_volume": tlt_volume,
            "shy_close": shy_close,
            "shy_volume": shy_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.03 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.34
        elif index == signal_index:
            current += 0.85
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        TLT_SHY_DURATION_ROTATION_FRAME_KEY: pressure,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_spy_tlt_risk_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    spy_close: list[float] = []
    tlt_close: list[float] = []
    spy_volume: list[float] = []
    tlt_volume: list[float] = []
    for index in range(560):
        if index < 430:
            spy_close.append(420.0 + (0.06 if index % 2 else -0.04))
            tlt_close.append(105.0 + (0.03 if index % 2 else -0.02))
        else:
            step = index - 429
            spy_close.append(420.0 - 0.82 * step)
            tlt_close.append(105.0 + 0.36 * step)
        spy_volume.append(80_000_000.0 + 150_000.0 * (index % 17))
        tlt_volume.append(35_000_000.0 + 95_000.0 * (index % 13))
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "spy_close": spy_close,
            "spy_volume": spy_volume,
            "tlt_close": tlt_close,
            "tlt_volume": tlt_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.03 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.34
        elif index == signal_index:
            current += 0.85
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        SPY_TLT_RISK_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_tip_ief_real_yield_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    tip_close: list[float] = []
    ief_close: list[float] = []
    tip_volume: list[float] = []
    ief_volume: list[float] = []
    for index in range(560):
        if index < 430:
            tip_close.append(100.0 + (0.02 if index % 2 else -0.02))
            ief_close.append(105.0 + (0.02 if index % 2 else -0.02))
        else:
            step = index - 429
            tip_close.append(100.0 + 0.10 * step)
            ief_close.append(105.0 - 0.10 * step)
        tip_volume.append(2_500_000.0 + 12_000.0 * (index % 17))
        ief_volume.append(7_000_000.0 + 18_000.0 * (index % 13))
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "tip_close": tip_close,
            "tip_volume": tip_volume,
            "ief_close": ief_close,
            "ief_volume": ief_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.03 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.34
        elif index == signal_index:
            current += 0.85
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        TIP_IEF_REAL_YIELD_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_dbc_uup_commodity_dollar_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    dbc_close: list[float] = []
    uup_close: list[float] = []
    dbc_volume: list[float] = []
    uup_volume: list[float] = []
    for index in range(560):
        if index < 430:
            dbc_close.append(24.0 + (0.02 if index % 2 else -0.02))
            uup_close.append(28.0 + (0.01 if index % 2 else -0.01))
        else:
            step = index - 429
            dbc_close.append(24.0 + 0.08 * step)
            uup_close.append(28.0 - 0.025 * step)
        dbc_volume.append(2_800_000.0 + 14_000.0 * (index % 17))
        uup_volume.append(2_000_000.0 + 10_000.0 * (index % 13))
    pressure = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "dbc_close": dbc_close,
            "dbc_volume": dbc_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.03 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.34
        elif index == signal_index:
            current += 0.85
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        DBC_UUP_COMMODITY_DOLLAR_FRAME_KEY: pressure,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_uso_uup_oil_dollar_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    uso_close: list[float] = []
    uup_close: list[float] = []
    uso_volume: list[float] = []
    uup_volume: list[float] = []
    for index in range(560):
        if index < 430:
            uso_close.append(70.0 + (0.08 if index % 2 else -0.08))
            uup_close.append(28.0 + (0.01 if index % 2 else -0.01))
        else:
            step = index - 429
            uso_close.append(70.0 + 0.220 * step)
            uup_close.append(28.0 - 0.025 * step)
        uso_volume.append(3_800_000.0 + 18_000.0 * (index % 17))
        uup_volume.append(2_000_000.0 + 10_000.0 * (index % 13))
    pressure = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "uso_close": uso_close,
            "uso_volume": uso_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.03 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.34
        elif index == signal_index:
            current += 0.85
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        USO_UUP_OIL_DOLLAR_FRAME_KEY: pressure,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_dbb_uup_industrial_metals_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    dbb_close: list[float] = []
    uup_close: list[float] = []
    dbb_volume: list[float] = []
    uup_volume: list[float] = []
    for index in range(560):
        if index < 430:
            dbb_close.append(20.0 + (0.015 if index % 2 else -0.015))
            uup_close.append(28.0 + (0.01 if index % 2 else -0.01))
        else:
            step = index - 429
            dbb_close.append(20.0 + 0.065 * step)
            uup_close.append(28.0 - 0.020 * step)
        dbb_volume.append(850_000.0 + 7_000.0 * (index % 17))
        uup_volume.append(2_000_000.0 + 10_000.0 * (index % 13))
    pressure = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "dbb_close": dbb_close,
            "dbb_volume": dbb_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.31
        elif index == signal_index:
            current += 0.78
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        DBB_UUP_INDUSTRIAL_METALS_FRAME_KEY: pressure,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_hyg_ief_credit_risk_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    hyg_close: list[float] = []
    ief_close: list[float] = []
    hyg_volume: list[float] = []
    ief_volume: list[float] = []
    for index in range(560):
        if index < 430:
            hyg_close.append(82.0 + (0.03 if index % 2 else -0.03))
            ief_close.append(102.0 + (0.02 if index % 2 else -0.02))
        else:
            step = index - 429
            hyg_close.append(82.0 - 0.075 * step)
            ief_close.append(102.0 + 0.075 * step)
        hyg_volume.append(18_000_000.0 + 60_000.0 * (index % 17))
        ief_volume.append(7_000_000.0 + 30_000.0 * (index % 13))
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "hyg_close": hyg_close,
            "hyg_volume": hyg_volume,
            "ief_close": ief_close,
            "ief_volume": ief_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.32
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        HYG_IEF_CREDIT_RISK_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_xlu_xlk_defensive_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    xlu_close: list[float] = []
    xlk_close: list[float] = []
    xlu_volume: list[float] = []
    xlk_volume: list[float] = []
    for index in range(560):
        if index < 430:
            xlu_close.append(70.0 + (0.03 if index % 2 else -0.03))
            xlk_close.append(150.0 + (0.05 if index % 2 else -0.05))
        else:
            step = index - 429
            xlu_close.append(70.0 + 0.120 * step)
            xlk_close.append(150.0 - 0.120 * step)
        xlu_volume.append(12_000_000.0 + 45_000.0 * (index % 17))
        xlk_volume.append(6_000_000.0 + 28_000.0 * (index % 13))
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "xlu_close": xlu_close,
            "xlu_volume": xlu_volume,
            "xlk_close": xlk_close,
            "xlk_volume": xlk_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.32
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        XLU_XLK_DEFENSIVE_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_xlp_xly_consumer_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    xlp_close: list[float] = []
    xly_close: list[float] = []
    xlp_volume: list[float] = []
    xly_volume: list[float] = []
    for index in range(560):
        if index < 430:
            xlp_close.append(75.0 + (0.03 if index % 2 else -0.03))
            xly_close.append(180.0 + (0.06 if index % 2 else -0.06))
        else:
            step = index - 429
            xlp_close.append(75.0 + 0.115 * step)
            xly_close.append(180.0 - 0.115 * step)
        xlp_volume.append(9_000_000.0 + 35_000.0 * (index % 17))
        xly_volume.append(5_500_000.0 + 24_000.0 * (index % 13))
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "xlp_close": xlp_close,
            "xlp_volume": xlp_volume,
            "xly_close": xly_close,
            "xly_volume": xly_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.32
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        XLP_XLY_CONSUMER_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_xlf_xlu_financials_defensive_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    xlf_close: list[float] = []
    xlu_close: list[float] = []
    xlf_volume: list[float] = []
    xlu_volume: list[float] = []
    for index in range(560):
        if index < 430:
            xlf_close.append(39.0 + (0.03 if index % 2 else -0.03))
            xlu_close.append(70.0 + (0.03 if index % 2 else -0.03))
        else:
            step = index - 429
            xlf_close.append(39.0 - 0.075 * step)
            xlu_close.append(70.0 + 0.110 * step)
        xlf_volume.append(42_000_000.0 + 70_000.0 * (index % 17))
        xlu_volume.append(12_000_000.0 + 45_000.0 * (index % 13))
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "xlf_close": xlf_close,
            "xlf_volume": xlf_volume,
            "xlu_close": xlu_close,
            "xlu_volume": xlu_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.32
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        XLF_XLU_FINANCIALS_DEFENSIVE_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_xli_xlu_cyclical_defensive_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    xli_close: list[float] = []
    xlu_close: list[float] = []
    xli_volume: list[float] = []
    xlu_volume: list[float] = []
    for index in range(560):
        if index < 430:
            xli_close.append(98.0 + (0.04 if index % 2 else -0.04))
            xlu_close.append(70.0 + (0.03 if index % 2 else -0.03))
        else:
            step = index - 429
            xli_close.append(98.0 - 0.130 * step)
            xlu_close.append(70.0 + 0.115 * step)
        xli_volume.append(10_000_000.0 + 39_000.0 * (index % 17))
        xlu_volume.append(12_000_000.0 + 45_000.0 * (index % 13))
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "xli_close": xli_close,
            "xli_volume": xli_volume,
            "xlu_close": xlu_close,
            "xlu_volume": xlu_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.32
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        XLI_XLU_CYCLICAL_DEFENSIVE_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_xle_xlu_energy_defensive_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    xle_close: list[float] = []
    xlu_close: list[float] = []
    xle_volume: list[float] = []
    xlu_volume: list[float] = []
    for index in range(560):
        if index < 430:
            xle_close.append(64.0 + (0.05 if index % 2 else -0.05))
            xlu_close.append(70.0 + (0.03 if index % 2 else -0.03))
        else:
            step = index - 429
            xle_close.append(64.0 + 0.155 * step)
            xlu_close.append(70.0 - 0.020 * step)
        xle_volume.append(22_000_000.0 + 53_000.0 * (index % 17))
        xlu_volume.append(12_000_000.0 + 45_000.0 * (index % 13))
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "xle_close": xle_close,
            "xle_volume": xle_volume,
            "xlu_close": xlu_close,
            "xlu_volume": xlu_volume,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.32
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        XLE_XLU_ENERGY_DEFENSIVE_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_audjpy_usdjpy_fx_carry_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    audjpy_close: list[float] = []
    usdjpy_close: list[float] = []
    for index in range(560):
        if index < 430:
            audjpy_close.append(82.0 + (0.04 if index % 2 else -0.04))
            usdjpy_close.append(110.0 + (0.03 if index % 2 else -0.03))
        else:
            step = index - 429
            audjpy_close.append(82.0 - 0.115 * step)
            usdjpy_close.append(110.0 + 0.020 * step)
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "audjpy_close": audjpy_close,
            "usdjpy_close": usdjpy_close,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.32
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        AUDJPY_USDJPY_FX_CARRY_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=560, tz="UTC")
    eurjpy_close: list[float] = []
    usdjpy_close: list[float] = []
    for index in range(560):
        if index < 430:
            eurjpy_close.append(129.0 + (0.04 if index % 2 else -0.04))
            usdjpy_close.append(110.0 + (0.03 if index % 2 else -0.03))
        else:
            step = index - 429
            eurjpy_close.append(129.0 - 0.180 * step)
            usdjpy_close.append(110.0 + 0.030 * step)
    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "eurjpy_close": eurjpy_close,
            "usdjpy_close": usdjpy_close,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.02 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.32
        elif index == signal_index:
            current += 0.80
        else:
            current += 0.04 if index % 4 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    h4_times = pd.date_range(h1_times[0] + pd.Timedelta(hours=4), periods=120, freq="4h")
    h4_closes = [2000.0 + 0.02 * index for index in range(120)]
    h4 = _ohlc_from_closes(h4_times, h4_closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h1_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2008.0] * 40,
            "low": [1992.0] * 40,
            "close": [2001.0] * 40,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        EURJPY_USDJPY_FX_RISK_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_eem_spy_em_risk_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    eem_close: list[float] = []
    spy_close: list[float] = []
    eem_volume: list[float] = []
    spy_volume: list[float] = []
    eem_current = 50.0
    spy_current = 375.0
    for index in range(560):
        if index < 430:
            eem_current *= 1.0005 if index % 2 else 0.9994
            spy_current *= 1.0004 if index % 2 else 0.9996
        else:
            step = index - 429
            eem_current *= 0.9910
            spy_current *= 0.9980
            eem_volume.append(35_000_000.0 + 55_000.0 * step)
            spy_volume.append(80_000_000.0 + 40_000.0 * step)
            eem_close.append(eem_current)
            spy_close.append(spy_current)
            continue
        eem_volume.append(28_000_000.0 + 80_000.0 * (index % 7))
        spy_volume.append(70_000_000.0 + 100_000.0 * (index % 5))
        eem_close.append(eem_current)
        spy_close.append(spy_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "eem_close": eem_close,
            "eem_volume": eem_volume,
            "spy_close": spy_close,
            "spy_volume": spy_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        EEM_SPY_EM_RISK_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_acwx_spy_global_ex_us_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    acwx_close: list[float] = []
    spy_close: list[float] = []
    acwx_volume: list[float] = []
    spy_volume: list[float] = []
    acwx_current = 55.0
    spy_current = 375.0
    for index in range(560):
        if index < 430:
            acwx_current *= 1.0004 if index % 2 else 0.9995
            spy_current *= 1.0004 if index % 2 else 0.9996
        else:
            step = index - 429
            acwx_current *= 0.9910
            spy_current *= 0.9980
            acwx_volume.append(12_000_000.0 + 35_000.0 * step)
            spy_volume.append(80_000_000.0 + 40_000.0 * step)
            acwx_close.append(acwx_current)
            spy_close.append(spy_current)
            continue
        acwx_volume.append(8_000_000.0 + 35_000.0 * (index % 7))
        spy_volume.append(70_000_000.0 + 100_000.0 * (index % 5))
        acwx_close.append(acwx_current)
        spy_close.append(spy_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "acwx_close": acwx_close,
            "acwx_volume": acwx_volume,
            "spy_close": spy_close,
            "spy_volume": spy_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        ACWX_SPY_GLOBAL_EX_US_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_xme_spy_metals_mining_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    xme_close: list[float] = []
    spy_close: list[float] = []
    xme_volume: list[float] = []
    spy_volume: list[float] = []
    xme_current = 34.0
    spy_current = 375.0
    for index in range(560):
        if index < 430:
            xme_current *= 1.0007 if index % 2 else 0.9993
            spy_current *= 1.0004 if index % 2 else 0.9996
        else:
            step = index - 429
            xme_current *= 0.9900
            spy_current *= 0.9980
            xme_volume.append(5_500_000.0 + 30_000.0 * step)
            spy_volume.append(80_000_000.0 + 40_000.0 * step)
            xme_close.append(xme_current)
            spy_close.append(spy_current)
            continue
        xme_volume.append(4_500_000.0 + 25_000.0 * (index % 7))
        spy_volume.append(70_000_000.0 + 100_000.0 * (index % 5))
        xme_close.append(xme_current)
        spy_close.append(spy_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "xme_close": xme_close,
            "xme_volume": xme_volume,
            "spy_close": spy_close,
            "spy_volume": spy_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        XME_SPY_METALS_MINING_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_fxy_uup_safe_haven_fx_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    fxy_close: list[float] = []
    uup_close: list[float] = []
    fxy_volume: list[float] = []
    uup_volume: list[float] = []
    fxy_current = 80.0
    uup_current = 25.0
    for index in range(560):
        if index < 430:
            fxy_current *= 1.0002 if index % 2 else 0.9998
            uup_current *= 1.0001 if index % 2 else 0.9999
        else:
            step = index - 429
            fxy_current *= 1.0100
            uup_current *= 0.9980
            fxy_volume.append(1_500_000.0 + 12_000.0 * step)
            uup_volume.append(2_500_000.0 + 10_000.0 * step)
            fxy_close.append(fxy_current)
            uup_close.append(uup_current)
            continue
        fxy_volume.append(1_200_000.0 + 10_000.0 * (index % 7))
        uup_volume.append(2_000_000.0 + 15_000.0 * (index % 5))
        fxy_close.append(fxy_current)
        uup_close.append(uup_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "fxy_close": fxy_close,
            "fxy_volume": fxy_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        FXY_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_fxf_uup_safe_haven_fx_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    fxf_close: list[float] = []
    uup_close: list[float] = []
    fxf_volume: list[float] = []
    uup_volume: list[float] = []
    fxf_current = 95.0
    uup_current = 25.0
    for index in range(560):
        if index < 430:
            fxf_current *= 1.0002 if index % 2 else 0.9998
            uup_current *= 1.0001 if index % 2 else 0.9999
        else:
            step = index - 429
            fxf_current *= 1.0090
            uup_current *= 0.9980
            fxf_volume.append(450_000.0 + 5_000.0 * step)
            uup_volume.append(2_500_000.0 + 10_000.0 * step)
            fxf_close.append(fxf_current)
            uup_close.append(uup_current)
            continue
        fxf_volume.append(380_000.0 + 4_000.0 * (index % 7))
        uup_volume.append(2_000_000.0 + 15_000.0 * (index % 5))
        fxf_close.append(fxf_current)
        uup_close.append(uup_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "fxf_close": fxf_close,
            "fxf_volume": fxf_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        FXF_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_fxe_uup_euro_dollar_fx_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    fxe_close: list[float] = []
    uup_close: list[float] = []
    fxe_volume: list[float] = []
    uup_volume: list[float] = []
    fxe_current = 105.0
    uup_current = 25.0
    for index in range(560):
        if index < 430:
            fxe_current *= 1.0002 if index % 2 else 0.9998
            uup_current *= 1.0001 if index % 2 else 0.9999
        else:
            step = index - 429
            fxe_current *= 1.0095
            uup_current *= 0.9980
            fxe_volume.append(900_000.0 + 7_500.0 * step)
            uup_volume.append(2_500_000.0 + 10_000.0 * step)
            fxe_close.append(fxe_current)
            uup_close.append(uup_current)
            continue
        fxe_volume.append(700_000.0 + 6_000.0 * (index % 7))
        uup_volume.append(2_000_000.0 + 15_000.0 * (index % 5))
        fxe_close.append(fxe_current)
        uup_close.append(uup_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "fxe_close": fxe_close,
            "fxe_volume": fxe_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        FXE_UUP_EURO_DOLLAR_FX_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    cyb_close: list[float] = []
    uup_close: list[float] = []
    cyb_volume: list[float] = []
    uup_volume: list[float] = []
    cyb_current = 25.0
    uup_current = 25.0
    for index in range(560):
        if index < 430:
            cyb_current *= 1.0001 if index % 2 else 0.9999
            uup_current *= 1.0001 if index % 2 else 0.9999
        else:
            step = index - 429
            cyb_current *= 1.0075
            uup_current *= 0.9980
            cyb_volume.append(120_000.0 + 2_000.0 * step)
            uup_volume.append(2_500_000.0 + 10_000.0 * step)
            cyb_close.append(cyb_current)
            uup_close.append(uup_current)
            continue
        cyb_volume.append(85_000.0 + 1_000.0 * (index % 7))
        uup_volume.append(2_000_000.0 + 15_000.0 * (index % 5))
        cyb_close.append(cyb_current)
        uup_close.append(uup_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "cyb_close": cyb_close,
            "cyb_volume": cyb_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        CYB_UUP_YUAN_DOLLAR_FX_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_cny_dollar_pressure_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    cny_per_usd: list[float] = []
    dollar_index: list[float] = []
    cny_current = 7.10
    dollar_current = 105.0
    for index in range(560):
        if index < 430:
            cny_current *= 1.0001 if index % 2 else 0.9999
            dollar_current *= 1.0001 if index % 3 else 0.9999
        else:
            cny_current *= 0.9960
            dollar_current *= 0.9980
        cny_per_usd.append(cny_current)
        dollar_index.append(dollar_current)

    pressure = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "cny_per_usd": cny_per_usd,
            "dollar_index_broad": dollar_index,
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        CNY_DOLLAR_PRESSURE_FRAME_KEY: pressure,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    fxa_close: list[float] = []
    uup_close: list[float] = []
    fxa_volume: list[float] = []
    uup_volume: list[float] = []
    fxa_current = 75.0
    uup_current = 25.0
    for index in range(560):
        if index < 430:
            fxa_current *= 1.0002 if index % 2 else 0.9998
            uup_current *= 1.0001 if index % 2 else 0.9999
        else:
            step = index - 429
            fxa_current *= 1.0095
            uup_current *= 0.9980
            fxa_volume.append(250_000.0 + 3_500.0 * step)
            uup_volume.append(2_500_000.0 + 10_000.0 * step)
            fxa_close.append(fxa_current)
            uup_close.append(uup_current)
            continue
        fxa_volume.append(200_000.0 + 2_000.0 * (index % 7))
        uup_volume.append(2_000_000.0 + 15_000.0 * (index % 5))
        fxa_close.append(fxa_current)
        uup_close.append(uup_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "fxa_close": fxa_close,
            "fxa_volume": fxa_volume,
            "uup_close": uup_close,
            "uup_volume": uup_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        FXA_UUP_AUSSIE_DOLLAR_FX_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_broker_fx_usd_pressure_followthrough_context() -> dict:
    periods = 420
    signal_index = 300
    h1_times = pd.date_range("2024-01-03T01:00:00Z", periods=periods, freq="1h")

    eurusd_returns: list[float] = []
    usdjpy_returns: list[float] = []
    xau_returns: list[float] = []
    for index in range(periods):
        if index < signal_index - 24:
            eurusd_returns.append(0.00003 if index % 2 else -0.00002)
            usdjpy_returns.append(0.00002 if index % 2 else -0.00003)
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            eurusd_returns.append(0.00045)
            usdjpy_returns.append(-0.00040)
            xau_returns.append(0.00055)
        elif index == signal_index:
            eurusd_returns.append(0.00035)
            usdjpy_returns.append(-0.00030)
            xau_returns.append(0.00150)
        else:
            eurusd_returns.append(0.00002 if index % 2 else -0.00002)
            usdjpy_returns.append(-0.00001 if index % 2 else 0.00001)
            xau_returns.append(0.00002 if index % 4 else -0.00001)

    xau_close = _price_path(2000.0, xau_returns)
    eurusd_close = _price_path(1.1000, eurusd_returns)
    usdjpy_close = _price_path(145.0, usdjpy_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    eurusd = _ohlc_from_closes(h1_times, eurusd_close, "capital_com", "EURUSD", "H1")
    usdjpy = _ohlc_from_closes(h1_times, usdjpy_close, "capital_com", "USDJPY", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "intermarket_proxy": {"EURUSD": eurusd, "USDJPY": usdjpy},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_broker_fx_usd_pressure_conflict_reversion_context() -> dict:
    periods = 420
    signal_index = 300
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")

    eurusd_returns: list[float] = []
    usdjpy_returns: list[float] = []
    xau_returns: list[float] = []
    for index in range(periods):
        if index < signal_index - 24:
            eurusd_returns.append(0.00003 if index % 2 else -0.00002)
            usdjpy_returns.append(0.00002 if index % 2 else -0.00003)
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            eurusd_returns.append(0.00045)
            usdjpy_returns.append(-0.00040)
            xau_returns.append(-0.00055)
        elif index == signal_index:
            eurusd_returns.append(0.00035)
            usdjpy_returns.append(-0.00030)
            xau_returns.append(0.00100)
        else:
            eurusd_returns.append(0.00002 if index % 2 else -0.00002)
            usdjpy_returns.append(-0.00001 if index % 2 else 0.00001)
            xau_returns.append(0.00002 if index % 4 else -0.00001)

    xau_close = _price_path(2000.0, xau_returns)
    eurusd_close = _price_path(1.1000, eurusd_returns)
    usdjpy_close = _price_path(145.0, usdjpy_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    eurusd = _ohlc_from_closes(h1_times, eurusd_close, "capital_com", "EURUSD", "H1")
    usdjpy = _ohlc_from_closes(h1_times, usdjpy_close, "capital_com", "USDJPY", "H1")
    _widen_ohlc_ranges(h1, 1.3)
    h1.loc[h1.index[signal_index], "open"] = float(h1.loc[h1.index[signal_index], "close"]) - 1.2
    h1.loc[h1.index[signal_index], "high"] = max(
        float(h1.loc[h1.index[signal_index], "high"]),
        float(h1.loc[h1.index[signal_index], "close"]) + 0.8,
    )
    h1.loc[h1.index[signal_index], "low"] = min(
        float(h1.loc[h1.index[signal_index], "low"]),
        float(h1.loc[h1.index[signal_index], "open"]) - 0.8,
    )

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "intermarket_proxy": {"EURUSD": eurusd, "USDJPY": usdjpy},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_btc_risk_pressure_gold_followthrough_context() -> dict:
    dates = pd.date_range("2021-01-01", periods=560, freq="1D", tz="UTC")
    btc_close: list[float] = []
    btc_volume: list[float] = []
    current_btc = 30000.0
    for index in range(560):
        if index < 430:
            current_btc *= 1.0005 if index % 2 else 0.9996
            btc_volume.append(20_000_000_000.0 + 1_000_000.0 * (index % 7))
        else:
            current_btc *= 0.9800
            btc_volume.append(35_000_000_000.0 + 10_000_000.0 * (index % 5))
        btc_close.append(current_btc)
    btc = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "btc_close": btc_close,
            "btc_volume": btc_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        BTC_RISK_PRESSURE_FRAME_KEY: btc,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_qqq_spy_growth_risk_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    qqq_close: list[float] = []
    spy_close: list[float] = []
    qqq_volume: list[float] = []
    spy_volume: list[float] = []
    qqq_current = 310.0
    spy_current = 375.0
    for index in range(560):
        if index < 430:
            qqq_current *= 1.0006 if index % 2 else 0.9995
            spy_current *= 1.0004 if index % 2 else 0.9996
        else:
            step = index - 429
            qqq_current *= 0.9920
            spy_current *= 0.9990
            qqq_volume.append(70_000_000.0 + 50_000.0 * step)
            spy_volume.append(80_000_000.0 + 40_000.0 * step)
            qqq_close.append(qqq_current)
            spy_close.append(spy_current)
            continue
        qqq_volume.append(50_000_000.0 + 100_000.0 * (index % 7))
        spy_volume.append(70_000_000.0 + 100_000.0 * (index % 5))
        qqq_close.append(qqq_current)
        spy_close.append(spy_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "qqq_close": qqq_close,
            "qqq_volume": qqq_volume,
            "spy_close": spy_close,
            "spy_volume": spy_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        QQQ_SPY_GROWTH_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_gld_spy_safe_haven_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    gld_close: list[float] = []
    spy_close: list[float] = []
    gld_volume: list[float] = []
    spy_volume: list[float] = []
    qqq_close: list[float] = []
    qqq_volume: list[float] = []
    gld_current = 175.0
    spy_current = 375.0
    qqq_current = 310.0
    for index in range(560):
        if index < 430:
            gld_current *= 1.0002 if index % 3 else 0.9998
            spy_current *= 1.0004 if index % 2 else 0.9996
            qqq_current *= 1.0005 if index % 2 else 0.9995
        else:
            step = index - 429
            gld_current *= 1.0065
            spy_current *= 0.9980
            qqq_current *= 0.9990
            gld_volume.append(14_000_000.0 + 20_000.0 * step)
            spy_volume.append(85_000_000.0 + 40_000.0 * step)
            qqq_volume.append(65_000_000.0 + 30_000.0 * step)
            gld_close.append(gld_current)
            spy_close.append(spy_current)
            qqq_close.append(qqq_current)
            continue
        gld_volume.append(8_000_000.0 + 50_000.0 * (index % 7))
        spy_volume.append(70_000_000.0 + 100_000.0 * (index % 5))
        qqq_volume.append(50_000_000.0 + 100_000.0 * (index % 7))
        gld_close.append(gld_current)
        spy_close.append(spy_current)
        qqq_close.append(qqq_current)

    gld_flow = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "close": gld_close,
            "volume": gld_volume,
            "source_symbol": ["GLD"] * len(dates),
            "source": ["synthetic"] * len(dates),
        }
    )
    qqq_spy = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "qqq_close": qqq_close,
            "qqq_volume": qqq_volume,
            "spy_close": spy_close,
            "spy_volume": spy_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        GLD_ETF_FLOW_FRAME_KEY: gld_flow,
        QQQ_SPY_GROWTH_ROTATION_FRAME_KEY: qqq_spy,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_iwm_spy_size_risk_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    iwm_close: list[float] = []
    spy_close: list[float] = []
    iwm_volume: list[float] = []
    spy_volume: list[float] = []
    iwm_current = 190.0
    spy_current = 375.0
    for index in range(560):
        if index < 430:
            iwm_current *= 1.0005 if index % 2 else 0.9994
            spy_current *= 1.0004 if index % 2 else 0.9996
        else:
            step = index - 429
            iwm_current *= 0.9900
            spy_current *= 0.9985
            iwm_volume.append(60_000_000.0 + 60_000.0 * step)
            spy_volume.append(80_000_000.0 + 40_000.0 * step)
            iwm_close.append(iwm_current)
            spy_close.append(spy_current)
            continue
        iwm_volume.append(45_000_000.0 + 100_000.0 * (index % 7))
        spy_volume.append(70_000_000.0 + 100_000.0 * (index % 5))
        iwm_close.append(iwm_current)
        spy_close.append(spy_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "iwm_close": iwm_close,
            "iwm_volume": iwm_volume,
            "spy_close": spy_close,
            "spy_volume": spy_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        IWM_SPY_SIZE_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_slv_gld_precious_beta_rotation_followthrough_context() -> dict:
    dates = pd.bdate_range("2021-01-04", periods=560, tz="UTC")
    slv_close: list[float] = []
    gld_close: list[float] = []
    slv_volume: list[float] = []
    gld_volume: list[float] = []
    slv_current = 22.0
    gld_current = 170.0
    for index in range(560):
        if index < 430:
            slv_current *= 1.0006 if index % 2 else 0.9993
            gld_current *= 1.0004 if index % 2 else 0.9995
        else:
            step = index - 429
            slv_current *= 1.0100
            gld_current *= 1.0015
            slv_volume.append(28_000_000.0 + 55_000.0 * step)
            gld_volume.append(7_000_000.0 + 25_000.0 * step)
            slv_close.append(slv_current)
            gld_close.append(gld_current)
            continue
        slv_volume.append(20_000_000.0 + 90_000.0 * (index % 7))
        gld_volume.append(6_000_000.0 + 45_000.0 * (index % 5))
        slv_close.append(slv_current)
        gld_close.append(gld_current)

    rotation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "slv_close": slv_close,
            "slv_volume": slv_volume,
            "gld_close": gld_close,
            "gld_volume": gld_volume,
            "source": ["synthetic"] * len(dates),
        }
    )

    h1_periods = 420
    signal_index = 300
    h1_times = pd.date_range(dates[465] + pd.Timedelta(hours=7), periods=h1_periods, freq="1h")
    xau_returns: list[float] = []
    for index in range(h1_periods):
        if index < signal_index - 24:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
        elif index < signal_index:
            xau_returns.append(0.00055)
        elif index == signal_index:
            xau_returns.append(0.00150)
        else:
            xau_returns.append(0.00002 if index % 4 else -0.00001)
    xau_close = _price_path(2000.0, xau_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 1.3)

    last_close = xau_close[-1]
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        SLV_GLD_PRECIOUS_ROTATION_FRAME_KEY: rotation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_breakeven_inflation_momentum_context() -> dict:
    inflation_dates = pd.bdate_range("2022-01-03", periods=380, tz="UTC")
    breakeven_5y: list[float] = []
    breakeven_10y: list[float] = []
    for index in range(380):
        if index < 260:
            breakeven_5y.append(2.00 + (0.01 if index % 2 else -0.01))
            breakeven_10y.append(2.10 + (0.005 if index % 2 else -0.005))
        else:
            breakeven_5y.append(2.00 + 0.012 * (index - 259))
            breakeven_10y.append(2.10 + 0.009 * (index - 259))
    inflation = pd.DataFrame(
        {
            "timestamp_utc": inflation_dates,
            "breakeven_5y": breakeven_5y,
            "breakeven_10y": breakeven_10y,
        }
    )

    h4_periods = 220
    h4_times = pd.date_range(
        inflation_dates[310] + pd.Timedelta(hours=4),
        periods=h4_periods,
        freq="4h",
    )
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.22 if index % 5 else -0.02
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=50, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 50,
            "high": [2005.0] * 50,
            "low": [1995.0] * 50,
            "close": [2001.0] * 50,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 432
    m5_times = pd.date_range(
        h4_times[0] + pd.Timedelta(minutes=5),
        periods=m5_periods,
        freq="5min",
    )
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "inflation_expectations": inflation,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_treasury_curve_stress_momentum_context() -> dict:
    treasury_dates = pd.bdate_range("2022-01-03", periods=380, tz="UTC")
    dgs2: list[float] = []
    dgs10: list[float] = []
    curve: list[float] = []
    for index in range(380):
        if index < 260:
            dgs2.append(4.30 + (0.01 if index % 2 else -0.01))
            dgs10.append(4.20 + (0.005 if index % 2 else -0.005))
            curve.append(-0.10 + (0.005 if index % 2 else -0.005))
        else:
            step = index - 259
            dgs2.append(4.30 - 0.018 * step)
            dgs10.append(4.20 - 0.012 * step)
            curve.append(-0.10 + 0.007 * step)
    treasury = pd.DataFrame(
        {
            "timestamp_utc": treasury_dates,
            "dgs2": dgs2,
            "dgs10": dgs10,
            "treasury_10y2y": curve,
        }
    )

    h4_periods = 220
    h4_times = pd.date_range(
        treasury_dates[310] + pd.Timedelta(hours=4),
        periods=h4_periods,
        freq="4h",
    )
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.24 if index % 5 else -0.01
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=50, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 50,
            "high": [2005.0] * 50,
            "low": [1995.0] * 50,
            "close": [2001.0] * 50,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 432
    m5_times = pd.date_range(
        h4_times[0] + pd.Timedelta(minutes=5),
        periods=m5_periods,
        freq="5min",
    )
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "treasury_curve": treasury,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_credit_spread_stress_momentum_context() -> dict:
    credit_dates = pd.bdate_range("2022-01-03", periods=380, tz="UTC")
    baa10y: list[float] = []
    aaa10y: list[float] = []
    for index in range(380):
        if index < 260:
            baa10y.append(1.80 + (0.01 if index % 2 else -0.01))
            aaa10y.append(1.10 + (0.005 if index % 2 else -0.005))
        else:
            step = index - 259
            baa10y.append(1.80 + 0.016 * step)
            aaa10y.append(1.10 + 0.006 * step)
    credit = pd.DataFrame(
        {
            "timestamp_utc": credit_dates,
            "baa10y": baa10y,
            "aaa10y": aaa10y,
        }
    )

    h4_periods = 220
    h4_times = pd.date_range(
        credit_dates[310] + pd.Timedelta(hours=4),
        periods=h4_periods,
        freq="4h",
    )
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.23 if index % 5 else -0.01
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=50, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 50,
            "high": [2005.0] * 50,
            "low": [1995.0] * 50,
            "close": [2001.0] * 50,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 432
    m5_times = pd.date_range(
        h4_times[0] + pd.Timedelta(minutes=5),
        periods=m5_periods,
        freq="5min",
    )
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "credit_spread": credit,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_macro_composite_risk_state_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=380, tz="UTC")
    macro_values: dict[str, list[float]] = {
        "real_yield_10y": [],
        "dollar_index_broad": [],
        "breakeven_5y": [],
        "breakeven_10y": [],
        "dgs2": [],
        "dgs10": [],
        "treasury_10y2y": [],
        "baa10y": [],
        "aaa10y": [],
        "vix_close": [],
        "gvz_close": [],
        "nfci": [],
        "anfci": [],
    }
    for index in range(380):
        if index < 260:
            step = 0.0
            wiggle = 0.01 if index % 2 else -0.01
        else:
            step = float(index - 259)
            wiggle = 0.0
        macro_values["real_yield_10y"].append(1.60 + wiggle - 0.010 * step)
        macro_values["dollar_index_broad"].append(120.0 + wiggle - 0.080 * step)
        macro_values["breakeven_5y"].append(2.00 + wiggle + 0.008 * step)
        macro_values["breakeven_10y"].append(2.10 + 0.5 * wiggle + 0.005 * step)
        macro_values["dgs2"].append(4.30 + wiggle - 0.010 * step)
        macro_values["dgs10"].append(4.20 + 0.5 * wiggle - 0.006 * step)
        macro_values["treasury_10y2y"].append(-0.10 + 0.5 * wiggle + 0.004 * step)
        macro_values["baa10y"].append(1.80 + wiggle + 0.008 * step)
        macro_values["aaa10y"].append(1.10 + 0.5 * wiggle + 0.003 * step)
        macro_values["vix_close"].append(16.0 + 0.5 * wiggle + 0.200 * step)
        macro_values["gvz_close"].append(18.0 + 0.5 * wiggle + 0.180 * step)
        macro_values["nfci"].append(-0.40 + 0.5 * wiggle + 0.030 * step)
        macro_values["anfci"].append(-0.35 + 0.5 * wiggle + 0.025 * step)

    macro = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "real_yield_10y": macro_values["real_yield_10y"],
            "dollar_index_broad": macro_values["dollar_index_broad"],
        }
    )
    inflation = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "breakeven_5y": macro_values["breakeven_5y"],
            "breakeven_10y": macro_values["breakeven_10y"],
        }
    )
    treasury = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "dgs2": macro_values["dgs2"],
            "dgs10": macro_values["dgs10"],
            "treasury_10y2y": macro_values["treasury_10y2y"],
        }
    )
    credit = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "baa10y": macro_values["baa10y"],
            "aaa10y": macro_values["aaa10y"],
        }
    )
    vix = pd.DataFrame({"timestamp_utc": dates, "vix_close": macro_values["vix_close"]})
    gvz = pd.DataFrame({"timestamp_utc": dates, "gvz_close": macro_values["gvz_close"]})
    conditions = pd.DataFrame(
        {
            "timestamp_utc": dates,
            "nfci": macro_values["nfci"],
            "anfci": macro_values["anfci"],
        }
    )

    h4_periods = 220
    h4_times = pd.date_range(dates[310] + pd.Timedelta(hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.25 if index % 5 else -0.01
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=50, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 50,
            "high": [2005.0] * 50,
            "low": [1995.0] * 50,
            "close": [2001.0] * 50,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 432
    m5_times = pd.date_range(h4_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "macro_proxy": macro,
        "inflation_expectations": inflation,
        "treasury_curve": treasury,
        "credit_spread": credit,
        "vix_risk": vix,
        "gvz_volatility": gvz,
        "financial_conditions": conditions,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_macro_composite_pullback_context() -> dict:
    context = _h4_macro_composite_risk_state_context()
    h1_periods = 520
    h1_times = pd.date_range("2023-04-03T00:00:00Z", periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        current += 0.08
        if index % 24 in (6, 7, 8):
            current -= 0.18
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    signal_index = 320
    ema_anchor = closes[signal_index - 1] - 0.20
    h1.loc[signal_index, ["open", "high", "low", "close"]] = [
        ema_anchor,
        ema_anchor + 1.40,
        ema_anchor - 0.30,
        ema_anchor + 1.10,
    ]
    context["H1"] = h1

    m5_periods = h1_periods * 12 + 144
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [h1.loc[signal_index, "close"]] * m5_periods,
            "high": [h1.loc[signal_index, "close"] + 1.5] * m5_periods,
            "low": [h1.loc[signal_index, "close"] - 1.5] * m5_periods,
            "close": [h1.loc[signal_index, "close"] + 0.4] * m5_periods,
            "mid_open": [h1.loc[signal_index, "close"]] * m5_periods,
            "mid_close": [h1.loc[signal_index, "close"] + 0.4] * m5_periods,
            "bid_open": [h1.loc[signal_index, "close"] - 0.1] * m5_periods,
            "ask_open": [h1.loc[signal_index, "close"] + 0.1] * m5_periods,
            "bid_close": [h1.loc[signal_index, "close"] + 0.3] * m5_periods,
            "ask_close": [h1.loc[signal_index, "close"] + 0.5] * m5_periods,
        }
    )
    context["M5"] = m5
    return context


def _h1_macro_composite_state_reversion_context() -> dict:
    context = _h4_macro_composite_risk_state_context()
    h1_periods = 520
    signal_index = 321
    h1_times = pd.date_range("2023-04-03T00:00:00Z", periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < signal_index - 24:
            current += 0.04 if index % 5 else -0.01
        elif index < signal_index:
            current += 0.51
        elif index == signal_index:
            current -= 1.50
        else:
            current -= 0.04 if index % 3 else -0.01
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 3.0)
    context["H1"] = h1

    m5_periods = h1_periods * 12 + 144
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    last_close = closes[signal_index]
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * m5_periods,
            "high": [last_close + 1.5] * m5_periods,
            "low": [last_close - 1.5] * m5_periods,
            "close": [last_close - 0.4] * m5_periods,
            "mid_open": [last_close] * m5_periods,
            "mid_close": [last_close - 0.4] * m5_periods,
            "bid_open": [last_close - 0.1] * m5_periods,
            "ask_open": [last_close + 0.1] * m5_periods,
            "bid_close": [last_close - 0.5] * m5_periods,
            "ask_close": [last_close - 0.3] * m5_periods,
        }
    )
    context["M5"] = m5
    return context


def _h1_month_turn_flow_continuation_context() -> dict:
    h1_periods = 260
    h1_times = pd.date_range("2024-01-20T00:00:00Z", periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        current += 0.18 if index % 8 != 3 else -0.03
        closes.append(current)
    opens = [closes[0] - 0.08, *closes[:-1]]
    highs = [max(open_price, close) + 0.24 for open_price, close in zip(opens, closes)]
    lows = [min(open_price, close) - 0.24 for open_price, close in zip(opens, closes)]
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )

    h4_times = pd.date_range(h1_times[0].floor("4h"), periods=80, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [2000.0] * 80,
            "high": [2010.0] * 80,
            "low": [1995.0] * 80,
            "close": [2005.0] * 80,
        }
    )
    d1_times = pd.date_range(h1_times[0].normalize(), periods=20, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 20,
            "high": [2010.0] * 20,
            "low": [1995.0] * 20,
            "close": [2005.0] * 20,
        }
    )
    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=h1_periods * 12 + 144, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * len(m5_times),
            "high": [last_close + 1.0] * len(m5_times),
            "low": [last_close - 1.0] * len(m5_times),
            "close": [last_close + 0.2] * len(m5_times),
            "mid_open": [last_close] * len(m5_times),
            "mid_close": [last_close + 0.2] * len(m5_times),
            "bid_open": [last_close - 0.05] * len(m5_times),
            "ask_open": [last_close + 0.05] * len(m5_times),
            "bid_close": [last_close + 0.15] * len(m5_times),
            "ask_close": [last_close + 0.25] * len(m5_times),
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_month_turn_flow_reversion_context() -> dict:
    h1_periods = 200
    h1_times = pd.date_range("2024-01-20T00:00:00Z", periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < h1_periods - 24:
            current += 0.04 if index % 6 else -0.02
        else:
            current -= 0.33 if index % 4 else 0.42
        closes.append(current)

    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    _widen_ohlc_ranges(h1, 3.0)
    signal_index = h1_periods - 1
    signal_close = float(h1.loc[signal_index, "close"])
    signal_open = signal_close + 0.82
    h1.loc[signal_index, ["open", "high", "low", "close"]] = [
        signal_open,
        signal_open + 3.20,
        signal_close - 0.22,
        signal_close,
    ]
    for prefix in ("mid", "bid", "ask"):
        h1.loc[signal_index, f"{prefix}_open"] = signal_open
        h1.loc[signal_index, f"{prefix}_high"] = signal_open + 3.20
        h1.loc[signal_index, f"{prefix}_low"] = signal_close - 0.22
        h1.loc[signal_index, f"{prefix}_close"] = signal_close

    h4_times = pd.date_range(h1_times[0].floor("4h"), periods=64, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [2000.0] * 64,
            "high": [2012.0] * 64,
            "low": [1988.0] * 64,
            "close": [1998.0] * 64,
        }
    )
    d1_times = pd.date_range(h1_times[0].normalize(), periods=16, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 16,
            "high": [2012.0] * 16,
            "low": [1988.0] * 16,
            "close": [1998.0] * 16,
        }
    )

    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [signal_close] * 180,
            "high": [signal_close + 1.2] * 180,
            "low": [signal_close - 0.8] * 180,
            "close": [signal_close + 0.3] * 180,
            "mid_open": [signal_close] * 180,
            "mid_close": [signal_close + 0.3] * 180,
            "bid_open": [signal_close - 0.1] * 180,
            "ask_open": [signal_close + 0.1] * 180,
            "bid_close": [signal_close + 0.2] * 180,
            "ask_close": [signal_close + 0.4] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_friday_position_squaring_reversion_context() -> dict:
    h1_periods = 132
    h1_times = pd.date_range("2024-04-01T00:00:00Z", periods=h1_periods, freq="1h")
    closes = [100.0 + 0.015 * index for index in range(h1_periods)]
    signal_index = 110
    closes[86] = 100.65
    closes[104] = 101.55
    closes[105] = 101.65
    closes[106] = 101.75
    closes[107] = 101.85
    closes[108] = 102.00
    closes[109] = 102.12
    closes[110] = 102.25

    opens = [closes[0] - 0.04, *closes[:-1]]
    opens[signal_index] = 102.05
    highs = [max(open_price, close) + 0.20 for open_price, close in zip(opens, closes)]
    lows = [min(open_price, close) - 0.20 for open_price, close in zip(opens, closes)]
    highs[signal_index] = 102.37
    lows[signal_index] = 101.92

    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )
    h4_times = pd.date_range(h1_times[0].floor("4h"), periods=48, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * len(h4_times),
            "high": [103.0] * len(h4_times),
            "low": [99.0] * len(h4_times),
            "close": [101.0] * len(h4_times),
        }
    )
    d1_times = pd.date_range(h1_times[0].normalize(), periods=12, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * len(d1_times),
            "high": [103.0] * len(d1_times),
            "low": [99.0] * len(d1_times),
            "close": [101.0] * len(d1_times),
        }
    )
    last_close = closes[signal_index]
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=h1_periods * 12 + 72, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * len(m5_times),
            "high": [last_close + 0.40] * len(m5_times),
            "low": [last_close - 0.55] * len(m5_times),
            "close": [last_close - 0.15] * len(m5_times),
            "mid_open": [last_close] * len(m5_times),
            "mid_close": [last_close - 0.15] * len(m5_times),
            "bid_open": [last_close - 0.05] * len(m5_times),
            "ask_open": [last_close + 0.05] * len(m5_times),
            "bid_close": [last_close - 0.20] * len(m5_times),
            "ask_close": [last_close - 0.10] * len(m5_times),
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_session_impulse_reversion_context() -> dict:
    h1_periods = 132
    h1_times = pd.date_range("2024-04-01T00:00:00Z", periods=h1_periods, freq="1h")
    closes = [100.0 + 0.02 * index for index in range(h1_periods)]
    signal_index = 110
    closes[104] = 102.05
    closes[105] = 101.95
    closes[106] = 101.88
    closes[107] = 101.82
    closes[108] = 101.65
    closes[109] = 101.45
    closes[110] = 101.20

    opens = [closes[0] - 0.05, *closes[:-1]]
    opens[signal_index] = 101.55
    highs = [max(open_price, close) + 0.22 for open_price, close in zip(opens, closes)]
    lows = [min(open_price, close) - 0.22 for open_price, close in zip(opens, closes)]
    highs[signal_index] = 101.65
    lows[signal_index] = 101.05

    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )
    h4_times = pd.date_range(h1_times[0].floor("4h"), periods=48, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * len(h4_times),
            "high": [103.0] * len(h4_times),
            "low": [99.0] * len(h4_times),
            "close": [101.0] * len(h4_times),
        }
    )
    d1_times = pd.date_range(h1_times[0].normalize(), periods=12, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * len(d1_times),
            "high": [103.0] * len(d1_times),
            "low": [99.0] * len(d1_times),
            "close": [101.0] * len(d1_times),
        }
    )
    last_close = closes[signal_index]
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=h1_periods * 12 + 96, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * len(m5_times),
            "high": [last_close + 0.65] * len(m5_times),
            "low": [last_close - 0.55] * len(m5_times),
            "close": [last_close + 0.20] * len(m5_times),
            "mid_open": [last_close] * len(m5_times),
            "mid_close": [last_close + 0.20] * len(m5_times),
            "bid_open": [last_close - 0.05] * len(m5_times),
            "ask_open": [last_close + 0.05] * len(m5_times),
            "bid_close": [last_close + 0.15] * len(m5_times),
            "ask_close": [last_close + 0.25] * len(m5_times),
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_policy_uncertainty_safe_haven_context() -> dict:
    policy_dates = pd.bdate_range("2022-01-03", periods=420, tz="UTC")
    policy_values: list[float] = []
    for index in range(420):
        if index < 280:
            policy_values.append(120.0 + (6.0 if index % 2 else -6.0))
        else:
            step = index - 279
            policy_values.append(120.0 + 3.0 * step)
    policy = pd.DataFrame(
        {
            "timestamp_utc": policy_dates,
            "policy_uncertainty": policy_values,
        }
    )

    h4_periods = 220
    h4_times = pd.date_range(
        policy_dates[340] + pd.Timedelta(hours=4),
        periods=h4_periods,
        freq="4h",
    )
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.23 if index % 5 else -0.01
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=50, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 50,
            "high": [2005.0] * 50,
            "low": [1995.0] * 50,
            "close": [2001.0] * 50,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 432
    m5_times = pd.date_range(
        h4_times[0] + pd.Timedelta(minutes=5),
        periods=m5_periods,
        freq="5min",
    )
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "policy_uncertainty": policy,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_financial_conditions_stress_reversal_context() -> dict:
    condition_dates = pd.date_range("2018-01-05", periods=220, freq="7D", tz="UTC")
    nfci: list[float] = []
    anfci: list[float] = []
    for index in range(220):
        if index < 160:
            nfci.append(-0.45 + 0.01 * (index % 5))
            anfci.append(-0.40 + 0.01 * (index % 5))
        else:
            nfci.append(-0.45 + 0.035 * (index - 159))
            anfci.append(-0.40 + 0.030 * (index - 159))
    financial_conditions = pd.DataFrame(
        {"timestamp_utc": condition_dates, "nfci": nfci, "anfci": anfci}
    )

    h4_periods = 180
    h4_times = pd.date_range(
        condition_dates[190] + pd.Timedelta(hours=4),
        periods=h4_periods,
        freq="4h",
    )
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        if index < 120:
            current -= 1.15
        elif index == 120:
            current += 3.10
        else:
            current += 0.10 if index % 4 else -0.04
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")
    h4["high"] = h4[["open", "close"]].max(axis=1) + 5.0
    h4["low"] = h4[["open", "close"]].min(axis=1) - 20.0

    d1_times = pd.date_range(h4_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2005.0] * 40,
            "low": [1995.0] * 40,
            "close": [1998.0] * 40,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 288
    m5_times = pd.date_range(
        h4_times[0] + pd.Timedelta(minutes=5),
        periods=m5_periods,
        freq="5min",
    )
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "financial_conditions": financial_conditions,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_gvz_volatility_panic_reversal_context() -> dict:
    gvz_dates = pd.bdate_range("2022-01-03", periods=340, tz="UTC")
    gvz_close: list[float] = []
    for index in range(340):
        if index < 260:
            gvz_close.append(18.0 + 0.03 * (index % 8))
        else:
            gvz_close.append(18.0 + 0.24 * (index - 259))
    gvz = pd.DataFrame({"timestamp_utc": gvz_dates, "gvz_close": gvz_close})

    h4_periods = 180
    h4_times = pd.date_range(gvz_dates[300] + pd.Timedelta(hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        if index < 120:
            current -= 1.20
        elif index == 120:
            current += 3.20
        else:
            current += 0.12 if index % 4 else -0.04
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2005.0] * 40,
            "low": [1995.0] * 40,
            "close": [1998.0] * 40,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 288
    m5_times = pd.date_range(h4_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "gvz_volatility": gvz,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_vix_risk_off_reversal_context() -> dict:
    vix_dates = pd.bdate_range("2022-01-03", periods=340, tz="UTC")
    vix_close: list[float] = []
    for index in range(340):
        if index < 260:
            vix_close.append(18.0 + 0.04 * (index % 7))
        else:
            vix_close.append(18.0 + 0.25 * (index - 259))
    vix = pd.DataFrame({"timestamp_utc": vix_dates, "vix_close": vix_close})

    h4_periods = 180
    h4_times = pd.date_range(vix_dates[300] + pd.Timedelta(hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        if index < 120:
            current -= 1.15
        elif index == 120:
            current += 3.10
        else:
            current += 0.10 if index % 4 else -0.04
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")
    h4["high"] = h4[["open", "close"]].max(axis=1) + 5.0
    h4["low"] = h4[["open", "close"]].min(axis=1) - 20.0

    d1_times = pd.date_range(h4_times[0].normalize(), periods=40, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 40,
            "high": [2005.0] * 40,
            "low": [1995.0] * 40,
            "close": [1998.0] * 40,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    m5_periods = h4_periods * 48 + 288
    m5_times = pd.date_range(h4_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "vix_risk": vix,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_gvz_vix_vol_premium_reversal_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=360, tz="UTC")
    gvz_close: list[float] = []
    vix_close: list[float] = []
    for index in range(360):
        if index < 270:
            gvz_close.append(18.0 + 0.02 * (index % 9))
            vix_close.append(20.0 + 0.02 * (index % 7))
        else:
            step = index - 269
            gvz_close.append(18.0 + 0.32 * step)
            vix_close.append(20.0 + 0.04 * step)
    gvz = pd.DataFrame({"timestamp_utc": dates, "gvz_close": gvz_close})
    vix = pd.DataFrame({"timestamp_utc": dates, "vix_close": vix_close})

    h1_periods = 340
    h1_times = pd.date_range(dates[315] + pd.Timedelta(hours=1), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < 170:
            current -= 0.85
        elif index == 170:
            current += 2.90
        else:
            current += 0.08 if index % 5 else -0.03
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    h1["high"] = h1[["open", "close"]].max(axis=1) + 1.8
    h1["low"] = h1[["open", "close"]].min(axis=1) - 1.8
    h1.loc[170, ["open", "high", "low", "close"]] = [1853.50, 1855.30, 1852.70, 1854.90]

    h4_times = pd.date_range(h1_times[0].floor("4h") + pd.Timedelta(hours=4), periods=90, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [2000.0] * 90,
            "high": [2006.0] * 90,
            "low": [1994.0] * 90,
            "close": [1998.0] * 90,
        }
    )
    d1_times = pd.date_range(h1_times[0].normalize(), periods=30, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 30,
            "high": [2005.0] * 30,
            "low": [1995.0] * 30,
            "close": [1998.0] * 30,
        }
    )
    m5_periods = h1_periods * 12 + 288
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "gvz_volatility": gvz,
        "vix_risk": vix,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_move_vix_bond_vol_shock_reversal_context() -> dict:
    dates = pd.bdate_range("2022-01-03", periods=360, tz="UTC")
    move_close: list[float] = []
    vix_close: list[float] = []
    for index in range(360):
        if index < 270:
            move_close.append(92.0 + 0.05 * (index % 8))
            vix_close.append(20.0 + 0.02 * (index % 7))
        else:
            step = index - 269
            move_close.append(92.0 + 2.80 * step)
            vix_close.append(20.0 + 0.02 * step)
    move = pd.DataFrame({"timestamp_utc": dates, "move_close": move_close})
    vix = pd.DataFrame({"timestamp_utc": dates, "vix_close": vix_close})

    h1_periods = 340
    h1_times = pd.date_range(dates[315] + pd.Timedelta(hours=1), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        if index < 170:
            current -= 0.85
        elif index == 170:
            current += 2.90
        else:
            current += 0.08 if index % 5 else -0.03
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    h1["high"] = h1[["open", "close"]].max(axis=1) + 1.8
    h1["low"] = h1[["open", "close"]].min(axis=1) - 1.8
    h1.loc[170, ["open", "high", "low", "close"]] = [1853.50, 1855.30, 1852.70, 1854.90]

    h4_times = pd.date_range(h1_times[0].floor("4h") + pd.Timedelta(hours=4), periods=90, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [2000.0] * 90,
            "high": [2006.0] * 90,
            "low": [1994.0] * 90,
            "close": [1998.0] * 90,
        }
    )
    d1_times = pd.date_range(h1_times[0].normalize(), periods=30, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 30,
            "high": [2005.0] * 30,
            "low": [1995.0] * 30,
            "close": [1998.0] * 30,
        }
    )
    m5_periods = h1_periods * 12 + 288
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        MOVE_BOND_VOL_FRAME_KEY: move,
        "vix_risk": vix,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_gc_xau_basis_reversion_context() -> dict:
    daily_times = pd.date_range("2022-01-03", periods=340, freq="1D", tz="UTC")
    xau_close: list[float] = []
    gc_close: list[float] = []
    current_xau = 1900.0
    current_gc = 1902.0
    for index in range(340):
        current_xau += 0.30 if index % 5 else -0.10
        current_gc += 0.30 if index % 5 else -0.10
        if index > 250:
            current_gc += 5.20
        xau_close.append(current_xau)
        gc_close.append(current_gc)
    gc = pd.DataFrame(
        {
            "timestamp_utc": daily_times,
            "open": [value - 0.5 for value in gc_close],
            "high": [value + 1.0 for value in gc_close],
            "low": [value - 1.0 for value in gc_close],
            "close": gc_close,
            "volume": [150000 + 10 * (index % 20) for index in range(340)],
            "source_symbol": ["GC=F"] * 340,
            "source": ["synthetic GC daily proxy"] * 340,
        }
    )

    d1 = pd.DataFrame(
        {
            "timestamp_utc": daily_times,
            "bar_start_utc": daily_times - pd.Timedelta(days=1),
            "open": [value - 0.2 for value in xau_close],
            "high": [value + 1.5 for value in xau_close],
            "low": [value - 1.5 for value in xau_close],
            "close": xau_close,
        }
    )

    signal_start = daily_times[300] + pd.Timedelta(hours=1)
    h1_periods = 260
    h1_times = pd.date_range(signal_start, periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = xau_close[300]
    for index in range(h1_periods):
        if index < 150:
            current -= 0.18
        elif index == 150:
            current += 1.20
        else:
            current += 0.05 if index % 5 else -0.02
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    h1["high"] = h1[["open", "close"]].max(axis=1) + 1.2
    h1["low"] = h1[["open", "close"]].min(axis=1) - 1.2
    h1.loc[162, ["open", "high", "low", "close"]] = [
        xau_close[300] - 28.0,
        xau_close[300] - 24.7,
        xau_close[300] - 29.2,
        xau_close[300] - 25.4,
    ]

    h4_times = pd.date_range(h1_times[0].floor("4h") + pd.Timedelta(hours=4), periods=80, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [xau_close[300]] * 80,
            "high": [xau_close[300] + 4.0] * 80,
            "low": [xau_close[300] - 4.0] * 80,
            "close": [xau_close[300] + 0.5] * 80,
        }
    )
    m5_periods = h1_periods * 12 + 288
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "gc_futures_volume": gc,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_gc_momentum_pullback_context() -> dict:
    daily_times = pd.date_range("2022-01-03", periods=340, freq="1D", tz="UTC")
    gc_close: list[float] = []
    current_gc = 1900.0
    for index in range(340):
        current_gc += 2.60 if index > 250 else 0.15
        gc_close.append(current_gc)
    gc = pd.DataFrame(
        {
            "timestamp_utc": daily_times,
            "open": [value - 0.5 for value in gc_close],
            "high": [value + 1.0 for value in gc_close],
            "low": [value - 1.0 for value in gc_close],
            "close": gc_close,
            "volume": [150000 + 10 * (index % 20) for index in range(340)],
            "source_symbol": ["GC=F"] * 340,
            "source": ["synthetic GC daily proxy"] * 340,
        }
    )

    signal_start = daily_times[300] + pd.Timedelta(hours=1)
    h1_periods = 260
    h1_times = pd.date_range(signal_start, periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 2000.0
    for index in range(h1_periods):
        current += 0.12
        if index % 24 in (6, 7, 8):
            current -= 0.20
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    signal_index = 162
    ema_anchor = closes[signal_index - 1] - 0.10
    h1.loc[signal_index, ["open", "high", "low", "close"]] = [
        ema_anchor - 0.45,
        ema_anchor + 1.40,
        ema_anchor - 0.60,
        ema_anchor + 1.05,
    ]

    d1_times = pd.date_range(h1_times[0].normalize(), periods=30, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [2000.0] * 30,
            "high": [2008.0] * 30,
            "low": [1996.0] * 30,
            "close": [2004.0] * 30,
        }
    )
    h4_times = pd.date_range(h1_times[0].floor("4h") + pd.Timedelta(hours=4), periods=80, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [2000.0] * 80,
            "high": [2006.0] * 80,
            "low": [1994.0] * 80,
            "close": [2004.0] * 80,
        }
    )
    m5_periods = h1_periods * 12 + 288
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "gc_futures_volume": gc,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _cot_gold_positioning_reversal_context() -> dict:
    cot_dates = pd.date_range("2020-01-07", periods=210, freq="7D", tz="UTC")
    open_interest = [400000.0] * 210
    mm_net: list[float] = []
    producer_net: list[float] = []
    for index in range(210):
        if index < 160:
            mm_net.append(0.10 + 0.001 * (index % 20))
            producer_net.append(-0.10 - 0.001 * (index % 20))
        else:
            mm_net.append(-0.24 + 0.004 * (index - 159))
            producer_net.append(0.24 - 0.001 * (index - 159))
    cot = pd.DataFrame(
        {
            "report_date": cot_dates,
            "market": ["GOLD - COMMODITY EXCHANGE INC."] * 210,
            "cftc_contract_market_code": ["088691"] * 210,
            "open_interest_all": open_interest,
            "producer_long_all": [160000.0 + max(value, 0) * 400000.0 for value in producer_net],
            "producer_short_all": [160000.0 + max(-value, 0) * 400000.0 for value in producer_net],
            "managed_money_long_all": [150000.0 + max(value, 0) * 400000.0 for value in mm_net],
            "managed_money_short_all": [150000.0 + max(-value, 0) * 400000.0 for value in mm_net],
        }
    )

    h4_periods = 260
    h4_times = pd.date_range(cot_dates[170] + pd.Timedelta(days=6, hours=4), periods=h4_periods, freq="4h")
    closes: list[float] = []
    current = 1900.0
    for index in range(h4_periods):
        current += 0.22 if index % 5 else -0.02
        closes.append(current)
    h4 = _ohlc_from_closes(h4_times, closes, "capital_com", "XAUUSD", "H4")

    d1_times = pd.date_range(h4_times[0].normalize(), periods=80, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [1900.0] * 80,
            "high": [1905.0] * 80,
            "low": [1895.0] * 80,
            "close": [1901.0] * 80,
        }
    )
    h1_times = pd.date_range(h4_times[0], periods=h4_periods * 4, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [closes[-1]] * len(h1_times),
            "high": [closes[-1] + 1.0] * len(h1_times),
            "low": [closes[-1] - 1.0] * len(h1_times),
            "close": [closes[-1]] * len(h1_times),
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h4_times[-1] + pd.Timedelta(minutes=5), periods=1200, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 1200,
            "high": [last_close + 2.0] * 1200,
            "low": [last_close - 2.0] * 1200,
            "close": [last_close + 0.5] * 1200,
            "mid_open": [last_close] * 1200,
            "mid_close": [last_close + 0.5] * 1200,
            "bid_open": [last_close - 0.1] * 1200,
            "ask_open": [last_close + 0.1] * 1200,
            "bid_close": [last_close + 0.4] * 1200,
            "ask_close": [last_close + 0.6] * 1200,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "cot_gold": cot,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_cot_positioning_continuation_context() -> dict:
    cot_dates = pd.date_range("2020-01-07", periods=215, freq="7D", tz="UTC")
    open_interest = [420000.0] * 215
    mm_net: list[float] = []
    producer_net: list[float] = []
    for index in range(215):
        if index < 160:
            mm_net.append(0.03 + 0.0005 * (index % 20))
            producer_net.append(-0.03 - 0.0005 * (index % 20))
        else:
            mm_net.append(0.09 + 0.0025 * (index - 159))
            producer_net.append(-0.09 - 0.0020 * (index - 159))
    cot = pd.DataFrame(
        {
            "report_date": cot_dates,
            "market": ["GOLD - COMMODITY EXCHANGE INC."] * 215,
            "cftc_contract_market_code": ["088691"] * 215,
            "open_interest_all": open_interest,
            "producer_long_all": [165000.0 + max(value, 0) * 420000.0 for value in producer_net],
            "producer_short_all": [165000.0 + max(-value, 0) * 420000.0 for value in producer_net],
            "managed_money_long_all": [155000.0 + max(value, 0) * 420000.0 for value in mm_net],
            "managed_money_short_all": [155000.0 + max(-value, 0) * 420000.0 for value in mm_net],
        }
    )

    h1_periods = 420
    h1_times = pd.date_range(cot_dates[174] + pd.Timedelta(days=6, hours=7), periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 1900.0
    for index in range(h1_periods):
        if index % 12 in {5, 6}:
            current -= 0.18
        else:
            current += 0.28
        closes.append(current)
    opens = [closes[0] - 0.15, *closes[:-1]]
    highs = [max(open_price, close) + 0.35 for open_price, close in zip(opens, closes)]
    lows = [min(open_price, close) - 2.00 for open_price, close in zip(opens, closes)]
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )

    h4_times = pd.date_range(h1_times[0].floor("4h"), periods=110, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [1900.0] * 110,
            "high": [1910.0] * 110,
            "low": [1895.0] * 110,
            "close": [1905.0] * 110,
        }
    )
    d1_times = pd.date_range(h1_times[0].normalize(), periods=30, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [1900.0] * 30,
            "high": [1910.0] * 30,
            "low": [1895.0] * 30,
            "close": [1905.0] * 30,
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=h1_periods * 12 + 360, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * len(m5_times),
            "high": [last_close + 2.0] * len(m5_times),
            "low": [last_close - 2.0] * len(m5_times),
            "close": [last_close + 0.5] * len(m5_times),
            "mid_open": [last_close] * len(m5_times),
            "mid_close": [last_close + 0.5] * len(m5_times),
            "bid_open": [last_close - 0.1] * len(m5_times),
            "ask_open": [last_close + 0.1] * len(m5_times),
            "bid_close": [last_close + 0.4] * len(m5_times),
            "ask_close": [last_close + 0.6] * len(m5_times),
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        "cot_gold": cot,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_walk_forward_knn_momentum_state_context() -> dict:
    h4_periods = 980
    h4_times = pd.date_range("2024-01-01T04:00:00Z", periods=h4_periods, freq="4h")
    h4_closes: list[float] = []
    current = 2000.0
    for index in range(h4_periods):
        current += 0.28 if index % 4 != 0 else -0.04
        h4_closes.append(current)
    h4_opens = [h4_closes[0] - 0.12, *h4_closes[:-1]]
    h4_highs = [max(open_price, close) + 0.18 for open_price, close in zip(h4_opens, h4_closes)]
    h4_lows = [min(open_price, close) - 0.18 for open_price, close in zip(h4_opens, h4_closes)]
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": h4_opens,
            "high": h4_highs,
            "low": h4_lows,
            "close": h4_closes,
        }
    )

    d1_periods = 220
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=d1_periods, freq="1D")
    d1_closes = [2000.0 + 1.0 * index for index in range(d1_periods)]
    d1_opens = [close - 0.35 for close in d1_closes]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": d1_opens,
            "high": [close + 1.0 for close in d1_closes],
            "low": [open_price - 0.8 for open_price in d1_opens],
            "close": d1_closes,
        }
    )

    last_close = h4_closes[-1]
    m5_times = pd.date_range(h4_times[-1] + pd.Timedelta(minutes=5), periods=240, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 240,
            "high": [last_close + 0.8] * 240,
            "low": [last_close - 0.8] * 240,
            "close": [last_close + 0.1] * 240,
            "mid_open": [last_close] * 240,
            "mid_close": [last_close + 0.1] * 240,
            "bid_open": [last_close - 0.1] * 240,
            "ask_open": [last_close + 0.1] * 240,
            "bid_close": [last_close] * 240,
            "ask_close": [last_close + 0.2] * 240,
        }
    )
    return {"M5": m5, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _w1_d1_momentum_continuation_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=90, freq="1D")
    d1_closes = [100.0 + 0.35 * index for index in range(90)]
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [close - 0.25 for close in d1_closes],
            "high": [close + 0.9 for close in d1_closes],
            "low": [close - 0.9 for close in d1_closes],
            "close": d1_closes,
        }
    )
    d1.loc[70, ["open", "high", "low", "close"]] = [124.2, 126.2, 124.0, 125.9]

    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=26000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [125.9] * 26000,
            "high": [126.5] * 26000,
            "low": [125.3] * 26000,
            "close": [125.9] * 26000,
            "mid_open": [125.9] * 26000,
            "mid_close": [125.9] * 26000,
            "bid_open": [125.8] * 26000,
            "ask_open": [126.0] * 26000,
            "bid_close": [125.8] * 26000,
            "ask_close": [126.0] * 26000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:15:00Z", periods=8700, freq="15min"),
            "open": [125.9] * 8700,
            "high": [126.5] * 8700,
            "low": [125.3] * 8700,
            "close": [125.9] * 8700,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:00:00Z", periods=2200, freq="1h"),
            "open": [125.9] * 2200,
            "high": [126.5] * 2200,
            "low": [125.3] * 2200,
            "close": [125.9] * 2200,
        }
    )
    h4 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:00:00Z", periods=550, freq="4h"),
            "open": [125.9] * 550,
            "high": [126.5] * 550,
            "low": [125.3] * 550,
            "close": [125.9] * 550,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_volatility_expansion_reversal_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=70, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * 70,
            "high": [101.0] * 70,
            "low": [99.0] * 70,
            "close": [100.0] * 70,
        }
    )
    for idx in range(50, 60):
        d1.loc[idx, ["open", "high", "low", "close"]] = [100.0 + idx * 0.1, 102.0 + idx * 0.1, 99.0 + idx * 0.1, 101.0 + idx * 0.1]
    d1.loc[60, ["open", "high", "low", "close"]] = [106.0, 111.0, 105.5, 110.5]

    h4_times = pd.date_range("2024-02-25T00:00:00Z", periods=140, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [108.0] * 140,
            "high": [108.7] * 140,
            "low": [107.3] * 140,
            "close": [108.0] * 140,
        }
    )
    h4.loc[31, ["open", "high", "low", "close"]] = [110.4, 111.2, 108.6, 109.0]

    m5_times = pd.date_range("2024-02-25T00:05:00Z", periods=7000, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [109.0] * 7000,
            "high": [109.6] * 7000,
            "low": [108.4] * 7000,
            "close": [109.0] * 7000,
            "mid_open": [109.0] * 7000,
            "mid_close": [109.0] * 7000,
            "bid_open": [108.9] * 7000,
            "ask_open": [109.1] * 7000,
            "bid_close": [108.9] * 7000,
            "ask_close": [109.1] * 7000,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-02-25T00:15:00Z", periods=2400, freq="15min"),
            "open": [109.0] * 2400,
            "high": [109.6] * 2400,
            "low": [108.4] * 2400,
            "close": [109.0] * 2400,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-02-25T00:00:00Z", periods=600, freq="1h"),
            "open": [109.0] * 600,
            "high": [109.6] * 600,
            "low": [108.4] * 600,
            "close": [109.0] * 600,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _h4_us_session_liquidity_reversal_context() -> dict:
    h4_times = pd.date_range("2024-05-01T00:00:00Z", periods=96, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 96,
            "high": [100.5] * 96,
            "low": [99.5] * 96,
            "close": [100.0] * 96,
        }
    )
    h4.loc[40, ["open", "high", "low", "close"]] = [102.0, 105.0, 99.0, 100.5]

    m5_periods = 96 * 48 + 576
    m5_times = pd.date_range("2024-05-01T00:05:00Z", periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.5] * m5_periods,
            "high": [101.0] * m5_periods,
            "low": [100.0] * m5_periods,
            "close": [100.5] * m5_periods,
            "mid_open": [100.5] * m5_periods,
            "mid_close": [100.5] * m5_periods,
            "bid_open": [100.4] * m5_periods,
            "ask_open": [100.6] * m5_periods,
            "bid_close": [100.4] * m5_periods,
            "ask_close": [100.6] * m5_periods,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:15:00Z", periods=1600, freq="15min"),
            "open": [100.5] * 1600,
            "high": [101.0] * 1600,
            "low": [100.0] * 1600,
            "close": [100.5] * 1600,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:00:00Z", periods=500, freq="1h"),
            "open": [100.5] * 500,
            "high": [101.0] * 500,
            "low": [100.0] * 500,
            "close": [100.5] * 500,
        }
    )
    d1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:00:00Z", periods=30, freq="1D"),
            "bar_start_utc": pd.date_range("2024-04-30T00:00:00Z", periods=30, freq="1D"),
            "open": [100.0] * 30,
            "high": [101.0] * 30,
            "low": [99.0] * 30,
            "close": [100.0] * 30,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _h4_gold_futures_volume_climax_context() -> dict:
    h4_periods = 320
    h4_times = pd.date_range("2024-01-01T00:00:00Z", periods=h4_periods, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * h4_periods,
            "high": [100.5] * h4_periods,
            "low": [99.5] * h4_periods,
            "close": [100.0] * h4_periods,
        }
    )
    signal_index = 260
    h4.loc[signal_index, ["open", "high", "low", "close"]] = [98.0, 100.0, 97.0, 99.7]

    m5_periods = h4_periods * 48 + 384
    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [99.7] * m5_periods,
            "high": [100.2] * m5_periods,
            "low": [99.2] * m5_periods,
            "close": [99.7] * m5_periods,
            "mid_open": [99.7] * m5_periods,
            "mid_close": [99.7] * m5_periods,
            "bid_open": [99.6] * m5_periods,
            "ask_open": [99.8] * m5_periods,
            "bid_close": [99.6] * m5_periods,
            "ask_close": [99.8] * m5_periods,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:15:00Z", periods=5200, freq="15min"),
            "open": [99.7] * 5200,
            "high": [100.2] * 5200,
            "low": [99.2] * 5200,
            "close": [99.7] * 5200,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:00:00Z", periods=1400, freq="1h"),
            "open": [99.7] * 1400,
            "high": [100.2] * 1400,
            "low": [99.2] * 1400,
            "close": [99.7] * 1400,
        }
    )

    d1_periods = 90
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=d1_periods, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * d1_periods,
            "high": [101.0] * d1_periods,
            "low": [99.0] * d1_periods,
            "close": [100.0] * d1_periods,
        }
    )
    prior_day = pd.Timestamp(h4_times[signal_index]).normalize() - pd.Timedelta(days=1)
    prior_index = d1.index[d1["timestamp_utc"] == prior_day][0]
    d1.loc[prior_index, ["open", "high", "low", "close"]] = [102.0, 104.0, 96.0, 98.0]

    gc_days = 430
    gc_times = pd.date_range("2023-01-01T00:00:00Z", periods=gc_days, freq="1D")
    gc_volume = pd.DataFrame(
        {
            "timestamp_utc": gc_times,
            "open": [1800.0] * gc_days,
            "high": [1810.0] * gc_days,
            "low": [1790.0] * gc_days,
            "close": [1800.0] * gc_days,
            "volume": [120000] * gc_days,
            "source_symbol": ["GC=F"] * gc_days,
            "source": ["synthetic"] * gc_days,
        }
    )
    gc_spike_day = prior_day
    gc_index = gc_volume.index[gc_volume["timestamp_utc"] == gc_spike_day][0]
    gc_volume.loc[gc_index, ["close", "volume"]] = [1780.0, 450000]

    return {
        "M5": m5,
        "M15": m15,
        "H1": h1,
        "H4": h4,
        "D1": d1,
        GC_FUTURES_VOLUME_FRAME_KEY: gc_volume,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h4_gld_etf_flow_reversal_context() -> dict:
    h4_periods = 320
    h4_times = pd.date_range("2024-01-01T00:00:00Z", periods=h4_periods, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.5] * h4_periods,
            "high": [101.0] * h4_periods,
            "low": [100.0] * h4_periods,
            "close": [100.5] * h4_periods,
        }
    )
    signal_index = 261
    h4.loc[signal_index - 12 : signal_index - 1, ["open", "high", "low", "close"]] = [
        100.6,
        101.0,
        99.9,
        100.6,
    ]
    h4.loc[signal_index, ["open", "high", "low", "close"]] = [98.0, 100.0, 97.0, 99.7]

    m5_periods = h4_periods * 48 + 288
    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [99.7] * m5_periods,
            "high": [100.2] * m5_periods,
            "low": [99.2] * m5_periods,
            "close": [99.7] * m5_periods,
            "mid_open": [99.7] * m5_periods,
            "mid_close": [99.7] * m5_periods,
            "bid_open": [99.6] * m5_periods,
            "ask_open": [99.8] * m5_periods,
            "bid_close": [99.6] * m5_periods,
            "ask_close": [99.8] * m5_periods,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:15:00Z", periods=5200, freq="15min"),
            "open": [99.7] * 5200,
            "high": [100.2] * 5200,
            "low": [99.2] * 5200,
            "close": [99.7] * 5200,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:00:00Z", periods=1400, freq="1h"),
            "open": [99.7] * 1400,
            "high": [100.2] * 1400,
            "low": [99.2] * 1400,
            "close": [99.7] * 1400,
        }
    )

    gld_days = 430
    gld_times = pd.date_range("2023-01-01T00:00:00Z", periods=gld_days, freq="1D")
    gld_flow = pd.DataFrame(
        {
            "timestamp_utc": gld_times,
            "open": [188.0] * gld_days,
            "high": [189.0] * gld_days,
            "low": [187.0] * gld_days,
            "close": [188.0] * gld_days,
            "volume": [10_000_000] * gld_days,
            "source_symbol": ["GLD"] * gld_days,
            "source": ["synthetic"] * gld_days,
        }
    )
    signal_day = pd.Timestamp(h4_times[signal_index]).normalize()
    gld_spike_day = signal_day - pd.Timedelta(days=1)
    previous_day = gld_spike_day - pd.Timedelta(days=1)
    previous_index = gld_flow.index[gld_flow["timestamp_utc"] == previous_day][0]
    spike_index = gld_flow.index[gld_flow["timestamp_utc"] == gld_spike_day][0]
    gld_flow.loc[previous_index, ["close", "volume"]] = [188.0, 10_000_000]
    gld_flow.loc[spike_index, ["open", "high", "low", "close", "volume"]] = [
        188.0,
        189.0,
        181.0,
        183.5,
        80_000_000,
    ]

    return {
        "M5": m5,
        "M15": m15,
        "H1": h1,
        "H4": h4,
        GLD_ETF_FLOW_FRAME_KEY: gld_flow,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_gld_flow_momentum_pullback_context() -> dict:
    h1_periods = 420
    h1_times = pd.date_range("2024-01-01T07:00:00Z", periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 100.0
    for index in range(h1_periods):
        if index % 12 in {5, 6}:
            current -= 0.10
        else:
            current += 0.16
        closes.append(current)
    opens = [closes[0] - 0.08, *closes[:-1]]
    highs = [max(open_price, close) + 0.22 for open_price, close in zip(opens, closes)]
    lows = [min(open_price, close) - 1.15 for open_price, close in zip(opens, closes)]
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )

    h4_times = pd.date_range(h1_times[0].floor("4h"), periods=110, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 110,
            "high": [105.0] * 110,
            "low": [98.0] * 110,
            "close": [103.0] * 110,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range(h1_times[0], periods=h1_periods * 4, freq="15min"),
            "open": [closes[-1]] * (h1_periods * 4),
            "high": [closes[-1] + 0.5] * (h1_periods * 4),
            "low": [closes[-1] - 0.5] * (h1_periods * 4),
            "close": [closes[-1]] * (h1_periods * 4),
        }
    )
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=h1_periods * 12 + 360, freq="5min")
    last_close = closes[-1]
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * len(m5_times),
            "high": [last_close + 1.0] * len(m5_times),
            "low": [last_close - 1.0] * len(m5_times),
            "close": [last_close + 0.2] * len(m5_times),
            "mid_open": [last_close] * len(m5_times),
            "mid_close": [last_close + 0.2] * len(m5_times),
            "bid_open": [last_close - 0.05] * len(m5_times),
            "ask_open": [last_close + 0.05] * len(m5_times),
            "bid_close": [last_close + 0.15] * len(m5_times),
            "ask_close": [last_close + 0.25] * len(m5_times),
        }
    )

    gld_days = 430
    gld_times = pd.date_range("2023-01-01T00:00:00Z", periods=gld_days, freq="1D")
    gld_closes = [188.0] * gld_days
    gld_volume = [10_000_000] * gld_days
    signal_day = pd.Timestamp(h1_times[300]).normalize()
    flow_day = signal_day - pd.Timedelta(days=1)
    previous_day = flow_day - pd.Timedelta(days=1)
    previous_index = list(gld_times).index(previous_day)
    flow_index = list(gld_times).index(flow_day)
    gld_closes[previous_index] = 188.0
    gld_closes[flow_index] = 190.5
    gld_volume[flow_index] = 85_000_000
    gld_flow = pd.DataFrame(
        {
            "timestamp_utc": gld_times,
            "open": [188.0] * gld_days,
            "high": [191.0] * gld_days,
            "low": [187.0] * gld_days,
            "close": gld_closes,
            "volume": gld_volume,
            "source_symbol": ["GLD"] * gld_days,
            "source": ["synthetic"] * gld_days,
        }
    )

    return {
        "M5": m5,
        "M15": m15,
        "H1": h1,
        "H4": h4,
        GLD_ETF_FLOW_FRAME_KEY: gld_flow,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_gld_flow_stress_reversal_context() -> dict:
    h1_periods = 420
    h1_times = pd.date_range("2024-01-01T07:00:00Z", periods=h1_periods, freq="1h")
    closes: list[float] = []
    current = 100.0
    for index in range(h1_periods):
        current += 0.05
        closes.append(current)
    signal_index = 300
    for offset, value in enumerate(
        [112.10, 112.18, 112.26, 112.35, 112.44, 112.55, 112.68, 112.82, 112.98, 113.15, 113.30, 113.42],
        start=signal_index - 12,
    ):
        closes[offset] = value
    closes[signal_index] = 113.18

    opens = [closes[0] - 0.04, *closes[:-1]]
    opens[signal_index] = 113.50
    highs = [max(open_price, close) + 0.18 for open_price, close in zip(opens, closes)]
    lows = [min(open_price, close) - 0.18 for open_price, close in zip(opens, closes)]
    highs[signal_index] = 113.62
    lows[signal_index] = 113.05
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
        }
    )

    h4_times = pd.date_range(h1_times[0].floor("4h"), periods=110, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 110,
            "high": [115.0] * 110,
            "low": [98.0] * 110,
            "close": [112.0] * 110,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range(h1_times[0], periods=h1_periods * 4, freq="15min"),
            "open": [closes[signal_index]] * (h1_periods * 4),
            "high": [closes[signal_index] + 0.5] * (h1_periods * 4),
            "low": [closes[signal_index] - 0.5] * (h1_periods * 4),
            "close": [closes[signal_index]] * (h1_periods * 4),
        }
    )
    last_close = closes[signal_index]
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=h1_periods * 12 + 360, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * len(m5_times),
            "high": [last_close + 0.45] * len(m5_times),
            "low": [last_close - 0.85] * len(m5_times),
            "close": [last_close - 0.20] * len(m5_times),
            "mid_open": [last_close] * len(m5_times),
            "mid_close": [last_close - 0.20] * len(m5_times),
            "bid_open": [last_close - 0.05] * len(m5_times),
            "ask_open": [last_close + 0.05] * len(m5_times),
            "bid_close": [last_close - 0.25] * len(m5_times),
            "ask_close": [last_close - 0.15] * len(m5_times),
        }
    )

    gld_days = 430
    gld_times = pd.date_range("2023-01-01T00:00:00Z", periods=gld_days, freq="1D")
    gld_closes = [188.0] * gld_days
    gld_volume = [10_000_000] * gld_days
    signal_day = pd.Timestamp(h1_times[signal_index]).normalize()
    flow_day = signal_day - pd.Timedelta(days=1)
    previous_day = flow_day - pd.Timedelta(days=1)
    previous_index = list(gld_times).index(previous_day)
    flow_index = list(gld_times).index(flow_day)
    gld_closes[previous_index] = 188.0
    gld_closes[flow_index] = 191.0
    gld_volume[flow_index] = 85_000_000
    gld_flow = pd.DataFrame(
        {
            "timestamp_utc": gld_times,
            "open": [188.0] * gld_days,
            "high": [191.5] * gld_days,
            "low": [187.0] * gld_days,
            "close": gld_closes,
            "volume": gld_volume,
            "source_symbol": ["GLD"] * gld_days,
            "source": ["synthetic"] * gld_days,
        }
    )

    return {
        "M5": m5,
        "M15": m15,
        "H1": h1,
        "H4": h4,
        GLD_ETF_FLOW_FRAME_KEY: gld_flow,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_gld_flow_stress_followthrough_context() -> dict:
    context = _h1_gld_flow_stress_reversal_context()
    h1 = context["H1"].copy()
    signal_index = 300
    h1.loc[signal_index, ["open", "high", "low", "close"]] = [113.25, 113.70, 113.05, 113.58]
    context["H1"] = h1

    last_close = float(h1.loc[signal_index, "close"])
    m5 = context["M5"].copy()
    m5.loc[:, ["open", "mid_open"]] = last_close
    m5.loc[:, "high"] = last_close + 0.90
    m5.loc[:, "low"] = last_close - 0.40
    m5.loc[:, ["close", "mid_close"]] = last_close + 0.20
    m5.loc[:, "bid_open"] = last_close - 0.05
    m5.loc[:, "ask_open"] = last_close + 0.05
    m5.loc[:, "bid_close"] = last_close + 0.15
    m5.loc[:, "ask_close"] = last_close + 0.25
    context["M5"] = m5
    return context


def _h4_gdx_gld_miner_divergence_context() -> dict:
    h4_periods = 320
    h4_times = pd.date_range("2024-01-01T00:00:00Z", periods=h4_periods, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.5] * h4_periods,
            "high": [101.0] * h4_periods,
            "low": [100.0] * h4_periods,
            "close": [100.5] * h4_periods,
        }
    )
    signal_index = 261
    h4.loc[signal_index - 12 : signal_index - 1, ["open", "high", "low", "close"]] = [
        100.6,
        101.0,
        99.9,
        100.6,
    ]
    h4.loc[signal_index, ["open", "high", "low", "close"]] = [98.0, 100.0, 97.0, 99.7]

    m5_periods = h4_periods * 48 + 288
    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [99.7] * m5_periods,
            "high": [100.2] * m5_periods,
            "low": [99.2] * m5_periods,
            "close": [99.7] * m5_periods,
            "mid_open": [99.7] * m5_periods,
            "mid_close": [99.7] * m5_periods,
            "bid_open": [99.6] * m5_periods,
            "ask_open": [99.8] * m5_periods,
            "bid_close": [99.6] * m5_periods,
            "ask_close": [99.8] * m5_periods,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:15:00Z", periods=5200, freq="15min"),
            "open": [99.7] * 5200,
            "high": [100.2] * 5200,
            "low": [99.2] * 5200,
            "close": [99.7] * 5200,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:00:00Z", periods=1400, freq="1h"),
            "open": [99.7] * 1400,
            "high": [100.2] * 1400,
            "low": [99.2] * 1400,
            "close": [99.7] * 1400,
        }
    )

    days = 430
    daily_times = pd.date_range("2023-01-01T00:00:00Z", periods=days, freq="1D")
    relative_flow = pd.DataFrame(
        {
            "timestamp_utc": daily_times,
            "date_utc": daily_times.date,
            "gld_open": [188.0] * days,
            "gld_high": [189.0] * days,
            "gld_low": [187.0] * days,
            "gld_close": [188.0] * days,
            "gld_volume": [10_000_000] * days,
            "gdx_open": [30.0] * days,
            "gdx_high": [30.4] * days,
            "gdx_low": [29.6] * days,
            "gdx_close": [30.0] * days,
            "gdx_volume": [35_000_000] * days,
            "source": ["synthetic"] * days,
        }
    )
    signal_day = pd.Timestamp(h4_times[signal_index]).normalize()
    divergence_day = signal_day - pd.Timedelta(days=1)
    previous_day = divergence_day - pd.Timedelta(days=1)
    previous_index = relative_flow.index[relative_flow["timestamp_utc"] == previous_day][0]
    divergence_index = relative_flow.index[relative_flow["timestamp_utc"] == divergence_day][0]
    relative_flow.loc[previous_index, ["gld_close", "gdx_close"]] = [188.0, 30.0]
    relative_flow.loc[divergence_index, ["gld_open", "gld_high", "gld_low", "gld_close"]] = [
        188.0,
        188.5,
        181.0,
        183.5,
    ]
    relative_flow.loc[divergence_index, ["gdx_open", "gdx_high", "gdx_low", "gdx_close"]] = [
        30.0,
        31.2,
        29.7,
        31.0,
    ]

    return {
        "M5": m5,
        "M15": m15,
        "H1": h1,
        "H4": h4,
        GDX_GLD_RELATIVE_FRAME_KEY: relative_flow,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_gdx_gld_trend_confirmation_context() -> dict:
    h1_periods = 420
    h1_times = pd.date_range("2024-01-01T00:00:00Z", periods=h1_periods, freq="1h")
    h1 = pd.DataFrame(
        {
            "timestamp_utc": h1_times,
            "bar_start_utc": h1_times - pd.Timedelta(hours=1),
            "open": [100.0] * h1_periods,
            "high": [100.4] * h1_periods,
            "low": [99.6] * h1_periods,
            "close": [100.0] * h1_periods,
        }
    )
    signal_index = 300
    h1.loc[signal_index - 80 : signal_index - 7, ["open", "high", "low", "close"]] = [
        101.0,
        101.6,
        100.8,
        101.2,
    ]
    h1.loc[signal_index - 6 : signal_index - 1, ["open", "high", "low", "close"]] = [
        101.0,
        101.4,
        100.4,
        100.9,
    ]
    h1.loc[signal_index, ["open", "high", "low", "close"]] = [100.8, 102.0, 100.4, 101.8]

    m5_periods = h1_periods * 12 + 144
    m5_times = pd.date_range("2024-01-01T00:05:00Z", periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [101.8] * m5_periods,
            "high": [102.3] * m5_periods,
            "low": [101.3] * m5_periods,
            "close": [101.8] * m5_periods,
            "mid_open": [101.8] * m5_periods,
            "mid_close": [101.8] * m5_periods,
            "bid_open": [101.7] * m5_periods,
            "ask_open": [101.9] * m5_periods,
            "bid_close": [101.7] * m5_periods,
            "ask_close": [101.9] * m5_periods,
        }
    )
    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:15:00Z", periods=1800, freq="15min"),
            "open": [101.8] * 1800,
            "high": [102.3] * 1800,
            "low": [101.3] * 1800,
            "close": [101.8] * 1800,
        }
    )
    h4 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-01-01T00:00:00Z", periods=120, freq="4h"),
            "open": [101.8] * 120,
            "high": [102.3] * 120,
            "low": [101.3] * 120,
            "close": [101.8] * 120,
        }
    )

    days = 430
    daily_times = pd.date_range("2023-01-01T00:00:00Z", periods=days, freq="1D")
    relative_flow = pd.DataFrame(
        {
            "timestamp_utc": daily_times,
            "date_utc": daily_times.date,
            "gld_open": [188.0] * days,
            "gld_high": [189.0] * days,
            "gld_low": [187.0] * days,
            "gld_close": [188.0] * days,
            "gld_volume": [10_000_000] * days,
            "gdx_open": [30.0] * days,
            "gdx_high": [30.4] * days,
            "gdx_low": [29.6] * days,
            "gdx_close": [30.0] * days,
            "gdx_volume": [35_000_000] * days,
            "source": ["synthetic"] * days,
        }
    )
    signal_day = pd.Timestamp(h1_times[signal_index]).normalize()
    confirmation_day = signal_day - pd.Timedelta(days=1)
    base_day = confirmation_day - pd.Timedelta(days=5)
    base_index = relative_flow.index[relative_flow["timestamp_utc"] == base_day][0]
    confirmation_index = relative_flow.index[relative_flow["timestamp_utc"] == confirmation_day][0]
    relative_flow.loc[base_index, ["gld_close", "gdx_close"]] = [188.0, 30.0]
    relative_flow.loc[confirmation_index, ["gld_open", "gld_high", "gld_low", "gld_close"]] = [
        188.0,
        189.0,
        186.5,
        189.0,
    ]
    relative_flow.loc[confirmation_index, ["gdx_open", "gdx_high", "gdx_low", "gdx_close"]] = [
        30.0,
        31.2,
        29.8,
        31.0,
    ]

    return {
        "M5": m5,
        "M15": m15,
        "H1": h1,
        "H4": h4,
        GDX_GLD_RELATIVE_FRAME_KEY: relative_flow,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _m15_inside_bar_breakout_context() -> dict:
    m5_times = pd.date_range("2024-05-01T06:05:00Z", periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 180,
            "high": [100.2] * 180,
            "low": [99.8] * 180,
            "close": [100.0] * 180,
            "atr14": [0.5] * 180,
            "mid_open": [100.0] * 180,
            "mid_close": [100.0] * 180,
            "bid_open": [99.9] * 180,
            "ask_open": [100.1] * 180,
            "bid_close": [99.9] * 180,
            "ask_close": [100.1] * 180,
        }
    )
    m5.loc[74, ["open", "high", "low", "close"]] = [100.35, 101.05, 100.30, 100.90]
    m5.loc[74, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.35,
        100.90,
        100.25,
        100.45,
        100.80,
        101.00,
    ]

    m15_times = pd.date_range("2024-05-01T06:15:00Z", periods=70, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 70,
            "high": [100.3] * 70,
            "low": [99.7] * 70,
            "close": [100.0] * 70,
            "atr14": [0.7] * 70,
        }
    )
    m15.loc[22, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.80, 99.20, 100.50, 0.7]
    m15.loc[23, ["open", "high", "low", "close", "atr14"]] = [100.35, 100.60, 99.80, 100.20, 0.7]

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:00:00Z", periods=30, freq="1h"),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [101.0] * 30,
            "ema50": [100.0] * 30,
            "ema50_slope12": [0.1] * 30,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _m15_two_bar_exhaustion_reversal_context() -> dict:
    periods = 80
    m15_times = pd.date_range("2024-05-02T00:15:00Z", periods=periods, freq="15min")
    closes = [2000.0 + (0.05 if index % 2 == 0 else -0.05) for index in range(periods)]
    opens = [2000.0] * periods
    highs = [2000.45] * periods
    lows = [1999.55] * periods

    opens[-3] = 2000.0
    closes[-3] = 2000.0
    highs[-3] = 2000.45
    lows[-3] = 1999.55
    opens[-2] = 2000.0
    closes[-2] = 1999.05
    highs[-2] = 2000.20
    lows[-2] = 1998.85
    opens[-1] = 1999.05
    closes[-1] = 1997.80
    highs[-1] = 1999.20
    lows[-1] = 1997.60

    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "bar_start_utc": m15_times - pd.Timedelta(minutes=15),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "mid_open": opens,
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": closes,
            "bid_open": [value - 0.01 for value in opens],
            "ask_open": [value + 0.01 for value in opens],
            "bid_close": [value - 0.01 for value in closes],
            "ask_close": [value + 0.01 for value in closes],
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(m15_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.8] * 180,
            "low": [last_close - 0.8] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "M15": m15, "symbol": "XAUUSD", "point_size": 0.01}


def _m15_two_bar_impulse_continuation_context() -> dict:
    periods = 80
    m15_times = pd.date_range("2024-05-03T00:15:00Z", periods=periods, freq="15min")
    closes = [2000.0 + (0.05 if index % 2 == 0 else -0.05) for index in range(periods)]
    opens = [2000.0] * periods
    highs = [2000.45] * periods
    lows = [1999.55] * periods

    opens[-3] = 2000.0
    closes[-3] = 2000.0
    highs[-3] = 2000.45
    lows[-3] = 1999.55
    opens[-2] = 2000.0
    closes[-2] = 2000.95
    highs[-2] = 2001.15
    lows[-2] = 1999.80
    opens[-1] = 2000.95
    closes[-1] = 2002.20
    highs[-1] = 2002.40
    lows[-1] = 2000.80

    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "bar_start_utc": m15_times - pd.Timedelta(minutes=15),
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "mid_open": opens,
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": closes,
            "bid_open": [value - 0.01 for value in opens],
            "ask_open": [value + 0.01 for value in opens],
            "bid_close": [value - 0.01 for value in closes],
            "ask_close": [value + 0.01 for value in closes],
        }
    )

    last_close = closes[-1]
    m5_times = pd.date_range(m15_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.8] * 180,
            "low": [last_close - 0.8] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "M15": m15, "symbol": "XAUUSD", "point_size": 0.01}


def _m5_impulse_continuation_context() -> dict:
    m5_times = pd.date_range("2024-05-01T06:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.2] * 120,
            "low": [99.8] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    m5.loc[74, ["open", "high", "low", "close"]] = [100.00, 100.45, 99.95, 100.35]
    m5.loc[75, ["open", "high", "low", "close"]] = [100.35, 100.82, 100.30, 100.76]
    for idx in (74, 75):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:00:00Z", periods=30, freq="1h"),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [101.0] * 30,
            "ema50": [100.0] * 30,
            "ema50_slope12": [0.1] * 30,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _london_fix_continuation_context() -> dict:
    m5_times = pd.date_range("2024-06-03T11:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.3] * 120,
            "low": [99.7] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    local_starts = pd.to_datetime(m5["bar_start_utc"], utc=True).dt.tz_convert("Europe/London")
    pre_fix_mask = (
        (local_starts.dt.hour == 14)
        & (local_starts.dt.minute >= 30)
        & (local_starts.dt.minute < 60)
    )
    m5.loc[pre_fix_mask, ["high", "low"]] = [101.0, 99.0]
    m5.loc[36, ["open", "high", "low", "close"]] = [100.80, 101.60, 100.70, 101.40]
    m5.loc[36, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.80,
        101.40,
        100.70,
        100.90,
        101.30,
        101.50,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-06-03T13:15:00Z", periods=40, freq="15min"),
            "open": [100.0] * 40,
            "high": [101.0] * 40,
            "low": [99.0] * 40,
            "close": [100.0] * 40,
            "atr14": [1.0] * 40,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-06-03T08:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _extreme_activity_mean_reversion_context() -> dict:
    m5_times = pd.date_range("2024-05-01T00:05:00Z", periods=360, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 360,
            "high": [100.2] * 360,
            "low": [99.8] * 360,
            "close": [100.0] * 360,
            "atr14": [1.0] * 360,
            "mid_open": [100.0] * 360,
            "mid_close": [100.0] * 360,
            "bid_open": [99.9] * 360,
            "ask_open": [100.1] * 360,
            "bid_close": [99.9] * 360,
            "ask_close": [100.1] * 360,
        }
    )
    m5.loc[320, ["open", "high", "low", "close"]] = [102.50, 103.00, 99.80, 100.05]
    m5.loc[320, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        102.50,
        100.05,
        102.40,
        102.60,
        99.95,
        100.15,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:15:00Z", periods=140, freq="15min"),
            "open": [100.0] * 140,
            "high": [101.0] * 140,
            "low": [99.0] * 140,
            "close": [100.0] * 140,
            "atr14": [1.5] * 140,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-05-01T00:00:00Z", periods=40, freq="1h"),
            "open": [100.0] * 40,
            "high": [102.0] * 40,
            "low": [98.0] * 40,
            "close": [100.0] * 40,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _compression_retest_continuation_context() -> dict:
    m15_times = pd.date_range("2024-07-01T00:15:00Z", periods=150, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 150,
            "high": [102.0] * 120 + [100.10] * 30,
            "low": [98.0] * 120 + [99.90] * 30,
            "close": [100.0] * 150,
        }
    )

    m5_times = pd.date_range("2024-07-01T00:05:00Z", periods=450, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 450,
            "high": [100.08] * 450,
            "low": [99.92] * 450,
            "close": [100.0] * 450,
            "atr14": [0.4] * 450,
            "mid_open": [100.0] * 450,
            "mid_close": [100.0] * 450,
            "bid_open": [99.9] * 450,
            "ask_open": [100.1] * 450,
            "bid_close": [99.9] * 450,
            "ask_close": [100.1] * 450,
        }
    )
    m5.loc[410, ["open", "high", "low", "close"]] = [100.00, 100.75, 99.98, 100.55]
    m5.loc[413, ["open", "high", "low", "close"]] = [100.30, 100.38, 100.12, 100.18]
    m5.loc[415, ["open", "high", "low", "close"]] = [100.25, 100.70, 100.22, 100.60]
    for idx in (410, 413, 415):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-07-01T00:00:00Z", periods=50, freq="1h"),
            "open": [100.0] * 50,
            "high": [102.0] * 50,
            "low": [98.0] * 50,
            "close": [100.0] * 50,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _asia_range_london_breakout_context() -> dict:
    m5_times = pd.date_range("2024-08-01T00:05:00Z", periods=160, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 160,
            "high": [100.3] * 160,
            "low": [99.7] * 160,
            "close": [100.0] * 160,
            "atr14": [0.5] * 160,
            "mid_open": [100.0] * 160,
            "mid_close": [100.0] * 160,
            "bid_open": [99.9] * 160,
            "ask_open": [100.1] * 160,
            "bid_close": [99.9] * 160,
            "ask_close": [100.1] * 160,
        }
    )
    asia_mask = (m5["bar_start_utc"].dt.hour >= 0) & (m5["bar_start_utc"].dt.hour < 6)
    m5.loc[asia_mask, ["high", "low"]] = [101.0, 99.0]
    m5.loc[90, ["open", "high", "low", "close"]] = [100.80, 101.70, 100.60, 101.50]
    m5.loc[90, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.80,
        101.50,
        100.70,
        100.90,
        101.40,
        101.60,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-08-01T00:15:00Z", periods=80, freq="15min"),
            "open": [100.0] * 80,
            "high": [101.0] * 80,
            "low": [99.0] * 80,
            "close": [100.0] * 80,
            "atr14": [1.2] * 80,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-08-01T00:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _asia_range_london_failed_break_reversal_context() -> dict:
    context = _asia_range_london_breakout_context()
    m5 = context["M5"].copy()
    m5.loc[90, ["open", "high", "low", "close"]] = [101.30, 101.60, 100.40, 100.60]
    m5.loc[90, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        101.30,
        100.60,
        101.20,
        101.40,
        100.50,
        100.70,
    ]
    context["M5"] = m5
    return context


def _previous_day_extreme_retest_context() -> dict:
    m5_times = pd.date_range("2024-09-01T00:05:00Z", periods=600, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 600,
            "high": [100.2] * 600,
            "low": [99.8] * 600,
            "close": [100.0] * 600,
            "atr14": [0.5] * 600,
            "mid_open": [100.0] * 600,
            "mid_close": [100.0] * 600,
            "bid_open": [99.9] * 600,
            "ask_open": [100.1] * 600,
            "bid_close": [99.9] * 600,
            "ask_close": [100.1] * 600,
        }
    )
    first_day = m5["bar_start_utc"].dt.strftime("%Y-%m-%d") == "2024-09-01"
    m5.loc[first_day, ["high", "low"]] = [101.0, 99.0]
    m5.loc[400, ["open", "high", "low", "close"]] = [100.20, 101.75, 100.15, 101.50]
    m5.loc[403, ["open", "high", "low", "close"]] = [101.30, 101.35, 101.05, 101.15]
    m5.loc[405, ["open", "high", "low", "close"]] = [101.20, 101.70, 101.15, 101.60]
    for idx in (400, 403, 405):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-09-01T00:15:00Z", periods=220, freq="15min"),
            "open": [100.0] * 220,
            "high": [101.0] * 220,
            "low": [99.0] * 220,
            "close": [100.0] * 220,
            "atr14": [1.0] * 220,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-09-01T00:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [102.0] * 60,
            "low": [98.0] * 60,
            "close": [100.0] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _round_number_retest_context() -> dict:
    context = _breakout_context()
    m5 = context["M5"].copy()
    m5["previous_daily_high"] = [pd.NA] * len(m5)
    m5["previous_daily_low"] = [pd.NA] * len(m5)
    m5["previous_weekly_high"] = [pd.NA] * len(m5)
    m5["previous_weekly_low"] = [pd.NA] * len(m5)
    m5["latest_swing_high"] = [pd.NA] * len(m5)
    m5["latest_swing_high_time_utc"] = [pd.NaT] * len(m5)
    m5["latest_swing_low"] = [pd.NA] * len(m5)
    m5["latest_swing_low_time_utc"] = [pd.NaT] * len(m5)
    context["M5"] = m5
    return context


def _session_extreme_retest_context() -> dict:
    m5 = _base_m5("2024-04-01T00:00:00Z", 120)
    m5["timestamp_utc"] = pd.to_datetime(m5["timestamp_utc"], utc=True)
    m5["bar_start_utc"] = pd.to_datetime(m5["bar_start_utc"], utc=True)
    m5["atr14"] = [1.0] * len(m5)
    asia_mask = m5["bar_start_utc"].dt.hour < 6
    m5.loc[asia_mask, ["high", "low", "close"]] = [100.0, 98.0, 99.0]
    m5.loc[86, ["open", "high", "low", "close"]] = [99.8, 101.0, 99.7, 100.5]
    m5.loc[88, ["open", "high", "low", "close"]] = [100.3, 100.4, 99.95, 100.1]
    m5.loc[89, ["open", "high", "low", "close"]] = [100.1, 100.6, 100.0, 100.5]
    for column in ("mid_open", "bid_open", "ask_open"):
        m5[column] = m5["open"]
    for column in ("mid_close", "bid_close", "ask_close"):
        m5[column] = m5["close"]
    m5["bid_open"] = m5["open"] - 0.1
    m5["ask_open"] = m5["open"] + 0.1
    m5["bid_close"] = m5["close"] - 0.1
    m5["ask_close"] = m5["close"] + 0.1
    return {"M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


def _symbol_round_sweep_reversal_context() -> dict:
    m5 = _base_m5("2024-12-03T09:00:00Z", 40)
    m5["atr14"] = [1.0] * 40
    m5.loc[30, ["open", "high", "low", "close"]] = [100.00, 100.45, 99.55, 100.25]
    m5.loc[30, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.00,
        100.25,
        99.90,
        100.10,
        100.15,
        100.35,
    ]
    return {"M5": m5, "symbol": "XAUUSD", "point_size": 0.01}


def _ny_am_pullback_continuation_context() -> dict:
    m5_times = pd.date_range("2024-10-01T13:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.2] * 120,
            "low": [99.8] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    m5.loc[6, ["open", "high", "low", "close"]] = [100.00, 100.35, 99.90, 100.25]
    m5.loc[7, ["open", "high", "low", "close"]] = [100.25, 100.75, 100.20, 100.65]
    m5.loc[8, ["open", "high", "low", "close"]] = [100.65, 101.10, 100.60, 101.00]
    m5.loc[9, ["open", "high", "low", "close"]] = [101.00, 101.35, 100.95, 101.20]
    m5.loc[10, ["open", "high", "low", "close"]] = [101.20, 101.40, 101.00, 101.25]
    m5.loc[11, ["open", "high", "low", "close"]] = [101.25, 101.45, 101.05, 101.30]
    m5.loc[24, ["open", "high", "low", "close"]] = [100.95, 101.00, 100.57, 100.75]
    m5.loc[26, ["open", "high", "low", "close"]] = [100.82, 101.28, 100.78, 101.20]
    for idx in (6, 7, 8, 9, 10, 11, 24, 26):
        m5.loc[idx, "mid_open"] = m5.loc[idx, "open"]
        m5.loc[idx, "mid_close"] = m5.loc[idx, "close"]
        m5.loc[idx, "bid_open"] = m5.loc[idx, "open"] - 0.1
        m5.loc[idx, "ask_open"] = m5.loc[idx, "open"] + 0.1
        m5.loc[idx, "bid_close"] = m5.loc[idx, "close"] - 0.1
        m5.loc[idx, "ask_close"] = m5.loc[idx, "close"] + 0.1

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T13:15:00Z", periods=50, freq="15min"),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
            "atr14": [1.0] * 50,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T10:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _ny_london_overlap_compression_break_context() -> dict:
    m15_times = pd.date_range("2024-10-01T00:15:00Z", periods=180, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "open": [100.0] * 180,
            "high": [102.0] * 130 + [100.12] * 50,
            "low": [98.0] * 130 + [99.88] * 50,
            "close": [100.0] * 180,
        }
    )

    m5_times = pd.date_range("2024-10-01T00:05:00Z", periods=500, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 500,
            "high": [100.10] * 500,
            "low": [99.90] * 500,
            "close": [100.0] * 500,
            "atr14": [1.0] * 448 + [0.35] * 52,
            "mid_open": [100.0] * 500,
            "mid_close": [100.0] * 500,
            "bid_open": [99.9] * 500,
            "ask_open": [100.1] * 500,
            "bid_close": [99.9] * 500,
            "ask_close": [100.1] * 500,
        }
    )
    m5.loc[450, ["open", "high", "low", "close", "atr14"]] = [100.0, 100.58, 99.96, 100.50, 0.35]
    m5.loc[450, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        100.0,
        100.50,
        99.9,
        100.1,
        100.40,
        100.60,
    ]

    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T00:00:00Z", periods=60, freq="1h"),
            "open": [100.0] * 60,
            "high": [102.0] * 60,
            "low": [99.0] * 60,
            "close": [101.0] * 60,
            "ema50": [100.0] * 60,
            "ema50_slope12": [0.1] * 60,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _opening_drive_failed_continuation_context() -> dict:
    m5_times = pd.date_range("2024-10-01T13:05:00Z", periods=120, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 120,
            "high": [100.2] * 120,
            "low": [99.8] * 120,
            "close": [100.0] * 120,
            "atr14": [0.5] * 120,
            "mid_open": [100.0] * 120,
            "mid_close": [100.0] * 120,
            "bid_open": [99.9] * 120,
            "ask_open": [100.1] * 120,
            "bid_close": [99.9] * 120,
            "ask_close": [100.1] * 120,
        }
    )
    for idx, values in {
        6: (100.00, 100.45, 99.95, 100.35),
        7: (100.35, 100.85, 100.30, 100.75),
        8: (100.75, 101.10, 100.70, 101.00),
        9: (101.00, 101.20, 100.92, 101.05),
        10: (101.05, 101.25, 100.95, 101.10),
        11: (101.10, 101.30, 101.00, 101.15),
        16: (101.55, 101.62, 100.80, 100.95),
    }.items():
        m5.loc[idx, ["open", "high", "low", "close"]] = values
        m5.loc[idx, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
            values[0],
            values[3],
            values[0] - 0.1,
            values[0] + 0.1,
            values[3] - 0.1,
            values[3] + 0.1,
        ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T13:15:00Z", periods=50, freq="15min"),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-10-01T10:00:00Z", periods=24, freq="1h"),
            "open": [100.0] * 24,
            "high": [102.0] * 24,
            "low": [98.0] * 24,
            "close": [100.0] * 24,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _weekly_level_reclaim_context() -> dict:
    m5_times = pd.date_range("2024-11-04T00:05:00Z", periods=2300, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 2300,
            "high": [100.2] * 2300,
            "low": [99.8] * 2300,
            "close": [100.0] * 2300,
            "atr14": [0.5] * 2300,
            "mid_open": [100.0] * 2300,
            "mid_close": [100.0] * 2300,
            "bid_open": [99.9] * 2300,
            "ask_open": [100.1] * 2300,
            "bid_close": [99.9] * 2300,
            "ask_close": [100.1] * 2300,
        }
    )
    first_week = m5["bar_start_utc"].dt.isocalendar().week == 45
    m5.loc[first_week, ["high", "low"]] = [101.0, 99.0]
    m5.loc[2100, ["open", "high", "low", "close"]] = [98.70, 99.40, 98.60, 99.20]
    m5.loc[2100, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        98.70,
        99.20,
        98.60,
        98.80,
        99.10,
        99.30,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-11-04T00:15:00Z", periods=780, freq="15min"),
            "open": [100.0] * 780,
            "high": [101.0] * 780,
            "low": [99.0] * 780,
            "close": [100.0] * 780,
            "atr14": [1.0] * 780,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-11-04T00:00:00Z", periods=200, freq="1h"),
            "open": [100.0] * 200,
            "high": [102.0] * 200,
            "low": [98.0] * 200,
            "close": [100.0] * 200,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _session_vwap_reclaim_context() -> dict:
    m5_times = pd.date_range("2024-12-02T06:05:00Z", periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 180,
            "high": [100.2] * 180,
            "low": [99.8] * 180,
            "close": [100.0] * 180,
            "atr14": [0.5] * 180,
            "mid_open": [100.0] * 180,
            "mid_close": [100.0] * 180,
            "bid_open": [99.9] * 180,
            "ask_open": [100.1] * 180,
            "bid_close": [99.9] * 180,
            "ask_close": [100.1] * 180,
        }
    )
    m5.loc[50, ["open", "high", "low", "close"]] = [99.25, 100.20, 99.20, 100.12]
    m5.loc[50, ["mid_open", "mid_close", "bid_open", "ask_open", "bid_close", "ask_close"]] = [
        99.25,
        100.12,
        99.15,
        99.35,
        100.02,
        100.22,
    ]

    m15 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-12-02T06:15:00Z", periods=70, freq="15min"),
            "open": [100.0] * 70,
            "high": [101.0] * 70,
            "low": [99.0] * 70,
            "close": [100.0] * 70,
            "atr14": [1.0] * 70,
        }
    )
    h1 = pd.DataFrame(
        {
            "timestamp_utc": pd.date_range("2024-12-02T00:00:00Z", periods=30, freq="1h"),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [100.0] * 30,
        }
    )
    return {"M5": m5, "M15": m15, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _weekly_open_reversion_context() -> dict:
    m15_times = pd.date_range("2024-12-02T00:15:00Z", periods=180, freq="15min")
    m15 = pd.DataFrame(
        {
            "timestamp_utc": m15_times,
            "bar_start_utc": m15_times - pd.Timedelta(minutes=15),
            "open": [100.0] * 180,
            "high": [100.4] * 180,
            "low": [99.6] * 180,
            "close": [100.0] * 180,
            "atr14": [1.0] * 180,
        }
    )
    m15.loc[128, ["open", "high", "low", "close"]] = [96.0, 97.0, 95.0, 96.8]

    m5_times = pd.date_range("2024-12-02T00:05:00Z", periods=540, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [100.0] * 540,
            "high": [100.2] * 540,
            "low": [99.8] * 540,
            "close": [100.0] * 540,
            "mid_open": [100.0] * 540,
            "mid_close": [100.0] * 540,
            "bid_open": [99.9] * 540,
            "ask_open": [100.1] * 540,
            "bid_close": [99.9] * 540,
            "ask_close": [100.1] * 540,
        }
    )
    return {"M5": m5, "M15": m15, "symbol": "XAUUSD", "point_size": 0.01}


def _gold_fx_proxy_divergence_context() -> dict:
    periods = 380
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    base_returns = [0.0001 if index % 2 == 0 else -0.00008 for index in range(periods)]
    usd_strength_returns = [0.0] * periods
    for index in range(periods - 30, periods):
        usd_strength_returns[index] = 0.0008

    eurusd_returns = [base_returns[index] - usd_strength_returns[index] for index in range(periods)]
    usdjpy_returns = [base_returns[index] + usd_strength_returns[index] for index in range(periods)]
    xau_returns = [0.00005 if index % 3 else -0.00004 for index in range(periods)]
    for index in range(periods - 30, periods):
        xau_returns[index] = 0.002

    xau_close = _price_path(2000.0, xau_returns)
    eurusd_close = _price_path(1.1000, eurusd_returns)
    usdjpy_close = _price_path(145.0, usdjpy_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    eurusd = _ohlc_from_closes(h1_times, eurusd_close, "capital_com", "EURUSD", "H1")
    usdjpy = _ohlc_from_closes(h1_times, usdjpy_close, "capital_com", "USDJPY", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "intermarket_proxy": {"EURUSD": eurusd, "USDJPY": usdjpy},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _h1_return_autocorrelation_state_context() -> dict:
    periods = 240
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    returns = [0.00008 if index % 2 == 0 else -0.00004 for index in range(periods)]
    for index in range(120, periods):
        returns[index] = 0.0012 if index % 3 else 0.0007

    closes = _price_path(2000.0, returns)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(120, periods):
        h1.loc[h1.index[index], "high"] = max(
            float(h1.loc[h1.index[index], "high"]),
            float(h1.loc[h1.index[index], "close"]) + 0.35,
        )

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.9] * 180,
            "low": [last_close - 0.9] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_m5_path_skew_reversal_context() -> dict:
    periods = 80
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0 + (0.15 if index % 2 == 0 else -0.10) for index in range(periods)]
    closes[-2] = 2002.0
    closes[-1] = 1999.75
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(periods - 1):
        h1.loc[h1.index[index], "high"] = max(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) + 0.50
        h1.loc[h1.index[index], "low"] = min(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) - 0.50
    h1.loc[h1.index[-1], "open"] = 2002.0
    h1.loc[h1.index[-1], "high"] = 2002.3
    h1.loc[h1.index[-1], "low"] = 1998.6
    h1.loc[h1.index[-1], "close"] = 1999.75

    m5_rows: list[dict[str, object]] = []
    for h1_index, h1_end in enumerate(h1_times):
        h1_start = h1_end - pd.Timedelta(hours=1)
        if h1_index == periods - 1:
            opens = [
                2002.0,
                2001.3,
                2000.6,
                1999.9,
                1999.3,
                1998.9,
                1998.8,
                1998.9,
                1999.0,
                1999.1,
                1999.3,
                1999.5,
            ]
            closes_m5 = [
                2001.3,
                2000.6,
                1999.9,
                1999.3,
                1998.9,
                1998.8,
                1998.9,
                1999.0,
                1999.1,
                1999.3,
                1999.5,
                1999.75,
            ]
        else:
            start_price = float(h1.iloc[h1_index]["open"])
            end_price = float(h1.iloc[h1_index]["close"])
            step = (end_price - start_price) / 12.0
            opens = [start_price + step * offset for offset in range(12)]
            closes_m5 = [start_price + step * (offset + 1) for offset in range(12)]
        for offset, (open_price, close_price) in enumerate(zip(opens, closes_m5), start=1):
            timestamp = h1_start + pd.Timedelta(minutes=5 * offset)
            high = max(open_price, close_price) + 0.08
            low = min(open_price, close_price) - 0.08
            m5_rows.append(
                {
                    "timestamp_utc": timestamp,
                    "bar_start_utc": timestamp - pd.Timedelta(minutes=5),
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close_price,
                    "mid_open": open_price,
                    "mid_close": close_price,
                    "bid_open": open_price - 0.1,
                    "ask_open": open_price + 0.1,
                    "bid_close": close_price - 0.1,
                    "ask_close": close_price + 0.1,
                }
            )
    m5 = pd.DataFrame(m5_rows)
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_smooth_trend_exhaustion_reversal_context() -> dict:
    periods = 140
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0] * periods
    for index in range(1, 110):
        closes[index] = closes[index - 1] + (0.05 if index % 2 == 0 else -0.04)
    for index in range(110, periods - 1):
        closes[index] = closes[index - 1] - 2.0
    closes[-1] = closes[-2] + 1.2

    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    h1.loc[h1.index[-1], "low"] = min(float(h1.loc[h1.index[-1], "low"]), closes[-2] - 0.3)
    h1.loc[h1.index[-1], "high"] = max(float(h1.loc[h1.index[-1], "high"]), closes[-1] + 0.1)

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.8] * 180,
            "low": [last_close - 0.8] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_tick_volume_climax_reversal_context() -> dict:
    periods = 300
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0 + (0.12 if index % 2 == 0 else -0.08) for index in range(periods)]
    closes[-2] = 2002.0
    closes[-1] = 1999.8
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(periods - 1):
        h1.loc[h1.index[index], "high"] = max(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) + 0.50
        h1.loc[h1.index[index], "low"] = min(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) - 0.50
        h1.loc[h1.index[index], "tick_count"] = 100.0 + (index % 7)
        h1.loc[h1.index[index], "volume_sum"] = 100.0 + (index % 7)
    h1.loc[h1.index[-1], "open"] = 2002.0
    h1.loc[h1.index[-1], "high"] = 2002.4
    h1.loc[h1.index[-1], "low"] = 1998.7
    h1.loc[h1.index[-1], "close"] = 1999.8
    h1.loc[h1.index[-1], "tick_count"] = 380.0
    h1.loc[h1.index[-1], "volume_sum"] = 380.0

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.9] * 180,
            "low": [last_close - 0.9] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_tick_volume_climax_continuation_context() -> dict:
    periods = 300
    h1_times = pd.date_range("2024-01-03T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0]
    for index in range(1, periods):
        change = 0.10 if index % 2 == 0 else -0.07
        if index > periods - 8:
            change = 0.35
        closes.append(closes[-1] + change)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(periods - 1):
        h1.loc[h1.index[index], "high"] = max(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) + 0.50
        h1.loc[h1.index[index], "low"] = min(
            float(h1.loc[h1.index[index], "open"]),
            float(h1.loc[h1.index[index], "close"]),
        ) - 0.50
        h1.loc[h1.index[index], "tick_count"] = 100.0 + (index % 7)
        h1.loc[h1.index[index], "volume_sum"] = 100.0 + (index % 7)

    previous_close = float(h1.loc[h1.index[-2], "close"])
    h1.loc[h1.index[-1], "open"] = previous_close
    h1.loc[h1.index[-1], "close"] = previous_close + 3.20
    h1.loc[h1.index[-1], "high"] = previous_close + 3.50
    h1.loc[h1.index[-1], "low"] = previous_close - 0.35
    h1.loc[h1.index[-1], "tick_count"] = 380.0
    h1.loc[h1.index[-1], "volume_sum"] = 380.0
    for column in ("mid_open", "bid_open", "ask_open"):
        h1.loc[h1.index[-1], column] = h1.loc[h1.index[-1], "open"]
    for column in ("mid_close", "bid_close", "ask_close"):
        h1.loc[h1.index[-1], column] = h1.loc[h1.index[-1], "close"]

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.9] * 180,
            "low": [last_close - 0.9] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_volatility_squeeze_breakout_context() -> dict:
    periods = 340
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    closes = [2000.0]
    for index in range(1, periods):
        if index < periods - 8:
            change = 0.06 if index % 2 == 0 else -0.05
        else:
            change = 0.45
        closes.append(closes[-1] + change)

    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    for index in range(periods - 8, periods):
        h1.loc[h1.index[index], "open"] = float(h1.loc[h1.index[index - 1], "close"])
        h1.loc[h1.index[index], "close"] = float(h1.loc[h1.index[index], "open"]) + 0.45
        h1.loc[h1.index[index], "high"] = float(h1.loc[h1.index[index], "close"]) + 0.08
        h1.loc[h1.index[index], "low"] = float(h1.loc[h1.index[index], "open"]) - 0.06
        for column in ("mid_open", "bid_open", "ask_open"):
            h1.loc[h1.index[index], column] = h1.loc[h1.index[index], "open"]
        for column in ("mid_close", "bid_close", "ask_close"):
            h1.loc[h1.index[index], column] = h1.loc[h1.index[index], "close"]

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_walk_forward_linear_state_context() -> dict:
    periods = 1320
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    returns: list[float] = []
    for index in range(periods):
        if index < 240:
            returns.append(0.00005 if index % 2 == 0 else -0.00004)
            continue

        regime = (index // 72) % 4
        if regime in (0, 1):
            returns.append(0.00110 if index % 6 else 0.00045)
        else:
            returns.append(-0.00110 if index % 6 else -0.00045)

    for index in range(periods - 120, periods):
        returns[index] = 0.00115 if index % 6 else 0.00050

    closes = _price_path(2000.0, returns)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")
    h1["tick_count"] = [120.0 + float(index % 19) + (8.0 if index % 6 else 0.0) for index in range(periods)]
    h1["volume_sum"] = h1["tick_count"]

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _h1_calendar_drift_state_context() -> dict:
    periods = 2400
    horizon = 6
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    target_timestamp = h1_times[-1]
    target_bucket = int(target_timestamp.dayofweek * 24 + target_timestamp.hour)
    returns = [0.00003 if index % 2 == 0 else -0.00002 for index in range(periods)]

    for index, timestamp in enumerate(h1_times[:-horizon]):
        bucket = int(timestamp.dayofweek * 24 + timestamp.hour)
        if bucket != target_bucket:
            continue
        for offset in range(1, horizon + 1):
            returns[index + offset] = 0.00100 if offset % 2 else 0.00075

    closes = _price_path(2000.0, returns)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 0.8] * 180,
            "low": [last_close - 0.8] * 180,
            "close": [last_close + 0.1] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.1] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close] * 180,
            "ask_close": [last_close + 0.2] * 180,
        }
    )
    return {"M5": m5, "H1": h1, "symbol": "XAUUSD", "point_size": 0.01}


def _xau_xag_relative_value_context() -> dict:
    periods = 720
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    xag_returns = [0.00008 if index % 2 == 0 else -0.00005 for index in range(periods)]
    xau_returns = [0.00007 if index % 2 == 0 else -0.00004 for index in range(periods)]
    for index in range(periods - 42, periods - 12):
        xag_returns[index] = 0.0012
        xau_returns[index] = -0.0007
    for index in range(periods - 12, periods):
        xag_returns[index] = 0.0001
        xau_returns[index] = 0.0015

    xau_close = _price_path(2000.0, xau_returns)
    xag_close = _price_path(24.0, xag_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    xag = _ohlc_from_closes(h1_times, xag_close, "capital_com", "XAGUSD", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "relative_value": {"XAGUSD": xag},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _xau_xag_fx_composite_reversion_context() -> dict:
    periods = 760
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    xag_returns = [0.00008 if index % 2 == 0 else -0.00005 for index in range(periods)]
    xau_returns = [0.00005 if index % 2 == 0 else -0.00004 for index in range(periods)]
    eurusd_returns = [0.00003 if index % 2 == 0 else -0.00002 for index in range(periods)]
    usdjpy_returns = [0.00002 if index % 2 == 0 else -0.00003 for index in range(periods)]

    for index in range(periods - 48, periods - 4):
        xag_returns[index] = 0.0011
        xau_returns[index] = -0.00055
        eurusd_returns[index] = 0.00070
        usdjpy_returns[index] = -0.00065
    for index in range(periods - 4, periods):
        xag_returns[index] = 0.00015
        xau_returns[index] = 0.00120
        eurusd_returns[index] = 0.00055
        usdjpy_returns[index] = -0.00055

    xau_close = _price_path(2000.0, xau_returns)
    xag_close = _price_path(24.0, xag_returns)
    eurusd_close = _price_path(1.10, eurusd_returns)
    usdjpy_close = _price_path(145.0, usdjpy_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    xag = _ohlc_from_closes(h1_times, xag_close, "capital_com", "XAGUSD", "H1")
    eurusd = _ohlc_from_closes(h1_times, eurusd_close, "capital_com", "EURUSD", "H1")
    usdjpy = _ohlc_from_closes(h1_times, usdjpy_close, "capital_com", "USDJPY", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "relative_value": {"XAGUSD": xag},
        "intermarket_proxy": {"EURUSD": eurusd, "USDJPY": usdjpy},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _xag_lead_xau_followthrough_context() -> dict:
    periods = 720
    h1_times = pd.date_range("2024-01-01T01:00:00Z", periods=periods, freq="1h")
    xag_returns = [0.00004 if index % 2 == 0 else -0.00003 for index in range(periods)]
    xau_returns = [0.00003 if index % 2 == 0 else -0.00002 for index in range(periods)]

    for index in range(periods - 24, periods - 4):
        xag_returns[index] = 0.00120
        xau_returns[index] = 0.00005
    for index in range(periods - 4, periods):
        xag_returns[index] = 0.00040
        xau_returns[index] = 0.00095

    xau_close = _price_path(2000.0, xau_returns)
    xag_close = _price_path(24.0, xag_returns)
    h1 = _ohlc_from_closes(h1_times, xau_close, "capital_com", "XAUUSD", "H1")
    xag = _ohlc_from_closes(h1_times, xag_close, "capital_com", "XAGUSD", "H1")

    last_close = float(h1["close"].iloc[-1])
    m5_times = pd.date_range(h1_times[-1] + pd.Timedelta(minutes=5), periods=180, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [last_close] * 180,
            "high": [last_close + 1.0] * 180,
            "low": [last_close - 1.0] * 180,
            "close": [last_close + 0.2] * 180,
            "mid_open": [last_close] * 180,
            "mid_close": [last_close + 0.2] * 180,
            "bid_open": [last_close - 0.1] * 180,
            "ask_open": [last_close + 0.1] * 180,
            "bid_close": [last_close + 0.1] * 180,
            "ask_close": [last_close + 0.3] * 180,
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        "relative_value": {"XAGUSD": xag},
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _price_path(start: float, returns: list[float]) -> list[float]:
    prices: list[float] = []
    current = start
    for value in returns:
        current *= 1.0 + value
        prices.append(current)
    return prices


def _h1_macro_event_aftershock_context() -> dict:
    h1_times = pd.date_range("2022-01-03T00:00:00Z", periods=220, freq="1h")
    event_timestamp = pd.Timestamp("2022-01-07T13:30:00Z")
    confirm_timestamp = pd.Timestamp("2022-01-07T15:00:00Z")
    closes: list[float] = []
    current = 2000.0
    for timestamp in h1_times:
        current += 0.08 if timestamp.hour % 2 else -0.03
        if timestamp >= confirm_timestamp:
            current += 1.15
        closes.append(current)
    h1 = _ohlc_from_closes(h1_times, closes, "capital_com", "XAUUSD", "H1")

    m5_periods = len(h1_times) * 12 + 144
    m5_times = pd.date_range(h1_times[0] + pd.Timedelta(minutes=5), periods=m5_periods, freq="5min")
    m5 = pd.DataFrame(
        {
            "timestamp_utc": m5_times,
            "bar_start_utc": m5_times - pd.Timedelta(minutes=5),
            "open": [closes[-1]] * m5_periods,
            "high": [closes[-1] + 2.0] * m5_periods,
            "low": [closes[-1] - 2.0] * m5_periods,
            "close": [closes[-1] + 0.5] * m5_periods,
            "mid_open": [closes[-1]] * m5_periods,
            "mid_close": [closes[-1] + 0.5] * m5_periods,
            "bid_open": [closes[-1] - 0.1] * m5_periods,
            "ask_open": [closes[-1] + 0.1] * m5_periods,
            "bid_close": [closes[-1] + 0.4] * m5_periods,
            "ask_close": [closes[-1] + 0.6] * m5_periods,
        }
    )
    events = pd.DataFrame(
        {
            "timestamp_utc": [event_timestamp],
            "event_type": ["NFP_FIRST_FRIDAY"],
            "source_rule": ["NFP_FIRST_FRIDAY"],
            "local_date": ["2022-01-07"],
            "local_time_et": ["08:30"],
        }
    )
    return {
        "M5": m5,
        "H1": h1,
        MACRO_EVENT_FRAME_KEY: events,
        "symbol": "XAUUSD",
        "point_size": 0.01,
    }


def _ohlc_from_closes(
    timestamps: pd.DatetimeIndex,
    closes: list[float],
    broker: str,
    symbol: str,
    timeframe: str,
) -> pd.DataFrame:
    opens = [closes[0], *closes[:-1]]
    highs = [max(open_price, close) + 0.05 for open_price, close in zip(opens, closes)]
    lows = [min(open_price, close) - 0.05 for open_price, close in zip(opens, closes)]
    starts = timestamps - pd.Timedelta(hours=1)
    return pd.DataFrame(
        {
            "timestamp_utc": timestamps,
            "bar_start_utc": starts,
            "bar_end_utc": timestamps,
            "broker": broker,
            "symbol": symbol,
            "timeframe": timeframe,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "mid_open": opens,
            "mid_high": highs,
            "mid_low": lows,
            "mid_close": closes,
            "bid_open": [value - 0.01 for value in opens],
            "bid_high": [value - 0.01 for value in highs],
            "bid_low": [value - 0.01 for value in lows],
            "bid_close": [value - 0.01 for value in closes],
            "ask_open": [value + 0.01 for value in opens],
            "ask_high": [value + 0.01 for value in highs],
            "ask_low": [value + 0.01 for value in lows],
            "ask_close": [value + 0.01 for value in closes],
            "spread_open_points": [2.0] * len(closes),
            "spread_close_points": [2.0] * len(closes),
            "spread_median_points": [2.0] * len(closes),
            "spread_p95_points": [3.0] * len(closes),
            "tick_count": [10] * len(closes),
            "volume_sum": [100] * len(closes),
        }
    )


def _widen_ohlc_ranges(frame: pd.DataFrame, padding: float) -> None:
    opens = pd.to_numeric(frame["open"], errors="coerce")
    closes = pd.to_numeric(frame["close"], errors="coerce")
    highs = pd.concat([opens, closes], axis=1).max(axis=1) + padding
    lows = pd.concat([opens, closes], axis=1).min(axis=1) - padding
    frame["high"] = highs
    frame["low"] = lows
    for prefix in ("mid", "bid", "ask"):
        high_col = f"{prefix}_high"
        low_col = f"{prefix}_low"
        if high_col in frame:
            frame[high_col] = highs
        if low_col in frame:
            frame[low_col] = lows


def _d1_inside_day_breakout_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=30, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [100.0] * 30,
            "atr14": [5.0] * 30,
        }
    )
    d1.loc[21, ["open", "high", "low", "close"]] = [100.0, 105.0, 95.0, 100.0]
    d1.loc[22, ["open", "high", "low", "close"]] = [100.0, 103.0, 97.0, 100.0]

    h4_times = pd.date_range("2024-01-17T12:00:00Z", periods=50, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
            "atr14": [2.0] * 50,
        }
    )
    h4.loc[34, ["open", "high", "low", "close"]] = [103.5, 106.0, 103.0, 105.5]

    m5 = _base_m5("2024-01-17T12:00:00Z", 240)
    return {"M5": m5, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}


def _d1_outside_day_followthrough_context() -> dict:
    d1_times = pd.date_range("2024-01-01T00:00:00Z", periods=30, freq="1D")
    d1 = pd.DataFrame(
        {
            "timestamp_utc": d1_times,
            "bar_start_utc": d1_times - pd.Timedelta(days=1),
            "open": [100.0] * 30,
            "high": [102.0] * 30,
            "low": [98.0] * 30,
            "close": [100.0] * 30,
            "atr14": [4.0] * 30,
        }
    )
    d1.loc[21, ["open", "high", "low", "close"]] = [100.0, 103.0, 97.0, 100.0]
    d1.loc[22, ["open", "high", "low", "close"]] = [99.0, 106.0, 96.0, 105.0]

    h4_times = pd.date_range("2024-01-17T12:00:00Z", periods=50, freq="4h")
    h4 = pd.DataFrame(
        {
            "timestamp_utc": h4_times,
            "bar_start_utc": h4_times - pd.Timedelta(hours=4),
            "open": [100.0] * 50,
            "high": [101.0] * 50,
            "low": [99.0] * 50,
            "close": [100.0] * 50,
            "atr14": [2.0] * 50,
        }
    )
    h4.loc[34, ["open", "high", "low", "close"]] = [105.0, 107.0, 104.7, 106.2]

    m5 = _base_m5("2024-01-17T12:00:00Z", 240)
    return {"M5": m5, "H4": h4, "D1": d1, "symbol": "XAUUSD", "point_size": 0.01}

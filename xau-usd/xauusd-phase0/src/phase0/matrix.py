from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from phase0.audjpy_usdjpy_fx_carry_rotation_data import (
    AUDJPY_USDJPY_FX_CARRY_ROTATION_FRAME_KEY,
)
from phase0.audjpy_usdjpy_fx_carry_rotation_data import (
    EXPERT_NAMES as AUDJPY_USDJPY_FX_CARRY_ROTATION_EXPERT_NAMES,
)
from phase0.audjpy_usdjpy_fx_carry_rotation_data import (
    load_audjpy_usdjpy_fx_carry_rotation_context,
)
from phase0.backtester import matrix_output_stem, run_backtest, write_backtest_outputs
from phase0.btc_risk_pressure_data import BTC_RISK_PRESSURE_FRAME_KEY
from phase0.btc_risk_pressure_data import EXPERT_NAMES as BTC_RISK_PRESSURE_EXPERT_NAMES
from phase0.btc_risk_pressure_data import load_btc_risk_pressure_context
from phase0.config import ConfigError, ProjectConfig, build_cell_configs, resolve_symbol
from phase0.cot_gold_data import COT_FRAME_KEY
from phase0.cot_gold_data import EXPERT_NAMES as COT_GOLD_EXPERT_NAMES
from phase0.cot_gold_data import load_cot_gold_context
from phase0.credit_spread_data import CREDIT_SPREAD_FRAME_KEY
from phase0.credit_spread_data import EXPERT_NAME as CREDIT_SPREAD_EXPERT_NAME
from phase0.credit_spread_data import load_credit_spread_context
from phase0.dbc_uup_commodity_dollar_data import EXPERT_NAMES as DBC_UUP_COMMODITY_DOLLAR_EXPERT_NAMES
from phase0.dbc_uup_commodity_dollar_data import DBC_UUP_COMMODITY_DOLLAR_FRAME_KEY
from phase0.dbc_uup_commodity_dollar_data import load_dbc_uup_commodity_dollar_context
from phase0.dbb_uup_industrial_metals_data import EXPERT_NAMES as DBB_UUP_INDUSTRIAL_METALS_EXPERT_NAMES
from phase0.dbb_uup_industrial_metals_data import DBB_UUP_INDUSTRIAL_METALS_FRAME_KEY
from phase0.dbb_uup_industrial_metals_data import load_dbb_uup_industrial_metals_context
from phase0.data_loader import processed_bars_dir
from phase0.eurjpy_usdjpy_fx_risk_rotation_data import EURJPY_USDJPY_FX_RISK_ROTATION_FRAME_KEY
from phase0.eurjpy_usdjpy_fx_risk_rotation_data import (
    EXPERT_NAMES as EURJPY_USDJPY_FX_RISK_ROTATION_EXPERT_NAMES,
)
from phase0.eurjpy_usdjpy_fx_risk_rotation_data import load_eurjpy_usdjpy_fx_risk_rotation_context
from phase0.eem_spy_em_risk_rotation_data import EEM_SPY_EM_RISK_ROTATION_FRAME_KEY
from phase0.eem_spy_em_risk_rotation_data import EXPERT_NAMES as EEM_SPY_EM_RISK_ROTATION_EXPERT_NAMES
from phase0.eem_spy_em_risk_rotation_data import load_eem_spy_em_risk_rotation_context
from phase0.acwx_spy_global_ex_us_rotation_data import ACWX_SPY_GLOBAL_EX_US_ROTATION_FRAME_KEY
from phase0.acwx_spy_global_ex_us_rotation_data import (
    EXPERT_NAMES as ACWX_SPY_GLOBAL_EX_US_ROTATION_EXPERT_NAMES,
)
from phase0.acwx_spy_global_ex_us_rotation_data import load_acwx_spy_global_ex_us_rotation_context
from phase0.xme_spy_metals_mining_rotation_data import XME_SPY_METALS_MINING_ROTATION_FRAME_KEY
from phase0.xme_spy_metals_mining_rotation_data import (
    EXPERT_NAMES as XME_SPY_METALS_MINING_ROTATION_EXPERT_NAMES,
)
from phase0.xme_spy_metals_mining_rotation_data import load_xme_spy_metals_mining_rotation_context
from phase0.fxy_uup_safe_haven_fx_rotation_data import FXY_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY
from phase0.fxy_uup_safe_haven_fx_rotation_data import (
    EXPERT_NAMES as FXY_UUP_SAFE_HAVEN_FX_ROTATION_EXPERT_NAMES,
)
from phase0.fxy_uup_safe_haven_fx_rotation_data import load_fxy_uup_safe_haven_fx_rotation_context
from phase0.fxf_uup_safe_haven_fx_rotation_data import FXF_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY
from phase0.fxf_uup_safe_haven_fx_rotation_data import (
    EXPERT_NAMES as FXF_UUP_SAFE_HAVEN_FX_ROTATION_EXPERT_NAMES,
)
from phase0.fxf_uup_safe_haven_fx_rotation_data import load_fxf_uup_safe_haven_fx_rotation_context
from phase0.fxe_uup_euro_dollar_fx_rotation_data import FXE_UUP_EURO_DOLLAR_FX_ROTATION_FRAME_KEY
from phase0.fxe_uup_euro_dollar_fx_rotation_data import (
    EXPERT_NAMES as FXE_UUP_EURO_DOLLAR_FX_ROTATION_EXPERT_NAMES,
)
from phase0.fxe_uup_euro_dollar_fx_rotation_data import load_fxe_uup_euro_dollar_fx_rotation_context
from phase0.cyb_uup_yuan_dollar_fx_rotation_data import CYB_UUP_YUAN_DOLLAR_FX_ROTATION_FRAME_KEY
from phase0.cyb_uup_yuan_dollar_fx_rotation_data import (
    EXPERT_NAMES as CYB_UUP_YUAN_DOLLAR_FX_ROTATION_EXPERT_NAMES,
)
from phase0.cyb_uup_yuan_dollar_fx_rotation_data import load_cyb_uup_yuan_dollar_fx_rotation_context
from phase0.fxa_uup_aussie_dollar_fx_rotation_data import FXA_UUP_AUSSIE_DOLLAR_FX_ROTATION_FRAME_KEY
from phase0.fxa_uup_aussie_dollar_fx_rotation_data import (
    EXPERT_NAMES as FXA_UUP_AUSSIE_DOLLAR_FX_ROTATION_EXPERT_NAMES,
)
from phase0.fxa_uup_aussie_dollar_fx_rotation_data import load_fxa_uup_aussie_dollar_fx_rotation_context
from phase0.data_validator import (
    MAX_ALLOWED_BAR_GAPS,
    bar_identity_issues,
    largest_bar_gap_issue,
    validate_bars,
)
from phase0.gold_fx_proxy_data import EXPERT_NAME as GOLD_FX_PROXY_EXPERT_NAME
from phase0.gold_fx_proxy_data import check_gold_fx_proxy_data
from phase0.gold_fx_proxy_data import load_gold_fx_proxy_h1_context
from phase0.financial_conditions_data import (
    EXPERT_NAME as FINANCIAL_CONDITIONS_EXPERT_NAME,
)
from phase0.financial_conditions_data import FINANCIAL_CONDITIONS_FRAME_KEY
from phase0.financial_conditions_data import load_financial_conditions_context
from phase0.gdx_gld_relative_data import EXPERT_NAMES as GDX_GLD_RELATIVE_EXPERT_NAMES
from phase0.gdx_gld_relative_data import GDX_GLD_RELATIVE_FRAME_KEY
from phase0.gdx_gld_relative_data import load_gdx_gld_relative_context
from phase0.gld_etf_flow_data import EXPERT_NAMES as GLD_ETF_FLOW_EXPERT_NAMES
from phase0.gld_etf_flow_data import GLD_ETF_FLOW_FRAME_KEY
from phase0.gld_etf_flow_data import load_gld_etf_flow_context
from phase0.gc_futures_volume_data import EXPERT_NAMES as GC_FUTURES_VOLUME_EXPERT_NAMES
from phase0.gc_futures_volume_data import GC_FUTURES_VOLUME_FRAME_KEY
from phase0.gc_futures_volume_data import load_gc_futures_volume_context
from phase0.gvz_volatility_data import EXPERT_NAME as GVZ_VOLATILITY_EXPERT_NAME
from phase0.gvz_volatility_data import GVZ_FRAME_KEY
from phase0.gvz_volatility_data import load_gvz_volatility_context
from phase0.move_bond_vol_data import MOVE_BOND_VOL_FRAME_KEY
from phase0.move_bond_vol_data import EXPERT_NAME as MOVE_BOND_VOL_EXPERT_NAME
from phase0.move_bond_vol_data import load_move_bond_vol_context
from phase0.hyg_ief_credit_risk_rotation_data import EXPERT_NAMES as HYG_IEF_CREDIT_RISK_ROTATION_EXPERT_NAMES
from phase0.hyg_ief_credit_risk_rotation_data import HYG_IEF_CREDIT_RISK_ROTATION_FRAME_KEY
from phase0.hyg_ief_credit_risk_rotation_data import load_hyg_ief_credit_risk_rotation_context
from phase0.iwm_spy_size_rotation_data import IWM_SPY_SIZE_ROTATION_FRAME_KEY
from phase0.iwm_spy_size_rotation_data import EXPERT_NAMES as IWM_SPY_SIZE_ROTATION_EXPERT_NAMES
from phase0.iwm_spy_size_rotation_data import load_iwm_spy_size_rotation_context
from phase0.slv_gld_precious_rotation_data import EXPERT_NAMES as SLV_GLD_PRECIOUS_ROTATION_EXPERT_NAMES
from phase0.slv_gld_precious_rotation_data import SLV_GLD_PRECIOUS_ROTATION_FRAME_KEY
from phase0.slv_gld_precious_rotation_data import load_slv_gld_precious_rotation_context
from phase0.xle_xlu_energy_defensive_rotation_data import (
    EXPERT_NAMES as XLE_XLU_ENERGY_DEFENSIVE_ROTATION_EXPERT_NAMES,
)
from phase0.xle_xlu_energy_defensive_rotation_data import XLE_XLU_ENERGY_DEFENSIVE_ROTATION_FRAME_KEY
from phase0.xle_xlu_energy_defensive_rotation_data import load_xle_xlu_energy_defensive_rotation_context
from phase0.xlf_xlu_financials_defensive_rotation_data import (
    EXPERT_NAMES as XLF_XLU_FINANCIALS_DEFENSIVE_ROTATION_EXPERT_NAMES,
)
from phase0.xlf_xlu_financials_defensive_rotation_data import (
    XLF_XLU_FINANCIALS_DEFENSIVE_ROTATION_FRAME_KEY,
)
from phase0.xlf_xlu_financials_defensive_rotation_data import (
    load_xlf_xlu_financials_defensive_rotation_context,
)
from phase0.xli_xlu_cyclical_defensive_rotation_data import (
    EXPERT_NAMES as XLI_XLU_CYCLICAL_DEFENSIVE_ROTATION_EXPERT_NAMES,
)
from phase0.xli_xlu_cyclical_defensive_rotation_data import (
    XLI_XLU_CYCLICAL_DEFENSIVE_ROTATION_FRAME_KEY,
)
from phase0.xli_xlu_cyclical_defensive_rotation_data import (
    load_xli_xlu_cyclical_defensive_rotation_context,
)
from phase0.xlp_xly_consumer_rotation_data import EXPERT_NAMES as XLP_XLY_CONSUMER_ROTATION_EXPERT_NAMES
from phase0.xlp_xly_consumer_rotation_data import XLP_XLY_CONSUMER_ROTATION_FRAME_KEY
from phase0.xlp_xly_consumer_rotation_data import load_xlp_xly_consumer_rotation_context
from phase0.inflation_expectations_data import (
    EXPERT_NAME as INFLATION_EXPECTATIONS_EXPERT_NAME,
)
from phase0.inflation_expectations_data import INFLATION_EXPECTATIONS_FRAME_KEY
from phase0.inflation_expectations_data import load_inflation_expectations_context
from phase0.macro_event_calendar import EXPERT_NAME as MACRO_EVENT_EXPERT_NAME
from phase0.macro_event_calendar import MACRO_EVENT_FRAME_KEY
from phase0.macro_event_calendar import load_macro_event_calendar_context
from phase0.macro_real_yield_data import EXPERT_NAMES as MACRO_REAL_YIELD_EXPERT_NAMES
from phase0.macro_real_yield_data import MACRO_FRAME_KEY
from phase0.macro_real_yield_data import load_macro_real_yield_context
from phase0.policy_uncertainty_data import EXPERT_NAME as POLICY_UNCERTAINTY_EXPERT_NAME
from phase0.policy_uncertainty_data import POLICY_UNCERTAINTY_FRAME_KEY
from phase0.policy_uncertainty_data import load_policy_uncertainty_context
from phase0.qqq_spy_growth_rotation_data import QQQ_SPY_GROWTH_ROTATION_FRAME_KEY
from phase0.qqq_spy_growth_rotation_data import (
    EXPERT_NAMES as QQQ_SPY_GROWTH_ROTATION_EXPERT_NAMES,
)
from phase0.qqq_spy_growth_rotation_data import load_qqq_spy_growth_rotation_context
from phase0.run_context import context_with_symbol_metadata
from phase0.spy_tlt_risk_rotation_data import EXPERT_NAMES as SPY_TLT_RISK_ROTATION_EXPERT_NAMES
from phase0.spy_tlt_risk_rotation_data import SPY_TLT_RISK_ROTATION_FRAME_KEY
from phase0.spy_tlt_risk_rotation_data import load_spy_tlt_risk_rotation_context
from phase0.tip_ief_real_yield_rotation_data import EXPERT_NAMES as TIP_IEF_REAL_YIELD_ROTATION_EXPERT_NAMES
from phase0.tip_ief_real_yield_rotation_data import TIP_IEF_REAL_YIELD_ROTATION_FRAME_KEY
from phase0.tip_ief_real_yield_rotation_data import load_tip_ief_real_yield_rotation_context
from phase0.strategies.registry import enabled_strategy_names, get_strategy
from phase0.synthetic import synthetic_context_for_expert
from phase0.treasury_curve_data import EXPERT_NAME as TREASURY_CURVE_EXPERT_NAME
from phase0.treasury_curve_data import TREASURY_CURVE_FRAME_KEY
from phase0.treasury_curve_data import load_treasury_curve_context
from phase0.tlt_uup_macro_pressure_data import EXPERT_NAMES as TLT_UUP_PRESSURE_EXPERT_NAMES
from phase0.tlt_uup_macro_pressure_data import TLT_UUP_PRESSURE_FRAME_KEY
from phase0.tlt_uup_macro_pressure_data import load_tlt_uup_macro_pressure_context
from phase0.tlt_shy_duration_rotation_data import EXPERT_NAMES as TLT_SHY_DURATION_ROTATION_EXPERT_NAMES
from phase0.tlt_shy_duration_rotation_data import TLT_SHY_DURATION_ROTATION_FRAME_KEY
from phase0.tlt_shy_duration_rotation_data import load_tlt_shy_duration_rotation_context
from phase0.uso_uup_oil_dollar_data import EXPERT_NAMES as USO_UUP_OIL_DOLLAR_EXPERT_NAMES
from phase0.uso_uup_oil_dollar_data import USO_UUP_OIL_DOLLAR_FRAME_KEY
from phase0.uso_uup_oil_dollar_data import load_uso_uup_oil_dollar_context
from phase0.vix_risk_data import EXPERT_NAME as VIX_RISK_EXPERT_NAME
from phase0.vix_risk_data import VIX_FRAME_KEY
from phase0.vix_risk_data import load_vix_risk_context
from phase0.xlu_xlk_defensive_rotation_data import EXPERT_NAMES as XLU_XLK_DEFENSIVE_ROTATION_EXPERT_NAMES
from phase0.xlu_xlk_defensive_rotation_data import XLU_XLK_DEFENSIVE_ROTATION_FRAME_KEY
from phase0.xlu_xlk_defensive_rotation_data import load_xlu_xlk_defensive_rotation_context
from phase0.xau_xag_relative_data import EXPERT_NAME as XAU_XAG_RELATIVE_EXPERT_NAME
from phase0.xau_xag_relative_data import check_xau_xag_relative_data
from phase0.xau_xag_relative_data import load_xau_xag_relative_h1_context

XAG_LEAD_XAU_FOLLOWTHROUGH_EXPERT_NAME = "xag_lead_xau_followthrough_v0"
XAU_XAG_FX_COMPOSITE_EXPERT_NAME = "xau_xag_fx_composite_reversion_v0"
BROKER_FX_USD_PRESSURE_EXPERT_NAME = "h1_broker_fx_usd_pressure_followthrough_v0"
BROKER_FX_USD_PRESSURE_CONFLICT_EXPERT_NAME = "h1_broker_fx_usd_pressure_conflict_reversion_v0"
BROKER_FX_PROXY_EXPERT_NAMES = (
    GOLD_FX_PROXY_EXPERT_NAME,
    BROKER_FX_USD_PRESSURE_EXPERT_NAME,
    BROKER_FX_USD_PRESSURE_CONFLICT_EXPERT_NAME,
)
MACRO_COMPOSITE_EXPERT_NAMES = (
    "h4_macro_composite_risk_state_v0",
    "h4_macro_composite_risk_state_v1",
    "h1_macro_composite_pullback_v0",
    "h1_macro_composite_trend_continuation_v0",
    "h1_macro_composite_state_reversion_v0",
)
GVZ_VIX_VOL_PREMIUM_EXPERT_NAME = "h1_gvz_vix_vol_premium_reversal_v0"


@dataclass(frozen=True)
class MatrixRunOutput:
    expert: str
    cell_id: int
    summary_path: Path
    trades_path: Path
    equity_path: Path


def run_phase0_matrix(
    config: ProjectConfig,
    expert: str,
    synthetic_sample: bool = False,
    allow_research_candidate: bool = False,
) -> list[MatrixRunOutput]:
    outputs: list[MatrixRunOutput] = []
    context_cache: dict[tuple[str, str, pd.Timestamp, pd.Timestamp], dict[str, Any]] = {}
    for expert_name in enabled_strategy_names(expert, allow_research_candidate=allow_research_candidate):
        strategy = get_strategy(expert_name, allow_research_candidate=allow_research_candidate)
        if expert_name in BROKER_FX_PROXY_EXPERT_NAMES and not synthetic_sample:
            _assert_gold_fx_proxy_data_ready(config)
        if expert_name == XAU_XAG_RELATIVE_EXPERT_NAME and not synthetic_sample:
            _assert_xau_xag_relative_data_ready(config)
        if expert_name == XAU_XAG_FX_COMPOSITE_EXPERT_NAME and not synthetic_sample:
            _assert_gold_fx_proxy_data_ready(config)
            _assert_xau_xag_relative_data_ready(config)
        if expert_name == XAG_LEAD_XAU_FOLLOWTHROUGH_EXPERT_NAME and not synthetic_sample:
            _assert_xau_xag_relative_data_ready(config)
        if expert_name in MACRO_REAL_YIELD_EXPERT_NAMES and not synthetic_sample:
            _assert_macro_real_yield_data_ready(config)
        if expert_name == MACRO_EVENT_EXPERT_NAME and not synthetic_sample:
            _assert_macro_event_calendar_ready(config)
        if expert_name == POLICY_UNCERTAINTY_EXPERT_NAME and not synthetic_sample:
            _assert_policy_uncertainty_data_ready(config)
        if expert_name in COT_GOLD_EXPERT_NAMES and not synthetic_sample:
            _assert_cot_gold_data_ready(config)
        if expert_name in DBC_UUP_COMMODITY_DOLLAR_EXPERT_NAMES and not synthetic_sample:
            _assert_dbc_uup_commodity_dollar_data_ready(config)
        if expert_name in DBB_UUP_INDUSTRIAL_METALS_EXPERT_NAMES and not synthetic_sample:
            _assert_dbb_uup_industrial_metals_data_ready(config)
        if expert_name == CREDIT_SPREAD_EXPERT_NAME and not synthetic_sample:
            _assert_credit_spread_data_ready(config)
        if expert_name in MACRO_COMPOSITE_EXPERT_NAMES and not synthetic_sample:
            _assert_macro_composite_data_ready(config)
        if expert_name == GVZ_VOLATILITY_EXPERT_NAME and not synthetic_sample:
            _assert_gvz_volatility_data_ready(config)
        if expert_name == VIX_RISK_EXPERT_NAME and not synthetic_sample:
            _assert_vix_risk_data_ready(config)
        if expert_name == GVZ_VIX_VOL_PREMIUM_EXPERT_NAME and not synthetic_sample:
            _assert_gvz_volatility_data_ready(config)
            _assert_vix_risk_data_ready(config)
        if expert_name == MOVE_BOND_VOL_EXPERT_NAME and not synthetic_sample:
            _assert_move_bond_vol_data_ready(config)
            _assert_vix_risk_data_ready(config)
        if expert_name == FINANCIAL_CONDITIONS_EXPERT_NAME and not synthetic_sample:
            _assert_financial_conditions_data_ready(config)
        if expert_name in GDX_GLD_RELATIVE_EXPERT_NAMES and not synthetic_sample:
            _assert_gdx_gld_relative_data_ready(config)
        if expert_name in GLD_ETF_FLOW_EXPERT_NAMES and not synthetic_sample:
            _assert_gld_etf_flow_data_ready(config)
        if expert_name in GC_FUTURES_VOLUME_EXPERT_NAMES and not synthetic_sample:
            _assert_gc_futures_volume_data_ready(config)
        if expert_name in AUDJPY_USDJPY_FX_CARRY_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_audjpy_usdjpy_fx_carry_rotation_data_ready(config)
        if expert_name in EURJPY_USDJPY_FX_RISK_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_eurjpy_usdjpy_fx_risk_rotation_data_ready(config)
        if expert_name in BTC_RISK_PRESSURE_EXPERT_NAMES and not synthetic_sample:
            _assert_btc_risk_pressure_data_ready(config)
        if expert_name in QQQ_SPY_GROWTH_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_qqq_spy_growth_rotation_data_ready(config)
        if expert_name in IWM_SPY_SIZE_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_iwm_spy_size_rotation_data_ready(config)
        if expert_name in SLV_GLD_PRECIOUS_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_slv_gld_precious_rotation_data_ready(config)
        if expert_name in EEM_SPY_EM_RISK_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_eem_spy_em_risk_rotation_data_ready(config)
        if expert_name in ACWX_SPY_GLOBAL_EX_US_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_acwx_spy_global_ex_us_rotation_data_ready(config)
        if expert_name in XME_SPY_METALS_MINING_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_xme_spy_metals_mining_rotation_data_ready(config)
        if expert_name in FXY_UUP_SAFE_HAVEN_FX_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_fxy_uup_safe_haven_fx_rotation_data_ready(config)
        if expert_name in FXF_UUP_SAFE_HAVEN_FX_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_fxf_uup_safe_haven_fx_rotation_data_ready(config)
        if expert_name in FXE_UUP_EURO_DOLLAR_FX_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_fxe_uup_euro_dollar_fx_rotation_data_ready(config)
        if expert_name in CYB_UUP_YUAN_DOLLAR_FX_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_cyb_uup_yuan_dollar_fx_rotation_data_ready(config)
        if expert_name in FXA_UUP_AUSSIE_DOLLAR_FX_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_fxa_uup_aussie_dollar_fx_rotation_data_ready(config)
        if expert_name == INFLATION_EXPECTATIONS_EXPERT_NAME and not synthetic_sample:
            _assert_inflation_expectations_data_ready(config)
        if expert_name == TREASURY_CURVE_EXPERT_NAME and not synthetic_sample:
            _assert_treasury_curve_data_ready(config)
        if expert_name in TLT_UUP_PRESSURE_EXPERT_NAMES and not synthetic_sample:
            _assert_tlt_uup_macro_pressure_data_ready(config)
        if expert_name in TLT_SHY_DURATION_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_tlt_shy_duration_rotation_data_ready(config)
        if expert_name in USO_UUP_OIL_DOLLAR_EXPERT_NAMES and not synthetic_sample:
            _assert_uso_uup_oil_dollar_data_ready(config)
        if expert_name in SPY_TLT_RISK_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_spy_tlt_risk_rotation_data_ready(config)
        if expert_name in TIP_IEF_REAL_YIELD_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_tip_ief_real_yield_rotation_data_ready(config)
        if expert_name in HYG_IEF_CREDIT_RISK_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_hyg_ief_credit_risk_rotation_data_ready(config)
        if expert_name in XLF_XLU_FINANCIALS_DEFENSIVE_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_xlf_xlu_financials_defensive_rotation_data_ready(config)
        if expert_name in XLI_XLU_CYCLICAL_DEFENSIVE_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_xli_xlu_cyclical_defensive_rotation_data_ready(config)
        if expert_name in XLP_XLY_CONSUMER_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_xlp_xly_consumer_rotation_data_ready(config)
        if expert_name in XLU_XLK_DEFENSIVE_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_xlu_xlk_defensive_rotation_data_ready(config)
        if expert_name in XLE_XLU_ENERGY_DEFENSIVE_ROTATION_EXPERT_NAMES and not synthetic_sample:
            _assert_xle_xlu_energy_defensive_rotation_data_ready(config)
        cells = build_cell_configs(config, symbol="XAUUSD")
        for cell in cells:
            if synthetic_sample:
                data_context = synthetic_context_for_expert(expert_name)
            else:
                cache_key = (cell.broker, cell.symbol, cell.start_utc, cell.end_utc)
                if cache_key not in context_cache:
                    context_cache[cache_key] = context_with_symbol_metadata(
                        config,
                        load_cell_data_context(
                            config,
                            cell.broker,
                            cell.symbol,
                            required_start=cell.start_utc,
                            required_end=cell.end_utc,
                        ),
                        cell.symbol,
                    )
                data_context = context_cache[cache_key]
                if expert_name in BROKER_FX_PROXY_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        "intermarket_proxy": load_gold_fx_proxy_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == XAU_XAG_RELATIVE_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        "relative_value": load_xau_xag_relative_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == XAG_LEAD_XAU_FOLLOWTHROUGH_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        "relative_value": load_xau_xag_relative_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == XAU_XAG_FX_COMPOSITE_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        "intermarket_proxy": load_gold_fx_proxy_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        "relative_value": load_xau_xag_relative_h1_context(
                            config,
                            cell.broker,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in MACRO_REAL_YIELD_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        MACRO_FRAME_KEY: load_macro_real_yield_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == MACRO_EVENT_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        MACRO_EVENT_FRAME_KEY: load_macro_event_calendar_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == POLICY_UNCERTAINTY_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        POLICY_UNCERTAINTY_FRAME_KEY: load_policy_uncertainty_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in COT_GOLD_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        COT_FRAME_KEY: load_cot_gold_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == CREDIT_SPREAD_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        CREDIT_SPREAD_FRAME_KEY: load_credit_spread_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in MACRO_COMPOSITE_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        MACRO_FRAME_KEY: load_macro_real_yield_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        INFLATION_EXPECTATIONS_FRAME_KEY: load_inflation_expectations_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        TREASURY_CURVE_FRAME_KEY: load_treasury_curve_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        CREDIT_SPREAD_FRAME_KEY: load_credit_spread_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        VIX_FRAME_KEY: load_vix_risk_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        GVZ_FRAME_KEY: load_gvz_volatility_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        FINANCIAL_CONDITIONS_FRAME_KEY: load_financial_conditions_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == GVZ_VOLATILITY_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        GVZ_FRAME_KEY: load_gvz_volatility_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == VIX_RISK_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        VIX_FRAME_KEY: load_vix_risk_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == GVZ_VIX_VOL_PREMIUM_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        GVZ_FRAME_KEY: load_gvz_volatility_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        VIX_FRAME_KEY: load_vix_risk_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == MOVE_BOND_VOL_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        MOVE_BOND_VOL_FRAME_KEY: load_move_bond_vol_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                        VIX_FRAME_KEY: load_vix_risk_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == FINANCIAL_CONDITIONS_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        FINANCIAL_CONDITIONS_FRAME_KEY: load_financial_conditions_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in GDX_GLD_RELATIVE_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        GDX_GLD_RELATIVE_FRAME_KEY: load_gdx_gld_relative_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in GLD_ETF_FLOW_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        GLD_ETF_FLOW_FRAME_KEY: load_gld_etf_flow_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in GC_FUTURES_VOLUME_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        GC_FUTURES_VOLUME_FRAME_KEY: load_gc_futures_volume_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in AUDJPY_USDJPY_FX_CARRY_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        AUDJPY_USDJPY_FX_CARRY_ROTATION_FRAME_KEY: load_audjpy_usdjpy_fx_carry_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in EURJPY_USDJPY_FX_RISK_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        EURJPY_USDJPY_FX_RISK_ROTATION_FRAME_KEY: load_eurjpy_usdjpy_fx_risk_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in BTC_RISK_PRESSURE_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        BTC_RISK_PRESSURE_FRAME_KEY: load_btc_risk_pressure_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in QQQ_SPY_GROWTH_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        QQQ_SPY_GROWTH_ROTATION_FRAME_KEY: load_qqq_spy_growth_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in IWM_SPY_SIZE_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        IWM_SPY_SIZE_ROTATION_FRAME_KEY: load_iwm_spy_size_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in SLV_GLD_PRECIOUS_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        SLV_GLD_PRECIOUS_ROTATION_FRAME_KEY: load_slv_gld_precious_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in EEM_SPY_EM_RISK_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        EEM_SPY_EM_RISK_ROTATION_FRAME_KEY: load_eem_spy_em_risk_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in ACWX_SPY_GLOBAL_EX_US_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        ACWX_SPY_GLOBAL_EX_US_ROTATION_FRAME_KEY: load_acwx_spy_global_ex_us_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in XME_SPY_METALS_MINING_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        XME_SPY_METALS_MINING_ROTATION_FRAME_KEY: load_xme_spy_metals_mining_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in FXY_UUP_SAFE_HAVEN_FX_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        FXY_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY: load_fxy_uup_safe_haven_fx_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in FXF_UUP_SAFE_HAVEN_FX_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        FXF_UUP_SAFE_HAVEN_FX_ROTATION_FRAME_KEY: load_fxf_uup_safe_haven_fx_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in FXE_UUP_EURO_DOLLAR_FX_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        FXE_UUP_EURO_DOLLAR_FX_ROTATION_FRAME_KEY: load_fxe_uup_euro_dollar_fx_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in CYB_UUP_YUAN_DOLLAR_FX_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        CYB_UUP_YUAN_DOLLAR_FX_ROTATION_FRAME_KEY: load_cyb_uup_yuan_dollar_fx_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in FXA_UUP_AUSSIE_DOLLAR_FX_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        FXA_UUP_AUSSIE_DOLLAR_FX_ROTATION_FRAME_KEY: load_fxa_uup_aussie_dollar_fx_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in TLT_UUP_PRESSURE_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        TLT_UUP_PRESSURE_FRAME_KEY: load_tlt_uup_macro_pressure_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in DBC_UUP_COMMODITY_DOLLAR_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        DBC_UUP_COMMODITY_DOLLAR_FRAME_KEY: load_dbc_uup_commodity_dollar_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in DBB_UUP_INDUSTRIAL_METALS_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        DBB_UUP_INDUSTRIAL_METALS_FRAME_KEY: load_dbb_uup_industrial_metals_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in USO_UUP_OIL_DOLLAR_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        USO_UUP_OIL_DOLLAR_FRAME_KEY: load_uso_uup_oil_dollar_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in TLT_SHY_DURATION_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        TLT_SHY_DURATION_ROTATION_FRAME_KEY: load_tlt_shy_duration_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in SPY_TLT_RISK_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        SPY_TLT_RISK_ROTATION_FRAME_KEY: load_spy_tlt_risk_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in TIP_IEF_REAL_YIELD_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        TIP_IEF_REAL_YIELD_ROTATION_FRAME_KEY: load_tip_ief_real_yield_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in HYG_IEF_CREDIT_RISK_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        HYG_IEF_CREDIT_RISK_ROTATION_FRAME_KEY: load_hyg_ief_credit_risk_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in XLF_XLU_FINANCIALS_DEFENSIVE_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        XLF_XLU_FINANCIALS_DEFENSIVE_ROTATION_FRAME_KEY: load_xlf_xlu_financials_defensive_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in XLI_XLU_CYCLICAL_DEFENSIVE_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        XLI_XLU_CYCLICAL_DEFENSIVE_ROTATION_FRAME_KEY: load_xli_xlu_cyclical_defensive_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in XLP_XLY_CONSUMER_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        XLP_XLY_CONSUMER_ROTATION_FRAME_KEY: load_xlp_xly_consumer_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in XLU_XLK_DEFENSIVE_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        XLU_XLK_DEFENSIVE_ROTATION_FRAME_KEY: load_xlu_xlk_defensive_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name in XLE_XLU_ENERGY_DEFENSIVE_ROTATION_EXPERT_NAMES:
                    data_context = {
                        **data_context,
                        XLE_XLU_ENERGY_DEFENSIVE_ROTATION_FRAME_KEY: load_xle_xlu_energy_defensive_rotation_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == INFLATION_EXPECTATIONS_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        INFLATION_EXPECTATIONS_FRAME_KEY: load_inflation_expectations_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }
                if expert_name == TREASURY_CURVE_EXPERT_NAME:
                    data_context = {
                        **data_context,
                        TREASURY_CURVE_FRAME_KEY: load_treasury_curve_context(
                            config,
                            cell.start_utc,
                            cell.end_utc,
                        ),
                    }

            result = run_backtest(
                config=config,
                strategy=strategy,
                data_context=data_context,
                broker=cell.broker,
                cost_model=cell.cost_model,
                starting_equity=config.phase0["project"]["starting_equity_usd"],
                risk_per_trade_pct=config.phase0["project"]["phase0_risk_per_trade_pct"],
                period_start=cell.start_utc,
                period_end=cell.end_utc,
            )
            result.metrics.update(
                {
                    "cell_id": cell.cell_id,
                    "time_window": f"{cell.start_utc.isoformat()} to {cell.end_utc.isoformat()}",
                    "tick_source": cell.broker,
                    "time_window_start": cell.start_utc.isoformat(),
                    "time_window_end": cell.end_utc.isoformat(),
                }
            )
            output_dir = config.root / "outputs" / "matrix_results" / expert_name
            stem = matrix_output_stem(cell.cell_id, expert_name, cell.broker, cell.cost_model)
            summary_path, trades_path, equity_path = write_backtest_outputs(result, output_dir, stem)
            outputs.append(
                MatrixRunOutput(
                    expert=expert_name,
                    cell_id=cell.cell_id,
                    summary_path=summary_path,
                    trades_path=trades_path,
                    equity_path=equity_path,
                )
            )
    return outputs


def _assert_gold_fx_proxy_data_ready(config: ProjectConfig) -> None:
    missing = [check for check in check_gold_fx_proxy_data(config) if not check.available]
    if not missing:
        return
    lines = [
        f"- broker={check.broker}, symbol={check.symbol}, timeframe={check.timeframe}, "
        f"dir={check.directory}, first_issue={check.issues[0] if check.issues else 'no candidate CSV files'}"
        for check in missing
    ]
    raise ConfigError(
        f"{GOLD_FX_PROXY_EXPERT_NAME} research matrix is blocked by missing proxy data:\n"
        + "\n".join(lines)
        + "\nRun generate-gold-fx-proxy-data-readiness for the exact acquisition checklist."
    )


def _assert_xau_xag_relative_data_ready(config: ProjectConfig) -> None:
    missing = [check for check in check_xau_xag_relative_data(config) if not check.available]
    if not missing:
        return
    lines = [
        f"- broker={check.broker}, symbol={check.symbol}, timeframe={check.timeframe}, "
        f"dir={check.directory}, first_issue={check.issues[0] if check.issues else 'no candidate CSV files'}"
        for check in missing
    ]
    raise ConfigError(
        f"{XAU_XAG_RELATIVE_EXPERT_NAME} research matrix is blocked by missing XAGUSD data:\n"
        + "\n".join(lines)
        + "\nRun generate-xau-xag-relative-data-readiness for the exact acquisition checklist."
    )


def _assert_macro_real_yield_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_macro_real_yield_context(config, start, end)


def _assert_macro_event_calendar_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_macro_event_calendar_context(config, start, end)


def _assert_policy_uncertainty_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_policy_uncertainty_context(config, start, end)


def _assert_cot_gold_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_cot_gold_context(config, start, end)


def _assert_credit_spread_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_credit_spread_context(config, start, end)


def _assert_macro_composite_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_macro_real_yield_context(config, start, end)
    load_inflation_expectations_context(config, start, end)
    load_treasury_curve_context(config, start, end)
    load_credit_spread_context(config, start, end)
    load_vix_risk_context(config, start, end)
    load_gvz_volatility_context(config, start, end)
    load_financial_conditions_context(config, start, end)


def _assert_gvz_volatility_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_gvz_volatility_context(config, start, end)


def _assert_vix_risk_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_vix_risk_context(config, start, end)


def _assert_move_bond_vol_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_move_bond_vol_context(config, start, end)


def _assert_financial_conditions_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_financial_conditions_context(config, start, end)


def _assert_gdx_gld_relative_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_gdx_gld_relative_context(config, start, end)


def _assert_gc_futures_volume_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_gc_futures_volume_context(config, start, end)


def _assert_audjpy_usdjpy_fx_carry_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_audjpy_usdjpy_fx_carry_rotation_context(config, start, end)


def _assert_eurjpy_usdjpy_fx_risk_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_eurjpy_usdjpy_fx_risk_rotation_context(config, start, end)


def _assert_btc_risk_pressure_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_btc_risk_pressure_context(config, start, end)


def _assert_qqq_spy_growth_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_qqq_spy_growth_rotation_context(config, start, end)


def _assert_iwm_spy_size_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_iwm_spy_size_rotation_context(config, start, end)


def _assert_slv_gld_precious_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_slv_gld_precious_rotation_context(config, start, end)


def _assert_eem_spy_em_risk_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_eem_spy_em_risk_rotation_context(config, start, end)


def _assert_acwx_spy_global_ex_us_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_acwx_spy_global_ex_us_rotation_context(config, start, end)


def _assert_xme_spy_metals_mining_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_xme_spy_metals_mining_rotation_context(config, start, end)


def _assert_fxy_uup_safe_haven_fx_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_fxy_uup_safe_haven_fx_rotation_context(config, start, end)


def _assert_fxf_uup_safe_haven_fx_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_fxf_uup_safe_haven_fx_rotation_context(config, start, end)


def _assert_fxe_uup_euro_dollar_fx_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_fxe_uup_euro_dollar_fx_rotation_context(config, start, end)


def _assert_cyb_uup_yuan_dollar_fx_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_cyb_uup_yuan_dollar_fx_rotation_context(config, start, end)


def _assert_fxa_uup_aussie_dollar_fx_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_fxa_uup_aussie_dollar_fx_rotation_context(config, start, end)


def _assert_gld_etf_flow_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_gld_etf_flow_context(config, start, end)


def _assert_inflation_expectations_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_inflation_expectations_context(config, start, end)


def _assert_treasury_curve_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_treasury_curve_context(config, start, end)


def _assert_tlt_uup_macro_pressure_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_tlt_uup_macro_pressure_context(config, start, end)


def _assert_tlt_shy_duration_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_tlt_shy_duration_rotation_context(config, start, end)


def _assert_uso_uup_oil_dollar_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_uso_uup_oil_dollar_context(config, start, end)


def _assert_spy_tlt_risk_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_spy_tlt_risk_rotation_context(config, start, end)


def _assert_dbc_uup_commodity_dollar_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_dbc_uup_commodity_dollar_context(config, start, end)


def _assert_dbb_uup_industrial_metals_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_dbb_uup_industrial_metals_context(config, start, end)


def _assert_tip_ief_real_yield_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_tip_ief_real_yield_rotation_context(config, start, end)


def _assert_hyg_ief_credit_risk_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_hyg_ief_credit_risk_rotation_context(config, start, end)


def _assert_xlf_xlu_financials_defensive_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_xlf_xlu_financials_defensive_rotation_context(config, start, end)


def _assert_xli_xlu_cyclical_defensive_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_xli_xlu_cyclical_defensive_rotation_context(config, start, end)


def _assert_xlp_xly_consumer_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_xlp_xly_consumer_rotation_context(config, start, end)


def _assert_xlu_xlk_defensive_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_xlu_xlk_defensive_rotation_context(config, start, end)


def _assert_xle_xlu_energy_defensive_rotation_data_ready(config: ProjectConfig) -> None:
    start = min(pd.Timestamp(cell.start_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    end = max(pd.Timestamp(cell.end_utc) for cell in build_cell_configs(config, symbol="XAUUSD"))
    load_xle_xlu_energy_defensive_rotation_context(config, start, end)


def load_cell_data_context(
    config: ProjectConfig,
    broker: str,
    symbol: str,
    required_start: object | None = None,
    required_end: object | None = None,
) -> dict:
    canonical_symbol = resolve_symbol(config, symbol)
    bars_root = processed_bars_dir(config, broker, canonical_symbol)
    if not bars_root.exists():
        raise ConfigError(
            f"Processed bars not found at {bars_root}. "
            "Run import-required-bars for direct OHLC bar exports, or use --synthetic-sample for a smoke test."
        )

    context: dict[str, Any] = {"symbol": canonical_symbol}
    for timeframe in ("M5", "M15", "H1", "H4", "D1"):
        timeframe_dir = bars_root / timeframe
        files = sorted(timeframe_dir.glob("*.csv")) if timeframe_dir.exists() else []
        if not files:
            raise ConfigError(f"Missing processed {timeframe} bars in {timeframe_dir}.")
        frame = _load_processed_timeframe_bars(files, broker, canonical_symbol, timeframe)
        _assert_bar_coverage(frame, timeframe_dir, timeframe, required_start, required_end)
        context[timeframe] = frame
    return context


def _load_processed_timeframe_bars(
    files: list[Path],
    broker: str,
    symbol: str,
    timeframe: str,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for path in files:
        try:
            frames.append(pd.read_csv(path))
        except Exception as exc:
            raise ConfigError(
                f"Failed to read processed {timeframe} bars in {path}: {exc}"
            ) from exc

    combined = pd.concat(frames, ignore_index=True)
    if "timestamp_utc" in combined.columns:
        timestamps = pd.to_datetime(combined["timestamp_utc"], utc=True, errors="coerce")
        combined = (
            combined.assign(_phase0_sort_timestamp=timestamps)
            .sort_values("_phase0_sort_timestamp", na_position="last")
            .drop(columns="_phase0_sort_timestamp")
            .reset_index(drop=True)
        )

    report = validate_bars(combined, name=f"{timeframe} processed bars", fail_on_error=False)
    if report.error_count:
        first_issue = next(issue for issue in report.issues if issue.severity == "ERROR")
        raise ConfigError(
            f"Processed {timeframe} bars failed validation after combining {len(files)} file(s): "
            f"{first_issue.column} {first_issue.message}"
        )

    identity_issues = bar_identity_issues(combined, broker, symbol, timeframe)
    if identity_issues:
        raise ConfigError(
            f"Processed {timeframe} bars failed identity check after combining "
            f"{len(files)} file(s): {identity_issues[0]}."
        )

    gap_issue = largest_bar_gap_issue(combined["bar_end_utc"], timeframe)
    if gap_issue:
        raise ConfigError(
            f"Processed {timeframe} bars failed continuity check after combining "
            f"{len(files)} file(s): {gap_issue}."
        )
    return combined


def _assert_bar_coverage(
    frame: pd.DataFrame,
    source: Path,
    timeframe: str,
    required_start: object | None,
    required_end: object | None,
) -> None:
    if required_start is None or required_end is None:
        return
    missing = [column for column in ("bar_start_utc", "bar_end_utc") if column not in frame.columns]
    if missing:
        raise ConfigError(
            f"Processed {timeframe} bars in {source} missing coverage column(s): "
            f"{', '.join(missing)}."
        )

    starts = pd.to_datetime(frame["bar_start_utc"], utc=True, errors="coerce").dropna()
    ends = pd.to_datetime(frame["bar_end_utc"], utc=True, errors="coerce").dropna()
    if starts.empty or ends.empty:
        raise ConfigError(
            f"Processed {timeframe} bars in {source} have no valid coverage timestamps."
        )

    coverage_start = pd.Timestamp(starts.min())
    coverage_end = pd.Timestamp(ends.max())
    needed_start = _utc_timestamp(required_start)
    needed_end = _utc_timestamp(required_end)
    allowed_boundary_gap = MAX_ALLOWED_BAR_GAPS[timeframe]
    starts_too_late = (
        coverage_start > needed_start and coverage_start - needed_start > allowed_boundary_gap
    )
    ends_too_early = coverage_end < needed_end and needed_end - coverage_end > allowed_boundary_gap
    if starts_too_late or ends_too_early:
        raise ConfigError(
            f"Processed {timeframe} bars in {source} cover "
            f"{coverage_start.isoformat()} to {coverage_end.isoformat()}, "
            f"but required {needed_start.isoformat()} to {needed_end.isoformat()}. "
            "Run import-required-bars for direct OHLC bar exports, or regenerate processed bars."
        )


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")

# Next Independent Research Lane

Last updated: 2026-05-30

Overall status: NO_INDEPENDENT_APPROVAL_AFTER_126_RESULT_PRODUCING_CANDIDATES

This document defines what can still be done while Phase 1 soak, code-freeze, and measured-cost clocks mature. It does not approve any new EA and it does not reopen rejected candidates.

## Current Finding

The current approved/provisional set is still one correlated edge family:

```text
level-and-pullback / breakout-retest
```

The project has already tested 126 result-producing candidates plus one data-blocked CYB/UUP lane, including non-level, H4/D1/W1, intermarket, macro-regime, macro-shock, BTC crypto risk pressure, QQQ/SPY growth-risk rotation, IWM/SPY size-risk breadth rotation, SLV/GLD precious-beta rotation, XLE/XLU energy-defensive rotation, EEM/SPY emerging-market risk rotation, ACWX/SPY global ex-US rotation, XME/SPY metals-mining rotation, FXY/UUP, FXF/UUP, FXE/UUP, CYB/UUP, and FXA/UUP FX rotation, broker-consistent FX dollar pressure, FX-cross carry/risk rotation, volatility-regime, event-regime, calendar-flow, session impulse-reversion, Friday position-squaring, AI-style fixed-state concepts, official CFTC gold COT positioning, a non-authoritative GC continuous futures daily-volume proxy, public GLD ETF daily-flow proxies, public GDX/GLD miner-relative proxies, TLT/UUP traded ETF rates-dollar pressure, TLT/SHY traded ETF duration rotation, SPY/TLT traded ETF equity-vs-Treasury risk rotation, TIP/IEF traded ETF real-yield rotation, DBC/UUP broad-commodity versus dollar pressure, DBB/UUP industrial-metals versus dollar pressure, USO/UUP crude-oil versus dollar pressure, HYG/IEF credit-risk versus Treasury rotation, XLU/XLK defensive-sector rotation, XLP/XLY consumer rotation, XLF/XLU financials-defensive rotation, XLI/XLU cyclical-defensive rotation, GVZ/VIX volatility-premium context, VIX/VXV term-structure context, MOVE/VIX bond-volatility context, GC/XAU futures-spot basis context, GC futures-proxy momentum context, and same-family level variants. No genuinely independent candidate has passed first pass. Candidate 68, `h4_gld_etf_flow_reversal_v0`, remains the strongest independent PF lead because it reached 9/9 PF cells above 1.30, but it failed trade-count and concentration/activity gates. Candidates 88-103 each reached adequate trade count across traded ETF pressure/rotation, FX-cross, or broker-consistent FX-pressure lanes, but all failed with 0/9 PF cells. Candidate 104 had a Capital.com-only PF pocket but failed sample-size and cross-broker gates. Candidate 105 added BTC-USD crypto risk pressure and failed with 0/9 PF cells despite enough trades. Candidate 106 added QQQ/SPY growth-risk rotation and failed with 0/9 PF cells despite enough trades. Candidate 107 added IWM/SPY size-risk breadth rotation and failed with 0/9 PF cells despite enough trades. Candidate 108 added SLV/GLD precious-beta rotation and failed because the 3/9 PF pocket was Pepperstone-only. Candidate 109 added XLE/XLU energy-defensive rotation and failed with 0/9 PF cells despite enough trades. Candidate 110 added EEM/SPY EM-risk rotation and failed with 0/9 PF cells despite enough trades; Capital.com/Pepperstone were near flat and Dukascopy was materially negative. Candidate 111 added ACWX/SPY global ex-US rotation and failed with 0/9 PF cells despite enough trades; Pepperstone was positive below threshold while Capital.com/Dukascopy were negative. Candidate 112 added XME/SPY metals-mining rotation and failed with 0/9 PF cells despite enough trades; all broker windows were negative after costs. Candidate 113 added FXY/UUP safe-haven FX rotation and failed with 0/9 PF cells despite enough trades; Pepperstone was mildly positive below threshold while Capital.com/Dukascopy were negative. Candidate 114 added FXF/UUP safe-haven FX rotation and failed with 0/9 PF cells despite enough trades; Dukascopy was mildly positive below threshold while Capital.com/Pepperstone were negative. Candidate 115 added FXE/UUP euro-dollar FX rotation and failed with 0/9 PF cells despite enough trades; Pepperstone was weakly positive below threshold while Capital.com/Dukascopy were negative. Candidate 116 CYB/UUP is data-blocked because public coverage ends in 2023. Candidate 117 added FXA/UUP Aussie-dollar FX rotation and failed with 0/9 PF cells despite enough trades; Capital.com/Pepperstone were weakly positive below threshold while Dukascopy was flat-to-negative. Candidate 118 added MOVE/VIX bond-volatility shock reversal and failed with 0/9 PF cells, only 6/9 trade-count cells, and max zero-trade months of 14. Candidate 119 replaced stale CYB with official FRED CNY pressure and failed with 0/9 PF cells. Candidate 120 tested broker-native tick-volume continuation and failed with 0/9 PF cells. Candidate 121 tested month-turn reversion and failed with 0/9 PF cells. Candidate 122 tested GLD ETF flow reversal v2 and failed sample-size/concentration despite 6/9 PF pockets. Candidate 123 tested GLD/SPY safe-haven rotation and failed with 0/9 PF cells. Candidate 124 tested VIX risk-off followthrough and failed with 0/9 PF cells. Candidate 125 tested VIX/VXV term-structure inversion reversal and failed with 0/9 PF cells. Candidate 126 tested VIX/VXV term-structure inversion followthrough and failed with 0/9 PF cells. Candidate 73, `quarter_round_retest_v0`, passed automated gates but is explicitly same-family and still Gate 9 pending.

## Research Boundary

Allowed:

- new versioned hypotheses
- new data classes
- mechanical definitions written before testing
- SHA256 registration before any result-producing run
- one small smoke check before matrix
- first-pass rejection without tuning

Forbidden:

- tuning rejected v0 candidates in place
- relabeling same-family retests as diversification
- lowering Phase 0 gates because an idea is low frequency
- starting EA code for a candidate before Phase 0 PASS
- using Phase 2 paper-mode as a way to rescue failed Phase 0 logic

## Current Data Constraint

The existing local evidence set is strong for:

- XAUUSD OHLC bars across Capital.com, Pepperstone, and Dukascopy
- EURUSD/USDJPY proxy bars
- XAGUSD relative bars
- public daily or weekly macro proxies from FRED/CFTC where already acquired
- deterministic event slots

The current evidence set is weak or missing for:

- real exchange-traded gold futures volume
- COMEX order-flow or depth
- options skew beyond coarse GVZ-style daily volatility
- broker-specific execution/fill slippage
- live news surprise magnitude
- intraday Treasury/real-yield shocks

That means the next independent candidate should either be:

```text
A. a genuinely new data-class hypothesis, or
B. a current-data hypothesis with a clearly different mechanism from breakout/retest and from rejected v0 families.
```

## Candidate Triage

| Candidate idea | Data class | Current-data feasible | Independence | Recommendation |
| --- | --- | --- | --- | --- |
| `h4_us_session_liquidity_reversal_v0` | XAU OHLC only | Yes | Medium | REJECTED_FIRST_PASS; do not tune v0. |
| `h4_gold_futures_volume_climax_v0` | GC continuous futures daily-volume proxy | Yes | High | REJECTED_FIRST_PASS using Yahoo `GC=F`; primary CME/order-flow data remains a separate future lane. |
| `h4_gld_etf_flow_reversal_v0` | GLD ETF daily OHLCV flow proxy | Yes | High | REJECTED_FIRST_PASS; strongest independent PF lead so far, but below 40 trades/cell with concentration/activity failures. |
| `h4_gdx_gld_miner_divergence_v0` | GDX/GLD ETF relative proxy | Yes | High | REJECTED_FIRST_PASS; 0/9 PF cells and 0/9 trade-count cells. |
| `h1_gdx_gld_trend_confirmation_v0` | GDX/GLD ETF relative proxy | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells. |
| `h4_gld_etf_flow_reversal_v1` | GLD ETF daily OHLCV flow proxy | Yes | High | REJECTED_FIRST_PASS; result-informed v1 solved trade count but diluted to 0/9 PF cells. |
| `h1_macro_composite_pullback_v0` | FRED macro/risk composite | Yes | High | REJECTED_FIRST_PASS; 3/9 PF cells and 0/9 trade-count cells. |
| `h1_macro_composite_trend_continuation_v0` | FRED macro/risk composite with H1 trend timing | Yes | High | REJECTED_FIRST_PASS; 3/9 PF cells and 6/9 trade-count cells, Pepperstone-only strength. |
| `h1_macro_composite_state_reversion_v0` | FRED macro/risk composite with H1 exhaustion reversion | Yes | High | REJECTED_FIRST_PASS; 0/9 trade-count cells and only 93 total cost-cell trades. |
| `h1_month_turn_flow_continuation_v0` | H1 calendar-flow / month-turn timing | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells and Dukascopy negative. |
| `h1_session_impulse_reversion_v0` | H1 session impulse exhaustion / mean reversion | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells and Capital.com strongly negative. |
| `h1_friday_position_squaring_reversion_v0` | H1 Friday position-squaring / mean reversion | Yes | High | REJECTED_FIRST_PASS; 0/9 PF cells and only 3/9 trade-count cells. |
| `h1_gvz_vix_vol_premium_reversal_v0` | FRED GVZ/VIX relative volatility premium | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells and weak cross-broker persistence. |
| `h1_move_vix_bond_vol_shock_reversal_v0` | Yahoo MOVE plus FRED VIX bond-volatility shock | Yes | High | REJECTED_FIRST_PASS; 6/9 trade-count cells, 0/9 PF cells, and max zero-trade months of 14. |
| `h4_vix_risk_off_followthrough_v0` | FRED VIX equity-risk implied-volatility followthrough | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells, with only Capital.com positive below threshold. |
| `h1_vix_term_structure_inversion_reversal_v0` | FRED VIX/VXV equity-volatility term structure | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells, with Pepperstone/Dukascopy positive below threshold and Capital.com negative. |
| `h1_vix_term_structure_inversion_followthrough_v0` | FRED VIX/VXV equity-volatility term structure | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells, with best PF only 1.0207 and Pepperstone materially negative. |
| `h1_gc_xau_basis_reversion_v0` | GC futures / XAU spot relative value | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells and Dukascopy-only strength below threshold. |
| `h1_gc_momentum_pullback_v0` | GC futures-proxy momentum with XAU H1 pullback | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells. |
| `h1_cot_positioning_continuation_v0` | Official CFTC gold COT positioning with XAU H1 pullback | Yes | High | REJECTED_FIRST_PASS; solved sample size with 9/9 trade-count cells but 0/9 PF cells. |
| `h1_gld_flow_momentum_pullback_v0` | GLD ETF flow-aligned H1 momentum pullback | Yes | High | REJECTED_FIRST_PASS; solved sample size with 9/9 trade-count cells but 0/9 PF cells. |
| `h1_gld_flow_stress_reversal_v0` | GLD ETF flow-stress H1 reversal | Yes | High | REJECTED_FIRST_PASS; 3/9 PF cells, 0/9 trade-count cells, and Dukascopy-only strength. |
| `h1_gld_flow_stress_followthrough_v0` | GLD ETF flow-stress H1 follow-through | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but only 2/9 PF cells and Dukascopy-only threshold strength. |
| `h1_real_yield_dollar_shock_reversal_v0` | FRED real-yield plus broad-dollar H1 shock reversal | Yes | High | REJECTED_FIRST_PASS; 0/9 PF cells and only 6/9 trade-count cells. |
| `h1_real_yield_dollar_shock_followthrough_v0` | FRED real-yield plus broad-dollar H1 shock follow-through | Yes | High | REJECTED_FIRST_PASS; 3/9 PF cells, only 6/9 trade-count cells, and Pepperstone-only strength. |
| `h1_tlt_uup_pressure_reversion_v0` | Yahoo TLT/UUP traded rates-dollar ETF pressure reversion | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells and every broker window negative. |
| `h1_tlt_uup_pressure_followthrough_v0` | Yahoo TLT/UUP traded rates-dollar ETF pressure follow-through | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone positive but below threshold. |
| `h1_spy_tlt_risk_rotation_followthrough_v0` | Yahoo SPY/TLT traded equity-vs-Treasury risk rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Pepperstone positive below threshold and Dukascopy negative. |
| `h1_tip_ief_real_yield_rotation_followthrough_v0` | Yahoo TIP/IEF traded real-yield/inflation-protection rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone positive below threshold and Capital.com/Dukascopy negative. |
| `h1_dbc_uup_commodity_dollar_followthrough_v0` | Yahoo DBC/UUP traded broad-commodity versus dollar pressure | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone positive below threshold and Capital.com/Dukascopy negative. |
| `h1_dbb_uup_industrial_metals_followthrough_v0` | Yahoo DBB/UUP traded industrial-metals versus dollar pressure | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com positive below threshold and Pepperstone/Dukascopy negative. |
| `h1_uso_uup_oil_dollar_followthrough_v0` | Yahoo USO/UUP traded crude-oil versus dollar pressure | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone positive below threshold and Capital.com/Dukascopy negative. |
| `h1_hyg_ief_credit_risk_rotation_followthrough_v0` | Yahoo HYG/IEF traded credit-risk versus Treasury rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Pepperstone positive below threshold and Dukascopy negative. |
| `h1_xlu_xlk_defensive_rotation_followthrough_v0` | Yahoo XLU/XLK traded defensive-sector versus technology-risk rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com positive below threshold and Pepperstone/Dukascopy negative. |
| `h1_xlp_xly_consumer_rotation_followthrough_v0` | Yahoo XLP/XLY traded consumer-defensive versus discretionary rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com positive below threshold, Pepperstone flat, and Dukascopy negative. |
| `h1_tlt_shy_duration_rotation_followthrough_v0` | Yahoo TLT/SHY traded long-duration versus short-duration Treasury rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone/Dukascopy small positive pockets stayed below threshold and Capital.com was negative. |
| `h1_xlf_xlu_financials_defensive_rotation_followthrough_v0` | Yahoo XLF/XLU traded financials versus defensive utilities rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Pepperstone positive pockets stayed below threshold and Dukascopy was flat/negative. |
| `h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0` | Yahoo XLI/XLU traded industrial-cyclical versus defensive utilities rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Pepperstone positive pockets stayed below threshold and Dukascopy was negative. |
| `h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0` | Yahoo AUDJPY/USDJPY daily FX-cross carry-risk rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Dukascopy negative and Pepperstone positive below threshold. |
| `h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_v0` | Yahoo EURJPY/USDJPY daily FX-cross risk rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Dukascopy negative and Pepperstone positive below threshold. |
| `h1_broker_fx_usd_pressure_followthrough_v0` | Broker-consistent EURUSD/USDJPY H1 dollar pressure | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Pepperstone positive below threshold and Dukascopy negative. |
| `h1_broker_fx_usd_pressure_conflict_reversion_v0` | Broker-consistent EURUSD/USDJPY H1 dollar pressure | Yes | High | REJECTED_FIRST_PASS; 3/9 PF cells and only 3/9 trade-count cells; Capital.com pocket did not generalize. |
| `h1_btc_risk_pressure_gold_followthrough_v0` | Yahoo BTC-USD daily crypto risk pressure | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells and all broker windows negative. |
| `h1_qqq_spy_growth_risk_rotation_followthrough_v0` | Yahoo QQQ/SPY daily growth-risk style rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone positive below threshold and Dukascopy negative. |
| `h1_iwm_spy_size_risk_rotation_followthrough_v0` | Yahoo IWM/SPY daily size-risk breadth rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone positive below threshold and Capital.com/Dukascopy weak. |
| `h1_slv_gld_precious_beta_rotation_followthrough_v0` | Yahoo SLV/GLD daily precious-beta rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells and 3/9 PF cells, but all PF cells were Pepperstone-only while Capital.com/Dukascopy were negative. |
| `h1_xle_xlu_energy_defensive_rotation_followthrough_v0` | Yahoo XLE/XLU daily energy-defensive rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone positive below threshold and Capital.com/Dukascopy negative. |
| `h1_eem_spy_em_risk_rotation_followthrough_v0` | Yahoo EEM/SPY daily emerging-market risk rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Pepperstone near flat and Dukascopy materially negative. |
| `h1_acwx_spy_global_ex_us_rotation_followthrough_v0` | Yahoo ACWX/SPY daily global ex-US rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone positive below threshold and Capital.com/Dukascopy negative. |
| `h1_xme_spy_metals_mining_rotation_followthrough_v0` | Yahoo XME/SPY daily metals-mining rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; all broker windows negative after costs. |
| `h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0` | Yahoo FXY/UUP daily safe-haven FX rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone mildly positive below threshold and Capital.com/Dukascopy negative. |
| `h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0` | Yahoo FXF/UUP daily safe-haven FX rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Dukascopy mildly positive below threshold and Capital.com/Pepperstone negative. |
| `h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0` | Yahoo FXE/UUP daily euro-dollar FX rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Pepperstone weakly positive below threshold and Capital.com/Dukascopy negative. |
| `h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0` | Yahoo CYB/UUP daily yuan-dollar FX rotation | Partial | High | BLOCKED_DATA_COVERAGE; public proxy ends in 2023, before the full matrix end date. |
| `h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0` | Yahoo FXA/UUP daily Aussie-dollar FX rotation | Yes | High | REJECTED_FIRST_PASS; 9/9 trade-count cells but 0/9 PF cells; Capital.com/Pepperstone weakly positive below threshold and Dukascopy flat-to-negative. |
| `quarter_round_retest_v0` | XAU/OHLC level-and-retest | Yes | Low | PROVISIONAL_PASS_PENDING_GATE9; same-family, not independent diversification. |
| `h1_real_yield_intraday_shock_v0` | Intraday rates/real-yield proxy | No | High | Defer until intraday rate data exists. |
| `h1_news_surprise_repricing_v0` | Actual economic surprise values | No | High | Defer until event surprise data exists. |
| `d1_macro_liquidity_regime_v0` | Central-bank liquidity and USD funding proxies | Partial | High | Possible later, but likely slow-moving and low trade count. |
| `xau_options_skew_reversal_v0` | Gold options skew | No | High | Defer until options-skew source exists. |

## Latest Tested Candidate

The latest current-data candidate was:

```text
h1_vix_term_structure_inversion_followthrough_v0
```

Mechanism:

```text
Shifted VIX/VXV term-structure inversion may mark equity-risk stress that spills into XAU safe-haven continuation.
The candidate trades only after shifted VIX/VXV term-structure state and a completed H1 XAU continuation candle align.
```

Why this is not same-family:

- It does not trade retests of levels.
- It does not require a broken support/resistance level.
- It is equity-volatility term-structure pressure, not breakout continuation.
- It uses shifted public FRED VIX/VXV daily observations plus H1 XAU confirmation state, not M5/M15 retest mechanics.

Why it is still risky:

- It reached the trade-count floor in 9/9 cells.
- It failed PF persistence with 0/9 PF cells above 1.30.
- Best PF was only 1.0207; Pepperstone was materially negative.
- Neither VIX/VXV inversion reversal nor followthrough is approved.

## Pre-Registration Status

Before any result-producing run, the following files now exist:

```text
docs/hypothesis_h4_gld_etf_flow_reversal_v0.md
docs/hypothesis_h4_gld_etf_flow_reversal_v1.md
docs/hypothesis_h4_gdx_gld_miner_divergence_v0.md
docs/hypothesis_h1_gdx_gld_trend_confirmation_v0.md
docs/hypothesis_h1_real_yield_dollar_shock_reversal_v0.md
docs/hypothesis_h1_real_yield_dollar_shock_followthrough_v0.md
docs/hypothesis_h1_macro_composite_state_reversion_v0.md
docs/hypothesis_h1_tlt_uup_pressure_reversion_v0.md
docs/hypothesis_h1_tlt_uup_pressure_followthrough_v0.md
docs/hypothesis_h1_spy_tlt_risk_rotation_followthrough_v0.md
docs/hypothesis_h1_tip_ief_real_yield_rotation_followthrough_v0.md
docs/hypothesis_h1_dbc_uup_commodity_dollar_followthrough_v0.md
docs/hypothesis_h1_dbb_uup_industrial_metals_followthrough_v0.md
docs/hypothesis_h1_uso_uup_oil_dollar_followthrough_v0.md
docs/hypothesis_h1_hyg_ief_credit_risk_rotation_followthrough_v0.md
docs/hypothesis_h1_xlu_xlk_defensive_rotation_followthrough_v0.md
docs/hypothesis_h1_xlp_xly_consumer_rotation_followthrough_v0.md
docs/hypothesis_h1_tlt_shy_duration_rotation_followthrough_v0.md
docs/hypothesis_h1_xlf_xlu_financials_defensive_rotation_followthrough_v0.md
docs/hypothesis_h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0.md
docs/hypothesis_h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0.md
docs/hypothesis_h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_v0.md
docs/hypothesis_h1_broker_fx_usd_pressure_followthrough_v0.md
docs/hypothesis_h1_broker_fx_usd_pressure_conflict_reversion_v0.md
docs/hypothesis_h1_btc_risk_pressure_gold_followthrough_v0.md
docs/hypothesis_h1_qqq_spy_growth_risk_rotation_followthrough_v0.md
docs/hypothesis_h1_iwm_spy_size_risk_rotation_followthrough_v0.md
docs/hypothesis_h1_slv_gld_precious_beta_rotation_followthrough_v0.md
docs/hypothesis_h1_xle_xlu_energy_defensive_rotation_followthrough_v0.md
docs/hypothesis_h1_eem_spy_em_risk_rotation_followthrough_v0.md
docs/hypothesis_h1_acwx_spy_global_ex_us_rotation_followthrough_v0.md
docs/hypothesis_h1_xme_spy_metals_mining_rotation_followthrough_v0.md
docs/hypothesis_h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0.md
docs/hypothesis_h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0.md
docs/hypothesis_h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0.md
docs/hypothesis_h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0.md
docs/hypothesis_h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0.md
docs/hypothesis_h1_vix_term_structure_inversion_reversal_v0.md
docs/hypothesis_h1_vix_term_structure_inversion_followthrough_v0.md
src/phase0/strategies/h4_gld_etf_flow_reversal_v0.py
src/phase0/strategies/h4_gld_etf_flow_reversal_v1.py
src/phase0/strategies/h4_gdx_gld_miner_divergence_v0.py
src/phase0/strategies/h1_gdx_gld_trend_confirmation_v0.py
src/phase0/strategies/h1_real_yield_dollar_shock_reversal_v0.py
src/phase0/strategies/h1_real_yield_dollar_shock_followthrough_v0.py
src/phase0/strategies/h1_macro_composite_state_reversion_v0.py
src/phase0/strategies/h1_tlt_uup_pressure_reversion_v0.py
src/phase0/strategies/h1_tlt_uup_pressure_followthrough_v0.py
src/phase0/strategies/h1_spy_tlt_risk_rotation_followthrough_v0.py
src/phase0/strategies/h1_tip_ief_real_yield_rotation_followthrough_v0.py
src/phase0/strategies/h1_dbc_uup_commodity_dollar_followthrough_v0.py
src/phase0/strategies/h1_dbb_uup_industrial_metals_followthrough_v0.py
src/phase0/strategies/h1_uso_uup_oil_dollar_followthrough_v0.py
src/phase0/strategies/h1_hyg_ief_credit_risk_rotation_followthrough_v0.py
src/phase0/strategies/h1_xlu_xlk_defensive_rotation_followthrough_v0.py
src/phase0/strategies/h1_xlp_xly_consumer_rotation_followthrough_v0.py
src/phase0/strategies/h1_tlt_shy_duration_rotation_followthrough_v0.py
src/phase0/strategies/h1_xlf_xlu_financials_defensive_rotation_followthrough_v0.py
src/phase0/strategies/h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0.py
src/phase0/strategies/h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0.py
src/phase0/strategies/h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_v0.py
src/phase0/strategies/h1_broker_fx_usd_pressure_followthrough_v0.py
src/phase0/strategies/h1_broker_fx_usd_pressure_conflict_reversion_v0.py
src/phase0/strategies/h1_btc_risk_pressure_gold_followthrough_v0.py
src/phase0/strategies/h1_qqq_spy_growth_risk_rotation_followthrough_v0.py
src/phase0/strategies/h1_iwm_spy_size_risk_rotation_followthrough_v0.py
src/phase0/strategies/h1_slv_gld_precious_beta_rotation_followthrough_v0.py
src/phase0/strategies/h1_xle_xlu_energy_defensive_rotation_followthrough_v0.py
src/phase0/strategies/h1_eem_spy_em_risk_rotation_followthrough_v0.py
src/phase0/strategies/h1_acwx_spy_global_ex_us_rotation_followthrough_v0.py
src/phase0/strategies/h1_xme_spy_metals_mining_rotation_followthrough_v0.py
src/phase0/strategies/h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0.py
src/phase0/strategies/h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0.py
src/phase0/strategies/h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0.py
src/phase0/strategies/h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0.py
src/phase0/strategies/h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0.py
src/phase0/strategies/h1_vix_term_structure_inversion_reversal_v0.py
src/phase0/strategies/h1_vix_term_structure_inversion_followthrough_v0.py
tests/test_h4_gld_etf_flow_reversal_v0.py
tests/test_h4_gld_etf_flow_reversal_v1.py
tests/test_h4_gdx_gld_miner_divergence_v0.py
tests/test_h1_gdx_gld_trend_confirmation_v0.py
tests/test_h1_real_yield_dollar_shock_reversal_v0.py
tests/test_h1_real_yield_dollar_shock_followthrough_v0.py
tests/test_h1_macro_composite_state_reversion_v0.py
tests/test_h1_tlt_uup_pressure_reversion_v0.py
tests/test_h1_tlt_uup_pressure_followthrough_v0.py
tests/test_h1_spy_tlt_risk_rotation_followthrough_v0.py
tests/test_h1_tip_ief_real_yield_rotation_followthrough_v0.py
tests/test_h1_dbc_uup_commodity_dollar_followthrough_v0.py
tests/test_h1_dbb_uup_industrial_metals_followthrough_v0.py
tests/test_h1_uso_uup_oil_dollar_followthrough_v0.py
tests/test_h1_hyg_ief_credit_risk_rotation_followthrough_v0.py
tests/test_h1_xlu_xlk_defensive_rotation_followthrough_v0.py
tests/test_h1_xlp_xly_consumer_rotation_followthrough_v0.py
tests/test_h1_tlt_shy_duration_rotation_followthrough_v0.py
tests/test_h1_xlf_xlu_financials_defensive_rotation_followthrough_v0.py
tests/test_h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0.py
tests/test_h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0.py
tests/test_h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_v0.py
tests/test_h1_broker_fx_usd_pressure_followthrough_v0.py
tests/test_h1_broker_fx_usd_pressure_conflict_reversion_v0.py
tests/test_h1_btc_risk_pressure_gold_followthrough_v0.py
tests/test_h1_qqq_spy_growth_risk_rotation_followthrough_v0.py
tests/test_h1_iwm_spy_size_risk_rotation_followthrough_v0.py
tests/test_h1_slv_gld_precious_beta_rotation_followthrough_v0.py
tests/test_h1_xle_xlu_energy_defensive_rotation_followthrough_v0.py
tests/test_h1_eem_spy_em_risk_rotation_followthrough_v0.py
tests/test_h1_acwx_spy_global_ex_us_rotation_followthrough_v0.py
tests/test_h1_xme_spy_metals_mining_rotation_followthrough_v0.py
tests/test_h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0.py
tests/test_h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0.py
tests/test_h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0.py
tests/test_h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0.py
tests/test_h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0.py
tests/test_h1_vix_term_structure_inversion_reversal_v0.py
tests/test_h1_vix_term_structure_inversion_followthrough_v0.py
```

Registration, smoke, and first-pass status:

```text
Research hypothesis: REGISTERED
Latest SHA256: 89157f81ac11345de02b0292fd8f6558eb53075de8ff921ee6131babeb7b7c47
Synthetic smoke: PASS
First-pass matrix: REJECTED_FIRST_PASS
Latest matrix trades: 897 across cost cells
Latest PF cells >= 1.30: 0/9
Latest minimum cell trades: 86
```

## First-Pass Result

`h4_gld_etf_flow_reversal_v0` did not clear the full first-pass gate set. It produced the strongest independent PF profile so far, with all 9 matrix cells above PF 1.30 and all P95-cost cells still above PF 1.30. It still failed because no cell reached the 40-trade minimum, max zero-trade months exceeded the threshold, and concentration was too high.

`h4_gld_etf_flow_reversal_v1` tested a broader, explicitly result-informed version. It solved trade count in all cells and kept max zero-trade months within the threshold, but PF diluted to 0/9 cells above 1.30. The correct action is to reject v1 without tuning.

`h1_real_yield_dollar_shock_reversal_v0` tested a distinct macro-shock H1 reversal lane using full-history FRED `DFII10` and `DTWEXBGS` inputs. It produced enough activity in Pepperstone and Dukascopy but failed with 0/9 PF cells above 1.30 and only 6/9 cells over the 40-trade minimum. The correct action is to reject v0 without tuning.

`h1_real_yield_dollar_shock_followthrough_v0` tested the paired macro-shock H1 continuation lane. It improved to 3/9 PF cells, but all passing cells were Pepperstone-only and below the trade-count floor, while Dukascopy was negative. The correct action is to reject v0 without tuning.

`h1_macro_composite_state_reversion_v0` tested H1 exhaustion reversion inside the strongest fixed macro-composite state. It was too sparse, with 0/9 trade-count cells and only two Pepperstone trades behind the 3/9 PF cells. The correct action is to reject v0 without tuning.

`h1_tlt_uup_pressure_reversion_v0` and `h1_tlt_uup_pressure_followthrough_v0` tested a fresh traded ETF rates-dollar data class. Both produced enough sample size, but both failed with 0/9 PF cells. The correct action is to reject both v0 hypotheses without tuning and move to a different data class.

`h1_spy_tlt_risk_rotation_followthrough_v0` tested a fresh traded ETF equity-vs-Treasury risk-rotation data class. It produced enough sample size, but failed with 0/9 PF cells and negative Dukascopy performance. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_tip_ief_real_yield_rotation_followthrough_v0` tested a fresh traded ETF real-yield/inflation-protection rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone-only strength stayed below threshold while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_dbc_uup_commodity_dollar_followthrough_v0` tested a fresh traded ETF broad-commodity versus dollar data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone-only strength stayed below threshold while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_dbb_uup_industrial_metals_followthrough_v0` tested a narrower traded ETF industrial-metals versus dollar data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com-only strength stayed below threshold while Pepperstone and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_hyg_ief_credit_risk_rotation_followthrough_v0` tested a traded ETF credit-risk versus Treasury data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com and Pepperstone strength stayed below threshold while Dukascopy was negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_xlu_xlk_defensive_rotation_followthrough_v0` tested a traded ETF defensive-sector versus technology-risk rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com strength stayed below threshold while Pepperstone and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_xlp_xly_consumer_rotation_followthrough_v0` tested a traded ETF consumer-defensive versus discretionary rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com strength stayed below threshold while Pepperstone was roughly flat and Dukascopy was negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_uso_uup_oil_dollar_followthrough_v0` tested a traded ETF crude-oil versus dollar pressure data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone strength stayed below threshold while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_tlt_shy_duration_rotation_followthrough_v0` tested a traded ETF long-duration versus short-duration Treasury rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone and Dukascopy had small positive pockets below threshold while Capital.com was negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_xlf_xlu_financials_defensive_rotation_followthrough_v0` tested a traded ETF financials versus defensive-utilities rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com and Pepperstone were positive below threshold while Dukascopy was flat/negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0` tested a traded ETF industrial-cyclical versus defensive-utilities rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com and Pepperstone were positive below threshold while Dukascopy was negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0` tested a daily FX-cross carry-risk rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com and Dukascopy were negative while Pepperstone was positive below threshold. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_qqq_spy_growth_risk_rotation_followthrough_v0` tested a public QQQ/SPY daily growth-risk rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone was positive below threshold while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_iwm_spy_size_risk_rotation_followthrough_v0` tested a public IWM/SPY daily size-risk breadth rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone was positive below threshold while Capital.com and Dukascopy were weak/negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_slv_gld_precious_beta_rotation_followthrough_v0` tested a public SLV/GLD daily precious-beta rotation data class. It produced enough sample size and reached 3/9 PF cells, but all PF-passing cells were Pepperstone-only while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_xle_xlu_energy_defensive_rotation_followthrough_v0` tested a public XLE/XLU daily energy-defensive rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone was positive below threshold while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_eem_spy_em_risk_rotation_followthrough_v0` tested a public EEM/SPY daily emerging-market risk rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com and Pepperstone were near flat while Dukascopy was materially negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_acwx_spy_global_ex_us_rotation_followthrough_v0` tested a public ACWX/SPY daily global ex-US rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone was positive below threshold while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_xme_spy_metals_mining_rotation_followthrough_v0` tested a public XME/SPY daily metals-mining rotation data class. It produced enough sample size, but failed with 0/9 PF cells; all broker windows were negative after costs. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0` tested a public FXY/UUP daily safe-haven FX rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone was mildly positive below threshold while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0` tested a public FXF/UUP daily safe-haven FX rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Dukascopy was mildly positive below threshold while Capital.com and Pepperstone were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0` tested a public FXE/UUP daily euro-dollar FX rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Pepperstone was weakly positive below threshold while Capital.com and Dukascopy were negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

`h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0` tested whether a public CYB/UUP yuan-dollar proxy could support the same H1 XAU follow-through concept, but the public Yahoo CYB data ended in 2023 and did not cover the full matrix. The correct action is to treat it as blocked, not rejected, until a full-coverage yuan data source exists.

`h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0` tested a public FXA/UUP daily Aussie-dollar FX rotation data class. It produced enough sample size, but failed with 0/9 PF cells; Capital.com and Pepperstone were weakly positive below threshold while Dukascopy was flat-to-negative. The correct action is to reject v0 without tuning and keep searching for a different independent data class or behavior family.

Required mechanical definition:

- GLD daily volume and return features are shifted by one observation before any XAU H4 merge.
- GLD flow stress requires high rolling volume percentile, high log-volume or dollar-volume z-score, and a minimum one-day GLD return shock.
- XAU H4 must already have moved in the same direction as the GLD shock over the prior 12 H4 bars.
- Entry occurs only after the current H4 bar closes as a reversal candle.
- Stop, target, time stop, and decision hours are fixed before the run.
- Maximum one signal per UTC day per direction.
- No news filters or post-result threshold changes are allowed.

Suggested fixed first-pass parameters:

```text
H4 ATR lookback: 14
GLD volume percentile: >= 0.75
GLD volume z-score: >= 0.80
GLD one-day return shock: abs(return) >= 0.003
XAU H4 12-bar return threshold: abs(return) >= 0.0025
Stop: 1.15 x H4 ATR14
Target: 1.50R
Time stop: 6 H4 bars
Decision hours: 08:00, 12:00, 16:00, 20:00 UTC
```

These were first-pass v1 values, not tuning handles. Because this version failed, reject it and do not tune v1.

## Pass/Fail Rule

Use the same Phase 0 first-pass rule:

```text
PASS only if at least 7/9 matrix cells reach PF >= 1.30,
trade count is sufficient,
concentration gates pass,
cost sensitivity passes,
and no procedural gate is bypassed.
```

If it fails, record it as:

```text
REJECTED_FIRST_PASS
```

Then move to a new data-class candidate. Additional GLD-flow broadening is lower priority because v1 already showed PF dilution under broader sampling.

## Better Strategic Next Move

The stronger next research move is to add a higher-quality new data class before more OHLC-only attempts:

```text
Primary COMEX/CME futures volume/order-flow or options-skew data.
```

Reason:

The current OHLC/macro/intermarket/COT/ETF-flow search has already covered enough nearby hypotheses that another OHLC-only candidate has a low prior probability. The non-authoritative GC continuous-volume proxy failed outright, the official COT continuation lane solved sample size but had no PF persistence, the GDX/GLD relative proxy failed, the GLD ETF flow proxy only survived in the narrow under-sampled v0 form, and the H1 GLD-flow continuation variant also failed 0/9 PF cells. The next lift should be primary COMEX/CME/order-flow/options-skew data or another genuinely new data class, not another GLD/GDX/COT threshold variant.

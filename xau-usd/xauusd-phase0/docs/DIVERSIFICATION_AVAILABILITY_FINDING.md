# Diversification Availability Finding

Last updated: 2026-05-30

## Finding

As of 2026-05-30, the project has tested a broad set of non-level, intermarket, macro-regime, AI-style macro-composite, policy-uncertainty, nominal-rate, yield-curve, corporate-credit, futures-positioning, options-implied-volatility, equity-risk implied-volatility, GVZ/VIX relative volatility-premium, GVZ/realized-volatility spread, real-yield / breakeven-inflation mix, GC/XAU futures-spot basis, GC futures-proxy momentum, official CFTC COT continuation, calendar-flow, session impulse-reversion, Friday position-squaring, financial-conditions, breakeven-inflation, volatility-regime, event-regime, non-authoritative futures-volume proxy, public GLD ETF flow proxy, public GDX/GLD miner-relative proxy, public FX ETF rotation proxies, and higher-timeframe XAUUSD candidates under the locked Phase 0 research lane. Twenty-nine H4/D1/W1 candidates plus additional H1 intermarket, volatility-regime, event-regime, ETF-relative, ETF-flow, macro-composite, macro-decomposition, calendar-flow, session impulse-reversion, Friday position-squaring, volatility-premium, futures-spot relative-value, futures-proxy momentum, FX-rotation, and futures-positioning candidates were registered, SHA256-locked, smoke-tested, and run through the real 9-cell matrix without tuning. Zero produced a full independent Phase 0 first-pass approval. One GLD ETF flow v0 candidate produced PF >= 1.30 in 9/9 cells, but failed trade-count, activity, and concentration gates; broader GLD-flow versions either solved trade count while diluting PF or preserved only one-broker pockets. Both real-yield / breakeven-inflation mix reversal and follow-through expressions failed PF persistence. A new `quarter_round_retest_v0` same-family level candidate passed automated gates, but it is not diversification and remains Gate 9 pending.

The current evidence supports this operating conclusion:

```text
The project has one approved edge family inside the current XAUUSD research scope:
level-and-pullback / breakout-retest.
```

Same-family variants may be useful for observation, cost study, and future comparison, but they do not provide portfolio diversification.

## Evidence Set

| # | Candidate | Decision cadence | PF >= 1.30 cells | First-pass status |
| ---: | --- | --- | ---: | --- |
| 1 | `d1_momentum_h4_pullback_v0` | H4/D1 | 3/9 | REJECTED_FIRST_PASS |
| 2 | `d1_volatility_expansion_reversal_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 3 | `d1_compression_h4_expansion_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 4 | `d1_multi_day_exhaustion_reversion_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 5 | `h4_d1_momentum_expansion_continuation_v0` | H4/D1 | 3/9 | REJECTED_FIRST_PASS |
| 6 | `h4_inside_bar_d1_momentum_breakout_v0` | H4/D1 | 2/9 | REJECTED_FIRST_PASS |
| 7 | `w1_d1_momentum_continuation_v0` | W1/D1 | 3/9 | REJECTED_FIRST_PASS |
| 8 | `weekly_open_reversion_v0` | W1/M15 | 0/9 | REJECTED_FIRST_PASS |
| 9 | `d1_inside_day_breakout_v0` | H4/D1 | 3/9 | REJECTED_FIRST_PASS |
| 10 | `d1_outside_day_followthrough_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 11 | `d1_w1_momentum_h4_pullback_v0` | H4/D1 with W1 state | 3/9 | REJECTED_FIRST_PASS |
| 12 | `h4_walk_forward_knn_momentum_state_v0` | H4/D1 | 0/9 | REJECTED_FIRST_PASS |
| 13 | `h4_real_yield_proxy_momentum_v0` | H4/D1 with FRED real-yield/dollar state | 3/9 | REJECTED_FIRST_PASS |
| 14 | `cot_gold_positioning_reversal_v0` | H4 with official CFTC gold COT positioning | 0/9 | REJECTED_FIRST_PASS |
| 15 | `h4_gvz_volatility_panic_reversal_v0` | H4 with FRED GVZ gold-options implied volatility | 0/9 | REJECTED_FIRST_PASS |
| 16 | `h4_vix_risk_off_reversal_v0` | H4 with FRED VIX equity-risk implied volatility | 3/9 | REJECTED_FIRST_PASS |
| 17 | `h4_vix_risk_off_followthrough_v0` | H4 with FRED VIX equity-risk implied volatility | 0/9 | REJECTED_FIRST_PASS |
| 18 | `h4_financial_conditions_stress_reversal_v0` | H4 with FRED NFCI/ANFCI financial conditions | 0/9 | REJECTED_FIRST_PASS |
| 19 | `h4_breakeven_inflation_momentum_v0` | H4 with FRED T5YIE/T10YIE breakeven inflation momentum | 0/9 | REJECTED_FIRST_PASS |
| 20 | `h4_treasury_curve_stress_momentum_v0` | H4 with FRED DGS2/DGS10/T10Y2Y Treasury curve stress | 3/9 | REJECTED_FIRST_PASS |
| 21 | `h4_credit_spread_stress_momentum_v0` | H4 with FRED BAA10Y/AAA10Y corporate credit spread stress | 0/9 | REJECTED_FIRST_PASS |
| 22 | `h4_macro_composite_risk_state_v0` | H4 with fixed AI-style FRED macro/risk vote | 6/9 | REJECTED_FIRST_PASS |
| 23 | `h4_macro_composite_risk_state_v1` | H4 with broader fixed AI-style FRED macro/risk vote | 3/9 | REJECTED_FIRST_PASS |
| 24 | `h4_policy_uncertainty_safe_haven_v0` | H4 with FRED USEPUINDXD policy-uncertainty safe-haven state | 3/9 | REJECTED_FIRST_PASS |
| 25 | `h4_gold_futures_volume_climax_v0` | H4 with Yahoo `GC=F` continuous futures daily-volume proxy | 0/9 | REJECTED_FIRST_PASS |
| 26 | `h4_gld_etf_flow_reversal_v0` | H4 with Yahoo `GLD` ETF daily OHLCV flow proxy | 9/9 | REJECTED_FIRST_PASS: sample-size, activity, and concentration failed |
| 27 | `h4_gdx_gld_miner_divergence_v0` | H4 with Yahoo `GDX`/`GLD` ETF relative proxy | 0/9 | REJECTED_FIRST_PASS |
| 28 | `h4_gld_etf_flow_reversal_v1` | H4 with Yahoo `GLD` ETF daily OHLCV flow proxy | 0/9 | REJECTED_FIRST_PASS: result-informed v1 diluted PF |
| 29 | `h4_gld_etf_flow_reversal_v2` | H4 with Yahoo `GLD` ETF daily OHLCV flow proxy | 6/9 | REJECTED_FIRST_PASS: sample-size, activity, and concentration failed |

Additional H1 intermarket, volatility-regime, and event-regime diversification attempts:

| # | Candidate | Input Family | PF >= 1.30 cells | First-pass status |
| ---: | --- | --- | ---: | --- |
| 1 | `gold_fx_proxy_divergence_v0` | EURUSD/USDJPY proxy | 0/9 | REJECTED_FIRST_PASS |
| 2 | `xau_xag_relative_value_v0` | XAGUSD relative value | 0/9 | REJECTED_FIRST_PASS |
| 3 | `xau_xag_fx_composite_reversion_v0` | XAGUSD plus EURUSD/USDJPY proxy | 0/9 | REJECTED_FIRST_PASS |
| 4 | `xag_lead_xau_followthrough_v0` | XAGUSD lead-lag continuation | 0/9 | REJECTED_FIRST_PASS |
| 5 | `h1_volatility_squeeze_breakout_v0` | H1 volatility-compression expansion | 3/9 | REJECTED_FIRST_PASS |
| 6 | `h1_macro_event_aftershock_v0` | H1 standardized US macro-event aftershock continuation | 0/9 | REJECTED_FIRST_PASS |
| 7 | `h1_gdx_gld_trend_confirmation_v0` | GDX/GLD ETF relative trend confirmation | 0/9 | REJECTED_FIRST_PASS |
| 8 | `h1_macro_composite_pullback_v0` | FRED macro-composite H1 pullback | 3/9 | REJECTED_FIRST_PASS |
| 9 | `h1_macro_composite_trend_continuation_v0` | FRED macro-composite H1 trend continuation | 3/9 | REJECTED_FIRST_PASS |
| 10 | `h1_gvz_vix_vol_premium_reversal_v0` | FRED GVZ/VIX relative volatility premium | 0/9 | REJECTED_FIRST_PASS |
| 11 | `h1_gc_xau_basis_reversion_v0` | GC futures / XAU spot relative-value convergence | 0/9 | REJECTED_FIRST_PASS |
| 12 | `h1_gc_momentum_pullback_v0` | GC futures-proxy momentum with XAU H1 pullback | 0/9 | REJECTED_FIRST_PASS |
| 13 | `h1_cot_positioning_continuation_v0` | Official CFTC gold COT positioning with XAU H1 pullback | 0/9 | REJECTED_FIRST_PASS |
| 14 | `h1_gld_flow_momentum_pullback_v0` | GLD ETF flow-aligned H1 momentum pullback | 0/9 | REJECTED_FIRST_PASS |
| 15 | `h1_month_turn_flow_continuation_v0` | Calendar-flow / month-turn H1 trend continuation | 0/9 | REJECTED_FIRST_PASS |
| 16 | `h1_session_impulse_reversion_v0` | Session impulse exhaustion / H1 mean reversion | 0/9 | REJECTED_FIRST_PASS |
| 17 | `h1_friday_position_squaring_reversion_v0` | Friday position-squaring / H1 mean reversion | 0/9 | REJECTED_FIRST_PASS |
| 18 | `h1_gld_flow_stress_reversal_v0` | GLD ETF flow-stress H1 reversal | 3/9 | REJECTED_FIRST_PASS |
| 19 | `h1_gld_flow_stress_followthrough_v0` | GLD ETF flow-stress H1 follow-through | 2/9 | REJECTED_FIRST_PASS |
| 20 | `h1_real_yield_dollar_shock_reversal_v0` | FRED real-yield plus broad-dollar H1 shock reversal | 0/9 | REJECTED_FIRST_PASS |
| 21 | `h1_real_yield_dollar_shock_followthrough_v0` | FRED real-yield plus broad-dollar H1 shock follow-through | 3/9 | REJECTED_FIRST_PASS |
| 22 | `h1_macro_composite_state_reversion_v0` | FRED macro-composite H1 exhaustion reversion | 3/9 | REJECTED_FIRST_PASS: 0/9 trade-count cells |
| 23 | `h1_tlt_uup_pressure_reversion_v0` | Yahoo TLT/UUP traded ETF rates-dollar pressure reversion | 0/9 | REJECTED_FIRST_PASS |
| 24 | `h1_tlt_uup_pressure_followthrough_v0` | Yahoo TLT/UUP traded ETF rates-dollar pressure follow-through | 0/9 | REJECTED_FIRST_PASS |
| 25 | `h1_spy_tlt_risk_rotation_followthrough_v0` | Yahoo SPY/TLT traded ETF equity-vs-Treasury risk rotation | 0/9 | REJECTED_FIRST_PASS |
| 26 | `h1_tip_ief_real_yield_rotation_followthrough_v0` | Yahoo TIP/IEF traded ETF real-yield/inflation-protection rotation | 0/9 | REJECTED_FIRST_PASS |
| 27 | `h1_dbc_uup_commodity_dollar_followthrough_v0` | Yahoo DBC/UUP traded ETF broad-commodity versus dollar pressure | 0/9 | REJECTED_FIRST_PASS |
| 28 | `h1_dbb_uup_industrial_metals_followthrough_v0` | Yahoo DBB/UUP traded ETF industrial-metals versus dollar pressure | 0/9 | REJECTED_FIRST_PASS |
| 29 | `h1_hyg_ief_credit_risk_rotation_followthrough_v0` | Yahoo HYG/IEF traded ETF credit-risk versus Treasury rotation | 0/9 | REJECTED_FIRST_PASS |
| 30 | `h1_xlu_xlk_defensive_rotation_followthrough_v0` | Yahoo XLU/XLK traded ETF defensive-sector versus technology-risk rotation | 0/9 | REJECTED_FIRST_PASS |
| 31 | `h1_xlp_xly_consumer_rotation_followthrough_v0` | Yahoo XLP/XLY traded ETF consumer-defensive versus discretionary rotation | 0/9 | REJECTED_FIRST_PASS |
| 32 | `h1_uso_uup_oil_dollar_followthrough_v0` | Yahoo USO/UUP traded ETF crude-oil versus dollar pressure | 0/9 | REJECTED_FIRST_PASS |
| 33 | `h1_tlt_shy_duration_rotation_followthrough_v0` | Yahoo TLT/SHY traded ETF long-duration versus short-duration Treasury rotation | 0/9 | REJECTED_FIRST_PASS |
| 34 | `h1_xlf_xlu_financials_defensive_rotation_followthrough_v0` | Yahoo XLF/XLU traded ETF financials versus defensive utilities rotation | 0/9 | REJECTED_FIRST_PASS |
| 35 | `h1_xli_xlu_cyclical_defensive_rotation_followthrough_v0` | Yahoo XLI/XLU traded ETF industrial-cyclical versus defensive utilities rotation | 0/9 | REJECTED_FIRST_PASS |
| 36 | `h1_audjpy_usdjpy_fx_carry_rotation_followthrough_v0` | Yahoo AUDJPY/USDJPY daily FX-cross carry-risk rotation | 0/9 | REJECTED_FIRST_PASS |
| 37 | `h1_eurjpy_usdjpy_fx_risk_rotation_followthrough_v0` | Yahoo EURJPY/USDJPY daily FX-cross risk rotation | 0/9 | REJECTED_FIRST_PASS |
| 38 | `h1_broker_fx_usd_pressure_followthrough_v0` | Broker-consistent EURUSD/USDJPY H1 dollar-pressure follow-through | 0/9 | REJECTED_FIRST_PASS |
| 39 | `h1_broker_fx_usd_pressure_conflict_reversion_v0` | Broker-consistent EURUSD/USDJPY H1 dollar-pressure conflict reversion | 3/9 | REJECTED_FIRST_PASS |
| 40 | `h1_btc_risk_pressure_gold_followthrough_v0` | Yahoo BTC-USD daily crypto risk-pressure follow-through | 0/9 | REJECTED_FIRST_PASS |
| 41 | `h1_qqq_spy_growth_risk_rotation_followthrough_v0` | Yahoo QQQ/SPY daily growth-risk style rotation | 0/9 | REJECTED_FIRST_PASS |
| 42 | `h1_iwm_spy_size_risk_rotation_followthrough_v0` | Yahoo IWM/SPY daily size-risk breadth rotation | 0/9 | REJECTED_FIRST_PASS |
| 43 | `h1_slv_gld_precious_beta_rotation_followthrough_v0` | Yahoo SLV/GLD daily precious-beta rotation | 3/9 | REJECTED_FIRST_PASS |
| 44 | `h1_xle_xlu_energy_defensive_rotation_followthrough_v0` | Yahoo XLE/XLU daily energy-defensive rotation | 0/9 | REJECTED_FIRST_PASS |
| 45 | `h1_eem_spy_em_risk_rotation_followthrough_v0` | Yahoo EEM/SPY daily emerging-market risk rotation | 0/9 | REJECTED_FIRST_PASS |
| 46 | `h1_acwx_spy_global_ex_us_rotation_followthrough_v0` | Yahoo ACWX/SPY daily global ex-US rotation | 0/9 | REJECTED_FIRST_PASS |
| 47 | `h1_xme_spy_metals_mining_rotation_followthrough_v0` | Yahoo XME/SPY daily metals-mining rotation | 0/9 | REJECTED_FIRST_PASS |
| 48 | `h1_fxy_uup_safe_haven_fx_rotation_followthrough_v0` | Yahoo FXY/UUP daily safe-haven FX rotation | 0/9 | REJECTED_FIRST_PASS |
| 49 | `h1_fxf_uup_safe_haven_fx_rotation_followthrough_v0` | Yahoo FXF/UUP daily safe-haven FX rotation | 0/9 | REJECTED_FIRST_PASS |
| 50 | `h1_fxe_uup_euro_dollar_fx_rotation_followthrough_v0` | Yahoo FXE/UUP daily euro-dollar FX rotation | 0/9 | REJECTED_FIRST_PASS |
| 51 | `h1_cyb_uup_yuan_dollar_fx_rotation_followthrough_v0` | Yahoo CYB/UUP daily yuan-dollar FX rotation | n/a | BLOCKED_DATA_COVERAGE |
| 52 | `h1_fxa_uup_aussie_dollar_fx_rotation_followthrough_v0` | Yahoo FXA/UUP daily Aussie-dollar FX rotation | 0/9 | REJECTED_FIRST_PASS |
| 53 | `h1_move_vix_bond_vol_shock_reversal_v0` | Yahoo MOVE plus FRED VIX bond-volatility shock reversal | 0/9 | REJECTED_FIRST_PASS |
| 54 | `h1_vix_term_structure_inversion_reversal_v0` | FRED VIX/VXV equity-volatility term structure | 0/9 | REJECTED_FIRST_PASS |
| 55 | `h1_vix_term_structure_inversion_followthrough_v0` | FRED VIX/VXV equity-volatility term structure | 0/9 | REJECTED_FIRST_PASS |
| 56 | `h1_policy_uncertainty_intraday_reversal_v0` | FRED USEPUINDXD policy-uncertainty shock reversal | 0/9 | REJECTED_FIRST_PASS |
| 57 | `h1_breakeven_inflation_shock_reversal_v0` | FRED T5YIE/T10YIE breakeven-inflation shock reversal | 0/9 | REJECTED_FIRST_PASS |
| 58 | `h1_treasury_curve_shock_reversal_v0` | FRED DGS2/DGS10/T10Y2Y Treasury-rate/curve shock reversal | 0/9 | REJECTED_FIRST_PASS |
| 59 | `h1_credit_spread_shock_reversal_v0` | FRED BAA10Y/AAA10Y corporate credit-spread shock reversal | 0/9 | REJECTED_FIRST_PASS |
| 60 | `h1_financial_conditions_shock_reversal_v0` | FRED NFCI/ANFCI financial-conditions shock reversal | 0/9 | REJECTED_FIRST_PASS |
| 61 | `h1_gvz_realized_vol_spread_reversal_v0` | FRED GVZ gold implied volatility versus H1 realized XAU volatility | 1/9 | REJECTED_FIRST_PASS |
| 62 | `h1_real_yield_inflation_mix_reversal_v0` | FRED real-yield plus breakeven-inflation mix reversal | 0/9 | REJECTED_FIRST_PASS |
| 63 | `h1_real_yield_inflation_mix_followthrough_v0` | FRED real-yield plus breakeven-inflation mix follow-through | 0/9 | REJECTED_FIRST_PASS |

Supporting artifacts:

- `docs/CANDIDATE_RESEARCH_BACKLOG.md`
- `outputs/reports/PHASE0_REJECTED_CANDIDATE_GATE_AUDIT.md`
- `outputs/reports/PHASE0_CONCENTRATION_FREQUENCY_NORMALIZED_AUDIT.md`
- Per-candidate `*_FIRST_PASS.md` files in `docs/`

## Gate-Bias Check

The frequency-normalized concentration audit did not rescue or reclassify any rejected candidate. It found review-context normalized ratios, but no candidate crossed the pre-review context thresholds in a way that invalidated the original rejection. `h4_gld_etf_flow_reversal_v0` is explicitly marked as a frequency/sample-size lead rather than an approved expert; `h4_gld_etf_flow_reversal_v1` confirms that broader sampling diluted the PF edge.

This means the current single-family state is not being treated as an artifact of an obvious low-frequency concentration-gate bias.

## Operational Consequence

The Phase 2 operating frame is single-edge:

```text
Execution-eligible first paper stream: breakout_retest only
Same-family variants: observer-only unless separately authorized later
Diversification uplift: none
Compounding: disabled through paper and any future micro pilot
Measured-cost floor: suspend if net expectancy after measured cost falls below +0.15R
```

The controlling operational document is:

- `xau-usd/xauusd-phase1/docs/PHASE2_SINGLE_EDGE_RISK_PLAN.md`

## Conditions To Reopen Diversification Research

The project may reopen diversification research only under one of these conditions:

1. A new data class is added, such as real-yield, DXY, Treasury-rate, futures-volume, options, or news-calendar data.
2. A new broker or venue data source materially changes the available microstructure evidence.
3. A new author proposes a mechanically distinct hypothesis family and pre-registers it before any result-producing run.
4. A future review explicitly asks for a new versioned candidate class and accepts the opportunity cost.

Any reopened idea must use a new versioned hypothesis, a new SHA256 registration, and the forward-looking gates in `docs/HYPOTHESIS_LOCKING.md`.

## Prohibited Interpretation

This finding must not be used to:

- tune rejected v0 hypotheses in place
- lower gates for old results
- count same-family candidates as diversified portfolio legs
- authorize Phase 2 or live trading before the measured-cost and soak gates pass

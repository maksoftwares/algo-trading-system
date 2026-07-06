# Forex Research Lane Status - 2026-07-03

Status: ACTIVE_RESEARCH_ONLY

## 2026-07-04 MT5 Addendum

The lane now has actual MT5 Strategy Tester evidence, separate from the July 3 Python/proxy screens. The best raw frequency-first lead is `EURUSD rsi_extreme_fade_m15_long_rr0p80`, tested from 2022-07-01 through 2026-07-02 with 1524 trades, CSV PF 1.1336, MT5 report PF about 1.12, and +$97.94 at fixed 0.01 lots. Both chronological halves are positive: 2022-2024 PF 1.0839 / +$33.28, and 2024-2026 PF 1.1924 / +$64.66.

A constrained tuning pass blocked only entry hours `1`, `7`, and `21`, selected from the raw robustness report. That tuned full run improved to 1309 trades, CSV PF 1.1705, MT5 report PF about 1.15, and +$108.84. Splits stayed positive but uneven: 2022-2024 PF 1.0875 / +$30.87, and 2024-2026 PF 1.2733 / +$77.97.

Status is `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE`, not demo-forward. The tuned edge is still small, only 27/49 active months are positive, and the worst tuned 250-trade rolling window is PF 0.8131 / -$25.78. See `forex-research/docs/FOREX_MT5_FREQUENCY_STATUS_2026_07_04.md`, `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_RR0P8_ROBUSTNESS_2026_07_04.md`, and `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md`.

Portability review then replayed the frozen tuned rule on GBPUSD and USDJPY. It failed both symbols, including the current 2024-2026 split. See `forex-research/docs/FOREX_MT5_FREQUENCY_PORTABILITY_REVIEW_2026_07_04.md`. Result: no additional Forex candidate, and the EURUSD lead remains an EURUSD-only watchlist clue rather than a broad Forex mean-reversion substrate.

## Boundary

This is a separate Forex research lane. No MT5 runtime, demo terminal, XAU EA, chart profile, preset, order, position, or broker-action file is touched by this lane.

## Data Inventory Snapshot

Initial local processed-bar inventory:

- EURUSD: Capital.com M5/M15/H1/H4/D1 through 2025-07-01; Dukascopy M5/M15/H1/H4/D1 through 2025-06-30; Pepperstone H1 only through 2022-01-01.
- USDJPY: Capital.com M5/M15/H1/H4/D1 through 2025-07-01; Dukascopy H1 only through 2024-12-31; Pepperstone H1 only through 2022-01-01.
- GBPUSD: no processed local bar data found in the Phase 0 processed-bar tree.

The first cost scan should therefore rank Capital.com EURUSD/USDJPY M5/M15/H1/H4 cells first because those cells have both clean OHLC and usable spread columns. Dukascopy EURUSD can be used as an OHLC robustness venue with a disclosed Capital.com cost proxy; it does not carry clean local spread fields in the derived processed bars.

## Prior Research To Respect

- Short-window M5 EUR/GBP continuation/reversion probes from 2026-06-14 were rejected for split instability.
- The 2026-06-16 profitable-hours note was a null result after lot normalization, de-duplication, and best-day removal.
- EURUSD H4 swing trend-continuation pullback v0 failed the standard bar on 2026-06-19, with negative net expectancy and high drawdown.
- Public FX ETF/proxy rotation candidates in the old XAU Phase 0 search were rejected first-pass.

## Current Work Items

1. Cost-geometry scan complete: `forex-research/outputs/reports/FOREX_COST_GEOMETRY_SCAN_2026_07_03.md`.
2. First candidate screen complete: `forex-research/outputs/reports/FOREX_FIRST_CANDIDATE_SCREEN_2026_07_03.md`.
3. Second-pass screen complete: `forex-research/outputs/reports/FOREX_SECOND_PASS_SCREEN_2026_07_03.md`.
4. Recent public Yahoo FX proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_RECENT_YAHOO_PROXY_ACQUISITION_2026_07_03.md` and `forex-research/outputs/reports/FOREX_RECENT_PROXY_STRESS_2026_07_03.md`.
5. Macro/rate screen complete: `forex-research/outputs/reports/FOREX_MACRO_RATE_SCREEN_2026_07_03.md`.
6. CNY/dollar pressure screen complete: `forex-research/outputs/reports/FOREX_CNY_DOLLAR_PRESSURE_SCREEN_2026_07_03.md`.
7. Calendar/session screen complete: `forex-research/outputs/reports/FOREX_CALENDAR_SESSION_SCREEN_2026_07_03.md`.
8. Global risk/credit screen complete: `forex-research/outputs/reports/FOREX_GLOBAL_RISK_CREDIT_SCREEN_2026_07_03.md`.
9. Commodity/dollar screen complete: `forex-research/outputs/reports/FOREX_COMMODITY_DOLLAR_SCREEN_2026_07_03.md`.
10. Recent commodity/dollar proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_RECENT_COMMODITY_DOLLAR_PROXY_ACQUISITION_2026_07_03.md` and `forex-research/outputs/reports/FOREX_COMMODITY_DOLLAR_RECENT_STRESS_2026_07_03.md`.
11. Rates/dollar screen plus recent proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_RATES_DOLLAR_SCREEN_2026_07_03.md`, `forex-research/outputs/reports/FOREX_RECENT_RATES_DOLLAR_PROXY_ACQUISITION_2026_07_03.md`, and `forex-research/outputs/reports/FOREX_RATES_DOLLAR_RECENT_STRESS_2026_07_03.md`.
12. Broker data refresh spec complete: `forex-research/docs/FOREX_BROKER_DATA_REFRESH_SPEC_2026_07_03.md`; it now requires terminal/account provenance and validator-recorded file SHA256s for broker-authoritative evidence.
13. Broker refresh validator complete: `forex-research/outputs/reports/FOREX_BROKER_REFRESH_VALIDATION_2026_07_03.md`; current status is `NO_REFRESH_FILES_FOUND`. The validator records raw/normalized SHA256s and provenance status when files exist. Frozen broker-refresh retest harness complete: `forex-research/outputs/reports/FOREX_BROKER_REFRESH_RETEST_2026_07_03.md`; current status is `NO_VALIDATED_REFRESH_FILES`.
14. External flow screen complete: `forex-research/outputs/reports/FOREX_EXTERNAL_FLOW_SCREEN_2026_07_03.md`.
15. VIX/VXV risk-regime screen complete: `forex-research/outputs/reports/FOREX_RISK_REGIME_SCREEN_2026_07_03.md`.
16. FX-cross rotation screen complete: `forex-research/outputs/reports/FOREX_FX_CROSS_SCREEN_2026_07_03.md`.
17. Equity-leadership screen plus recent proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_EQUITY_LEADERSHIP_SCREEN_2026_07_03.md`, `forex-research/outputs/reports/FOREX_RECENT_EQUITY_LEADERSHIP_PROXY_ACQUISITION_2026_07_03.md`, and `forex-research/outputs/reports/FOREX_EQUITY_LEADERSHIP_RECENT_STRESS_2026_07_03.md`.
18. Bond-volatility screen plus recent proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_BOND_VOL_SCREEN_2026_07_03.md`, `forex-research/outputs/reports/FOREX_RECENT_BOND_VOL_PROXY_ACQUISITION_2026_07_03.md`, and `forex-research/outputs/reports/FOREX_BOND_VOL_RECENT_STRESS_2026_07_03.md`.
19. Weekly-structure screen complete: `forex-research/outputs/reports/FOREX_WEEKLY_STRUCTURE_SCREEN_2026_07_03.md`.
20. Financial/liquidity screen complete: `forex-research/outputs/reports/FOREX_FINANCIAL_LIQUIDITY_SCREEN_2026_07_03.md`.
21. CFTC financial COT acquisition and positioning screen complete: `forex-research/outputs/reports/FOREX_COT_FINANCIAL_ACQUISITION_2026_07_03.md` and `forex-research/outputs/reports/FOREX_COT_POSITIONING_SCREEN_2026_07_03.md`.
22. Crypto-risk screen plus recent proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_CRYPTO_RISK_SCREEN_2026_07_03.md`, `forex-research/outputs/reports/FOREX_RECENT_CRYPTO_RISK_PROXY_ACQUISITION_2026_07_03.md`, and `forex-research/outputs/reports/FOREX_CRYPTO_RISK_RECENT_STRESS_2026_07_03.md`.
23. Sector-rotation screen plus recent proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_SECTOR_ROTATION_SCREEN_2026_07_03.md`, `forex-research/outputs/reports/FOREX_RECENT_SECTOR_ROTATION_PROXY_ACQUISITION_2026_07_03.md`, and `forex-research/outputs/reports/FOREX_SECTOR_ROTATION_RECENT_STRESS_2026_07_03.md`.
24. Currency-basket screen plus recent proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_CURRENCY_BASKET_SCREEN_2026_07_03.md`, `forex-research/outputs/reports/FOREX_RECENT_CURRENCY_BASKET_PROXY_ACQUISITION_2026_07_03.md`, and `forex-research/outputs/reports/FOREX_CURRENCY_BASKET_RECENT_STRESS_2026_07_03.md`.
25. Real-asset rotation screen plus recent proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_REAL_ASSET_ROTATION_SCREEN_2026_07_03.md`, `forex-research/outputs/reports/FOREX_RECENT_REAL_ASSET_ROTATION_PROXY_ACQUISITION_2026_07_03.md`, and `forex-research/outputs/reports/FOREX_REAL_ASSET_ROTATION_RECENT_STRESS_2026_07_03.md`.
26. Haven/liquidity screen plus recent proxy acquisition and stress test complete: `forex-research/outputs/reports/FOREX_HAVEN_LIQUIDITY_SCREEN_2026_07_03.md`, `forex-research/outputs/reports/FOREX_RECENT_HAVEN_LIQUIDITY_PROXY_ACQUISITION_2026_07_03.md`, and `forex-research/outputs/reports/FOREX_HAVEN_LIQUIDITY_RECENT_STRESS_2026_07_03.md`.
27. Treasury curve screen complete: `forex-research/outputs/reports/FOREX_TREASURY_CURVE_SCREEN_2026_07_03.md`.
28. Independent review response complete: `forex-research/docs/FOREX_RESEARCH_LANE_REVIEW_RESPONSE_2026_07_03.md`; methodology sound, no survivor, and refreshed broker data remains the next required evidence.
29. FX relative-strength screen complete: `forex-research/outputs/reports/FOREX_FX_RELATIVE_STRENGTH_SCREEN_2026_07_03.md`. Four EURUSD/USDJPY same-time USD-pressure catch-up / dispersion-reversal candidates were tested; all rejected historically and recent proxy stress left only tiny low-sample pockets.
30. Policy-uncertainty screen complete: `forex-research/outputs/reports/FOREX_POLICY_UNCERTAINTY_SCREEN_2026_07_03.md`. Four EURUSD/USDJPY lagged FRED USEPUINDXD policy-stress/relief candidates were tested; EURUSD H4 was positive but below gate at 367 trades, PF 1.0998, +17.57R, 23.85R DD, and recent proxy stress had only 4 trades. The other three candidates failed historically. Review note: the +1 day EPU availability lag is acceptable for rejection evidence only; any EPU watchlist/promotion attempt must be rerun with a 5-day availability lag and revision-robustness check.
31. Short-rate differential screen complete: `forex-research/outputs/reports/FOREX_SHORT_RATE_DIFFERENTIAL_SCREEN_2026_07_03.md`. Four Fed-vs-ECB / Fed-vs-Japan short-rate differential H4/H1 candidates were tested; all rejected historically. EURUSD H4 PF 0.9416 / -21.12R, EURUSD H1 PF 0.8242 / -130.49R, USDJPY H4 PF 0.6932 / -38.14R, USDJPY H1 PF 0.8801 / -25.28R.
32. No v0, v1, recent-proxy, macro/rate, CNY/dollar, calendar/session, weekly-structure, financial/liquidity, CFTC/COT positioning, global-risk/credit, commodity/dollar, commodity/dollar recent stress, real-asset rotation, real-asset rotation recent stress, haven/liquidity, haven/liquidity recent stress, rates/dollar, rates/dollar recent stress, Treasury curve, external-flow, risk-regime, FX-cross, FX relative-strength, policy-uncertainty, short-rate differential, equity-leadership, equity-leadership recent-stress, sector-rotation, sector-rotation recent-stress, currency-basket, currency-basket recent-stress, bond-volatility, bond-volatility recent-stress, crypto-risk, or crypto-risk recent-stress probe survived. Do not prepare or attach a Forex demo EA from this batch.
33. MT5 frequency-first scout complete: `forex-research/docs/FOREX_MT5_FREQUENCY_STATUS_2026_07_04.md` and `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_RR0P8_ROBUSTNESS_2026_07_04.md`. One EURUSD M15 RSI mean-reversion raw lead is watchlist-only.
34. Constrained MT5 tuning pass complete: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md`. Blocking hours `1`, `7`, and `21` improved the lead, but status remains `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE`; no demo-forward spec is prepared.
35. MT5 portability review complete: `forex-research/docs/FOREX_MT5_FREQUENCY_PORTABILITY_REVIEW_2026_07_04.md`. The frozen tuned rule failed on GBPUSD and USDJPY, including the current 2024-2026 split. No new Forex candidate.
36. Next allowed work: freeze EURUSD for genuinely fresh validation, supply/refresh authoritative Forex broker CSVs under the broker-refresh spec, or return to frequency-first discovery with a different Forex-native family. Do not symbol-tune from the failed portability result.

## Cost Geometry Result

Best clean spread-bearing local cells:

| Rank | Cell | Recent p95 cost_R | Read |
| ---: | --- | ---: | --- |
| 1 | USDJPY H4 Capital.com | 0.0206 | Best cost geometry. |
| 2 | EURUSD H4 Capital.com | 0.0282 | Clean and low cost, but first compression screen failed. |
| 3 | USDJPY H1 Capital.com | 0.0565 | Acceptable cost, but Tokyo failed-break screen failed. |
| 4 | EURUSD H1 Capital.com | 0.0573 | Acceptable cost, but London/Asia breakout screen failed. |

M15/M5 cells are materially more cost-fragile and were not prioritized for the first screen.

## First-Screen Verdict

| Candidate | Trades | PF | Net R | Max DD R | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| `eurusd_h4_compression_breakout_v0` | 82 | 0.9887 | -0.57 | 9.35 | REJECT_WEAK_NET_EDGE |
| `eurusd_h1_london_asia_range_breakout_v0` | 4518 | 0.9535 | -88.78 | 175.40 | REJECT_WEAK_NET_EDGE |
| `usdjpy_h4_trend_continuation_pullback_v0` | 917 | 1.0159 | +7.77 | 48.56 | REJECT_WEAK_NET_EDGE |
| `usdjpy_h1_tokyo_range_failed_break_v0` | 2328 | 0.8148 | -249.96 | 292.28 | REJECT_WEAK_NET_EDGE |

Diagnostic clue: USDJPY H4 long-only Asia/NY-morning trades had 366 trades, PF 1.2844, +48.81R, and 12.01R drawdown overall, but Pepperstone 2019-2021 was negative (50 trades, PF 0.7956, -6.34R). Treat this as a possible carry-regime research clue only, not a candidate survivor.

## Second-Pass Verdict

| Candidate | Trades | PF | Net R | Max DD R | Broker/era read | Verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `usdjpy_h4_carry_session_pullback_v1` | 466 | 1.0878 | +20.58 | 27.41 | Pepperstone -11.67R / PF 0.7124; pre-2022 -1.94R / PF 0.9817 | REJECT_SECOND_PASS_WEAK_NET_EDGE |
| `eurusd_h4_range_rejection_reversion_v0` | 372 | 0.9653 | -5.78 | 39.34 | Capital.com and Pepperstone negative; pre-2022 -10.01R / PF 0.9156 | REJECT_SECOND_PASS_WEAK_NET_EDGE |

Second-pass read: USDJPY H4 remains a structured carry-regime clue, but it is not a robust all-era/all-broker EA candidate. EURUSD H4 range rejection did not produce an edge. No demo-forward-test spec is prepared.

## Recent Proxy Stress Verdict

Public Yahoo H1 proxy bars were acquired for EURUSD, GBPUSD, and USDJPY from 2025-07-01 through 2026-07-03. This is current-market triage only, not broker-authoritative evidence; costs use historical Capital.com spread proxies where available.

| Candidate | Trades | PF | Net R | Gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_compression_breakout_v0` | 0 | n/a | 0.00 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `eurusd_h1_london_asia_range_breakout_v0` | 202 | 0.9660 | -2.78 | RECENT_PROXY_FAIL_WEAK_EDGE |
| `usdjpy_h4_trend_continuation_pullback_v0` | 50 | 0.7691 | -6.37 | RECENT_PROXY_FAIL_WEAK_EDGE |
| `usdjpy_h1_tokyo_range_failed_break_v0` | 171 | 0.7411 | -25.72 | RECENT_PROXY_FAIL_WEAK_EDGE |
| `usdjpy_h4_carry_session_pullback_v1` | 41 | 0.6647 | -8.11 | RECENT_PROXY_FAIL_WEAK_EDGE |
| `eurusd_h4_range_rejection_reversion_v0` | 17 | 1.1655 | +1.19 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: the recent proxy period specifically weakens the USDJPY carry/session clue. EURUSD H4 range rejection has a tiny positive recent pocket, but only 17 trades and prior broker/era evidence already failed, so it is not a survivor.

## Macro/Rate Screen Verdict

Lagged FRED real-yield (`DFII10`) and broad-dollar (`DTWEXBGS`) context was joined with a one-day availability lag to avoid same-day lookahead. Macro observations cover 2006-01-30 through 2026-05-21, available through 2026-05-22.

| Candidate | Historical trades | Historical PF | Historical net R | Recent proxy trades | Recent proxy PF | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `eurusd_h4_real_yield_dollar_pressure_reversal_v0` | 147 | 1.3882 | +23.47 | 2 | 0.7486 | REJECT_MACRO_RECENT_LOW_SAMPLE |
| `eurusd_h4_real_yield_dollar_pressure_followthrough_v0` | 582 | 0.9739 | -7.50 | 19 | 0.2844 | REJECT_MACRO_WEAK_HISTORICAL_EDGE |
| `usdjpy_h4_real_yield_dollar_pressure_followthrough_v0` | 407 | 0.8839 | -24.11 | 24 | 0.8047 | REJECT_MACRO_WEAK_HISTORICAL_EDGE |

Read: EURUSD H4 macro-pressure reversal is the first useful historical lead in this lane, but it has no current/recent confirmation and cannot become a demo-forward candidate without refreshed broker-authoritative 2026 data. The other macro/rate candidates are rejected outright.

## CNY/Dollar Pressure Screen Verdict

Lagged FRED USD/CNY (`DEXCHUS`) plus broad-dollar (`DTWEXBGS`) context was tested as a separate official macro signal class. DEXCHUS is yuan per USD, so positive USD/CNY change means CNY depreciation and dollar pressure. Observations were shifted one day before joining to H4 bars. Context rows cover 2006-01-30 through 2026-05-22, available through 2026-05-23.

| Candidate | Historical trades | Historical PF | Historical net R | Recent proxy trades | Recent proxy PF | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `eurusd_h4_cny_dollar_pressure_pullback_v0` | 569 | 0.9339 | -18.75 | 13 | 0.5126 | REJECT_CNY_WEAK_HISTORICAL_EDGE |
| `usdjpy_h4_cny_shock_yen_reversion_v0` | 73 | 0.6335 | -17.07 | 0 | n/a | REJECT_CNY_LOW_HISTORICAL_SAMPLE |

Read: the CNY/dollar pressure idea is rejected as a v0 screen. EURUSD had enough trades but negative aggregate edge and all broker splits were negative. USDJPY was low-sample and negative. No CNY/dollar survivor.

## Calendar/Session Screen Verdict

Price-only FX calendar/session hypotheses were tested so the lane was not dependent on stale external reference files. EURUSD tested NY-fix overextension reversion on H1; USDJPY tested month-turn carry pullbacks on H4. Both were stressed on recent public Yahoo proxy bars from 2025-07-01 through 2026-07-03.

| Candidate | Historical trades | Historical PF | Historical net R | Recent proxy trades | Recent proxy PF | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `eurusd_h1_ny_fix_overextension_reversion_v0` | 2427 | 0.8861 | -115.38 | 114 | 0.6064 | REJECT_CALENDAR_WEAK_HISTORICAL_EDGE |
| `usdjpy_h4_month_turn_carry_pullback_v0` | 305 | 0.8611 | -23.01 | 20 | 0.7400 | REJECT_CALENDAR_WEAK_HISTORICAL_EDGE |

Read: the calendar/session idea is rejected as a v0 screen. EURUSD was negative across all brokers and failed recent proxy stress badly. USDJPY had a small positive Pepperstone split only, but aggregate historical and recent proxy evidence were negative. No calendar/session survivor.

## Weekly Structure Screen Verdict

Price-only weekly FX structure was tested so this pass did not depend on stale external reference data. EURUSD tested early-week failed probes beyond the prior-week range and mid/late-week extension away from the weekly open. USDJPY tested prior-week expansion followed by H4 carry-trend pullbacks. All candidates were also stressed on recent public Yahoo FX proxy bars from 2025-07-01 through 2026-07-03.

| Candidate | Historical trades | Historical PF | Historical net R | Recent proxy trades | Recent proxy PF | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `eurusd_h4_weekly_liquidity_reversion_v0` | 82 | 0.6611 | -12.56 | 3 | 0.0000 | REJECT_WEEKLY_STRUCTURE_WEAK_HISTORICAL_EDGE |
| `usdjpy_h4_weekly_carry_continuation_v0` | 301 | 0.9569 | -6.73 | 19 | 0.6450 | REJECT_WEEKLY_STRUCTURE_WEAK_HISTORICAL_EDGE |
| `eurusd_h4_weekly_open_reversion_v0` | 753 | 0.8191 | -65.04 | 35 | 0.8172 | REJECT_WEEKLY_STRUCTURE_WEAK_HISTORICAL_EDGE |

Read: the weekly-structure idea is rejected as a v0 screen. The USDJPY weekly carry continuation variant had enough trades but negative aggregate edge, a 31.79R drawdown, and broker instability. EURUSD weekly fades were negative historically and weak in recent proxy stress. No weekly-structure survivor and no demo-forward spec.

## Financial/Liquidity Screen Verdict

Lagged FRED NFCI, ANFCI, and WALCL financial/liquidity context was tested as a separate broad dollar-liquidity signal class. Weekly observations were shifted seven days before joining to H4 bars. Context rows cover 2003-01-31 through 2026-06-03, available through 2026-06-10.

| Candidate | Historical trades | Historical PF | Historical net R | Recent proxy trades | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| `eurusd_h4_financial_liquidity_dollar_squeeze_pullback_v0` | 33 | 0.8054 | -3.68 | 0 | REJECT_FINANCIAL_LIQUIDITY_LOW_HISTORICAL_SAMPLE |
| `usdjpy_h4_financial_liquidity_carry_pullback_v0` | 16 | 1.0367 | +0.29 | 0 | REJECT_FINANCIAL_LIQUIDITY_LOW_HISTORICAL_SAMPLE |

Read: the financial/liquidity idea is rejected as a v0 screen. EURUSD was low-sample and negative; USDJPY was low-sample, weak, Pepperstone-negative, and top-winner-removal negative. No financial/liquidity survivor and no demo-forward spec.

## CFTC COT Positioning Screen Verdict

Official CFTC Traders in Financial Futures futures-only archives were acquired for 2016 through 2026. The screen used Euro FX and Japanese Yen leveraged-money positioning, with Japanese Yen futures inverted so positive spot-oriented net means USDJPY-bullish. Weekly reports were shifted seven days before joining to H4 bars. Context rows cover 2016-12-27 through 2026-06-23, available through 2026-06-30.

| Candidate | Historical trades | Historical PF | Historical net R | Recent proxy trades | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| `eurusd_h4_cot_lev_positioning_reversal_v0` | 54 | 0.7354 | -8.51 | 0 | REJECT_COT_LOW_HISTORICAL_SAMPLE |
| `usdjpy_h4_cot_yen_positioning_reversal_v0` | 11 | 1.3561 | +1.88 | 0 | REJECT_COT_LOW_HISTORICAL_SAMPLE |

Read: COT positioning is rejected as a v0 screen. EURUSD was negative and low-sample; USDJPY was superficially positive but only 11 trades across the historical replay and zero recent proxy trades. No COT survivor and no demo-forward spec.

## Global Risk/Credit Screen Verdict

Lagged daily EEM/SPY and HYG/IEF ETF ratios were tested as a separate global-risk and credit-appetite signal class. Positive changes indicate emerging-market and credit risk appetite; negative changes indicate defensive pressure. Observations were shifted one day before joining to H4 bars. Reference rows cover 2015-02-02 through 2025-06-30, available through 2025-07-01.

| Candidate | Trades | PF | Net R | Gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_global_risk_dollar_beta_pullback_v0` | 76 | 0.4461 | -28.02 | REJECT_GLOBAL_RISK_LOW_SAMPLE |
| `usdjpy_h4_global_risk_credit_pullback_v0` | 43 | 1.1682 | +3.50 | REJECT_GLOBAL_RISK_LOW_SAMPLE |

Read: EURUSD global-risk dollar-beta pullback is rejected outright. USDJPY global-risk/credit pullback is a tiny positive clue across historical broker splits, but only 43 deduped trades, about 4.9 trades/year, and stale reference data keep it below the research bar. No global-risk/credit survivor.

## Commodity/Dollar Screen Verdict

Lagged daily DBC/UUP and DBB/UUP ETF ratios were tested as a commodity-vs-dollar signal class. Positive changes indicate commodity strength versus the dollar; negative changes indicate commodity weakness versus the dollar. Observations were shifted one day before joining to H4 bars. Reference rows cover 2015-02-02 through 2025-06-30, available through 2025-07-01.

| Candidate | Trades | PF | Net R | Gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_commodity_dollar_reflation_pullback_v0` | 233 | 0.8911 | -13.44 | REJECT_COMMODITY_DOLLAR_WEAK_EDGE |
| `usdjpy_h4_commodity_dollar_reflation_pullback_v0` | 64 | 1.5453 | +14.45 | REJECT_COMMODITY_DOLLAR_LOW_SAMPLE |

Read: EURUSD commodity/dollar reflation pullback is rejected. USDJPY commodity/dollar reflation pullback was the cleanest positive clue in this external-reference batch, with all historical broker splits positive, but only 64 deduped trades, about 7.2 trades/year, and stale reference data kept it below the watchlist bar.

Recent public DBC/DBB/UUP ETF proxy files were acquired from Yahoo Finance through 2026-07-02 and joined with recent public FX proxy bars. This is recency triage only, not broker-authoritative evidence.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_commodity_dollar_reflation_pullback_v0` | 8 | 0.0000 | -8.18 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `usdjpy_h4_commodity_dollar_reflation_pullback_v0` | 6 | 0.8725 | -0.39 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: the historical USDJPY commodity/dollar clue was not confirmed by recent public ETF/FX proxy stress. It remains rejected and should not trigger broker-refresh work unless new independent evidence appears. No commodity/dollar survivor.

## Real-Asset Rotation Screen Verdict

Lagged daily USO/UUP, HG/GC, and SLV/GLD ETF/futures ratios were tested as a separate real-asset rotation signal class. Positive USO/UUP indicates oil strength versus the dollar; positive HG/GC and SLV/GLD indicate cyclical metal beta versus gold safe-haven strength. Observations were shifted one day before joining to H4 bars. Historical reference rows cover 2015-02-02 through 2025-06-30, available through 2025-07-01.

| Candidate | Historical trades | Historical PF | Historical net R | Historical gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_real_asset_reflation_pullback_v0` | 107 | 0.8384 | -10.15 | REJECT_REAL_ASSET_ROTATION_WEAK_EDGE |
| `usdjpy_h4_real_asset_carry_pullback_v0` | 112 | 1.1465 | +8.00 | REJECT_REAL_ASSET_ROTATION_WEAK_EDGE |

USDJPY was mildly positive in aggregate, but below the PF gate and broker-unstable: Capital.com and Dukascopy were positive while Pepperstone was negative.

Recent public USO/UUP, HG/GC, and SLV/GLD proxy files were acquired from Yahoo Finance through 2026-07-02/2026-07-03 and joined with recent public FX proxy bars. This is recency triage only, not broker-authoritative evidence.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Recent gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_real_asset_reflation_pullback_v0` | 0 | n/a | 0.00 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `usdjpy_h4_real_asset_carry_pullback_v0` | 6 | 0.8737 | -0.39 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: real-asset rotation is rejected as a v0 screen. EURUSD is historically negative. USDJPY is too weak historically and not confirmed by recent proxy stress. No real-asset rotation demo spec.

## Haven/Liquidity Screen Verdict

Lagged daily GLD, GDX/GLD, SPY/TLT, and XLU/XLK ETF context was tested as a separate safe-haven/liquidity signal class. Positive score indicates GLD strength, miner participation, equity weakness versus duration, and utilities leadership versus tech. Observations were shifted one day before joining to H4 bars. Historical reference rows cover 2015-02-02 through 2025-06-30, available through 2025-07-01.

| Candidate | Historical trades | Historical PF | Historical net R | Historical gate |
| --- | ---: | ---: | ---: | --- |
| `usdjpy_h4_haven_liquidity_yen_pullback_v0` | 129 | 0.8966 | -7.09 | REJECT_HAVEN_LIQUIDITY_WEAK_EDGE |
| `eurusd_h4_haven_liquidity_dollar_pullback_v0` | 193 | 0.9041 | -9.50 | REJECT_HAVEN_LIQUIDITY_WEAK_EDGE |

Recent public GLD, GDX/GLD, SPY/TLT, and XLU/XLK proxy files were acquired from Yahoo Finance through 2026-07-02 and joined with recent public FX proxy bars. This is recency triage only, not broker-authoritative evidence.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Recent gate |
| --- | ---: | ---: | ---: | --- |
| `usdjpy_h4_haven_liquidity_yen_pullback_v0` | 8 | 1.4047 | +1.25 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `eurusd_h4_haven_liquidity_dollar_pullback_v0` | 3 | 0.8986 | -0.15 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: haven/liquidity is rejected as a v0 screen. Both historical candidates have negative aggregate edge, and the recent proxy evidence is too sparse to rescue them. No haven/liquidity demo spec.

## Rates/Dollar Screen Verdict

Lagged daily TLT/UUP and TLT/SHY ETF ratios were tested as a rates-vs-dollar signal class. Positive changes indicate duration strength versus the dollar/cash; negative changes indicate yield/dollar pressure. Observations were shifted one day before joining to H4 bars. Historical reference rows cover 2015-02-02 through 2025-06-30, available through 2025-07-01.

| Candidate | Historical trades | Historical PF | Historical net R | Historical gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_rates_dollar_duration_pullback_v0` | 575 | 1.0664 | +18.16 | REJECT_RATES_DOLLAR_WEAK_EDGE |
| `usdjpy_h4_rates_dollar_yield_pullback_v0` | 452 | 0.8938 | -24.98 | REJECT_RATES_DOLLAR_WEAK_EDGE |
| `eurusd_h4_rates_dollar_yield_pressure_short_session_v1` | 295 | 1.2258 | +29.97 | RATES_DOLLAR_WATCHLIST_ONLY_NEEDS_RECENT_FLOW_AND_BROKER_REFRESH |

Recent public TLT/UUP and TLT/SHY ETF proxy files were acquired from Yahoo Finance through 2026-07-02 and joined with recent public FX proxy bars. This is recency triage only, not broker-authoritative evidence.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Recent gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_rates_dollar_duration_pullback_v0` | 13 | 2.2318 | +5.43 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `usdjpy_h4_rates_dollar_yield_pullback_v0` | 14 | 0.3616 | -6.02 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `eurusd_h4_rates_dollar_yield_pressure_short_session_v1` | 9 | 2.5920 | +4.89 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: EURUSD rates/dollar short-session v1 is the best new historical Forex clue in this pass, with all historical broker splits positive, PF 1.2258, and +29.97R. The recent proxy check is directionally positive but only 9 trades, so it is not a survivor and no demo-forward spec is prepared. It can be kept as a broker-refresh watchlist item only.

## Treasury Curve Screen Verdict

Lagged FRED DGS2, DGS10, and T10Y2Y Treasury curve context was tested as a separate official macro signal class. Front-end pressure means rising DGS2 with 2s10s flattening; bull-steepening relief means falling DGS2 with 2s10s steepening. Observations were shifted one day before joining to H4 bars. Context rows cover 1976-08-25 through 2026-05-22, available through 2026-05-23.

| Candidate | Historical trades | Historical PF | Historical net R | Recent proxy trades | Recent proxy PF | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `usdjpy_h4_treasury_curve_frontend_pullback_v0` | 83 | 0.8635 | -6.24 | 1 | 0.0000 | REJECT_TREASURY_CURVE_WEAK_HISTORICAL_EDGE |
| `eurusd_h4_treasury_curve_dollar_pressure_pullback_v0` | 68 | 0.9078 | -3.36 | 1 | 0.0000 | REJECT_TREASURY_CURVE_LOW_HISTORICAL_SAMPLE |

Read: Treasury curve v0 is rejected. USDJPY had enough trades but negative edge and top-winner-removed net R; EURUSD was low-sample and negative. Recent public FX proxy stress produced one losing trade per candidate, so there is no Treasury curve survivor and no demo-forward spec.

## Equity-Leadership Screen Verdict

Lagged daily ACWX/SPY, IWM/SPY, and XLF/XLU ETF ratios were tested as a separate equity-leadership signal class. ACWX/SPY approximates ex-US versus US equity leadership; IWM/SPY and XLF/XLU approximate US cyclical/risk leadership. Observations were shifted one day before joining to H4 bars. Historical reference rows cover 2015-02-02 through 2025-06-30, available through 2025-07-01.

| Candidate | Historical trades | Historical PF | Historical net R | Historical gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_exus_equity_leadership_pullback_v0` | 705 | 0.8534 | -54.47 | REJECT_EQUITY_LEADERSHIP_WEAK_EDGE |
| `usdjpy_h4_us_cyclical_leadership_pullback_v0` | 206 | 0.8661 | -14.47 | REJECT_EQUITY_LEADERSHIP_WEAK_EDGE |

Recent public ACWX/SPY, IWM/SPY, and XLF/XLU ETF proxy files were acquired from Yahoo Finance through 2026-07-02 and joined with recent public FX proxy bars. This is recency triage only, not broker-authoritative evidence.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Recent gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_exus_equity_leadership_pullback_v0` | 9 | 1.2051 | +0.90 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `usdjpy_h4_us_cyclical_leadership_pullback_v0` | 9 | 1.3548 | +1.09 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: equity-leadership v0 is rejected. Both candidates are historically negative across aggregate and broker splits. The recent proxy window is slightly positive but only 9 trades per candidate and top-winner-removal is negative, so there is no equity-leadership survivor and no demo-forward spec.

## Sector-Rotation Screen Verdict

Lagged daily XLY/XLP, QQQ/SPY, XLE/XLU, XLI/XLU, XME/SPY, and TIP/IEF ETF ratios were tested as a separate sector-rotation signal class. Positive XLY/XLP and QQQ/SPY indicate growth/risk appetite; positive XLE/XLU, XLI/XLU, and XME/SPY indicate cyclical/inflation leadership; positive TIP/IEF indicates inflation-linked bond leadership versus nominals. Observations were shifted one day before joining to H4 bars. Historical reference rows cover 2015-02-02 through 2025-06-30, available through 2025-07-01.

| Candidate | Historical trades | Historical PF | Historical net R | Historical gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_sector_growth_rotation_pullback_v0` | 293 | 1.1123 | +15.53 | REJECT_SECTOR_ROTATION_WEAK_EDGE |
| `usdjpy_h4_sector_cyclical_carry_pullback_v0` | 183 | 0.8338 | -17.51 | REJECT_SECTOR_ROTATION_WEAK_EDGE |

EURUSD was mildly positive in aggregate, but below the PF bar and unstable by broker: Dukascopy was positive, Capital.com was weak, and Pepperstone was negative.

Recent public sector ETF proxy files were acquired from Yahoo Finance through 2026-07-02 and joined with recent public FX proxy bars. This is recency triage only, not broker-authoritative evidence.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Recent gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_sector_growth_rotation_pullback_v0` | 12 | 1.2934 | +1.57 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `usdjpy_h4_sector_cyclical_carry_pullback_v0` | 4 | 0.4343 | -1.74 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: sector-rotation is rejected as a v0 screen. EURUSD is a mild clue only, not a survivor, because historical PF is below the gate, max drawdown sits around the limit, Pepperstone is negative, and recent proxy evidence is only 12 trades. USDJPY is rejected outright. No sector-rotation demo spec.

## Currency-Basket Screen Verdict

Lagged daily FXA/UUP, FXF/UUP, and CYB/UUP ETF ratios were tested as a Forex-native currency-basket signal class. Positive FXA/UUP and CYB/UUP indicate risk/non-USD currency strength versus UUP; positive FXF/UUP indicates Swiss-franc safe-haven strength versus UUP. Observations were shifted one day before joining to H4 bars. Historical reference rows cover 2015-02-02 through 2025-06-30, available through 2025-07-01.

| Candidate | Historical trades | Historical PF | Historical net R | Historical gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_currency_basket_dollar_pressure_pullback_v0` | 752 | 0.7531 | -103.29 | REJECT_CURRENCY_BASKET_WEAK_EDGE |
| `usdjpy_h4_safe_haven_currency_rotation_pullback_v0` | 32 | 2.5935 | +14.89 | REJECT_CURRENCY_BASKET_LOW_SAMPLE |

USDJPY had a superficially strong historical PF, but only 32 deduped trades across the full reference window, about 3.7 trades/year, so it is a low-sample clue only.

Recent public FXA/UUP and FXF/UUP ETF proxy files were acquired from Yahoo Finance through 2026-07-02 and joined with recent public FX proxy bars. Yahoo returned no usable recent CYB rows, so the EURUSD candidate that requires CYB/UUP was not stressed in the recent pass. This is recency triage only, not broker-authoritative evidence.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Recent gate |
| --- | ---: | ---: | ---: | --- |
| `usdjpy_h4_safe_haven_currency_rotation_pullback_v0` | 1 | 0.0000 | -1.03 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: currency-basket is rejected as a v0 screen. EURUSD is historically negative. USDJPY is low-sample historically and the recent proxy window produced only one losing trade. No currency-basket demo spec.

## Bond-Volatility Screen Verdict

Lagged daily MOVE bond-volatility proxy was tested as a separate Treasury-rate volatility signal class. Rising/elevated MOVE indicates rates-volatility stress; falling MOVE indicates rates-volatility calm/carry relief. Observations were shifted one day before joining to H4 bars. Historical reference rows cover 2015-03-03 through 2025-06-30, available through 2025-07-01.

| Candidate | Historical trades | Historical PF | Historical net R | Historical gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_bond_vol_dollar_stress_pullback_v0` | 359 | 0.9627 | -6.94 | REJECT_BOND_VOL_WEAK_EDGE |
| `usdjpy_h4_bond_vol_carry_pullback_v0` | 190 | 1.0819 | +7.24 | REJECT_BOND_VOL_WEAK_EDGE |
| `usdjpy_h4_bond_vol_asia_session_carry_relief_v1` | 125 | 2.0645 | +48.23 | BOND_VOL_WATCHLIST_ONLY_NEEDS_RECENT_FLOW_AND_BROKER_REFRESH |

The USDJPY Asia-session v1 historical clue had all historical broker splits positive: Capital.com +25.33R / PF 1.8665, Dukascopy +14.21R / PF 4.8883, Pepperstone +8.69R / PF 1.6994. This is a useful clue, not an approval, because reference data is stale and the v1 came from a session diagnostic.

Recent public MOVE proxy files were acquired from Yahoo Finance through 2026-06-26 and joined with recent public FX proxy bars. This is recency triage only, not broker-authoritative evidence; MOVE availability lags the current date by about a week.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Recent gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_bond_vol_dollar_stress_pullback_v0` | 10 | 1.6925 | +2.83 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `usdjpy_h4_bond_vol_carry_pullback_v0` | 11 | 1.1580 | +0.73 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `usdjpy_h4_bond_vol_asia_session_carry_relief_v1` | 7 | 0.3170 | -2.98 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: USDJPY bond-vol Asia-session v1 is the strongest historical Forex clue found so far, but the recent proxy stress is low-sample and negative for that exact v1. It is not a survivor, no demo-forward spec is prepared, and it should not trigger broker-refresh work unless new independent evidence appears.

## Crypto-Risk Screen Verdict

Lagged daily BTC-USD was tested as a separate crypto-risk appetite signal class. Strong positive BTC momentum approximates crypto/risk appetite; sharp negative BTC momentum approximates crypto-risk stress. Observations were shifted one day before joining to H4 bars. Historical reference rows cover 2015-03-02 through 2025-07-01, available through 2025-07-02.

| Candidate | Historical trades | Historical PF | Historical net R | Historical gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_btc_risk_beta_pullback_v0` | 253 | 0.8955 | -13.03 | REJECT_CRYPTO_RISK_WEAK_EDGE |
| `usdjpy_h4_btc_risk_carry_pullback_v0` | 122 | 0.9345 | -4.10 | REJECT_CRYPTO_RISK_WEAK_EDGE |

Recent public BTC-USD proxy files were acquired from Yahoo Finance through 2026-07-03 and joined with recent public FX proxy bars. This is recency triage only, not broker-authoritative evidence.

| Candidate | Recent proxy trades | Recent proxy PF | Recent proxy net R | Recent gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_btc_risk_beta_pullback_v0` | 3 | 1.1910 | +0.21 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |
| `usdjpy_h4_btc_risk_carry_pullback_v0` | 1 | 0.0000 | -1.02 | RECENT_PROXY_LOW_SAMPLE_CLUE_NOT_SURVIVOR |

Read: the BTC crypto-risk idea is rejected as a v0 screen. Both historical candidates have negative aggregate edge and top-winner-removed results, with broker instability. Recent proxy stress is too sparse to rescue the idea. No crypto-risk survivor and no demo-forward spec.

## External Flow Screen Verdict

Lagged daily currency ETF relative-flow proxies were tested as a separate intermarket signal class. FXE/UUP was used for EURUSD; FXY/UUP was inverted for USDJPY so positive flow aligned with USDJPY strength. ETF observations were shifted to the next UTC date before joining to H4 bars.

| Candidate | Trades | PF | Net R | Gate |
| --- | ---: | ---: | ---: | --- |
| `eurusd_h4_currency_etf_flow_pullback_v0` | 795 | 0.8008 | -87.77 | REJECT_EXTERNAL_FLOW_WEAK_EDGE |
| `usdjpy_h4_currency_etf_flow_pullback_v0` | 461 | 0.9474 | -12.53 | REJECT_EXTERNAL_FLOW_WEAK_EDGE |

Read: the external-flow idea is rejected as a v0 screen. USDJPY long-only/session pockets were not enough to overcome weak aggregate edge, drawdown, and broker instability, so no tuned promotion is prepared.

## Risk-Regime Screen Verdict

Lagged FRED VIX and VXV context was tested as a separate risk-regime input. Risk-off required rising/elevated VIX plus elevated VIX/VXV term structure; risk-on required falling VIX plus calmer term structure. Observations were shifted one day before joining to H4 bars.

| Candidate | Historical trades | Historical PF | Historical net R | Recent proxy trades | Recent proxy PF | Gate |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `eurusd_h4_vix_vxv_risk_regime_pullback_v0` | 306 | 0.8816 | -18.96 | 8 | 0.7813 | REJECT_RISK_REGIME_WEAK_HISTORICAL_EDGE |
| `usdjpy_h4_vix_vxv_risk_regime_pullback_v0` | 250 | 0.9814 | -2.39 | 6 | 0.4373 | REJECT_RISK_REGIME_WEAK_HISTORICAL_EDGE |

Read: the VIX/VXV risk-regime idea is rejected as a v0 screen. USDJPY was mildly positive on Capital.com and Dukascopy but failed aggregate, Pepperstone, drawdown, and recent proxy checks.

## FX-Cross Rotation Screen Verdict

Lagged daily public FX cross ratios were tested as a Forex-native reference input. AUDJPY/USDJPY was used as an AUD-vs-USD risk-rotation proxy for USDJPY; EURJPY/USDJPY was used as a euro-vs-dollar confirmation proxy for EURUSD. Observations were shifted one day before joining to H4 bars.

| Candidate | Trades | PF | Net R | Gate |
| --- | ---: | ---: | ---: | --- |
| `usdjpy_h4_audjpy_cross_risk_rotation_pullback_v0` | 140 | 1.0822 | +5.66 | REJECT_FX_CROSS_WEAK_EDGE |
| `eurusd_h4_eurjpy_cross_confirmation_pullback_v0` | 653 | 0.7325 | -99.43 | REJECT_FX_CROSS_WEAK_EDGE |

Read: USDJPY/AUDJPY-cross is a weak positive clue across all three historical venues, but PF 1.08, low frequency, and stale reference data keep it below the watchlist bar. EURUSD/EURJPY-cross is rejected outright.

## Broker Data Refresh Requirement

The independent review accepted the lane methodology and no-survivor conclusion, then expanded the broker-refresh target. The broker-refresh spec now requests Capital.com EURUSD and USDJPY H1/H4 data from 2022-01-01 through current, including measured/exported spread, as the priority-1 input for retesting the frozen EURUSD macro-pressure reversal, frozen EURUSD rates/dollar short-session, and frozen USDJPY bond-vol v0/v1 families. Secondary asks are independent EURUSD/USDJPY H1/H4 over the same window and GBPUSD only after the priority refresh.

Storage target: `forex-research/data/broker_refresh/raw/<broker>/<symbol>/<timeframe>/`.

Validation command: `python forex-research\scripts\run_forex_research_lane.py broker-refresh-validate`.

Current validation status: `NO_REFRESH_FILES_FOUND`; no broker-refresh CSVs are available yet.

Validation provenance rule: each refresh CSV should include terminal/account provenance by CSV columns or sidecar JSON. The validator records raw-file SHA256, normalized-file SHA256, provenance status, provenance source, terminal, account login/server, export time, timezone, and export method.

Frozen retest command: `python forex-research\scripts\run_forex_research_lane.py broker-refresh-retest`.

Current frozen retest status: `NO_VALIDATED_REFRESH_FILES`; the command is ready and confirmed to write an explicit no-data report until validated CSVs exist.

Even if a refreshed clue passes its gates, the next status is WATCHLIST_ONLY. A Forex demo-forward-test spec still requires a separate owner-approved step. No threshold/session edits are allowed during the refresh evaluation; any edited family restarts its evidence at zero.

## Staleness

Local processed Forex bars end around 2025-06/2025-07 while the current date is 2026-07-03. Any future survivor needs refreshed data or a forward-shadow period before a demo-forward-test spec.

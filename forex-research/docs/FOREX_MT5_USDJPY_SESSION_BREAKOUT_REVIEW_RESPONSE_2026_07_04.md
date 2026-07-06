# Independent Review Response - USDJPY MT5 Session Breakout Lead

Verdict: METHODOLOGY SOUND FOR WATCHLIST ONLY. Demo-forward remains blocked.

## Review Scope

This review checked the new USDJPY session-breakout EA, the actual MT5 report packets, the robustness report, and the review prompt.

Evidence reviewed:

- EA: `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`
- Full MT5 packet: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2022_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Pre-2022 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2022_2020_2022_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Full long-history extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Robustness packet: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`
- Portability packet: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PORTABILITY_FULL_2022_2026_SESSION_BREAKOUT_LONDON120_M15_BOTH.md`

Supplemental evidence added after the original review:

- Pre-2020 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Full 2018-2026 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2018_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`

## Runtime Isolation

PASS. The EA contains `CTrade` because it must place simulated Strategy Tester trades, but `OnInit()` fails unless `MQLInfoInteger(MQL_TESTER)` is true. The runner used `C:\MT5A1M5MomentumBacktest` with Strategy Tester settings and no live/demo chart attachment. The full-window startup log records `is_tester=true`.

No evidence shows live/demo terminal, XAU EA, order, chart, preset, or profile modification.

## Causality

PASS. The rule builds the 06:00-08:00 broker-server range from completed historical bars, then evaluates completed M15 signal bars during the 08:00-12:00 trade window. Entry occurs after the completed-bar decision through MT5 Strategy Tester execution. I found no lookahead in the range construction for this variant.

## Result Integrity

PASS for watchlist status.

Raw split results are coherent:

- 2022-2024: 243 trades, PF `1.5157`, +`$134.95`.
- 2024-2026: 278 trades, PF `1.2973`, +`$98.05`.
- Full 2022-2026: 521 trades, PF `1.3917`, +`$232.03`.

The combined trade CSV has both directions positive:

- Long: 295 trades, PF `1.4195`, +`$138.54`.
- Short: 226 trades, PF `1.3565`, +`$93.49`.

Robustness is credible but not final:

- Positive: every no-parameter-change yearly bucket is positive, `32/48` months positive, `119/201` weeks positive, `7/8` half-years positive, worst 250-trade rolling PF `1.1529`, top-30-winner removal PF `1.1164`.
- Negative: 2025 is thin at PF `1.0775`, worst 50-trade rolling PF `0.6492`, worst 100-trade rolling PF `0.9580`, top-50-winner removal PF `0.9758`, and sample size is only `521` trades.

Post-review long-history extension strengthens the watchlist case but does not change the verdict:

- Same-rule pre-2022 actual MT5 extension, 2020-01-01 to 2022-06-30: 338 trades, CSV PF `1.1580`, MT5 PF about `1.13`, +`$57.41`.
- Same-rule full actual MT5 extension, 2020-01-01 to 2026-07-02: 859 trades, CSV PF `1.3028`, MT5 PF about `1.28`, +`$289.44`.
- Entry-date yearly buckets are positive from 2020 through 2026.
- Long side remains strong over 2020-2026: 463 trades, PF `1.4045`, +`$198.86`.
- Short side is positive over 2020-2026: 396 trades, PF `1.1951`, +`$90.58`, but pre-2022 standalone shorts are slightly negative: 170 trades, PF `0.9856`, -`$2.91`.
- Weak half-years remain: 2021-H2 PF `0.9144`, -`$5.30`, and 2024-H1 PF `0.9350`, -`$4.26`.
- Longer-run worst 150-trade rolling window is negative at PF `0.9203`, -`$12.21`.
- Longer-run top-50-winner removal stays barely positive at PF `1.0157`, +`$15.00`, but top-75 and top-100 removal are negative.

Supplemental pre-2020 extension weakens the all-regime claim but does not automatically invalidate USDJPY-only watchlist status:

- Same-rule 2018-01-01 to 2019-12-31: 284 trades, CSV PF `0.9435`, MT5 PF about `0.94`, -`$15.09`.
- Same-rule 2018-01-01 to 2026-07-02: 1144 trades, CSV PF `1.2230`, MT5 PF about `1.21`, +`$273.09`.
- 2018 is flat at PF `1.0017`, +`$0.24`; 2019 is weak at PF `0.8718`, -`$16.59`.

Interpretation: the candidate remains a post-2020 USDJPY watchlist lead, not an all-regime session-breakout strategy.

## Portability

FAIL, but not a blocker to USDJPY-only watchlist status. The frozen same rule failed on EURUSD and GBPUSD:

- EURUSD: PF `0.8017`, -`$196.84`.
- GBPUSD: PF `0.9310`, -`$77.34`.

This means the candidate must be treated as USDJPY-specific, not as a pair-agnostic session-breakout system.

## Caveat

The full-window runner report says `Tuning attempted: true`. In this case, that flag comes from narrowing the validation rerun to the already-discovered M15 variant rather than changing the rule after discovery. The evidence packet now discloses that caveat. Future reports should distinguish "validation scope narrowed" from actual post-discovery tuning.

## Verdict

`USDJPY london120_break_m15` is a valid `WATCHLIST_ONLY_MT5_RAW_DIVERSIFICATION_LEAD`.

Demo-forward status must remain blocked because:

- The EA is new and needs one more reviewed pass before any spec drafting.
- The sample is now better at 859 trades over 2020-2026, but still shows weak regimes.
- The standalone 2018-2019 extension is negative, especially 2019.
- Short rolling windows still show adverse periods.
- Top-winner dependency remains material: 2022-2026 top-50 removal turns negative, and 2020-2026 top-75/top-100 removal is negative.
- EURUSD/GBPUSD portability failed.

Exact next allowed test: independent review of the long-history extension, then one pre-declared robustness step before tuning. The best next step is a no-parameter-change broker/export provenance check plus a recent-current rerun when refreshed broker-authoritative USDJPY M15 data is available. If using the existing MT5 tester data only, the next allowed research step is a constrained walk-forward split, preserving the same rule and reporting each year separately before any threshold/session/hour changes.

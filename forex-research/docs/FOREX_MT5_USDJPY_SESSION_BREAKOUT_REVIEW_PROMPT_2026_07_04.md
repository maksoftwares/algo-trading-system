# Independent Review Prompt - USDJPY MT5 Session Breakout Lead

Please independently review the new USDJPY session-breakout MT5 packet and give a direct verdict.

Question: is `USDJPY london120_break_m15` still a valid `WATCHLIST_ONLY` raw Forex diversification lead after the no-parameter-change 2020-2026 extension, and is it correctly blocked from demo-forward status pending further review?

Supplemental evidence added after the original prompt: the exact same rule was extended further back to 2018-2019. That standalone pre-2020 window failed, while the combined 2018-2026 window stayed positive. Please include this when judging whether the correct claim is post-2020 watchlist strength rather than all-regime robustness.

Scope to verify:

1. Actual MT5 evidence: confirm the reports came from MT5 Strategy Tester output, not a Python price simulator. Python only compiled/launched MT5 and parsed completed MT5 reports.
2. Runtime isolation: confirm the runner used isolated tester root `C:\MT5A1M5MomentumBacktest` and did not touch live/demo charts, presets, profiles, orders, positions, or XAU runtime terminals.
3. EA safety: review `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`; it contains `CTrade` for Strategy Tester execution, but `OnInit()` must fail when `!MQLInfoInteger(MQL_TESTER)`.
4. Hypothesis: USDJPY M15 session breakout, not EURUSD mean-reversion and not a gold-EA clone. It builds a 06:00-08:00 broker-server London range and trades breaks from 08:00 for four hours.
5. No post-discovery tuning: the raw both-direction rule is the lead. A long/short diagnostic was run, but no long-only or short-only promotion was made.
6. Split results:
   - 2022-07-01 to 2024-06-30: 243 trades, CSV PF 1.5157, MT5 PF about 1.49, +$134.95.
   - 2024-07-01 to 2026-07-02: 278 trades, CSV PF 1.2973, MT5 PF about 1.29, +$98.05.
   - 2022-07-01 to 2026-07-02: 521 trades, CSV PF 1.3917, MT5 PF about 1.38, +$232.03.
7. Direction read from the combined trade CSV:
   - Long: 295 trades, PF 1.4195, +$138.54.
   - Short: 226 trades, PF 1.3565, +$93.49.
8. No-parameter-change long-history extension:
   - Same rule, same symbol, same session, same direction mode, same RR, no hour/direction/filter tuning.
   - 2020-01-01 to 2022-06-30: 338 trades, CSV PF 1.1580, MT5 PF about 1.13, +$57.41.
   - 2020-01-01 to 2026-07-02: 859 trades, CSV PF 1.3028, MT5 PF about 1.28, +$289.44.
   - 2018-01-01 to 2019-12-31: 284 trades, CSV PF 0.9435, MT5 PF about 0.94, -$15.09.
   - 2018-01-01 to 2026-07-02: 1144 trades, CSV PF 1.2230, MT5 PF about 1.21, +$273.09.
   - Every entry-date calendar year from 2020 through 2026 is positive.
   - 2018 is flat at PF 1.0017 / +$0.24, while 2019 is weak at PF 0.8718 / -$16.59.
   - Full 2020-2026 direction read: long 463 trades, PF 1.4045, +$198.86; short 396 trades, PF 1.1951, +$90.58.
   - Caveats: pre-2022 shorts are slightly negative at 170 trades, PF 0.9856, -$2.91; 2021-H2 is PF 0.9144 / -$5.30; 2024-H1 is PF 0.9350 / -$4.26; worst 150-trade rolling window is PF 0.9203 / -$12.21; top-75/top-100-winner removal flips negative.
9. Robustness:
   - Positive: 32/48 active months positive; 7/8 half-years positive; worst 150-trade rolling window PF 1.0461 / +$10.02; worst 250-trade rolling window PF 1.1529 / +$47.40; top-30-winner removal PF 1.1164 / +$68.94.
   - Negative: worst 50-trade rolling window PF 0.6492 / -$19.37; worst 100-trade rolling window PF 0.9580 / -$6.27; top-50-winner removal PF 0.9758 / -$14.36.
10. Portability: frozen same rule failed on EURUSD and GBPUSD:
   - EURUSD full PF 0.8017 / -$196.84.
   - GBPUSD full PF 0.9310 / -$77.34.
11. Overclaim audit: status should be `WATCHLIST_ONLY_MT5_RAW_DIVERSIFICATION_LEAD`, no demo-forward spec yet, no approved-survivor claim.

Please answer with:

- Verdict: methodology sound or not.
- Whether watchlist-only raw-lead status is justified.
- Whether demo-forward status must remain blocked.
- Any blocker, caveat, or exact next test you require before any tuning or spec drafting.

Evidence files:

- Robustness report: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.json`
- Full MT5 report packet: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2022_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Pre-2022 MT5 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2022_2020_2022_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Full 2020-2026 MT5 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Pre-2020 2018-2019 MT5 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Full 2018-2026 MT5 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2018_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Portability packet: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PORTABILITY_FULL_2022_2026_SESSION_BREAKOUT_LONDON120_M15_BOTH.md`

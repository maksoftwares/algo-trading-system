# Review Prompt - Forex MT5 USDJPY London60 M30 BlockH7/11 Tuned Lead

Please independently review the new Forex MT5 evidence packet and answer whether the methodology supports `WATCHLIST_ONLY` status only, or whether even watchlist status should be downgraded.

## Scope

- Candidate: `USDJPY london60_break_m30_blockh7_11_rr1`
- EA: `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`
- Runner: `forex-research/scripts/run_forex_mt5_session_breakout_scout.py`
- Robustness packet: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_SESSION_BREAKOUT_TUNING_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_SESSION_BREAKOUT_TUNING_ROBUSTNESS_2026_07_04.json`

## What Was Done

The user asked to chase frequency first and then tune using actual MT5 Strategy Tester, not a Python backtester.

1. A fresh M30 session-breakout screen was run in actual MT5 across EURUSD/GBPUSD/USDJPY and four session variants.
2. The only raw M30 candidate that survived an unchanged 2020-2026 extension was `USDJPY london60_break_m30`.
3. RR/direction tuning was tested, but higher RR settings failed the recent 2024-2026 check.
4. Entry-hour diagnostics showed hours `7` and `11` were weak in both full and recent raw reads.
5. A small blocked-hour grid tested `7`, `11`, and `7,11`.
6. `blockh7_11_rr1` became the best current-regime tuned setting.
7. The exact tuned rule was replayed unchanged on EURUSD and GBPUSD for portability; both symbols failed in full and recent windows.
8. The exact tuned rule was extended back to 2018-2019 and failed that standalone pre-2020 window.

## Key Numbers

Raw M30 candidate:

- `USDJPY london60_break_m30`, 2024-07-01 to 2026-07-02: 480 trades, CSV PF `1.1206`, MT5 PF `1.12`, +`$70.14`.
- Same rule, 2020-01-01 to 2026-07-02: 1560 trades, CSV PF `1.1271`, MT5 PF `1.12`, +`$214.98`.

Best tuned candidate:

- `USDJPY london60_break_m30_blockh7_11_rr1`, 2020-01-01 to 2026-07-02: 1227 trades, CSV PF `1.2062`, MT5 PF `1.19`, +`$278.20`.
- Same tuned rule, 2024-07-01 to 2026-07-02: 384 trades, CSV PF `1.2057`, MT5 PF `1.20`, +`$94.87`.
- Same tuned rule, 2018-01-01 to 2019-12-31: 378 trades, CSV PF `0.9410`, MT5 PF `0.92`, -`$20.05`.
- Same tuned rule, 2018-01-01 to 2026-07-02: 1607 trades, CSV PF `1.1524`, MT5 PF `1.14`, +`$257.53`.

RR caveat:

- `blockh7_11_rr1p5` looks better on full history: 1113 trades, CSV PF `1.2182`, MT5 PF `1.21`, +`$324.16`.
- But it weakens on 2024-2026: 357 trades, CSV PF `1.0680`, MT5 PF `1.06`, +`$37.21`.
- Therefore RR `1.00` is the selected watchlist setting.

Robustness blockers:

- The blocked-hour filter is post-hoc from raw hour diagnostics.
- The standalone pre-2020 extension is negative: 378 trades, PF `0.9410`, -`$20.05`.
- 2019 is negative: 183 trades, PF `0.8602`, -`$20.81`.
- 2023 is negative: 186 trades, PF `0.9206`, -`$20.63`.
- 2023-H1 is materially negative: 91 trades, PF `0.6966`, -`$50.91`.
- Full 2020-2026 worst 250-trade rolling window is still negative: PF `0.9427`, -`$18.10`.
- Removing the top 50 winners flips full history slightly negative: PF `0.9987`, -`$1.70`.
- Removing the top 25 winners flips the recent window negative: PF `0.9236`, -`$35.24`.
- Recent long side is only barely positive: 221 trades, PF `1.0352`, +`$9.90`; recent edge is mostly short-side.
- Frozen same-rule portability failed:
  - EURUSD full 2020-2026: 1372 trades, PF `0.9992`, MT5 PF `0.99`, -`$1.47`.
  - GBPUSD full 2020-2026: 1340 trades, PF `0.9474`, MT5 PF `0.94`, -`$121.36`.
  - EURUSD recent 2024-2026: 412 trades, PF `0.9509`, MT5 PF `0.94`, -`$26.81`.
  - GBPUSD recent 2024-2026: 417 trades, PF `0.9967`, MT5 PF `0.99`, -`$2.04`.

## Review Questions

1. Does the actual-MT5 evidence support keeping this as `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_DIVERSIFICATION_LEAD`?
2. Is the hour filter too post-hoc to accept even as watchlist evidence?
3. Is RR `1.00` correctly preferred over RR `1.50` given the recent-window failure of RR `1.50`?
4. Do the rolling-window and top-winner failures block demo-forward promotion? My current answer is yes.
5. Given same-rule portability failed and pre-2020 is negative, is the next permissible test alternate-broker USDJPY only, stricter split/rolling validation, or rejection/downgrade?

## Required Verdict Format

Please return:

- Verdict: `WATCHLIST_ACCEPTED`, `WATCHLIST_REJECTED`, or `NEEDS_MORE_EVIDENCE`.
- Runtime/boundary finding.
- Methodology finding.
- Promotion decision: demo-forward should remain blocked unless you find a reason otherwise.
- Next allowed action.

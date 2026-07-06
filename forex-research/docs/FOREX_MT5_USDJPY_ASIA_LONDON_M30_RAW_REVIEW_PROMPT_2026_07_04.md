# Review Prompt - Forex MT5 USDJPY Asia-London M30 Raw Lead - 2026-07-04

Please independently review the new actual-MT5 raw frequency lead:

`USDJPY asia_london_break_m30`

Verdict I am asking you to check: `WATCHLIST_ONLY_MT5_RAW_FREQUENCY_DIVERSIFICATION_LEAD_NEEDS_REVIEW`. No demo-forward spec is prepared. No tuning has been applied to this candidate.

## Boundary

- Evidence source: actual MT5 Strategy Tester only, isolated root `C:\MT5A1M5MomentumBacktest`.
- EA: `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`.
- Runner: `forex-research/scripts/run_forex_mt5_session_breakout_scout.py`.
- Python only launched tester runs and parsed MT5 artifacts.
- No live/demo chart, order, position, preset, profile, XAU EA, or broker runtime state should have been touched.

## Candidate

- Symbol: `USDJPY`
- Variant: `asia_london_break_m30`
- Logic: broker-server Asia range from 00:00 to 06:00; trade M30 breakouts from 07:00 for four hours.
- Direction: both.
- RR: `1.00`.
- Lot: fixed `0.01`.
- Tuning: none.

## MT5 Results

| Window | Trades | CSV PF | MT5 PF | Parsed net | MT5 net | Win rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018-2019 | 207 | 1.1996 | 1.17 | $54.04 | $46.56 | 52.17% |
| 2020-2026 | 721 | 1.1564 | 1.14 | $179.97 | $161.13 | 52.70% |
| 2018-2026 | 928 | 1.1646 | 1.14 | $234.01 | $207.69 | 52.59% |

Direction split from full 2018-2026:

- Long: 500 trades, PF `1.2054`, +`$153.58`.
- Short: 428 trades, PF `1.1194`, +`$80.43`.

Year split:

- Positive years: 2018, 2019, 2020, 2022, 2024, 2025, 2026 partial.
- Negative years: 2021 PF `0.9798` / -`$3.33`; 2023 PF `0.8793` / -`$27.15`.
- Monthly activity: `58/102` active months positive.

Robustness:

- Worst 250-trade rolling window: PF `0.9142`, -`$30.37`.
- Worst 500-trade rolling window: PF `1.0948`, +`$64.52`.
- Top-10-winner removal: PF `1.1160`, +`$164.92`.
- Top-25-winner removal: PF `1.0522`, +`$74.28`.
- Top-50-winner removal: PF `0.9527`, -`$67.27`.

Comparison:

- Parallel `USDJPY london120_break_m30` diluted to 1297 trades, CSV PF `1.0748`, MT5 PF about `1.06`, +`$122.82` parsed / +`$95.79` MT5 over 2018-2026.
- `london120_break_m30` failed 2018-2019 at 311 trades, CSV PF `0.9691`, MT5 PF about `0.94`, -`$10.19` parsed.

## Questions

1. Confirm whether the runner/EA boundary is truly tester-only and cannot touch runtime.
2. Confirm whether this raw lead is causally clean: no lookahead, no post-discovery tuning, no data leakage.
3. Does the positive 2018-2019 and 2020-2026 split justify watchlist status despite low PF?
4. Do the negative 250-trade rolling window and top-50-winner removal block any tuning, or only block demo-forward promotion?
5. Is the next permissible step one pre-declared constrained tuning pass, alternate-broker USDJPY validation, or rejection/deprioritization?

## Evidence

- Robustness report: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.json`
- Full 2018-2026 MT5 aggregate: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2018_2026_USDJPY_M30_SESSION_RAW_NEXT_FREQ.md`
- Full 2020-2026 MT5 aggregate: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_USDJPY_M30_SESSION_RAW_NEXT_FREQ.md`
- Pre-2020 2018-2019 MT5 aggregate: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_USDJPY_M30_SESSION_RAW_NEXT_FREQ.md`

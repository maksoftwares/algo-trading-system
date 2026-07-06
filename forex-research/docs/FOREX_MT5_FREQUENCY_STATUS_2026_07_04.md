# Forex MT5 Frequency Status - 2026-07-04

Status: WATCHLIST_ONLY_MT5_RAW_AND_TUNED_FREQUENCY_EDGES_NO_DEMO

## Boundary

This pass used actual MT5 Strategy Tester runs from the isolated tester root `C:\MT5A1M5MomentumBacktest`. It did not attach an EA to any live/demo chart, did not place orders, and did not modify the existing XAU runtime terminals.

## What Changed

The research lane moved from Python-only/offline Forex screens to actual MT5 Strategy Tester evidence for frequency-first Forex candidates. Sparse H4 macro/proxy clues remain research-only, but the MT5 frequency scout found one real raw lead and one constrained tuned variant:

- Symbol: `EURUSD`
- Candidate: `rsi_extreme_fade_m15_long_rr0p80`
- EA: `forex-research/mt5/Experts/ForexMeanReversionScout.mq5`
- Runner: `forex-research/scripts/run_forex_mt5_mean_reversion_scout.py`
- Logic: M15 RSI extreme mean-reversion, long-only, RR 0.80, fixed 0.01 lots
- Decision status: watchlist only, not demo-forward

## Raw MT5 Result

| Window | Trades | PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022-07-01 to 2026-07-02 | 1524 | 1.1336 | $97.94 | 57.28% | $0.0643 |
| 2022-07-01 to 2024-06-30 | 785 | 1.0839 | $33.28 | 57.83% | $0.0424 |
| 2024-07-01 to 2026-07-02 | 739 | 1.1924 | $64.66 | 56.70% | $0.0875 |

MT5's own HTML report shows PF about `1.12` for the combined run. The CSV-derived PF is `1.1336`.

## Tuned MT5 Result

One constrained tuning pass was run after preserving the raw frequency substrate. The only change was blocking entry hours `1`, `7`, and `21`, selected from the raw untuned robustness report. No indicator threshold, stop, symbol, direction, or RR was changed.

| Window | Trades | PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2022-07-01 to 2026-07-02 | 1309 | 1.1705 | $108.84 | 58.14% | $0.0831 |
| 2022-07-01 to 2024-06-30 | 674 | 1.0875 | $30.87 | 58.01% | $0.0458 |
| 2024-07-01 to 2026-07-02 | 635 | 1.2733 | $77.97 | 58.27% | $0.1228 |

MT5's own HTML report shows PF about `1.15` for the tuned combined run. The CSV-derived PF is `1.1705`.

## Robustness Read

The tuned lead is legitimate enough to keep working:

- Both chronological halves are positive.
- Trade count is high enough for a frequency-first substrate.
- Top-winner removal does not destroy the edge: removing the top 10 winners leaves PF `1.1232` and +`$78.66`.
- Max trade-curve drawdown improves to `$32.72`, or `3.27%` of a `$1,000` fixed-lot reference balance.

The lead is not strong enough to promote:

- Full-window PF is only `1.1705`.
- Average trade is only `$0.0831` at 0.01 lots.
- Only `27/49` active months are positive.
- A 250-trade rolling window from 2025-07-07 to 2026-03-18 is still negative: PF `0.8131`, -`$25.78`.
- The older split barely improves over raw: PF `1.0875` versus raw PF `1.0839`.

## Evidence

- Combined MT5 report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2022_2026_M15_RSI_EXTREME_LONG_RR0P8.md`
- Robustness report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_RR0P8_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_RR0P8_ROBUSTNESS_2026_07_04.json`
- Tuned MT5 report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_TUNE_FULL_2022_2026_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8.md`
- Tuned robustness report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M15_RSI_EXTREME_LONG_BLOCKH1_7_21_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md`

## Next Allowed Work

Chase frequency first, then tune. One constrained tuning pass has now been done. The next step is independent review of the raw and tuned MT5 packets before any further tuning:

1. Confirm whether blocking hours `1`, `7`, and `21` is acceptable or too post-hoc.
2. Confirm whether PF `1.1705` with a weak 2022-2024 split is enough to keep researching.
3. If accepted, pre-declare the next robustness requirement before any spread/volatility guard is tested.

Any improvement remains `WATCHLIST_ONLY` until it survives split checks, rolling-window checks, top-winner removal, broker/account provenance review, and an owner-approved forward/demo-simulation step.

## M30 Frequency Follow-Up

After the M15 tuned lead was reviewed and portability failed, the lane continued exactly as requested: chase frequency first, then tune. A fresh M30 screen found a stronger EURUSD-only frequency packet:

- Raw candidate: `EURUSD rsi_bb_close_fade_m30_long_rr0p80`
- Tuned candidate: `EURUSD rsi_bb_close_fade_m30_long_blockh6_7_10_13_rr0p80`
- Signal timeframe: M30
- Execution chart: M5
- Direction/RR: long-only, RR `0.80`
- Tuning change: block entry hours `6,7,10,13`

Raw M30 baseline:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022-07-01 to 2024-06-30 | 585 | 1.0804 | 1.06 | $30.29 | 57.26% | $0.0518 |
| 2024-07-01 to 2026-07-02 | 560 | 1.1889 | 1.17 | $60.28 | 57.68% | $0.1076 |
| 2022-07-01 to 2026-07-02 | 1145 | 1.1301 | 1.11 | $90.57 | 57.55% | $0.0791 |

The hour-block tune was designed from the older 2022-2024 raw split, where the liquid weak hours were `6`, `7`, `10`, and `13`, then checked on the 2024-2026 validation split.

Tuned M30 result:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022-07-01 to 2024-06-30 | 405 | 1.1585 | 1.13 | $40.57 | 58.52% | $0.1002 |
| 2024-07-01 to 2026-07-02 | 426 | 1.3123 | 1.29 | $74.23 | 60.09% | $0.1742 |
| 2022-07-01 to 2026-07-02 | 831 | 1.2325 | 1.20 | $114.80 | 59.33% | $0.1381 |

Robustness read:

- Positive: both chronological halves are positive; current validation improved materially; `36/49` active months are positive; worst 250-trade rolling window is PF `0.9765` / -`$3.62`; worst 500-trade window is PF `1.1557` / +`$47.36`; top-10-winner removal remains PF `1.1641` / +`$80.99`.
- Blocking: worst 100-trade rolling window is PF `0.7357` / -`$20.81`; worst 150-trade rolling window is PF `0.8399` / -`$17.26`; removing the top 50 winners flips the run negative at PF `0.9735` / -`$13.10`; frozen portability failed on GBPUSD and USDJPY.

M30 portability failed:

- GBPUSD full 2022-2026: 791 trades, PF `0.9470`, -`$37.36`.
- GBPUSD current 2024-2026: 413 trades, PF `0.8537`, -`$52.84`.
- USDJPY full 2022-2026: 861 trades, PF `0.8367`, -`$125.30`.
- USDJPY current 2024-2026: 474 trades, PF `0.8128`, -`$78.50`.

Verdict: this is the strongest Forex MT5 packet so far, but it remains `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_EDGE`, not demo-forward and not a broad pair-agnostic Forex strategy.

M30 evidence:

- Robustness report: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M30_RSI_BB_LONG_BLOCKH6_7_10_13_RR0P8_TUNING_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_M30_RSI_BB_LONG_BLOCKH6_7_10_13_RR0P8_TUNING_ROBUSTNESS_2026_07_04.json`
- Review prompt: `forex-research/docs/FOREX_MT5_M30_FREQUENCY_LEAD_REVIEW_PROMPT_2026_07_04.md`

## USDJPY Session Breakout Diversification Lead

A fresh actual-MT5 session-breakout family was added after the EURUSD mean-reversion packets. This family is not a gold-EA clone and is not another EURUSD fade. It builds a broker-server London range and trades session breakouts.

- EA: `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`
- Raw candidate: `USDJPY london120_break_m15`
- Signal timeframe: M15
- Execution chart: M5
- Logic: 06:00-08:00 broker-server range, trade breaks from 08:00 for four hours
- Direction/RR: both directions, RR `1.00`
- Tuning: none after discovery; long/short split was diagnostic only
- Decision status: `WATCHLIST_ONLY_MT5_RAW_DIVERSIFICATION_LEAD`

Split results:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022-07-01 to 2024-06-30 | 243 | 1.5157 | 1.49 | $134.95 | 58.85% | $0.5553 |
| 2024-07-01 to 2026-07-02 | 278 | 1.2973 | 1.29 | $98.05 | 56.83% | $0.3527 |
| 2022-07-01 to 2026-07-02 | 521 | 1.3917 | 1.38 | $232.03 | 57.77% | $0.4454 |

No-parameter-change long-history extension:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2020-01-01 to 2022-06-30 | 338 | 1.1580 | 1.13 | $57.41 | 53.25% | $0.1699 |
| 2020-01-01 to 2026-07-02 | 859 | 1.3028 | 1.28 | $289.44 | 56.00% | $0.3369 |
| 2018-01-01 to 2019-12-31 | 284 | 0.9435 | 0.94 | -$15.09 | 46.13% | -$0.0531 |
| 2018-01-01 to 2026-07-02 | 1144 | 1.2230 | 1.21 | $273.09 | 53.50% | $0.2387 |

The 2020-2026 entry-date yearly split is positive in every bucket: 2020 PF `1.1398` / +`$26.03`, 2021 PF `1.1328` / +`$14.63`, 2022 PF `1.4904` / +`$66.93`, 2023 PF `1.6897` / +`$88.06`, 2024 PF `1.4703` / +`$60.64`, 2025 PF `1.0775` / +`$14.85`, and 2026 partial PF `1.2448` / +`$18.30`. The newly tested pre-2020 standalone window is negative: 2018 is flat at PF `1.0017` / +`$0.24`, while 2019 is weak at PF `0.8718` / -`$16.59`.

Direction read from the combined trade CSV:

- Long: 295 trades, PF `1.4195`, +`$138.54`.
- Short: 226 trades, PF `1.3565`, +`$93.49`.

Long-history direction read:

- 2020-2026 long: 463 trades, PF `1.4045`, +`$198.86`.
- 2020-2026 short: 396 trades, PF `1.1951`, +`$90.58`.
- Pre-2022 short side is the caveat: 170 trades, PF `0.9856`, -`$2.91`.

Robustness read:

- Positive: both original chronological halves are positive; every no-parameter-change yearly bucket from 2020 through 2026 is positive; both directions are positive over 2020-2026; `32/48` active months are positive in the original 2022-2026 packet; `11/13` long-history half-years are positive; worst 250-trade rolling window is PF `1.1529` / +`$47.40` in 2022-2026 and PF `1.0696` / +`$17.00` in 2020-2026; top-30-winner removal remains PF `1.1164` / +`$68.94` in 2022-2026 and PF `1.1169` / +`$111.74` in 2020-2026.
- Blocking: the standalone 2018-2019 pre-2020 extension is negative; 2019 is weak at PF `0.8718` / -`$16.59`; 2025 is thin at PF `1.0775` / +`$14.85`; weak half-years remain in 2021-H2 and 2024-H1; pre-2022 shorts are slightly negative; worst 50/100/150-trade rolling windows are negative in the long-history read; 2022-2026 top-50-winner removal flips negative and 2020-2026 top-75/top-100 removal flips negative; same-rule EURUSD/GBPUSD portability failed.

Portability failed:

- EURUSD full 2022-2026: 644 trades, PF `0.8017`, -`$196.84`.
- GBPUSD full 2022-2026: 624 trades, PF `0.9310`, -`$77.34`.

Verdict: this remains the strongest raw Forex diversification lead so far because it is raw, USDJPY-specific, session-breakout based, split-positive from 2020 onward, and still positive across the combined 2018-2026 MT5 extension. It is still `WATCHLIST_ONLY`, not demo-forward. The negative 2018-2019 standalone window means the correct claim is post-2020 watchlist strength, not all-regime robustness.

USDJPY session-breakout evidence:

- Robustness report: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.json`
- Pre-2022 MT5 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2022_2020_2022_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Full 2020-2026 MT5 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Pre-2020 2018-2019 MT5 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Full 2018-2026 MT5 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2018_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_BOTH.md`
- Review prompt: `forex-research/docs/FOREX_MT5_USDJPY_SESSION_BREAKOUT_REVIEW_PROMPT_2026_07_04.md`
- Review response: `forex-research/docs/FOREX_MT5_USDJPY_SESSION_BREAKOUT_REVIEW_RESPONSE_2026_07_04.md`

USDJPY review result: methodology sound for `WATCHLIST_ONLY_MT5_RAW_DIVERSIFICATION_LEAD`; demo-forward remains blocked. The review confirmed tester-only guard and no lookahead for this variant. The no-parameter-change 2020-2026 extension strengthens watchlist confidence, but it also exposes weak half-years, pre-2022 short-side weakness, negative short rolling windows, and larger top-winner dependency. It also notes the full-window runner's `Tuning attempted: true` flag is a validation-scope artifact from rerunning only the already-discovered M15 variant, not evidence of post-discovery parameter tuning.

## USDJPY M30 Frequency-First Tune

After the raw USDJPY M15 lead was reviewed, the lane continued the user's instruction: chase frequency first, then tune. A fresh actual-MT5 M30 session-breakout screen found one candidate that survived a no-parameter-change 2020-2026 stretch:

- Raw candidate: `USDJPY london60_break_m30`
- Tuned candidate: `USDJPY london60_break_m30_blockh7_11_rr1`
- EA: `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`
- Signal timeframe: M30
- Execution chart: M5
- Logic: 06:00-07:00 broker-server range, trade M30 breaks from 07:00 for four hours
- Tuning change: block broker-server entry hours `7` and `11`; RR remains `1.00`
- Decision status: `WATCHLIST_ONLY_MT5_TUNED_FREQUENCY_DIVERSIFICATION_LEAD`

Raw M30 stretch:

| Candidate | Window | Trades | CSV PF | MT5 PF | Net | Decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `USDJPY london60_break_m30` | 2024-07-01 to 2026-07-02 | 480 | 1.1206 | 1.12 | $70.14 | raw frequency candidate |
| `USDJPY london60_break_m30` | 2020-01-01 to 2026-07-02 | 1560 | 1.1271 | 1.12 | $214.98 | passed unchanged stretch |
| `GBPUSD asia_london_break_m30` | 2020-01-01 to 2026-07-02 | 1241 | 1.0007 | 0.99 | $1.69 | reject/deprioritize |
| `EURUSD ny60_break_m30` | 2020-01-01 to 2026-07-02 | 1336 | 0.9888 | 0.96 | -$23.37 | reject |

Best tuned M30 result:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2020-01-01 to 2026-07-02 | 1227 | 1.2062 | 1.19 | $278.20 | 54.44% | $0.2267 |
| 2024-07-01 to 2026-07-02 | 384 | 1.2057 | 1.20 | $94.87 | 54.43% | $0.2471 |
| 2018-01-01 to 2019-12-31 | 378 | 0.9410 | 0.92 | -$20.05 | 46.30% | -$0.0530 |
| 2018-01-01 to 2026-07-02 | 1607 | 1.1524 | 1.14 | $257.53 | 52.52% | $0.1603 |

RR tuning read:

- `blockh7_11_rr1p5` is better on full history at 1113 trades, CSV PF `1.2182`, MT5 PF `1.21`, +`$324.16`.
- It fails the current-regime preference test: 357 trades, CSV PF `1.0680`, MT5 PF `1.06`, +`$37.21` on 2024-2026.
- RR `1.00` is therefore the selected watchlist setting.

Robustness read:

- Positive: full 2020-2026 trade count is `1227`; recent 2024-2026 PF is not weaker than full history; long and short are both positive over full history; `6/7` calendar-year buckets are positive.
- Blocking: the hour filter is post-hoc; the standalone 2018-2019 pre-2020 extension is negative at 378 trades, PF `0.9410`, -`$20.05`; 2019 is negative at 183 trades, PF `0.8602`, -`$20.81`; 2023 is negative at 186 trades, PF `0.9206`, -`$20.63`; 2023-H1 is materially negative at 91 trades, PF `0.6966`, -`$50.91`; worst 50/100/150/250-trade rolling windows are negative in full history; removing the top 50 winners flips full history slightly negative; removing the top 25 winners flips the recent window negative; recent long side is only barely positive; frozen same-rule EURUSD/GBPUSD portability failed.

Frozen same-rule portability:

| Window | Symbol | Trades | CSV PF | MT5 PF | Net |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020-01-01 to 2026-07-02 | EURUSD | 1372 | 0.9992 | 0.99 | -$1.47 |
| 2020-01-01 to 2026-07-02 | GBPUSD | 1340 | 0.9474 | 0.94 | -$121.36 |
| 2024-07-01 to 2026-07-02 | EURUSD | 412 | 0.9509 | 0.94 | -$26.81 |
| 2024-07-01 to 2026-07-02 | GBPUSD | 417 | 0.9967 | 0.99 | -$2.04 |

Interpretation: this tuned M30 packet is USDJPY-specific, not a broad Forex session-breakout substrate.

Verdict: this is the best tuned high-frequency USDJPY session-breakout clue found so far, but it is still `WATCHLIST_ONLY`. It does not replace the raw `USDJPY london120_break_m15` as the cleanest raw diversification lead, and it does not justify a demo-forward spec. Its evidence is USDJPY-specific, post-2020-dependent, and weakened by failed portability.

M30 tuned USDJPY evidence:

- Robustness report: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_SESSION_BREAKOUT_TUNING_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_SESSION_BREAKOUT_TUNING_ROBUSTNESS_2026_07_04.json`
- Review prompt: `forex-research/docs/FOREX_MT5_USDJPY_LONDON60_M30_BLOCKH7_11_REVIEW_PROMPT_2026_07_04.md`
- Full portability replay: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PORTABILITY_FULL_2020_2026_USDJPY_LONDON60_M30_BLOCKH7_11_RR1.md`
- Recent portability replay: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PORTABILITY_RECENT_2024_2026_USDJPY_LONDON60_M30_BLOCKH7_11_RR1.md`
- Pre-2020 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_USDJPY_LONDON60_M30_BLOCKH7_11_RR1.md`
- Full 2018-2026 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2018_2026_USDJPY_LONDON60_M30_BLOCKH7_11_RR1.md`

## USDJPY Asia-London M30 Raw Frequency Lead

After rejecting the GBPUSD current-pocket extension and before any new tuning, the lane extended the remaining raw USDJPY M30 session-breakout pockets unchanged. The cleaner result is `USDJPY asia_london_break_m30`.

- Candidate: `USDJPY asia_london_break_m30`
- EA: `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`
- Runner: `forex-research/scripts/run_forex_mt5_session_breakout_scout.py`
- Logic: 00:00-06:00 broker-server Asia range, trade M30 breakouts from 07:00 for four hours
- Direction/RR: both directions, RR `1.00`
- Tuning: none
- Decision status: `WATCHLIST_ONLY_MT5_RAW_FREQUENCY_DIVERSIFICATION_LEAD_NEEDS_REVIEW`

Raw MT5 extension:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018-01-01 to 2019-12-31 | 207 | 1.1996 | 1.17 | $54.04 parsed / $46.56 MT5 | 52.17% | $0.2611 |
| 2020-01-01 to 2026-07-02 | 721 | 1.1564 | 1.14 | $179.97 parsed / $161.13 MT5 | 52.70% | $0.2496 |
| 2018-01-01 to 2026-07-02 | 928 | 1.1646 | 1.14 | $234.01 parsed / $207.69 MT5 | 52.59% | $0.2522 |

Direction read:

- Long: 500 trades, PF `1.2054`, +`$153.58`.
- Short: 428 trades, PF `1.1194`, +`$80.43`.

Year split:

- Positive: 2018, 2019, 2020, 2022, 2024, 2025, and 2026 partial.
- Negative: 2021 PF `0.9798` / -`$3.33`; 2023 PF `0.8793` / -`$27.15`.
- Monthly activity: `58/102` active months positive.

Robustness read:

- Positive: both pre-2020 and post-2020 windows are positive; full 2018-2026 has 928 trades; both directions are positive; worst 500-trade rolling window stays positive at PF `1.0948` / +`$64.52`; top-25-winner removal remains positive at PF `1.0522` / +`$74.28`.
- Blocking: headline PF is still only `1.1646` parsed / about `1.14` MT5; 2021 and 2023 are negative; only `58/102` active months are positive; worst 250-trade rolling window is negative at PF `0.9142` / -`$30.37`; top-50-winner removal flips negative at PF `0.9527` / -`$67.27`.

Comparison: parallel `USDJPY london120_break_m30` is weaker. It diluted to 1297 trades, CSV PF `1.0748`, MT5 PF about `1.06`, +`$122.82` parsed / +`$95.79` MT5 over 2018-2026 and failed 2018-2019 at 311 trades, CSV PF `0.9691`, MT5 PF about `0.94`, -`$10.19` parsed.

Verdict: this is the cleanest raw M30 USDJPY all-window frequency lead found so far, but it remains `WATCHLIST_ONLY`. It does not justify a demo-forward spec, and tuning should wait for review because rolling-window and top-winner-removal weakness are material.

USDJPY Asia-London M30 raw evidence:

- Robustness report: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.md`
- Robustness JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_SESSION_BREAKOUT_ROBUSTNESS_2026_07_04.json`
- Review prompt: `forex-research/docs/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_REVIEW_PROMPT_2026_07_04.md`
- Review response: `forex-research/docs/FOREX_MT5_USDJPY_ASIA_LONDON_M30_RAW_REVIEW_RESPONSE_2026_07_04.md`
- Full 2018-2026 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2018_2026_USDJPY_M30_SESSION_RAW_NEXT_FREQ.md`
- Full 2020-2026 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_USDJPY_M30_SESSION_RAW_NEXT_FREQ.md`
- Pre-2020 extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_USDJPY_M30_SESSION_RAW_NEXT_FREQ.md`

### Asia-London M30 Block-Hour Tune (Rejected)

The raw-lead review allowed exactly one constrained research tune:

- Design only on 2018-2023 raw trades.
- Block at most two worst entry hours with at least 50 design trades and PF below `0.95`.
- Keep symbol, range, timeframe, direction, RR, stop logic, and max trades/day unchanged.

Only broker-server entry hour `7` qualified: 192 design trades, PF `0.9443`, -`$16.80`. Hour `11` was worse but had only 43 trades, below the pre-declared threshold.

Raw versus tuned:

| Window | Version | Trades | CSV PF | MT5 PF | Parsed net | MT5 net | Win rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018-2023 design | raw | 676 | 1.1450 | n/a | $143.85 | n/a | 52.37% |
| 2018-2023 design | blockh7 | 627 | 1.1678 | 1.14 | $156.34 | $132.77 | 52.47% |
| 2024-2026 validation | raw | 252 | 1.2100 | n/a | $90.16 | n/a | 53.17% |
| 2024-2026 validation | blockh7 | 232 | 1.1750 | 1.16 | $70.37 | $66.16 | 52.59% |
| 2018-2026 full | raw | 928 | 1.1646 | n/a | $234.01 | n/a | 52.59% |
| 2018-2026 full | blockh7 | 859 | 1.1700 | 1.15 | $226.71 | $198.93 | 52.50% |

Tuned robustness still has the same blockers:

- Worst 100-trade rolling window: PF `0.6342`, -`$60.50`.
- Worst 250-trade rolling window: PF `0.9491`, -`$17.96`.
- Top-25-winner removal: PF `1.0481`, +`$64.16`.
- Top-50-winner removal flips negative: PF `0.9429`, -`$76.21`.

Verdict: `TUNE_REJECT_KEEP_RAW_WATCHLIST_PREFERRED`. The hour-7 block gives a trivial full-window PF improvement but reduces full-window net, reduces trade count, and reduces validation net. Keep the raw `USDJPY asia_london_break_m30` as the preferred watchlist form. No additional tuning and no demo-forward spec.

Asia-London M30 tuning evidence:

- Tuning robustness report: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_BLOCKH7_TUNING_ROBUSTNESS_2026_07_04.md`
- Tuning robustness JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_ASIA_LONDON_M30_BLOCKH7_TUNING_ROBUSTNESS_2026_07_04.json`
- Design replay: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_TUNE_DESIGN_2018_2023_USDJPY_ASIA_LONDON_M30_BLOCKH7.md`
- Validation replay: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_TUNE_VALIDATION_2024_2026_USDJPY_ASIA_LONDON_M30_BLOCKH7.md`
- Full replay: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_TUNE_FULL_2018_2026_USDJPY_ASIA_LONDON_M30_BLOCKH7.md`

## GBPUSD M30 Wick-Reclaim Extension (Rejected Before Tuning)

The next frequency-first check extended a current-window GBPUSD mean-reversion pocket before spending any tuning budget.

- Candidate: `GBPUSD bb_wick_reclaim_m30_rr0p80`
- EA: `forex-research/mt5/Experts/ForexMeanReversionScout.mq5`
- Runner: `forex-research/scripts/run_forex_mt5_mean_reversion_scout.py`
- Reason tested: the 2024-2026 current screen had 156 trades, CSV PF `1.1731`, MT5 PF about `1.15`, and +`$23.70`
- Tuning: none; fixed candidate replay only

No-parameter-change MT5 extension:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2020-01-01 to 2026-07-02 | 498 | 1.0717 | 1.06 | $35.05 parsed / $27.67 MT5 | 55.82% | $0.0704 |
| 2018-01-01 to 2019-12-31 | 157 | 0.9697 | 0.96 | -$5.22 parsed / -$7.54 MT5 | 53.50% | -$0.0332 |

Direction read:

- 2020-2026 long: 241 trades, PF `1.1164`, +`$27.43`.
- 2020-2026 short: 257 trades, PF `1.0301`, +`$7.62`.
- 2018-2019 long: 81 trades, PF `0.8190`, -`$17.28`.
- 2018-2019 short: 76 trades, PF `1.1574`, +`$12.06`.

Verdict: `REJECT_MT5_THIN_EDGE_NO_TUNING`. Frequency exists, but the full 2020-2026 edge is too thin and the standalone 2018-2019 extension is negative. Do not tune this pocket unless every stronger family is exhausted and the tuning plan is pre-declared.

GBPUSD M30 wick-reclaim evidence:

- Full 2020-2026 extension: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_GBPUSD_BB_WICK_RECLAIM_M30_RAW_EDGE.md`
- Full 2020-2026 JSON: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_GBPUSD_BB_WICK_RECLAIM_M30_RAW_EDGE.json`
- Pre-2020 extension: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_GBPUSD_BB_WICK_RECLAIM_M30_RAW_EDGE.md`
- Pre-2020 JSON: `forex-research/outputs/reports/mt5_backtests/mean_reversion_scout/FOREX_MT5_FREQUENCY_SCOUT_PRE2020_2018_2019_GBPUSD_BB_WICK_RECLAIM_M30_RAW_EDGE.json`

## M15 Session-Breakout Raw Frequency Sweep

Following the instruction to chase frequency before tuning, a broad raw M15 session-breakout sweep was run with no blocked hours, no RR changes, no direction split, and no symbol-specific tuning.

- Symbols: `EURUSD`, `GBPUSD`, `USDJPY`
- Variants: `london60_break`, `london120_break`, `ny60_break`, `asia_london_break`
- Window: 2024-07-01 to 2026-07-02
- Signal timeframe: M15
- Direction/RR: both directions, RR `1.00`

Top current-window rows:

| Candidate | Trades | CSV PF | MT5 PF | Net | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| `USDJPY london120_break_m15` | 278 | 1.2973 | 1.29 | $98.05 | known raw USDJPY lead current split |
| `EURUSD ny60_break_m15` | 490 | 1.0706 | 1.04 | $45.83 | new thin pocket, fixed extension required |
| `USDJPY london60_break_m15` | 540 | 1.0161 | 1.01 | $10.25 | too thin |
| `GBPUSD asia_london_break_m15` | 404 | 1.0054 | 0.99 | $3.94 | too thin |

The only new pocket with enough frequency to check was `EURUSD ny60_break_m15`. It failed the no-parameter-change 2020-2026 extension:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-07-01 to 2026-07-02 | 490 | 1.0706 | 1.04 | $45.83 | 50.82% | $0.0935 |
| 2020-01-01 to 2026-07-02 | 1532 | 0.9654 | 0.94 | -$79.73 | 49.54% | -$0.0520 |

Verdict: `REJECT_MT5_M15_SESSION_BREAKOUT_EXTENSION_FAIL_NO_TUNING`. The broad M15 sweep adds no new survivor. It mainly reconfirms that `USDJPY london120_break_m15` remains the cleanest raw M15 session-breakout lead, while the new EURUSD NY pocket is not worth tuning.

M15 raw sweep evidence:

- Current sweep: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_SESSION_BREAKOUT_M15_RAW_FREQ_SWEEP.md`
- Current sweep JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_SESSION_BREAKOUT_M15_RAW_FREQ_SWEEP.json`
- EURUSD fixed extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_EURUSD_NY60_M15_RAW_FREQ_EXTENSION.md`
- EURUSD fixed extension JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_EURUSD_NY60_M15_RAW_FREQ_EXTENSION.json`

## Extra-Major M15 Session-Breakout Raw Sweep

The isolated tester root had tick/history traces for additional major pairs, so a second raw M15 session-breakout sweep was run across `AUDUSD`, `NZDUSD`, `USDCAD`, and `USDCHF`.

- Window: 2024-07-01 to 2026-07-02
- Variants: `london60_break`, `london120_break`, `ny60_break`, `asia_london_break`
- Signal timeframe: M15
- Direction/RR: both directions, RR `1.00`
- Tuning: none

Top current-window rows:

| Candidate | Trades | CSV PF | MT5 PF | Net | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| `USDCHF asia_london_break_m15` | 365 | 1.1332 | 1.12 | $71.43 | new raw pocket, fixed extension required |
| `USDCHF london60_break_m15` | 572 | 0.9440 | 0.94 | -$36.98 | reject |
| `USDCAD ny60_break_m15` | 472 | 0.9411 | 0.91 | -$29.09 | reject |
| `AUDUSD ny60_break_m15` | 542 | 0.9202 | 0.90 | -$45.99 | reject |
| `NZDUSD ny60_break_m15` | 540 | 0.8282 | 0.81 | -$93.16 | reject |

The only new extra-major pocket, `USDCHF asia_london_break_m15`, failed the fixed 2020-2026 extension:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Avg/trade |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-07-01 to 2026-07-02 | 365 | 1.1332 | 1.12 | $71.43 | 52.88% | $0.1957 |
| 2020-01-01 to 2026-07-02 | 1432 | 0.9595 | 0.95 | -$87.14 | 48.39% | -$0.0609 |

Verdict: `REJECT_MT5_EXTRA_MAJOR_M15_EXTENSION_FAIL_NO_TUNING`. The extra-major current sweep produced no robust raw candidate and no demo-forward spec.

Extra-major M15 evidence:

- Current sweep: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_EXTRA_MAJORS_SESSION_BREAKOUT_M15_RAW_FREQ_SWEEP.md`
- Current sweep JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_CURRENT_2024_2026_EXTRA_MAJORS_SESSION_BREAKOUT_M15_RAW_FREQ_SWEEP.json`
- USDCHF fixed extension: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_USDCHF_ASIA_LONDON_M15_RAW_FREQ_EXTENSION.md`
- USDCHF fixed extension JSON: `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_FREQUENCY_SCOUT_FULL_2020_2026_USDCHF_ASIA_LONDON_M15_RAW_FREQ_EXTENSION.json`

## USDJPY Bond-Vol MT5 Cross-Check

This is not a frequency-first lead. It is an actual-MT5 cross-check of the frozen sparse H4 bond-volatility clue that earlier Python/proxy research had left as watchlist-only.

- Candidate: `usdjpy_h4_bond_vol_asia_session_carry_relief_v1`
- EA: `forex-research/mt5/Experts/ForexBondVolAsiaCarryReliefV1.mq5`
- Runner: `forex-research/scripts/run_forex_mt5_bond_vol_backtest.py`
- Context: combined MOVE reference/recent proxy, lagged to next UTC date, `2804` context rows, available through `2026-06-27T00:00:00Z`
- Boundary: actual MT5 Strategy Tester in isolated root `C:\MT5A1M5MomentumBacktest`; Python only prepared context, launched MT5, and parsed reports

Actual MT5 frozen run:

| Window | Trades | CSV PF | MT5 PF | Net | Win rate | Equity DD Max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2018-01-01 to 2026-06-27 | 79 | 1.7010 | 1.68 | $79.04 parsed / $77.37 MT5 | 55.70% | $37.68 |

Year splits from actual MT5 trades:

| Year | Trades | PF | Net |
| --- | ---: | ---: | ---: |
| 2018 | 14 | 2.6660 | $24.14 |
| 2019 | 14 | 1.5637 | $10.67 |
| 2020 | 11 | 0.7278 | -$7.35 |
| 2021 | 3 | 0.0000 | -$4.84 |
| 2022 | 4 | 0.5475 | -$4.48 |
| 2023 | 11 | 13.0963 | $48.99 |
| 2024 | 9 | 7.4201 | $24.91 |
| 2025 | 7 | 0.7838 | -$3.53 |
| 2026 partial | 6 | 0.2901 | -$9.47 |

Robustness read:

- Positive: actual MT5 confirms the frozen clue can produce a positive long-history run; both long and short directions are positive in the full run; top-5-winner removal remains positive at 74 trades, PF `1.2974`, +`$33.53`.
- Blocking: only `79` trades across more than eight years; 2020-2022 is negative; 2025-2026 is negative at 13 trades, PF `0.5618`, -`$13.00`; removing the top 10 winners leaves 69 trades, PF `1.0003`, +`$0.03`; this is far below the frequency-first standard.

Verdict: `WATCHLIST_ONLY_MT5_GATE_PASS_NO_DEMO_APPROVAL`, but not a tuning candidate. The MT5 result keeps the bond-vol clue alive for review, not deployment. No demo-forward spec.

Bond-vol MT5 evidence:

- MT5 report: `forex-research/outputs/reports/mt5_backtests/bond_vol_scout/FOREX_MT5_BOND_VOL_BACKTEST_FULL_2018_2026_BOND_VOL_V1_MT5.md`
- MT5 JSON: `forex-research/outputs/reports/mt5_backtests/bond_vol_scout/FOREX_MT5_BOND_VOL_BACKTEST_FULL_2018_2026_BOND_VOL_V1_MT5.json`
- Review prompt: `forex-research/docs/FOREX_MT5_BOND_VOL_REVIEW_PROMPT_2026_07_04.md`

## Review Result

Review response: `forex-research/docs/FOREX_MT5_FREQUENCY_LEAD_REVIEW_RESPONSE_2026_07_04.md`.

Review confirmed the current watchlist-only status and found no blocker to keeping the lead under research. It also confirmed three demo-forward blockers: the hour filter is post-hoc relative to the full raw sample, the edge remains thin, and the tuned 250-trade rolling weakness remains negative.

## Portability Result

Portability review: `forex-research/docs/FOREX_MT5_FREQUENCY_PORTABILITY_REVIEW_2026_07_04.md`.

The tuned EURUSD rule was replayed unchanged on GBPUSD and USDJPY. Portability failed:

- GBPUSD full 2022-2026: 1380 trades, PF `0.9597`, -`$38.75`.
- GBPUSD current 2024-2026: 704 trades, PF `0.8959`, -`$48.15`.
- USDJPY full 2022-2026: 1465 trades, PF `0.8838`, -`$122.40`.
- USDJPY current 2024-2026: 758 trades, PF `0.8128`, -`$102.23`.

This lowers promotion confidence. The lead remains an EURUSD-only watchlist clue, not a broad Forex mean-reversion substrate and not a portfolio-diversifying strategy yet.

# Forex USDJPY London120 D1 ATR20 Current Decision Packet

Date: 2026-07-04

Status: **WATCHLIST_V1_CONTINUE / NO DEMO SPEC**

Scope: Forex only. No current MT5 demo terminal, running XAU EA, chart, preset, order, or broker runtime state was touched.

## Candidate

- Symbol: `USDJPY`
- Base variant: `london120_break_m15`
- Watchlist-v1 variant: `london120_break_m15_d1atr20_guard`
- EA: `forex-research/mt5/Experts/ForexSessionBreakoutScout.mq5`
- Logic: broker-server `06:00-08:00` range, M15 breakout decisions from `08:00` for four hours, both directions, RR `1.00`, fixed `0.01` lot.
- Added v1 guard: require session range / previous completed D1 ATR(14) `>= 0.20`.

## What Improved

The one predeclared structural guard improved the main MT5 recency concern without a sweep:

| Evidence | Trades | PF | Net |
| --- | ---: | ---: | ---: |
| MT5 v0 full 2018-2026 | 1144 | 1.2231 | +$273.16 |
| MT5 v1 full 2018-2026 | 865 | 1.2551 | +$253.17 |
| MT5 v0 recent 2025-2026 | 218 | 1.1247 | +$33.20 |
| MT5 v1 recent 2025-2026 | 169 | 1.2114 | +$44.76 |
| MT5 v0 trailing 12M after +0.5 pip | 145 | 1.1188 | +$18.85 |
| MT5 v1 trailing 12M after +0.5 pip | 116 | 1.1527 | +$20.84 |

This is real progress. The v1 guard passes its own predeclared MT5 watchlist-v1 acceptance checks.

## What Got Worse Or Stayed Weak

The same v1 rule still has material robustness problems:

- 2019 remains bad: 91 trades, PF `0.7244`, net `-$26.84`.
- Worst 250-trade full-history rolling window is slightly negative: PF `0.9782`, net `-$5.99`.
- Top-50-winner removal flips negative: PF `0.9792`, net `-$20.60`.
- Full-history net is lower than v0 because the guard filters 279 trades.

## Dukascopy Alternate-Price-History Check

Public Dukascopy M5 bid candles were acquired separately from MT5 and replayed offline with the frozen v1 rule:

| Dukascopy bid-M5 replay | Trades | PF | Net |
| --- | ---: | ---: | ---: |
| Full available 2018-2026 | 1038 | 1.2164 | +$241.33 |
| Full available after +0.5 pip | 1038 | 1.1758 | +$199.39 |
| From 2020 | 789 | 1.2514 | +$225.82 |
| From 2022 | 528 | 1.2165 | +$144.08 |
| Trailing 12M after +0.5 pip | 119 | 1.1971 | +$24.72 |
| Recent 2025-2026 | 180 | 0.9275 | -$17.22 |
| Recent 2025-2026 after +0.5 pip | 180 | 0.9040 | -$23.11 |

Read: the long-window structure is not purely one-broker noise, but the recent alternate-history slice fails. This keeps the owner's recency-as-gate blocker alive.

## Ask-Side Attempt

Ask-side Dukascopy acquisition via `dukascopy-node` failed for M5 and tick probes. The blocker is documented in:

```text
forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_DUKASCOPY_USDJPY_ASK_ACQUISITION_ATTEMPT_2026_07_04.md
```

This does not make the candidate look better. The bid-only recent 2025-2026 replay is already negative before ask-side costs.

## Direct Dukascopy Bid/Ask Tick Replay

After the `dukascopy-node` wrapper failed on ask/tick acquisition, a direct Dukascopy `.bi5` tick downloader was added outside MT5 runtime:

```text
forex-research/scripts/replay_usdjpy_london120_d1atr20_on_dukascopy_ticks.py
```

It keeps the frozen v1 signal rule unchanged, uses Dukascopy bid ticks aggregated to M5/M15/D1 for signals, then executes with bid/ask ticks:

- Buy entry at ask, buy exits on bid.
- Sell entry at bid, sell exits on ask.
- No parameter, threshold, hour, direction, RR, or session change.

Recent direct-tick result:

| Direct Dukascopy bid/ask ticks | Trades | PF | Net |
| --- | ---: | ---: | ---: |
| 2025-01-01 through 2026-06-27 | 177 | 0.9578 | -$9.64 |
| Same plus +0.5 pip extra stress | 177 | 0.9333 | -$15.43 |

Direction and year split:

| Slice | Trades | PF | Net |
| --- | ---: | ---: | ---: |
| Long | 97 | 0.8611 | -$18.08 |
| Short | 80 | 1.0860 | +$8.44 |
| 2025 | 117 | 0.8366 | -$28.26 |
| 2026 partial | 60 | 1.3368 | +$18.62 |

Read: this closes the previous "wrapper blocked ask/tick" gap for practical research purposes. The stricter bid/ask tick replay still fails the owner-priority recent window, especially 2025. It remains research-only, not an MT5 custom-symbol Strategy Tester run, but it strengthens the **NO DEMO SPEC** decision.

Artifacts:

```text
forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_DIRECT_TICK_BIDASK_REPLAY_RECENT_2025_2026_2026_07_04.md
forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_DIRECT_TICK_BIDASK_REPLAY_RECENT_2025_2026_2026_07_04.json
forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_DIRECT_TICK_BIDASK_TRADES_RECENT_2025_2026_2026_07_04.csv
```

## Current Verdict

```text
WATCHLIST_V1_CONTINUE / NO DEMO SPEC
```

The candidate remains the best USDJPY Forex diversification lead, but it is not demo-ready. The latest evidence moves it forward on MT5 recency, then pulls it back on alternate-price-history recency; the direct bid/ask tick replay reinforces that the pullback is real enough to block demo.

## Next Allowed Work

Allowed:

- Send the updated review prompt:
  `forex-research/docs/FOREX_MT5_USDJPY_LONDON120_M15_D1ATR20_REVIEW_PROMPT_2026_07_04.md`
- Try another broker's MT5 Strategy Tester export or a true MT5 custom-symbol tester replay only if we want to spend one more validation iteration on this same lead.
- Keep monthly frozen-rule watch as new 2026 data accrues.

Not allowed from this result:

- No second D1 ATR threshold.
- No direction cut.
- No blocked-hour filter.
- No RR/session retune.
- No demo-forward spec.
- No attach to any MT5 demo chart.

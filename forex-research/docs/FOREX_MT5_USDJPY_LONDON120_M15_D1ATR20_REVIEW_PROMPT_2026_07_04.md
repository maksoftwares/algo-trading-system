# Review Prompt: Forex MT5 USDJPY London120 M15 D1 ATR20 Guard

You are reviewing the Forex-only MT5 research lane. Please be strict. The owner wants a usable demo-ready Forex strategy, but premature promotion is worse than no promotion.

## Context

Previous strict review verdict:

- `USDJPY london120_break_m15` was the best candidate to continue.
- Demo spec was blocked.
- Main blockers were recent-regime softness, EA/source review, slippage stress, survivorship ledger, exact alternate-history validation, and one predeclared structural range-quality guard test.
- Reviewer explicitly warned against more raw screens, direction cuts, blocked-hour tuning, RR/session retunes, and calendar/news filters.

## New Work Since That Review

We followed the allowed path: one predeclared structural range-quality guard, no sweep.

Predeclaration:

- File: `forex-research/docs/FOREX_MT5_USDJPY_LONDON120_M15_RANGE_QUALITY_GUARD_PREDECLARATION_2026_07_04.md`
- Pre-run spec SHA256: `42c26a283013ea74fd262e089e0254c979e027a5d46de39adecb109004b46b15`
- Pre-run EA SHA256 after adding disabled-by-default input: `a213342ad2d00c40b2470164822688b238e9a598ffc68f3fba7e4141d2a943a9`

Added guard:

```text
(06:00-08:00 session_range) / previous_completed_D1_ATR(14) >= 0.20
```

Implementation:

- EA input: `InpMinDailyRangeAtrFraction=0.20`
- Default remains `0.00`, so baseline v0 is unchanged unless this input is enabled.
- Daily ATR handle uses `PERIOD_D1`; guard uses `CopyBuffer(... shift=1)`, intended to mean previous completed D1 ATR.
- One actual MT5 Strategy Tester run only: USDJPY, M5 chart, M15 signal, `Model=0` every tick, 2018-01-01 through 2026-07-02, both directions, RR 1.00, fixed 0.01 lot.

## Key Artifacts

- Strict review packet after the review:
  `forex-research/docs/FOREX_MT5_USDJPY_LONDON120_M15_STRICT_REVIEW_PACKET_2026_07_04.md`
- Guard result:
  `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_D1ATR20_RANGE_QUALITY_GUARD_RESULT_2026_07_04.md`
- Guard robustness:
  `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_MT5_USDJPY_LONDON120_M15_D1ATR20_RANGE_QUALITY_GUARD_ROBUSTNESS_2026_07_04.md`
- Guard trade CSV:
  `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/ForexFreqScout_FULL_2018_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_D1ATR20_GUARD_USDJPY_M5_london120_break_m15_d1atr20_guard/ForexFreqScout_FULL_2018_2026_SESSION_BREAKOUT_USDJPY_LONDON120_M15_D1ATR20_GUARD_USDJPY_M5_london120_break_m15_d1atr20_guard_trades.csv`
- Dukascopy bid-M5 alternate-history replay:
  `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_DUKASCOPY_USDJPY_LONDON120_M15_D1ATR20_ALT_HISTORY_REPLAY_2026_07_04.md`
- Dukascopy ask/tick acquisition blocker:
  `forex-research/outputs/reports/mt5_backtests/session_breakout_scout/FOREX_DUKASCOPY_USDJPY_ASK_ACQUISITION_ATTEMPT_2026_07_04.md`
- Current decision packet:
  `forex-research/docs/FOREX_USDJPY_LONDON120_D1ATR20_CURRENT_DECISION_PACKET_2026_07_04.md`

## v0 Baseline Highlights

Baseline `USDJPY london120_break_m15`, no daily ATR guard:

- Full 2018-2026: 1144 trades, manual PF 1.2231, net +$273.16.
- Full 2022-2026: 521 trades, PF 1.3918, net +$232.06.
- Recent 2025-2026: 218 trades, PF 1.1247, net +$33.20.
- Trailing 12M: 145 trades, PF 1.1505, net +$23.54.
- Trailing 12M after +0.5 pip round-trip stress: PF 1.1188, net +$18.85.
- Survivorship ledger: at least 40 logged raw session-breakout cells.
- Exact Dukascopy replay is blocked locally: only USDJPY Dukascopy H1 exists; no local Dukascopy M15/M5/tick data found.

## v1 Guard Results

Predeclared acceptance checks all passed:

- Full 2018-2026: 865 trades, PF 1.2551, net +$253.17.
- Recent 2025-2026: 169 trades, PF 1.2114, net +$44.76.
- Trailing 12M: 116 trades, PF 1.1825, net +$24.60.
- Trailing 12M after +0.5 pip round-trip stress: PF 1.1527, net +$20.84.
- Recent 2025-2026 after +0.5 pip stress: PF 1.1831, net +$39.22.
- Full 2018-2026 after +0.5 pip stress: PF 1.2164, net +$218.25.

Robustness read:

- Yearly: 2018 +$7.62 / PF 1.0633; 2019 -$26.84 / PF 0.7244; 2020 +$35.44 / PF 1.2555; 2021 +$15.62 / PF 1.1520; 2022 +$56.85 / PF 1.4474; 2023 +$86.04 / PF 1.9374; 2024 +$33.68 / PF 1.3279; 2025 +$32.85 / PF 1.2194; 2026 partial +$11.91 / PF 1.1921.
- Direction: long 454 trades / PF 1.3935 / +$192.66; short 411 trades / PF 1.1203 / +$60.51.
- Breadth: positive half-years 12/17, positive months 58/102, positive weeks 206/369.
- Worst rolling windows: worst 50 PF 0.4186 / -$36.36; worst 100 PF 0.5736 / -$49.06; worst 150 PF 0.7487 / -$40.18; worst 250 PF 0.9782 / -$5.99; worst 400 PF 1.0169 / +$7.48; worst 500 PF 1.1036 / +$55.97.
- Top-winner removal: top 10 removed PF 1.1867 / +$185.30; top 20 removed PF 1.1286 / +$127.59; top 30 removed PF 1.0754 / +$74.81; top 50 removed PF 0.9792 / -$20.60.

## Dukascopy Alternate-Price-History Replay

We then acquired public Dukascopy USDJPY M5 bid candles with `dukascopy-node` into the Forex research folder, not MT5:

- Raw files:
  - `forex-research/data/alternate_history/dukascopy/USDJPY/M5/raw/USDJPY_dukascopy_M5_bid_20180101_20260703.csv.csv`
  - `forex-research/data/alternate_history/dukascopy/USDJPY/M5/raw/USDJPY_dukascopy_M5_bid_20230912_20260703.csv.csv`
- Effective merged coverage: 892,800 M5 bars from `2018-01-01T00:00:00Z` through `2026-06-27T23:55:00Z`.
- MT5-vs-Dukascopy price probes from known MT5 trades matched best at broker-server offset `0`, so the replay used Dukascopy UTC directly. No timezone-offset sweep was run.
- Replay limitation: bid-only M5 OHLC, not MT5 ticks and not ask-side spread. Exits use M5 adverse-first path; spread/cost is represented with explicit round-trip pip haircuts.
- Frozen rule: same D1 ATR20 watchlist-v1 rule, no parameter changes.

Dukascopy replay results:

- Full available 2018-2026: 1038 trades, PF 1.2164, net +$241.33.
- Full available after +0.5 pip round-trip stress: PF 1.1758, net +$199.39.
- From 2020: 789 trades, PF 1.2514, net +$225.82; after +0.5 pip: PF 1.2141, net +$195.20.
- From 2022: 528 trades, PF 1.2165, net +$144.08; after +0.5 pip: PF 1.1864, net +$125.56.
- Recent 2025-2026: 180 trades, PF 0.9275, net -$17.22; after +0.5 pip: PF 0.9040, net -$23.11.
- Trailing 12M 2025-06-19 to 2026-06-18: 119 trades, PF 1.2310, net +$28.57; after +0.5 pip: PF 1.1971, net +$24.72.
- Yearly: 2018 PF 1.1950 / +$23.31; 2019 PF 0.9200 / -$7.79; 2020 PF 1.3237 / +$44.58; 2021 PF 1.3919 / +$37.16; 2022 PF 1.5690 / +$87.50; 2023 PF 1.3505 / +$57.27; 2024 PF 1.1494 / +$16.54; 2025 PF 0.8266 / -$31.25; 2026 partial PF 1.2441 / +$14.02.

Interpretation before review: this is mixed. It supports that the structure is not purely one-broker random across the long window, but it reopens the recent-regime blocker because Dukascopy 2025 is negative.

## Ask-Side Acquisition Attempt

We tried to acquire stricter ask-side data through `dukascopy-node`:

- M5 ask for 2025: failed quickly with `Unknown error`.
- M5 ask for 2026 partial: failed quickly with `Unknown error`.
- M5 ask one-day probe: failed quickly with `Unknown error`.
- Tick ask one-day probe: attempted download, then failed with `Unknown error`.

This means the current Dukascopy artifact is bid-M5 OHLC only, plus explicit round-trip pip haircuts. However, the ask-side failure does not rescue the candidate: the bid-only recent 2025-2026 replay is already negative before stricter costs.

## Questions

1. Is the `InpMinDailyRangeAtrFraction=0.20` guard methodologically acceptable as the one predeclared structural test, or does it still look like hidden tuning?
2. Is `CopyBuffer(... shift=1)` on `PERIOD_D1` sufficient to avoid daily-ATR lookahead in the MT5 tester at the M15 signal time?
3. Does v1 meaningfully solve the recent-regime blocker, or is trailing-12M PF 1.1527 after +0.5 pip stress too narrow to count?
4. Does the 2019 failure and negative worst 250-trade rolling window block demo discussion outright, even though 2020-2026 and recent windows improved?
5. How should we weigh v1's lower full-history net but higher PF and better recent performance against v0?
6. Is the bid-M5 Dukascopy OHLC replay sufficient alternate-history evidence for watchlist continuation, or do we still need ask-side/tick-level Dukascopy or another broker's MT5 Strategy Tester export before any demo discussion?
7. Is the remaining top-winner dependence acceptable for a fixed-0.01 demo watchlist, or still a hard blocker?
8. Does the negative Dukascopy 2025 slice block `CONDITIONAL_DEMO_SPEC_ALLOWED` even though MT5 v1 recent and Dukascopy trailing-12M are positive?
9. Given the ask-side `dukascopy-node` failure, is it worth spending one more iteration on true Dukascopy tick/custom-symbol replay, or should we stop this candidate at watchlist-v1 and move the hunt elsewhere?
10. What exact next action should be taken: true Dukascopy tick/custom-symbol replay, another broker MT5 export, external EA/source review, monthly recent-regime watch, or conditional demo-spec draft with all blockers listed?
11. If no demo spec is allowed yet, how many more evidence iterations are realistically needed, and what would make you stop this candidate?

Please return:

- Verdict: `REJECT`, `WATCHLIST_V1_CONTINUE`, or `CONDITIONAL_DEMO_SPEC_ALLOWED`.
- Blocking issues, ordered by severity.
- Required next action.
- Any forbidden follow-up tests that would become data-mining.

# A1 XAU M5 Momentum Daily Guard Forward Draft - 2026-07-02

Status: REVIEW_DRAFT_NOT_ATTACHED

Boundary: demo-only forward-test draft. No canonical Phase 2 approval, no live trading, no real capital, and no MT5 runtime attachment is authorized by this document alone.

## Purpose

The owner rejected sparse monthly strategies as primary candidates. The target is an active intraday XAUUSD M5 portfolio that can produce multiple trades on active days while keeping win rate above 50%, positive PF/net, and a better chance of finishing the day positive.

This draft adds a portfolio-level daily guard on top of the repaired daily-fit portfolio. The guard is shared across the two planned magics so it matches the historical simulation; it is not a per-EA cap.

## Candidate

Base repaired daily-fit portfolio:

```text
freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1
+
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning with server hours 18 and 22 blocked
```

Daily guard:

```text
portfolio max trades per day: 6
portfolio daily loss stop: -25 USD
portfolio profit target: none
```

## Evidence

Source report:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.md`

| Metric | Repaired daily-fit no guard | Daily guarded |
|---|---:|---:|
| Trades | 2589 | 2130 |
| Retention | 100.00% | 82.27% |
| Win rate | 65.66% | 65.59% |
| Net USD | +1764.38 | +1450.35 |
| Profit factor | 1.31 | 1.33 |
| Active days | 645 | 645 |
| Trades / active day | 4.01 | 3.30 |
| 3+ trade active days | 55.04% | 55.04% |
| Positive active days | 53.02% | 55.35% |
| Median active-day PnL | +0.95 | +1.89 |
| Worst active day | -40.12 | -38.13 |
| Max closed drawdown | 108.59 | 90.82 |
| Top 100 winners removed | +681.97 | +403.96 |
| Older split net / PF | +376.50 / 1.19 | +295.57 / 1.18 |
| Newer split net / PF | +1387.88 / 1.38 | +1154.78 / 1.41 |

Interpretation: the guard improves daily shape and drawdown while preserving the hard minimum daily cadence. The cost is lower total net and lower top-winner-removed cushion because it skips late-day trades.

## Lane 1 - Long Weak-Hours Block With Portfolio Guard

Magic: 932270

Order comment: `A1_XAU_M5_MOM_DG_L`

Run id: `A1_XAU_M5_MOMENTUM_DAILY_GUARD_LONG_WEAK_HOURS_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | LONG only |
| Signal mode | Break-and-run default |
| H1 trend filter | true |
| H4 trend filter | true |
| Risk reward | 0.70 |
| Max estimated cost R | 0.05 |
| Blocked server hours | 2,9,10,11,12,17,22,23 |
| Individual max trades per day | 12 |
| Cooldown minutes | 5 |
| Portfolio daily guard | true |
| Portfolio guard magic CSV | 932270,932271 |
| Portfolio max trades/day | 6 |
| Portfolio daily loss stop USD | 25.00 |

## Lane 2 - V13 Directional EMA Trend, Repaired, With Portfolio Guard

Magic: 932271

Order comment: `A1_XAU_M5_MOM_DG_B`

Run id: `A1_XAU_M5_MOMENTUM_DAILY_GUARD_V13_BOTH_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | BOTH |
| Signal mode | M5 EMA trend continuation |
| H1 trend filter | true |
| H4 trend filter | true |
| Risk reward | 0.60 |
| Max estimated cost R | 0.05 |
| Blocked server hours | 0,2,4,9,10,11,12,16,18,19,20,22 |
| Blocked long server hours | 6,7,8 |
| Blocked short server hours | 13,14,15,17,18 |
| M5 EMA fast / slow | 8 / 21 |
| M5 slope bars | 3 |
| M5 min slope ATR | 0.03 |
| M5 max distance ATR | 1.20 |
| Min range ATR | 0.35 |
| Min body fraction | 0.30 |
| Long close location | 0.58 |
| Short close location | 0.42 |
| Min 3-bar move ATR | 0.10 |
| Individual max trades per day | 24 |
| Cooldown minutes | 0 |
| Portfolio daily guard | true |
| Portfolio guard magic CSV | 932270,932271 |
| Portfolio max trades/day | 6 |
| Portfolio daily loss stop USD | 25.00 |

## Forward-Test Rules

- Account: A1 demo account only unless owner explicitly approves another account.
- Lot: 0.01 fixed.
- Broker action: disabled until owner approval and reviewer signoff.
- No parameter changes during the forward test.
- No extra XAU momentum lanes added during the first scoring window.
- Existing sparse RR2 lane should not be stacked with this package by default.
- Daily and weekly reports must separate the two magics and also score the combined package.
- Duplicate scoring must use same-minute same-direction de-duplication.
- The daily scoreboard must track both trade-level and active-day-level performance.

## Promotion Bar

- At least 300 closed forward trades.
- At least 6 trading weeks.
- At least 3.0 trades per active day.
- At least 55% of active days have 3 or more trades.
- Portfolio WR >= 58%.
- Portfolio PF >= 1.25.
- Positive active-day rate >= 55%.
- Portfolio net positive after removing top 10 winners.
- No single day contributes more than 30% of net profit.
- No lane creates a persistent negative drag for two consecutive weeks.

## Kill Rules

- Portfolio net negative after 150 trades.
- Rolling 100-trade PF below 0.90.
- Closed drawdown exceeds 120 USD at 0.01 lot.
- Positive active-day rate below 48% after 150 trades.
- Shared portfolio guard does not block after 6 same-day entries.
- Shared portfolio guard does not block after closed same-day package PnL <= -25 USD.
- Any safety/broker-action mismatch appears.
- Runtime identity differs from the magics/comments in this document.

## Current Decision

This package is `DAILY_GUARD_REVIEW_CANDIDATE_NOT_ATTACHED`.

It is the strongest current daily-shape candidate because it trades actively, keeps win rate above 60%, preserves at least 3 trades per active day, and improves positive-day rate versus the unguarded repair. It still needs independent review before demo attachment because the daily guard is selected from historical simulation.

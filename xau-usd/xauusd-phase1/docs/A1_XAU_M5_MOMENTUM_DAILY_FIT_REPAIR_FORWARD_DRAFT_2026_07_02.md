# A1 XAU M5 Momentum Daily-Fit Repair Forward Draft - 2026-07-02

Status: REVIEW_DRAFT_NOT_ATTACHED

Boundary: demo-only forward-test draft. No canonical Phase 2 approval, no live trading, no real capital, and no MT5 runtime attachment is authorized by this document alone.

## Purpose

The daily-fit portfolio is the current best match for the owner's real requirement: multiple intraday trades on active days, win rate above 50%, positive PF/net, and low duplicate stacking.

This repair draft keeps the same two-lane portfolio but blocks two weak V13 member-hour pockets found by the repair diagnostic:

```text
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@18
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@22
```

No other lane is changed.

## Candidate

```text
freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1
+
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning with server hours 18 and 22 blocked
```

## Evidence

Source reports:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_STRESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.md`

| Metric | Baseline daily-fit | Repaired daily-fit |
|---|---:|---:|
| Deduped trades | 2785 | 2589 |
| Win rate | 65.35% | 65.66% |
| Net USD | +1757.13 | +1764.38 |
| Profit factor | 1.29 | 1.31 |
| Active days | 689 | 645 |
| Trades / active day | 4.04 | 4.01 |
| 3+ trade active days | 55.59% | 55.04% |
| Positive active days | 53.85% | 53.02% |
| Positive / negative months | 34 / 14 | 37 / 11 |
| Worst month | -35.87 | -28.45 |
| Top 25 winners removed | +1437.94 | +1445.19 |
| Top 100 winners removed | +672.60 | +681.97 |
| Max closed drawdown | 125.35 | 108.59 |
| Older split net / PF | +318.70 / 1.15 | +376.50 / 1.19 |
| Newer split net / PF | +1438.43 / 1.37 | +1387.88 / 1.38 |

Interpretation: the repair improves PF, older split, month stability, top-winner robustness, and drawdown while preserving the key daily-activity shape. The cost is fewer active days and a small dip in positive-day percentage. Because the repair is based on member-hour blocking, it must be reviewed for overfit before demo attachment.

## Lane 1 - Long Weak-Hours Block

Magic: 932260

Order comment: `A1_XAU_M5_MOM_DFR_L`

Run id: `A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_LONG_WEAK_HOURS_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | LONG only |
| Signal mode | Break-and-run default |
| H1 trend filter | true |
| H1 min slope points | 0 |
| H4 trend filter | true |
| H4 min slope points | 0 |
| Risk reward | 0.70 |
| Max estimated cost R | 0.05 |
| Blocked server hours | 2,9,10,11,12,17,22,23 |
| Max trades per day | 12 |
| Cooldown minutes | 5 |

## Lane 2 - V13 Directional EMA Trend, Repaired

Magic: 932261

Order comment: `A1_XAU_M5_MOM_DFR_B`

Run id: `A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_V13_BOTH_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | BOTH |
| Signal mode | M5 EMA trend continuation |
| H1 trend filter | true |
| H1 min slope points | 0 |
| H4 trend filter | true |
| H4 min slope points | 0 |
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
| Max trades per day | 24 |
| Cooldown minutes | 0 |

## Forward-Test Rules

- Account: A1 demo account only unless owner explicitly approves another account.
- Lot: 0.01 fixed.
- Broker action: disabled until owner approval and reviewer signoff.
- No parameter changes during the forward test.
- No extra XAU momentum lanes added during the first scoring window.
- Existing sparse RR2 lane should not be stacked with this package by default.
- Daily and weekly reports must separate the two magics.
- Duplicate scoring must use same-minute same-direction de-duplication.
- The daily scoreboard must track both trade-level and active-day-level performance.

## Promotion Bar

- At least 300 closed forward trades.
- At least 6 trading weeks.
- At least 3.0 trades per active day.
- At least 55% of active days have 3 or more trades.
- Portfolio WR >= 58%.
- Portfolio PF >= 1.25.
- Positive active-day rate >= 52%.
- Portfolio net positive after removing top 10 winners.
- No single day contributes more than 30% of net profit.
- No lane creates a persistent negative drag for two consecutive weeks.

## Kill Rules

- Portfolio net negative after 150 trades.
- Rolling 100-trade PF below 0.90.
- Closed drawdown exceeds 150 USD at 0.01 lot.
- Positive active-day rate below 45% after 150 trades.
- Any safety/broker-action mismatch appears.
- Runtime identity differs from the magics/comments in this document.

## Current Decision

This package is `DAILY_FIT_REPAIR_REVIEW_CANDIDATE_NOT_ATTACHED`.

It is the strongest current repaired candidate for the owner's daily-activity requirement, but it still needs independent review before demo attachment because the repair blocks member-hour pockets discovered from the same historical data.

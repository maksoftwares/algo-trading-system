# A1 XAU M5 Momentum Feature-Band Daily-Income Forward Draft - 2026-07-02

Status: FREQUENCY_FIRST_DAILY_INCOME_REVIEW_CANDIDATE_NOT_ATTACHED

Boundary: demo-only forward-test draft. This document does not approve canonical Phase 2, live trading, real capital, or any MT5 runtime attachment by itself.

## Purpose

The owner wants a frequent intraday engine that can realistically end more trading days positive. The max-net feature-band package is active and profitable over four years, but its positive active-day rate is only 56.23%. This draft freezes the owner-target daily-income version of the same package, which keeps a meaningful +50 USD daily target while staying above 3 trades per active day.

## Candidate

Base package:

```text
freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1
+
v13_feature_loss_short_extreme_band_m2p51_rr0p6
```

Shared daily-income guard:

```text
portfolio profit target: +50 USD
portfolio max trades per day: 6
portfolio daily loss stop: none
max loss count rule: none
```

## Evidence

Source report:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.md
```

| Metric | Daily-income feature-band package |
|---|---:|
| Trades | 1959 |
| Win rate | 66.31% |
| Net USD | +1431.19 |
| Profit factor | 1.35 |
| Active days | 594 |
| Trades / active day | 3.30 |
| 3+ trade active days | 53.54% |
| Positive active days | 58.59% |
| Median active-day PnL | +2.10 USD |
| Positive / negative months | 39 / 9 |
| Worst month | -47.21 USD |
| Top 25 winners removed | +1130.21 USD |
| Top 100 winners removed | +395.04 USD |
| Max closed drawdown | 105.72 USD |
| Older split net / PF | +338.36 / 1.24 |
| Newer split net / PF | +1092.83 / 1.41 |

Interpretation: this is not the max-net version and not the smoothest +25 version. It is the owner-target daily-income version. It keeps the desired +50 daily objective, preserves frequent trading, and still improves positive active-day rate versus the uncapped max-net package.

## Lane 1 - Long Weak-Hours Block With Shared Daily-Income Guard

Magic: 932292

Order comment: `A1_XAU_M5_MOM_DI_L`

Run id: `A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_LONG_20260702`

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
| Feature-loss filter | false |
| Portfolio daily guard | true |
| Portfolio guard magic CSV | 932292,932293 |
| Portfolio profit target USD | 50.00 |
| Portfolio max trades/day | 6 |
| Portfolio daily loss stop USD | 0.00 |

## Lane 2 - V13 Feature-Band Both-Direction Lane With Shared Daily-Income Guard

Magic: 932293

Order comment: `A1_XAU_M5_MOM_DI_B`

Run id: `A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_V13_20260702`

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
| Blocked server hours | 0,2,4,9,10,11,12,16,19,20 |
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
| Feature-loss filter | true |
| Feature-loss shadow-only | false |
| Short close-to-recent-extreme block min | -0.75 |
| Short close-to-recent-extreme block max enabled | true |
| Short close-to-recent-extreme block max | -2.51 |
| Individual max trades per day | 24 |
| Cooldown minutes | 0 |
| Portfolio daily guard | true |
| Portfolio guard magic CSV | 932292,932293 |
| Portfolio profit target USD | 50.00 |
| Portfolio max trades/day | 6 |
| Portfolio daily loss stop USD | 0.00 |

## Forward-Test Rules

- Account: A1 demo account only unless owner explicitly approves another account.
- Lot: 0.01 fixed.
- Broker action: disabled until owner approval and reviewer signoff.
- No parameter changes during the forward test.
- Do not run this package together with the max-net feature-band package unless one is shadow-only.
- Daily and weekly reports must separate the two magics and also score the combined package.
- Duplicate scoring must use same-minute same-direction de-duplication.
- The daily scoreboard must report both total net and positive active-day rate.
- This package must be judged as a two-lane portfolio; neither lane should be promoted alone from this draft.

## Promotion Bar

- At least 300 closed forward trades.
- At least 6 trading weeks.
- At least 3.0 trades per active day.
- At least 53% of active days have 3 or more trades.
- Portfolio WR >= 60%.
- Portfolio PF >= 1.25.
- Positive active-day rate >= 58%.
- Portfolio net positive after removing top 10 winners.
- No single day contributes more than 30% of net profit.
- No lane creates a persistent negative drag for two consecutive weeks.

## Kill Rules

- Portfolio net negative after 150 trades.
- Rolling 100-trade PF below 0.90.
- Closed drawdown exceeds 120 USD at 0.01 lot.
- Positive active-day rate below 52% after 150 trades.
- Actual trade cadence falls below 2 trades per active day after 100 trades.
- Shared profit-target/max-trades guard does not block after +50 USD closed same-day package PnL or 6 same-day package entries.
- Any safety/broker-action mismatch appears.
- Runtime identity differs from the magics/comments in this document.

## Current Decision

This package is `FREQUENCY_FIRST_DAILY_INCOME_REVIEW_CANDIDATE_NOT_ATTACHED`.

It should be reviewed as the owner-target daily-income alternative to the max-net feature-band package. It is not attached and no MT5 runtime was touched.

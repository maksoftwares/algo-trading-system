# A1 XAU M5 Momentum Feature-Band Forward Draft - 2026-07-02

Status: FREQUENCY_FIRST_REVIEW_CANDIDATE_NOT_ATTACHED

Boundary: demo-only forward-test draft. This document does not approve canonical Phase 2, live trading, real capital, or any MT5 runtime attachment by itself.

## Purpose

The owner clarified that sparse strategies do not satisfy the project goal. A candidate must produce multiple trades on active days, ideally 3-5, while keeping win rate above 50%, positive PF/net, and acceptable drawdown.

This draft freezes the current best exact MT5-backed frequency-first candidate. It combines:

```text
freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1
+
v13_feature_loss_short_extreme_band_m2p51_rr0p6
```

Unlike the prior feature-loss daily-guard draft, this package does not use a shared portfolio daily guard. The exact MT5 optimizer selected the unguarded deduped package because it produced better frequency and net while preserving the frequency requirement.

## Evidence

Source reports:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FEATURE_PAIR_BAND_FOUR_YEAR_2022_07_2026_06.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_PORTFOLIO_VERDICT_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_PAIR_FILTER_SEARCH_2026_07_02.md`

| Metric | Exact MT5-backed package |
|---|---:|
| Trades | 2480 |
| Win rate | 66.25% |
| Net USD | +1775.35 |
| Profit factor | 1.33 |
| Active days | 594 |
| Trades / active day | 4.18 |
| 3+ trade active days | 53.54% |
| Positive active days | 56.23% |
| Median active-day PnL | +2.10 USD |
| Positive / negative months | 40 / 8 |
| Worst month | -42.89 USD |
| Top 25 winners removed | +1456.16 USD |
| Top 100 winners removed | +696.56 USD |
| Max closed drawdown | 112.39 USD |
| Older split net / PF | +429.61 / 1.24 |
| Newer split net / PF | +1345.74 / 1.37 |
| Raw duplicate-like overlap | 4.57% |

Interpretation: this candidate better matches the owner's actual operating goal than the sparse RR2 lane and the guarded feature-loss draft. It keeps the trade engine active, has win rate well above 50%, remains positive after removing the top 100 winners, and has positive older/newer splits. It is still a historically selected review candidate, not proof.

## Lane 1 - Long Weak-Hours Block

Magic: 932290

Order comment: `A1_XAU_M5_MOM_FB_L`

Run id: `A1_XAU_M5_MOMENTUM_FEATURE_BAND_LONG_WEAK_HOURS_20260702`

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
| Portfolio daily guard | false |

## Lane 2 - V13 Feature-Band Both-Direction Lane

Magic: 932291

Order comment: `A1_XAU_M5_MOM_FB_B`

Run id: `A1_XAU_M5_MOMENTUM_FEATURE_BAND_V13_BOTH_20260702`

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
| Portfolio daily guard | false |

Feature-band rule:

```text
Block SHORT entries when close_to_recent_extreme >= -0.75.
Block SHORT entries when close_to_recent_extreme <= -2.51.
```

Plain-English meaning: skip shorts that are too close to the recent low, and skip shorts that are already too stretched below the recent low. The goal is to avoid late/exhausted shorts while keeping enough valid entries.

## Forward-Test Rules

- Account: A1 demo account only unless owner explicitly approves another account.
- Lot: 0.01 fixed.
- Broker action: disabled until owner approval and reviewer signoff.
- No parameter changes during the forward test.
- Existing sparse RR2 lane should not be stacked with this package by default.
- Older feature-guard variants `932280/932281` should not run at the same time as this package unless explicitly approved as shadow-only.
- Daily and weekly reports must separate the two magics and also score the combined package.
- Duplicate scoring must use same-minute same-direction de-duplication.
- The daily scoreboard must track both trade-level results and active-day-level results.
- This package must be judged as a two-lane portfolio; neither lane should be promoted alone from this draft.

## Promotion Bar

- At least 300 closed forward trades.
- At least 6 trading weeks.
- At least 3.0 trades per active day.
- At least 53% of active days have 3 or more trades.
- Portfolio WR >= 60%.
- Portfolio PF >= 1.25.
- Positive active-day rate >= 56%.
- Portfolio net positive after removing top 10 winners.
- No single day contributes more than 30% of net profit.
- No lane creates a persistent negative drag for two consecutive weeks.

## Kill Rules

- Portfolio net negative after 150 trades.
- Rolling 100-trade PF below 0.90.
- Closed drawdown exceeds 120 USD at 0.01 lot.
- Positive active-day rate below 50% after 150 trades.
- Actual trade cadence falls below 2 trades per active day after 100 trades.
- Any safety/broker-action mismatch appears.
- Runtime identity differs from the magics/comments in this document.

## Current Decision

This package is `FREQUENCY_FIRST_REVIEW_CANDIDATE_NOT_ATTACHED`.

It is currently the best exact MT5-backed candidate matching the owner's stated objective: multiple intraday trades, win rate above 50%, positive PF/net, and enough daily activity to matter. It still needs independent review, owner approval, and a frozen forward-test launch packet before any demo runtime replacement.

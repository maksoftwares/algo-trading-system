# A1 XAU M5 Momentum Daily-Fit Portfolio Forward Draft - 2026-07-02

Status: REVIEW_DRAFT_NOT_ATTACHED

Boundary: demo-only forward-test draft. No canonical Phase 2 approval, no live trading, no real capital, and no MT5 runtime attachment is authorized by this document alone.

## Purpose

The owner rejected sparse strategies as primary lanes. The target is an active intraday portfolio that can produce multiple trades on active days while keeping win rate above 50%, positive PF/net, and low duplicate stacking.

This draft packages the best candidate from the daily-fit search:

```text
freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1
+
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning
```

This candidate is not the highest possible net-profit portfolio. It is the best current match for the business shape: enough active days, enough 3+ trade days, good trade win rate, acceptable PF, and low duplicate-like overlap after deterministic de-duplication.

## Evidence

Source report:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.md`

| Metric | Value |
|---|---:|
| Deduped trades | 2785 |
| Raw trades | 2843 |
| Win rate | 65.35% |
| Net USD | +1757.13 |
| Profit factor | 1.29 |
| Active days | 689 |
| Trades / active day | 4.04 |
| 3+ trade active days | 383 / 689 = 55.59% |
| Positive active days | 53.85% |
| Median active-day PnL | +0.95 USD |
| Worst active day | -40.12 USD |
| Positive / negative months | 34 / 14 |
| Worst month | -35.87 USD |
| Top 25 winners removed | +1437.94 USD |
| Top 100 winners removed | +672.60 USD |
| Max closed drawdown | 125.35 USD |
| Raw duplicate-like overlap | 4.08% |
| Older split net / PF | +318.70 / 1.15 |
| Newer split net / PF | +1438.43 / 1.37 |

Interpretation: this candidate better matches the owner's active intraday goal than sparse RR2 lanes. Its main caveat is split-period asymmetry: the newer 2024-07 to 2026-06 window is much stronger than the older 2022-07 to 2024-06 window. That means it is review-worthy, not proven.

## Lane 1 - Long Weak-Hours Block

Magic: 932250

Order comment: `A1_XAU_M5_MOM_DF_L`

Run id: `A1_XAU_M5_MOMENTUM_DAILY_FIT_LONG_WEAK_HOURS_20260702`

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

## Lane 2 - V13 Directional EMA Trend

Magic: 932251

Order comment: `A1_XAU_M5_MOM_DF_B`

Run id: `A1_XAU_M5_MOMENTUM_DAILY_FIT_V13_BOTH_20260702`

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
- Older/newer live split cannot be measured yet, so weekly buckets must not show persistent one-week dependence.

## Kill Rules

- Portfolio net negative after 150 trades.
- Rolling 100-trade PF below 0.90.
- Closed drawdown exceeds 150 USD at 0.01 lot.
- Positive active-day rate below 45% after 150 trades.
- Any safety/broker-action mismatch appears.
- Runtime identity differs from the magics/comments in this document.

## Current Decision

This package is `DAILY_FIT_REVIEW_CANDIDATE_NOT_ATTACHED`.

It is the best current candidate for the owner's daily-activity requirement. It still needs independent review before demo attachment because the older split is only PF 1.15 and the result may be partly recent-regime dependent.

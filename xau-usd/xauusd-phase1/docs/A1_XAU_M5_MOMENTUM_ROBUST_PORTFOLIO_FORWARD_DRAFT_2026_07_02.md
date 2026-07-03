# A1 XAU M5 Momentum Robust Portfolio Forward Draft - 2026-07-02

Status: REVIEW_DRAFT_NOT_ATTACHED

Boundary: demo-only forward-test draft. No canonical Phase 2 approval, no live trading, no real capital, and no MT5 runtime attachment is authorized by this document alone.

## Purpose

The owner rejected sparse candidates as a primary path. The target shape is an active XAUUSD M5 strategy package with multiple intraday opportunities, win rate above 50%, positive net/PF, realistic cost gating, and no fake edge from duplicate stacking.

This draft replaces the earlier sparse RR2 primary idea with the best robustness-first portfolio found on 2026-07-02.

## Candidate

```text
v6_freq_v4_rr0p7_max2
+
v13_ema_trend_h1h4_long_rr0p6_no_morning
+
freq_h1_h4_short_rr0p7_v1_night_early
```

## Backtest Evidence

Source reports:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_STRESS_2026_07_02.md`

| Metric | Value |
|---|---:|
| Deduped trades | 2503 |
| Win rate | 66.40% |
| Net USD | +1933.57 |
| Profit factor | 1.37 |
| Active days | 603 |
| Trades / active day | 4.15 |
| Positive / negative months | 37 / 11 |
| Worst month USD | -21.84 |
| Max closed DD USD | 93.43 |
| Top 25 winners removed | +1611.51 |
| Top 100 winners removed | +839.77 |
| Raw duplicate-like trade pct | 2.84% |

Split-period check:

| Window | Trades | WR | Net USD | PF | Trades / active day |
|---|---:|---:|---:|---:|---:|
| 2022-07 to 2024-06 | 1169 | 64.50% | +441.29 | 1.24 | 3.72 |
| 2024-07 to 2026-06 | 1334 | 68.07% | +1492.28 | 1.44 | 4.62 |

Interpretation: this is the best current candidate that matches the frequency requirement while staying positive in both halves of the available four-year window. The older half is weaker than the newer half, so this is still a forward-test candidate, not proof of long-term live profitability.

Walk-forward stability:

- Report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_2026_07_02.md`
- Verdict: `REVIEW_FOR_FORWARD_TEST`
- Every half-year bucket is positive.
- Weakest half-year: `2022-H2`, `299` trades, WR `60.87%`, net `+32.38`, PF `1.07`.
- Strongest recent half-year: `2026-H1`, `183` trades, WR `69.95%`, net `+430.60`, PF `1.61`.
- Longest losing trade streak: `9`.
- Longest losing day streak: `6`.

Walk-forward interpretation: the candidate preserves activity and win rate across all windows, but early-history profitability was thin. This must be monitored during forward demo. If forward performance starts resembling the weak 2022-H2 bucket rather than the stronger 2024-2026 regime, the lane should not be promoted.

## Lane 1 - V6 Max2 Long

Magic: 932230

Order comment: `A1_XAU_M5_MOM_RB_L1`

Run id: `A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V6_MAX2_LONG_20260702`

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
| Blocked server hours | 2,9,10,11,12,13,17,19,21,23 |
| One position per magic | false |
| Max open positions per magic | 2 |
| Max trades per day | 20 |
| Cooldown minutes | 3 |

## Lane 2 - V13 Long No Morning

Magic: 932231

Order comment: `A1_XAU_M5_MOM_RB_L2`

Run id: `A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_V13_LONG_NO_MORNING_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | LONG only |
| Signal mode | M5 EMA trend continuation |
| H1 trend filter | true |
| H1 min slope points | 0 |
| H4 trend filter | true |
| H4 min slope points | 0 |
| Risk reward | 0.60 |
| Max estimated cost R | 0.05 |
| Blocked server hours | 0,2,4,9,10,11,12,16,19,20 |
| Blocked long server hours | 6,7,8 |
| M5 EMA fast / slow | 8 / 21 |
| M5 slope bars | 3 |
| M5 min slope ATR | 0.03 |
| M5 max distance ATR | 1.20 |
| Min range ATR | 0.35 |
| Min body fraction | 0.30 |
| Long close location | 0.58 |
| Min 3-bar move ATR | 0.10 |
| Max trades per day | 24 |
| Cooldown minutes | 0 |

## Lane 3 - Short Night/Early

Magic: 932232

Order comment: `A1_XAU_M5_MOM_RB_S`

Run id: `A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SHORT_NIGHT_EARLY_20260702`

Inputs:

| Input | Value |
|---|---|
| Symbol | XAUUSD |
| Timeframe | M5 |
| Direction | SHORT only |
| Signal mode | Break-and-run default |
| H1 trend filter | true |
| H1 min slope points | 0 |
| H4 trend filter | true |
| H4 min slope points | 0 |
| Risk reward | 0.70 |
| Max estimated cost R | 0.05 |
| Blocked server hours | 0,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23 |
| Max trades per day | 12 |
| Cooldown minutes | 5 |

## Forward-Test Rules

- Account: A1 demo account only unless owner explicitly approves another account.
- Lot: 0.01 fixed.
- Broker action: disabled until owner approval and reviewer signoff.
- No parameter changes during the forward test.
- No extra XAU momentum lanes added during the first scoring window.
- Daily and weekly reporting must separate the three magics.
- Duplicate scoring must use same-minute same-direction de-duplication.
- Compare combined portfolio and each lane independently.

## Promotion Bar

Minimum evaluation before promotion:

- At least 300 closed forward trades.
- At least 6 trading weeks.
- Portfolio WR >= 55%.
- Portfolio PF >= 1.25.
- Portfolio net positive after removing top 10 winners.
- No single day contributes more than 30% of net profit.
- No lane creates a persistent negative drag for two consecutive weeks.

## Kill Rules

Stop the forward test if any of these trigger:

- Portfolio net negative after 150 trades.
- Rolling 100-trade PF below 0.90.
- Closed drawdown exceeds 150 USD at 0.01 lot.
- Any safety/broker-action mismatch appears.
- Runtime identity differs from the magics/comments in this document.

## Current Decision

This package is `ROBUST_REVIEW_CANDIDATE_NOT_ATTACHED`.

It is closer to the project vision than sparse RR2 because it historically produces multiple intraday trades and keeps win rate above 50%. It still needs independent review before demo attachment.

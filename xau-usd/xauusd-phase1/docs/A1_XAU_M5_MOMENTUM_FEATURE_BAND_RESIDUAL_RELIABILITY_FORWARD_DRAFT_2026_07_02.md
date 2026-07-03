# A1 XAU M5 Momentum Feature-Band Residual Reliability Forward Draft - 2026-07-02

Status: REVIEW_READY_NOT_ATTACHED

Boundary: demo-only preparation. No MT5 runtime, charts, presets, orders, or positions were changed by this document. This draft does not approve canonical Phase 2 or live trading.

## Purpose

The owner rejected sparse strategies. This draft keeps the frequent intraday daily-reliability package and adds only residual blocks that preserve the core requirement: multiple intraday opportunities. A sparse strategy that produces only a few trades per month is ineligible even if its win rate or PF looks attractive.

Base package:

- XAUUSD M5 momentum feature-band portfolio.
- Shared package target: stop opening new package trades after +50 USD closed PnL on the broker day.
- Shared package cap: max 6 package entries per broker day.
- Shared package cooldown: after any closed losing package trade, wait 15 minutes before the next package entry.
- No daily loss stop.

Residual blocks:

- Block LONG entries at server hour 18.
- Tighten the SHORT close-to-recent-extreme block from `>= -0.75` to `>= -0.92`.

These are not proof. They are a review candidate because they improved positive active days without turning the system sparse.

## Historical result

Source report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.md`

Stress report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.md`

| Metric | Daily reliability baseline | Residual reliability candidate |
|---|---:|---:|
| Trades | 1894 | 1822 |
| Win rate | 68.74% | 69.10% |
| Profit factor | 1.49 | 1.52 |
| Net USD | 1817.95 | 1837.34 |
| Active days | 594 | 572 |
| Trades per active day | 3.19 | 3.19 |
| 3+ trade active days | 51.01% | 50.87% |
| Positive active days | 60.44% | 62.59% |
| Positive / negative months | 41 / 7 | 41 / 7 |
| Older split net / PF | 500.79 / 1.39 | 520.77 / 1.43 |
| Newer split net / PF | 1317.16 / 1.54 | 1316.57 / 1.56 |
| Top 100 winners removed | 784.20 | 806.20 |
| Max closed drawdown | 79.45 | 84.11 |

Trade-off: the residual candidate gains positive-day rate and PF while giving up 22 active days and slightly increasing drawdown. It still satisfies the multiple-trades/day requirement.

Stress result:

- Decision: `RESIDUAL_RELIABILITY_STRESS_PASS_REVIEW_READY`.
- No half-year bucket is net negative.
- No rolling 250-trade window is net negative.
- Top 100 winners removed remains `+806.20`.
- Top 200 winners removed remains `+36.55`.
- Cadence remains `3.19` trades per active day, with `66.08%` of active days having at least 2 trades and `50.87%` having at least 3 trades.

This is why the candidate remains eligible. If a future variant improves PF by dropping below this cadence shape, it must be rejected as a sparse strategy.

## Planned lanes

| Lane | Magic | Direction | Comment | Package magics |
|---|---:|---|---|---|
| Feature-band residual reliability long | 932296 | LONG only | `A1_XAU_M5_MOM_RR_L` | `932296,932297` |
| Feature-band residual reliability V13 both | 932297 | BOTH | `A1_XAU_M5_MOM_RR_B` | `932296,932297` |

## Frozen package guard

| Input | Value |
|---|---|
| `InpPortfolioDailyGuardEnabled` | `true` |
| `InpPortfolioGuardMagicCsv` | `932296,932297` |
| `InpPortfolioDailyProfitTargetUsd` | `50.00` |
| `InpPortfolioMaxTradesPerDay` | `6` |
| `InpPortfolioDailyLossStopUsd` | `0.00` |
| `InpPortfolioCooldownAfterLossMinutes` | `15` |

## Frozen residual blocks

| Lane | Input | Value |
|---|---|---|
| Long lane | `InpBlockedEntryHoursCsv` | `2,9,10,11,12,17,18,22,23` |
| V13 lane | `InpBlockedLongEntryHoursCsv` | `6,7,8,18` |
| V13 lane | `InpShortCloseToRecentExtremeBlockMin` | `-0.92` |
| V13 lane | `InpShortCloseToRecentExtremeBlockMaxEnabled` | `true` |
| V13 lane | `InpShortCloseToRecentExtremeBlockMax` | `-2.51` |

## Promotion rule

This is not attached yet. It can move to demo only after reviewer/owner approval. During any forward demo:

- Lot remains 0.01 fixed.
- No mid-test parameter tuning.
- No extra symbols.
- No extra EAs in this package.
- Report all package trades by magic, direction, session, hour, and day.
- Judge against frequency and daily reliability together.

Minimum forward review target:

- At least 2 weeks and at least 40 closed package trades before first judgment.
- Preferred: 4 weeks and at least 100 closed package trades.
- Must stay net positive, PF >= 1.25, WR >= 55%, and average at least 2 trades per active trading day.
- Preferred cadence remains 3-5 trades per active trading day.
- If forward cadence falls below 2 trades per active day, the package fails the owner's business-fit requirement even if profitable.
- If cadence stays above 2 but below 3 trades per active day, the result is a review warning, not a clean pass.

## Explicit non-goals

- This does not claim long-term live readiness.
- This does not touch current live/demo EAs.
- This does not rescue sparse strategies.
- This does not approve the old breakout-retest lane.
- This does not replace review.

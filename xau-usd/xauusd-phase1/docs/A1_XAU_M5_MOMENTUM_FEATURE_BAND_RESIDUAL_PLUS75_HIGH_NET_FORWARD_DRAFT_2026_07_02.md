# A1 XAU M5 Momentum Feature-Band Residual +75 High-Net Forward Draft - 2026-07-02

Status: REVIEW_READY_NOT_ATTACHED

Boundary: demo-only preparation. No MT5 runtime, charts, presets, orders, or positions were changed by this document. This draft does not approve canonical Phase 2 or live trading.

## Purpose

This draft locks the higher-net package found by the residual package optimizer. It is a separate alternative to the owner-target `+50/max6/10m` package, not a silent replacement.

The owner wants frequent intraday trading. This package preserves that requirement while allowing more trades on strong days:

- `+75 USD` daily package target.
- No shared package max-trade cap.
- `10` minute cooldown after any package loss.
- No daily loss stop.

## Signal Package

Base package:

- XAUUSD M5 momentum feature-band portfolio.
- Long lane: H1+H4 aligned long momentum with weak-hour blocks.
- V13 lane: both-direction M5 EMA trend continuation with feature-loss short extreme band.

Residual blocks:

- Block LONG entries at server hour `18`.
- Tighten the SHORT close-to-recent-extreme min block from `>= -0.75` to `>= -0.92`.
- Keep the SHORT close-to-recent-extreme max block at `<= -2.51`.

## Historical Evidence

Source reports:

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.md`

| Metric | +50/max6/10m owner-target package | +75/no-cap/10m high-net package |
|---|---:|---:|
| Trades | 1823 | 2231 |
| Win rate | 69.17% | 69.48% |
| Profit factor | 1.53 | 1.54 |
| Net USD | 1863.81 | 2400.90 |
| Active days | 572 | 572 |
| Trades per active day | 3.19 | 3.90 |
| 2+ trade active days | 66.08% | 66.08% |
| 3+ trade active days | 51.05% | 51.05% |
| Positive active days | 62.94% | 60.66% |
| Positive / negative months | 41 / 7 | 43 / 5 |
| Older split net / PF | 520.32 / 1.43 | 662.46 / 1.46 |
| Newer split net / PF | 1343.49 / 1.58 | 1738.44 / 1.58 |
| Top 100 winners removed | 829.08 | 1324.53 |
| Top 200 winners removed | 57.55 | 489.31 |
| Max closed drawdown | 84.11 | 91.59 |

Interpretation:

- The high-net package produces more total net, more trades, stronger top-winner robustness, and better month count.
- It gives up positive active-day rate versus the `+50/max6/10m` package.
- It should be reviewed as a higher-opportunity alternative, not as the default daily-income package.

## Planned Lanes

| Lane | Magic | Direction | Comment | Package magics |
|---|---:|---|---|---|
| Feature-band residual +75 high-net long | 932300 | LONG only | `A1_XAU_M5_MOM_RR75_L` | `932300,932301` |
| Feature-band residual +75 high-net V13 both | 932301 | BOTH | `A1_XAU_M5_MOM_RR75_B` | `932300,932301` |

## Frozen Package Guard

| Input | Value |
|---|---|
| `InpPortfolioDailyGuardEnabled` | `true` |
| `InpPortfolioGuardMagicCsv` | `932300,932301` |
| `InpPortfolioDailyProfitTargetUsd` | `75.00` |
| `InpPortfolioMaxTradesPerDay` | `0` |
| `InpPortfolioDailyLossStopUsd` | `0.00` |
| `InpPortfolioCooldownAfterLossMinutes` | `10` |

`InpPortfolioMaxTradesPerDay=0` means no shared package trade cap.

## Frozen Residual Blocks

| Lane | Input | Value |
|---|---|---|
| Long lane | `InpBlockedEntryHoursCsv` | `2,9,10,11,12,17,18,22,23` |
| V13 lane | `InpBlockedLongEntryHoursCsv` | `6,7,8,18` |
| V13 lane | `InpShortCloseToRecentExtremeBlockMin` | `-0.92` |
| V13 lane | `InpShortCloseToRecentExtremeBlockMaxEnabled` | `true` |
| V13 lane | `InpShortCloseToRecentExtremeBlockMax` | `-2.51` |

## Promotion Rule

This is not attached yet. It can move to demo only after reviewer/owner approval. During any forward demo:

- Lot remains `0.01` fixed.
- No mid-test parameter tuning.
- No extra symbols.
- No extra EAs in this package.
- Report all package trades by magic, direction, session, hour, and day.
- Judge against frequency and daily reliability together.

Minimum forward review target:

- At least 2 weeks and at least 40 closed package trades before first judgment.
- Preferred: 4 weeks and at least 100 closed package trades.
- Must stay net positive, PF `>= 1.25`, WR `>= 55%`, and average at least 2 trades per active trading day.
- Preferred cadence remains 3-5 trades per active trading day.
- If forward cadence falls below 2 trades per active day, the package fails the owner's business-fit requirement even if profitable.
- Because this is the higher-net package, it must also avoid runaway bad days: any single forward day worse than `-75 USD` requires review before continuation.

## Explicit Non-Goals

- This does not claim long-term live readiness.
- This does not touch current live/demo EAs.
- This does not rescue sparse strategies.
- This does not approve the old breakout-retest lane.
- This does not replace review.

# A1 XAU M5 Momentum Feature-Band Residual +50 Cooldown10 Forward Draft - 2026-07-02

Status: REVIEW_READY_NOT_ATTACHED

Boundary: demo-only preparation. No MT5 runtime, charts, presets, orders, or positions were changed by this document. This draft does not approve canonical Phase 2 or live trading.

## Purpose

The owner wants a frequent intraday engine: multiple trades on active days, win rate above 50%, and a realistic path to daily profitability. Sparse systems are rejected even when PF looks attractive.

This draft takes the residual-reliability candidate and locks the best owner-target package from the residual package optimizer:

- Keep the `+50 USD` daily package target.
- Keep the max `6` package trades/day cap.
- Change the cooldown after a package loss from `15` minutes to `10` minutes.

The optimizer showed the `10` minute cooldown preserves the same cadence while slightly improving net, PF, positive-day rate, and top-winner robustness.

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

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RELIABILITY_RESIDUAL_SEARCH_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_RELIABILITY_STRESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_RESIDUAL_PACKAGE_OPTIMIZER_2026_07_02.md`

| Metric | Residual +50/15m draft | Residual +50/10m package |
|---|---:|---:|
| Trades | 1822 | 1823 |
| Win rate | 69.10% | 69.17% |
| Profit factor | 1.52 | 1.53 |
| Net USD | 1837.34 | 1863.81 |
| Active days | 572 | 572 |
| Trades per active day | 3.19 | 3.19 |
| 2+ trade active days | 66.08% | 66.08% |
| 3+ trade active days | 50.87% | 51.05% |
| Positive active days | 62.59% | 62.94% |
| Positive / negative months | 41 / 7 | 41 / 7 |
| Older split net / PF | 520.77 / 1.43 | 520.32 / 1.43 |
| Newer split net / PF | 1316.57 / 1.56 | 1343.49 / 1.58 |
| Top 100 winners removed | 806.20 | 829.08 |
| Top 200 winners removed | 36.55 | 57.55 |
| Max closed drawdown | 84.11 | 84.11 |

Interpretation:

- The `+50/10m` package is a small but consistent improvement over `+50/15m`.
- It does not starve trade count.
- It remains a review candidate, not proof.

## Planned Lanes

| Lane | Magic | Direction | Comment | Package magics |
|---|---:|---|---|---|
| Feature-band residual +50 cooldown10 long | 932298 | LONG only | `A1_XAU_M5_MOM_RR10_L` | `932298,932299` |
| Feature-band residual +50 cooldown10 V13 both | 932299 | BOTH | `A1_XAU_M5_MOM_RR10_B` | `932298,932299` |

## Frozen Package Guard

| Input | Value |
|---|---|
| `InpPortfolioDailyGuardEnabled` | `true` |
| `InpPortfolioGuardMagicCsv` | `932298,932299` |
| `InpPortfolioDailyProfitTargetUsd` | `50.00` |
| `InpPortfolioMaxTradesPerDay` | `6` |
| `InpPortfolioDailyLossStopUsd` | `0.00` |
| `InpPortfolioCooldownAfterLossMinutes` | `10` |

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
- If cadence stays above 2 but below 3 trades per active day, the result is a review warning, not a clean pass.

## Explicit Non-Goals

- This does not claim long-term live readiness.
- This does not touch current live/demo EAs.
- This does not rescue sparse strategies.
- This does not approve the old breakout-retest lane.
- This does not replace review.

# A1 XAU M5 Momentum Feature-Band Daily Reliability Forward Draft - 2026-07-02

Status: REVIEW_READY_NOT_ATTACHED

Boundary: demo-only preparation. No MT5 runtime, charts, presets, orders, or positions were changed by this document. This draft does not approve canonical Phase 2 or live trading.

## Why this replaces sparse candidates

The owner requirement is not a sparse swing-style strategy. The forward candidate must keep multiple trades on active days while improving daily reliability. Strategies that produce only a few trades per month are out of scope for the current business goal, even if they look clean on paper.

This package is built from the A1 XAU M5 momentum feature-band trade stream and adds one causal day-management overlay:

- Shared package target: stop opening new package trades after +50 USD closed PnL on the broker day.
- Shared package cap: max 6 package entries per broker day.
- Shared package cooldown: after any closed losing package trade, wait 15 minutes before the next package entry.
- No daily loss stop in this draft.
- No change to existing 920101 breakout-retest runtime.
- No change to A2 or A3.

## Historical result

Source report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAY_STATE_SEARCH_2026_07_02.md`

| Metric | Value |
|---|---:|
| Trades | 1894 |
| Win rate | 68.74% |
| Profit factor | 1.49 |
| Net USD | 1817.95 |
| Active days | 594 |
| Trades per active day | 3.19 |
| 3+ trade active days | 51.01% |
| Positive active days | 60.44% |
| Positive / negative months | 41 / 7 |
| Older split net / PF | 500.79 / 1.39 |
| Newer split net / PF | 1317.16 / 1.54 |
| Top 100 winners removed | 784.20 |
| Max closed drawdown | 79.45 |
| Cooldown-skipped trades | 89 |

Cadence note: the 3+ trade-day rate drops from the +50 baseline's 53.54% to 51.01%, but the package still averages above 3 trades per active day and materially improves win rate, PF, net, positive-day rate, drawdown, and top-100 robustness.

## Planned lanes

The package consists of two A1-only XAUUSD M5 lanes that share the same package guard.

| Lane | Magic | Direction | Comment | Package magics |
|---|---:|---|---|---|
| Feature-band daily reliability long | 932294 | LONG only | `A1_XAU_M5_MOM_DR_L` | `932294,932295` |
| Feature-band daily reliability V13 both | 932295 | BOTH | `A1_XAU_M5_MOM_DR_B` | `932294,932295` |

## Frozen package guard

| Input | Value |
|---|---|
| `InpPortfolioDailyGuardEnabled` | `true` |
| `InpPortfolioGuardMagicCsv` | `932294,932295` |
| `InpPortfolioDailyProfitTargetUsd` | `50.00` |
| `InpPortfolioMaxTradesPerDay` | `6` |
| `InpPortfolioDailyLossStopUsd` | `0.00` |
| `InpPortfolioCooldownAfterLossMinutes` | `15` |

## Promotion rule

This is not attached yet. It can move to demo only after reviewer/owner approval. During any forward demo:

- Lot remains 0.01 fixed.
- No mid-test parameter tuning.
- No extra symbols.
- No extra EAs in this package.
- Report all package trades by magic, direction, session, and day.
- Judge against both frequency and reliability, not one metric alone.

Minimum forward review target:

- At least 2 weeks and at least 40 closed package trades before first judgment.
- Preferred: 4 weeks and at least 100 closed package trades.
- Must stay net positive, PF >= 1.25, WR >= 55%, and average at least 2 trades per active trading day.
- If forward cadence falls below 2 trades per active day, the package fails the owner's business-fit requirement even if it is profitable.

## Explicit non-goals

- This does not claim long-term live readiness.
- This does not touch the current live/demo EAs.
- This does not rescue sparse strategies.
- This does not approve the old breakout-retest lane.
- This does not replace review.

# Claude Review Prompt - A1 XAU M5 Momentum Feature-Band Candidate - 2026-07-02

Please independently review the new A1 XAUUSD M5 frequency-first momentum candidate. The owner has explicitly rejected sparse strategies; the goal is multiple trades on active days, ideally 3-5 trades per active day, while preserving win rate above 50%, positive PF/net, and acceptable drawdown.

Boundary: offline/repo review only. Do not touch MT5 runtime, presets, charts, orders, or positions.

## Candidate To Review

Forward draft:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_FORWARD_DRAFT_2026_07_02.md
```

Hash manifest:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_FORWARD_DRAFT_2026_07_02.md.sha256.json
```

Core package:

```text
freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1
+
v13_feature_loss_short_extreme_band_m2p51_rr0p6
```

Planned magics:

```text
932290 = long weak-hours lane
932291 = V13 feature-band both-direction lane
```

## Main Evidence

Exact MT5 four-year backtest report:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FEATURE_PAIR_BAND_FOUR_YEAR_2022_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FEATURE_PAIR_BAND_FOUR_YEAR_2022_07_2026_06.json
```

Exact MT5-backed portfolio replay/optimizer:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_PORTFOLIO_VERDICT_2026_07_02.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_LOSS_DAILY_GUARD_OPTIMIZER_2026_07_02.md
```

Feature-pair search that proposed the max-side short block:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_PAIR_FILTER_SEARCH_2026_07_02.md
```

## Headline Result To Verify

The exact MT5-backed optimizer selected the feature-band package with no shared daily guard:

| Metric | Value |
|---|---:|
| Trades | 2480 |
| Win rate | 66.25% |
| Net USD | +1775.35 |
| Profit factor | 1.33 |
| Active days | 594 |
| Trades / active day | 4.18 |
| 3+ trade active days | 53.54% |
| Positive active days | 56.23% |
| Positive / negative months | 40 / 8 |
| Top 100 winners removed | +696.56 |
| Max closed drawdown | 112.39 |
| Older split | +429.61 / PF 1.24 |
| Newer split | +1345.74 / PF 1.37 |

## What Changed Versus Prior Candidate

Prior feature-loss draft used:

```text
v13_feature_loss_short_extreme_rr0p6
shared package daily guard: max 6 trades/day and -20 USD daily loss stop
```

New feature-band candidate uses:

```text
v13_feature_loss_short_extreme_band_m2p51_rr0p6
no shared portfolio daily guard
```

Feature-band short rule:

```text
Block SHORT when close_to_recent_extreme >= -0.75.
Block SHORT when close_to_recent_extreme <= -2.51.
```

Plain English: skip shorts too close to the recent low and also skip shorts that are already too stretched below the recent low.

## Please Verify

1. Recompute the headline metrics from the referenced trade CSVs, not just the markdown.
2. Confirm this is not sparse and truly satisfies the owner's frequency requirement.
3. Confirm the new feature-band V13 lane is implemented faithfully in:

```text
xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5
xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py
xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py
```

4. Stress the result:
   - top 10 / top 25 / top 100 winners removed,
   - monthly stability,
   - older vs newer split,
   - long vs V13 feature-band contribution,
   - whether no shared daily guard is reasonable or too risky,
   - duplicate-like overlap risk,
   - whether the improvement is just selection pressure.
5. Challenge the active-day goal:
   - Is 56.23% positive active days good enough for demo forward testing?
   - If not, what exact non-sparse improvement should be tested next?
6. Give a verdict:

```text
APPROVE_FOR_SMALL_FORWARD_DEMO
APPROVE_WITH_CHANGES
REVISE
REJECT
```

If you approve, provide the exact forward-test conditions and kill rules. If you reject or revise, give the next specific feature/entry/exit experiment that could improve daily profitability without reducing activity below 3 trades per active day.

Important: do not recommend a sparse strategy as the primary answer. The owner wants a frequent intraday engine.

## Daily-Income Alternative To Review Too

The owner clarified that sparse strategies are not acceptable. The strategy must place multiple trades on active days and should be evaluated as a daily-income engine, not only by total historical net.

Please also review this daily-income tradeoff package:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.json
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_TRADEOFF_2026_07_02.csv
```

No-runtime readiness packet:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_READINESS_2026_07_02.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_READINESS_2026_07_02.json
```

Forward draft:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_FORWARD_DRAFT_2026_07_02.md
```

Hash manifest:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FEATURE_BAND_DAILY_INCOME_FORWARD_DRAFT_2026_07_02.md.sha256.json
```

Daily-income planned magics:

```text
932292 = long weak-hours lane, shared +50 USD package target / max 6 package trades per day
932293 = V13 feature-band both-direction lane, shared +50 USD package target / max 6 package trades per day
```

Owner-target daily-income candidate:

| Metric | Value |
|---|---:|
| Trades | 1959 |
| Win rate | 66.31% |
| Net USD | +1431.19 |
| Profit factor | 1.35 |
| Active days | 594 |
| Trades / active day | 3.30 |
| 3+ trade active days | 53.54% |
| Positive active days | 58.59% |
| Positive / negative months | 39 / 9 |
| Top 100 winners removed | +395.04 |
| Max closed drawdown | 105.72 |
| Older split | +338.36 / PF 1.24 |
| Newer split | +1092.83 / PF 1.41 |

Smoother +25 fallback:

```text
1922 trades / WR 66.29% / PF 1.35 / net +1361.02 / 3.24 trades per active day / 58.75% positive active days
```

Please compare:

1. Max-net feature-band package: higher total net, more trades, lower positive-day rate.
2. Owner-target daily-income package: lower total net than max-net, still frequent, better positive-day rate, +50 USD package target and max 6 package trades/day.
3. Smoother +25 fallback: slightly higher positive-day rate but weaker target and lower total net.

Question to answer plainly: for the owner's stated goal of multiple trades per active day and a realistic chance of daily profitability, which package should be forward-tested first, and what exact kill rules should govern it?

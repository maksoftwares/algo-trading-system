# A1 XAU M5 Momentum Deep Portfolio Search Verdict - 2026-07-02

## Objective

The owner clarified that a primary strategy cannot be sparse. A strategy that only creates a couple of trades in a month may be clean, but it does not match the intended trading system.

The target shape is:

- XAUUSD M5 intraday behavior.
- Multiple trades on active days.
- Win rate above 50%.
- Positive net result after realistic tester costs.
- No fake improvement from same-minute duplicate stacking.
- Enough active-day coverage to support daily profit objectives.

## Search performed

Script:

```text
xau-usd/xauusd-phase1/scripts/analyze_a1_momentum_deep_portfolio_search.py
```

Output:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.json
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DEEP_PORTFOLIO_SEARCH_2026_07_02.csv
```

Boundary:

```text
offline exact MT5 Strategy Tester trade CSV analysis only
no MT5 runtime changes
no chart changes
no preset changes
no orders or positions touched
```

The search tested one-, two-, and three-lane portfolios from the strongest four-year MT5 variant reports. It scored each portfolio after deterministic same-minute same-direction de-duplication, then reported the raw duplicate-like overlap separately.

## Main finding

The sparse RR2-style lane is not the right primary path. The deep search found portfolio shapes that fit the owner's original frequency goal much better.

The strongest practical candidate is not the absolute highest score if that candidate depends too heavily on raw overlap. The best actionable shape is the low-overlap, high-frequency portfolio below.

## Best low-overlap frequency portfolio

```text
v6_freq_v4_rr0p7_max2
+
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning
+
freq_h1_h4_short_rr0p7_v1_core_1_5_15_19
```

| Metric | Value |
|---|---:|
| Raw trades | 3107 |
| Deduped trades | 3058 |
| Win rate | 65.73% |
| Net USD | +2156.21 |
| Profit factor | 1.34 |
| Active days | 718 |
| Trades / active day | 4.26 |
| Positive months | 37 |
| Negative months | 11 |
| Worst month | -37.02 |
| Top 25 winners removed | +1835.20 |
| Max closed drawdown | 89.04 |
| Raw duplicate-like trade pct | 3.15% |
| Deduped trades removed | 49 |

Why this matters:

- It is not a two-trades-per-month strategy.
- It is not being carried by duplicate stacking.
- It keeps the win rate far above 50%.
- It creates roughly four trades per active day.
- It stays positive after removing the top 25 winners.
- It has broad active-day coverage across four years.

## Cleaner high-PF fallback

If the reviewer prioritizes PF/win-rate over active-day coverage, the best strict no-overlap fallback remains:

```text
v5_v4_move12
+
freq_h1_h4_short_rr0p7_v1_night_early
```

| Metric | Value |
|---|---:|
| Deduped trades | 1245 |
| Win rate | 65.14% |
| Net USD | +1143.45 |
| Profit factor | 1.47 |
| Active days | 506 |
| Trades / active day | 2.46 |
| Raw duplicate-like trade pct | 0.00% |

This fallback is cleaner, but it trades less often than the best low-overlap frequency portfolio.

## Decision

```text
Sparse RR2 lane: REJECT_AS_PRIMARY_TOO_SPARSE
Best low-overlap frequency portfolio: PRIMARY_REVIEW_CANDIDATE
Cleaner high-PF fallback: SECONDARY_REVIEW_CANDIDATE
```

## Recommended next move

1. Send the deep portfolio search report to independent review.
2. Ask the reviewer to challenge whether the three-lane low-overlap portfolio is too selected or still acceptable for minimum-lot demo forward testing.
3. If accepted, create a frozen forward-test spec for the three-lane portfolio.
4. Do not stack it with sparse RR2. Replace the sparse lane if the owner approves runtime deployment.
5. Keep forward lot at 0.01 and score the portfolio as one unit, not as isolated cherry-picked lanes.

## Important warning

This is still diagnostic. The search tested many combinations, so selection bias is real. The result is strong enough to review and possibly forward-test, not strong enough to claim a finished live strategy.


# A1 XAU M5 Momentum Frequency Requirement Verdict

Generated: 2026-07-02  
Scope: offline MT5 Strategy Tester analysis only; no live/demo MT5 runtime, chart, preset, or order setting was changed.

## Owner Clarification

The project goal is not simply to find a clean-looking strategy. The owner explicitly requires:

```text
1. Multiple trades on active trading days.
2. Win rate above 50%.
3. Positive net result after realistic trading friction.
4. Enough active days to support a daily-profit style system.
```

Therefore, sparse strategies that only produce a few trades per month are not acceptable as the primary lane, even if their individual trade statistics look strong.

## Frequency Gate

Going forward, every candidate must be tagged against this business-fit gate:

| Gate | Requirement |
|---|---|
| Minimum sample | At least 100 closed trades before judging |
| Active-day behavior | Hard minimum: at least 2 trades per active entry day; preferred operating band: 3-5 trades per active day |
| Sparse-strategy rule | A candidate with only a few trades per month is not primary-lane eligible |
| Quality floor | Win rate above 50%, PF at least 1.25 preferred, positive after top-winner removal |
| Promotion rule | Do not promote frequency alone if PF/month stability collapses |

## Four-Year Frequency Comparison

Window: 2022-07-01 through 2026-06-30  
Tester: isolated MT5 Strategy Tester, XAUUSD M5, 1000 USD tester currency  
Runtime touched: no

| Candidate | Trades | WR % | Net USD | PF | Active days | Trades / active day | +M | -M | Worst month | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| V4 long-only frequency candidate | 1132 | 65.90 | +1042.07 | 1.45 | 383 | 2.96 | 36 | 11 | -21.67 | Primary review candidate |
| V13 both 0.6R, no weak shorts | 1921 | 64.97 | +775.18 | 1.18 | 668 | 2.88 | 24 | 24 | -65.01 | Too noisy |
| V13 both 0.6R, no weak shorts / no long morning | 1596 | 65.54 | +778.77 | 1.23 | 651 | 2.45 | 27 | 21 | -38.11 | Coverage candidate only |
| V13 short-only core | 496 | 63.91 | +225.36 | 1.24 | 230 | 2.16 | 20 | 17 | -29.23 | Too small / low net |
| V13 long-only no morning | 1100 | 66.27 | +553.41 | 1.22 | 422 | 2.61 | 28 | 19 | -41.40 | Weaker than V4 |

## Interpretation

The sparse RR2-style strategy does not match the owner requirement. It may be clean, but it cannot be the main system if it only produces a couple of trades in a month. Any candidate with this shape is now tagged as research-only unless it is paired with a separate high-frequency primary lane.

The high-frequency V13 variants solve the activity problem, but most of them weaken the quality too much. They create more chances to trade, but the extra trades dilute PF, month stability, and average profit per trade.

The current best single-lane balance remains:

```text
V4: freq_h1_h4_long_rr0p7_v4_combo_rank1
```

It does not trade every market day, but when it is active it averages nearly 3 trades per active day and keeps the strongest long-window quality among the frequency-first candidates.

The current best portfolio-shaped candidate is the repaired robust portfolio:

```text
v6_freq_v4_rr0p7_max2
+
v13_ema_trend_h1h4_long_rr0p6_no_morning with server hour 18 blocked
+
freq_h1_h4_short_rr0p7_v1_night_early
```

That portfolio keeps the frequency requirement alive: 2443 trades, 600 active days, and 4.07 trades per active day in the offline MT5-derived trade CSV analysis.

## Current Verdict

```text
Sparse RR2 lane: TOO_SPARSE_FOR_PRIMARY_GOAL
V13 high-coverage lanes: NOT_READY_TO_REPLACE_V4
V4 frequency-first lane: BEST_CURRENT_PRIMARY_REVIEW_CANDIDATE
Robust repaired portfolio: BEST_CURRENT_PORTFOLIO_REVIEW_CANDIDATE
```

No candidate currently satisfies the full ideal of daily activity, win rate above 50%, strong PF, and stable monthly performance across almost every market day.

## Next Best Research Direction

Do not loosen filters blindly just to create trades. That reintroduces churn.

The next useful work is:

```text
1. Keep V4 as the best current review/demo candidate.
2. Treat V13 as a diagnostic companion only, not a replacement.
3. Search for one additional independent high-frequency signal family that can add active days without lowering PF below 1.25.
4. Every new family must pass the frequency gate and quality gate together.
```

The lesson is simple: frequency is mandatory, but frequency without edge is just a faster way to lose money.

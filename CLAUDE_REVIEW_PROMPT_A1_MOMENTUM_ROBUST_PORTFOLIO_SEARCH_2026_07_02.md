# Claude Review Prompt - A1 XAU M5 Momentum Robust Portfolio Search - 2026-07-02

Please independently review the latest A1 XAU M5 momentum candidate. The owner rejected sparse strategies as primary candidates; the target is an active intraday demo candidate with multiple trades per active day, win rate above 50%, positive PF/net, and no fake edge from duplicate stacking.

Boundary: offline review only. Do not touch MT5 runtime, charts, presets, orders, or positions.

## Files to Review

- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_SEARCH_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_STRESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_STRESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_WALKFORWARD_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_REPAIR_DIAGNOSTIC_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_WALKFORWARD_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_WALKFORWARD_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_WALKFORWARD_HALF_YEAR_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_WALKFORWARD_ROLLING_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_SEARCH_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_STRESS_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_STRESS_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_DAILY_LEDGER_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_DIAGNOSTIC_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_GUARD_SEARCH_2026_07_02.csv`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_SHAPE_OPTIMIZER_2026_07_02.md`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_SHAPE_OPTIMIZER_2026_07_02.json`
- `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_DAILY_SHAPE_OPTIMIZER_2026_07_02.csv`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_ROBUST_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_ROBUST_REPAIR_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DAILY_FIT_PORTFOLIO_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DAILY_FIT_REPAIR_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_DAILY_GUARD_FORWARD_DRAFT_2026_07_02.md`
- `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQUENCY_REQUIREMENT_VERDICT_2026_07_02.md`
- `xau-usd/xauusd-phase1/scripts/analyze_a1_momentum_robust_portfolio_search.py`
- `xau-usd/xauusd-phase1/scripts/analyze_a1_momentum_deep_portfolio_stress.py`
- `xau-usd/xauusd-phase1/scripts/analyze_a1_momentum_robust_portfolio_walkforward.py`
- `xau-usd/xauusd-phase1/scripts/analyze_a1_momentum_daily_guard_search.py`
- `xau-usd/xauusd-phase1/scripts/analyze_a1_momentum_daily_shape_optimizer.py`
- `xau-usd/xauusd-phase1/scripts/attach_a1_xau_m5_momentum_continuation.py`
- `xau-usd/xauusd-phase1/tests/test_a1_xau_m5_momentum_continuation.py`

## Candidate Under Review

```text
v6_freq_v4_rr0p7_max2
+
v13_ema_trend_h1h4_long_rr0p6_no_morning
+
freq_h1_h4_short_rr0p7_v1_night_early
```

Headline evidence:

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
| Top 25 winners removed | +1611.51 |
| Top 100 winners removed | +839.77 |
| Raw duplicate-like trade pct | 2.84% |

Split-period evidence:

| Window | Trades | WR | Net USD | PF | T/active |
|---|---:|---:|---:|---:|---:|
| 2022-07 to 2024-06 | 1169 | 64.50% | +441.29 | 1.24 | 3.72 |
| 2024-07 to 2026-06 | 1334 | 68.07% | +1492.28 | 1.44 | 4.62 |

Walk-forward caveat:

| Weakest bucket | Trades | WR | Net USD | PF | T/active |
|---|---:|---:|---:|---:|---:|
| 2022-H2 | 299 | 60.87% | +32.38 | 1.07 | 3.65 |

Best simple repair found:

```text
Block v13_ema_trend_h1h4_long_rr0p6_no_morning at server hour 18.
```

| Metric | Baseline robust | Repaired one-filter |
|---|---:|---:|
| Trades | 2503 | 2443 |
| WR | 66.40% | 66.56% |
| Net USD | +1933.57 | +1944.34 |
| PF | 1.37 | 1.38 |
| Active days | 603 | 600 |
| T/active | 4.15 | 4.07 |
| 2022-H2 net/PF | +32.38 / 1.07 | +46.68 / 1.10 |

Repaired walk-forward evidence:

| Check | Result |
|---|---:|
| Trades | 2443 |
| Active days | 600 |
| Trades / active day | 4.07 |
| Half-year buckets positive | 8 / 8 |
| Quarter buckets positive | 15 / 16 |
| Weakest quarter | 2022-Q3: -15.01 / PF 0.91 / 103 trades |
| Weakest rolling 250-trade window | +0.66 / PF 1.00 |

Owner constraint to keep front-and-center: sparse strategies are not acceptable as primary lanes. A candidate that only produces a few trades per month should be rejected or marked research-only even if PF looks clean. The preferred operating shape is roughly 3-5 trades per active day, with 2 trades per active day as the bare minimum.

## New Daily-Fit Candidate

Because the owner clarified that day-by-day behavior matters more than sparse PF, I added a daily-fit search. It explicitly gates on active days, trades per active day, 3+ trade active-day coverage, positive-day rate, PF/net, top-winner robustness, and duplicate-like overlap.

Top daily-fit candidate:

```text
freq_h1_h4_long_rr0p7_cost005_block_weak_hours_v1
+
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning
```

| Metric | Value |
|---|---:|
| Deduped trades | 2785 |
| Win rate | 65.35% |
| Net USD | +1757.13 |
| Profit factor | 1.29 |
| Active days | 689 |
| Trades / active day | 4.04 |
| 3+ trade active-day pct | 55.59% |
| Positive active-day pct | 53.85% |
| Median active-day PnL | +0.95 |
| Worst active day | -40.12 |
| Top 100 winners removed | +672.60 |
| Max closed DD | 125.35 |
| Raw duplicate-like overlap | 4.08% |
| Older split net/PF | +318.70 / 1.15 |
| Newer split net/PF | +1438.43 / 1.37 |

Planned magics if reviewed/approved later:

- `932250` daily-fit long weak-hours lane
- `932251` daily-fit V13 both-direction EMA trend lane

This candidate currently looks like the best match to the owner's real operating requirement, but it has a real caveat: older split PF is only 1.15, so please stress whether it is too recent-regime dependent.

## New Daily-Fit Repair Candidate

I then stress-tested the daily-fit candidate and ran a limited repair diagnostic against member-hour pockets. The best repair blocks only two weak V13 pockets:

```text
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@18
v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@22
```

It keeps the long weak-hours lane unchanged and changes only the V13 global blocked-hour list.

| Metric | Baseline daily-fit | Repaired daily-fit |
|---|---:|---:|
| Deduped trades | 2785 | 2589 |
| Win rate | 65.35% | 65.66% |
| Net USD | +1757.13 | +1764.38 |
| Profit factor | 1.29 | 1.31 |
| Active days | 689 | 645 |
| Trades / active day | 4.04 | 4.01 |
| 3+ trade active-day pct | 55.59% | 55.04% |
| Positive active-day pct | 53.85% | 53.02% |
| Positive / negative months | 34 / 14 | 37 / 11 |
| Worst month USD | -35.87 | -28.45 |
| Top 100 winners removed | +672.60 | +681.97 |
| Max closed DD | 125.35 | 108.59 |
| Older split net/PF | +318.70 / 1.15 | +376.50 / 1.19 |
| Newer split net/PF | +1438.43 / 1.37 | +1387.88 / 1.38 |

Planned repair magics if reviewed/approved later:

- `932260` daily-fit repair long weak-hours lane
- `932261` daily-fit repair V13 both-direction EMA trend lane

Important caveat: this repair is based on weak member-hour pockets discovered from the same historical data, so please treat it as a review candidate, not proof. The main question is whether the modest PF/DD/month-stability improvement is worth the added overfit risk.

## New Daily Guard Candidate

The owner rejected the sparse monthly path again: the main candidate must create multiple trades on active days. I added an offline daily lifecycle simulation over the repaired daily-fit package. This tests shared portfolio controls, not per-EA controls.

Best guard:

```text
Base: repaired daily-fit package
Profit target: none
Daily loss stop: -25 USD
Portfolio max trades/day: 6
Max losses/day: none
```

| Metric | Repaired daily-fit no guard | Daily guarded |
|---|---:|---:|
| Deduped trades | 2589 | 2130 |
| Retention | 100.00% | 82.27% |
| Win rate | 65.66% | 65.59% |
| Net USD | +1764.38 | +1450.35 |
| Profit factor | 1.31 | 1.33 |
| Active days | 645 | 645 |
| Trades / active day | 4.01 | 3.30 |
| 3+ trade active-day pct | 55.04% | 55.04% |
| Positive active-day pct | 53.02% | 55.35% |
| Median active-day PnL | +0.95 | +1.89 |
| Worst active day | -40.12 | -38.13 |
| Max closed DD | 108.59 | 90.82 |
| Top 25 winners removed | n/a | +1148.04 |
| Top 100 winners removed | +681.97 | +403.96 |
| Older split net/PF | +376.50 / 1.19 | +295.57 / 1.18 |
| Newer split net/PF | +1387.88 / 1.38 | +1154.78 / 1.41 |

Planned daily-guard magics if reviewed/approved later:

- `932270` daily-guard long weak-hours lane
- `932271` daily-guard V13 both-direction EMA trend lane

Important implementation note: the EA now has default-off portfolio daily guard inputs, and the planned variants use a shared guard magic CSV `932270,932271`. Please verify this is a faithful way to model the historical shared daily cap/loss stop. Existing runtime is unchanged.

## Daily-Shape Optimizer Confirmation

I then added a broader optimizer over weak member-hour blocks plus daily lifecycle guards. It searched `4800` permutations and converged on the same top candidate:

```text
Block:
- v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@18
- v13_ema_trend_h1h4_both_rr0p6_no_weak_short_no_long_morning@22

Guard:
- no profit target
- daily loss stop -25 USD
- max 6 shared portfolio trades/day
- no max-loss-count rule
```

Top result:

| Metric | Value |
|---|---:|
| Trades | 2130 |
| Retention | 82.27% |
| Win rate | 65.59% |
| Net USD | +1450.35 |
| Profit factor | 1.33 |
| Active days | 645 |
| Trades / active day | 3.30 |
| Positive active days | 55.35% |
| 3+ trade active days | 55.04% |
| Median active-day PnL | +1.89 |
| P25 active-day PnL | -3.82 |
| Worst active day | -38.13 |
| Top 100 winners removed | +403.96 |
| Max closed DD | 90.82 |
| Older split PF | 1.18 |
| Newer split PF | 1.41 |

Please verify whether this convergence is meaningful or whether the daily objective is still too weak because the positive active-day rate is only around 55%.

## What I Need You To Verify

1. Recompute the top candidate directly from the underlying trade CSVs, not from the summary.
2. Verify deterministic de-duplication: same-minute same-direction events must keep only the priority-selected row.
3. Challenge whether 2.84% raw duplicate-like overlap is acceptable.
4. Stress the older/newer split. Is PF 1.24 in the older half strong enough for forward demo, or is the candidate still too recent-regime dependent?
5. Stress the half-year and rolling 250-trade windows. Does weak-but-positive 2022-H2 invalidate the candidate, or is it acceptable for a small forward demo?
6. Decide whether the one-filter repair is worth using or whether it is overfitting the weak 2022-H2 bucket.
7. Check whether the result is carried by one lane, one direction, one session, or one year.
8. Verify top-winner removal: top 25 and top 100 winners removed should remain positive.
9. Review the forward drafts and attach config for fidelity to tested inputs:
   - `932230` V6 max2 long
   - `932231` V13 long no morning
   - `932232` short night/early
   - repaired candidate magics `932240`, `932241`, `932242`
   - daily-fit baseline magics `932250`, `932251`
   - daily-fit repair magics `932260`, `932261`
10. Confirm whether this candidate better fits the owner requirement than the sparse RR2 lane.
11. Compare the robust repaired portfolio, the daily-fit baseline, and the daily-fit repair. Which one should be the next demo-forward candidate if only one can be attached?
12. Review the daily guard candidate. Is max 6 portfolio trades/day plus a -25 USD daily loss stop a real improvement in daily shape, or is it giving up too much net/top-winner cushion?
13. Verify that the planned shared guard over magics `932270,932271` is faithful to the historical simulation and not a per-chart cap mismatch.
14. Return a verdict:
   - `ENDORSE_FOR_SMALL_FORWARD_DEMO`
   - `REVISE`
   - `REJECT`

## Be Constructive

If you reject or revise, please do not only say "overfit" or "not enough." Give the exact repair:

- which lane to remove or keep,
- which hour/session/direction is dragging results,
- whether to use two lanes instead of three,
- whether the 0.01-lot forward demo should run anyway as a low-risk discovery test,
- what pass/kill rules should be locked.

The owner wants a practical intraday EA portfolio, not sparse academic edge. We need enough trades to observe daily behavior while avoiding duplicate-stacked fake edge.

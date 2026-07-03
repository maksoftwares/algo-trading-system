# Claude Review Prompt — A1 XAU M5 Momentum V12 EMA-Trend Mask Candidate

Claude, please independently review the new V12 candidate. Be rigorous but constructive. The owner’s actual goal is not a sparse high-PF strategy; we need a strategy or portfolio lane that can produce multiple intraday opportunities on active days, maintain win rate above 50%, and remain net profitable after realistic cost.

Boundary:

```text
Offline/repo review only.
Do not touch MT5 runtime.
Do not attach EAs.
Do not modify presets or broker-action settings.
```

Primary verdict doc:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V12_EMA_TREND_MASK_VERDICT_2026_07_02.md
```

Primary MT5 outputs:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V12_EMA_TREND_MASK_TWO_YEAR_2024_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V12_EMA_TREND_MASK_TWO_YEAR_2024_07_2026_06.json
xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_freq_first_v12_ema_trend_mask_two_year_2024_07_2026_06_20260701/
```

Code changed:

```text
xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5
xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py
```

Context:

```text
V4 remains the prior best control:
- 612 trades
- 66.67% WR
- +732.83 USD
- PF 1.47
- 204 active days
- 3.00 trades per active day

V10 opening range solved frequency but failed edge.
V11 EMA-trend solved frequency but raw PF was too thin.
V12 uses V11-derived bad-hour masks and exact MT5 re-runs.
```

Leading V12 candidate:

```text
v12_ema_trend_h1h4_both_rr0p6_block_bad_hours

Two-year MT5:
- 1078 trades
- 67.63% WR
- +775.94 USD
- PF 1.25
- 324 active days
- 3.33 trades per active day
- 17 positive months / 7 negative months
- top-10 winners removed: +668.86
- top-25 winners removed: +513.68
```

Direction split:

```text
LONG: 820 trades, 67.32% WR, +497.06, PF 1.22
SHORT: 258 trades, 68.60% WR, +278.88, PF 1.33
```

Session split:

```text
Morning: 261 trades, 67.05% WR, +203.32, PF 1.28
Afternoon: 317 trades, 67.19% WR, +205.40, PF 1.18
Evening: 107 trades, 66.36% WR, +63.32, PF 1.20
Night: 393 trades, 68.70% WR, +303.90, PF 1.33
```

Main concern:

```text
The V12 hour mask was derived from V11 diagnostics on the same two-year window.
So this is a review candidate, not a proven deployable edge.
```

Please independently verify:

1. Recompute the V12 table from the trade CSVs.
2. Confirm the direction/session splits.
3. Check whether the V12 both-direction lane genuinely improves the project shape versus V4, despite lower PF.
4. Decide whether higher frequency + higher net + more active days is worth accepting lower PF than V4.
5. Check whether the hour masks are too post-hoc, and propose a stricter forward-test protocol.
6. Stress outlier concentration beyond top-25 removal if needed.
7. Check month stability and identify bad regimes.
8. Confirm no demo/runtime attachment is implied by the docs.
9. Recommend one of:
   - APPROVE_FOR_FROZEN_FORWARD_DEMO_SPEC
   - REVISE_BEFORE_FORWARD_SPEC
   - REJECT_AS_POST_HOC_MASK

If you approve, give the exact frozen forward-test spec:

```text
symbol
timeframe
magic number
lot
signal mode
blocked hours
direction mode
H1/H4 filter state
RR
cost cap
minimum sample
pass rule
kill rule
what must not change during test
```

Also answer this owner-level question plainly:

```text
If the owner wants multiple trades per active day and >50% win rate, is V12 a better demo candidate than V4, or should V4 remain primary and V12 run only as a separate experimental lane?
```


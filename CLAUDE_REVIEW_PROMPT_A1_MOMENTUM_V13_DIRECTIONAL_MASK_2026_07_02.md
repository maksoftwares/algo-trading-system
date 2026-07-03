# Claude Review Prompt — A1 XAU M5 Momentum V13 Directional-Mask Candidate

Claude, please independently review the new V13 candidate. Be rigorous, but keep the owner’s real objective in view:

```text
multiple intraday opportunities on active days
win rate above 50%
positive net/PF after realistic costs
enough active-day coverage to support a daily-profit style system
```

Boundary:

```text
Offline/repo review only.
Do not touch MT5 runtime.
Do not attach EAs.
Do not modify presets or broker-action settings.
```

Primary verdict doc:

```text
xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V13_DIRECTIONAL_MASK_VERDICT_2026_07_02.md
```

Primary MT5 outputs:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_TWO_YEAR_2024_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_TWO_YEAR_2024_07_2026_06.json
xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_freq_first_v13_directional_mask_two_year_2024_07_2026_06_20260701/
```

Code changed:

```text
xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5
xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py
```

Context:

```text
V4 remains the prior best control and has higher PF but lower frequency.
V12 was the first candidate with strong frequency but had weak direction/session pockets.
V13 adds direction-specific hour blocks to remove the weakest V12 short-side pockets.
```

V4 control:

```text
freq_h1_h4_long_rr0p7_v4_combo_rank1
- 612 trades
- 66.67% WR
- +732.83 USD
- PF 1.47
- 204 active days
- 3.00 trades per active day
- top-25 removed: +430.71
- 19 positive months / 5 negative months
```

V12 prior candidate:

```text
v12_ema_trend_h1h4_both_rr0p6_block_bad_hours
- 1078 trades
- 67.63% WR
- +775.94 USD
- PF 1.25
- 324 active days
- 3.33 trades per active day
- top-25 removed: +513.68
- 17 positive months / 7 negative months
```

Leading V13 candidate:

```text
v13_ema_trend_h1h4_both_rr0p7_no_weak_short
- 908 trades
- 65.09% WR
- +861.16 USD
- PF 1.32
- 306 active days
- 2.97 trades per active day
- 18 positive months / 6 negative months
- top-10 winners removed: +732.73
- top-25 winners removed: +553.62
- worst month: -57.42
- best month: +246.07
```

Four-year validation addendum:

```text
After the two-year result, Codex ran a longer validation from 2022-07-01 through 2026-06-30.

V4 control:
- 1132 trades
- 65.90% WR
- +1042.07 USD
- PF 1.45
- 383 active days
- 36 positive months / 11 negative months
- top-25 removed: +724.76
- worst month: -21.67

V13 leading candidate:
- 1786 trades
- 61.53% WR
- +862.93 USD
- PF 1.20
- 668 active days
- 25 positive months / 23 negative months
- top-25 removed: +555.39
- worst month: -57.42
```

Updated Codex interpretation:

```text
V13 should NOT replace V4.
V4 remains primary.
V13 is only a possible companion/shadow lane because it gives far more active-day coverage but lower quality.
```

Leading V13 inputs:

```text
Signal mode: SIGNAL_M5_EMA_TREND_CONTINUATION
Direction mode: both
H1 EMA20/50 trend filter: on
H4 EMA20/50 trend filter: on
Risk reward: 0.70R
Cost cap: 0.05R
General blocked hours: 0,2,4,9,10,11,12,16,19,20
Short-only blocked hours: 13,14,15,17,18
Long-only blocked hours: none
M5 EMA fast/slow: 8/21
M5 trend slope: 3 bars, minimum 0.03 ATR
Max distance from fast EMA: 1.20 ATR
Minimum range: 0.35 ATR
Minimum body fraction: 0.30
Long close location: >= 0.58
Short close location: <= 0.42
Minimum 3-bar move: 0.10 ATR
```

Direction split:

```text
LONG: 754 trades, 64.1% WR, +547 USD, PF 1.24
SHORT: 154 trades, 70.1% WR, +315 USD, PF 1.72
```

Please independently verify:

1. Recompute the V13 table from the trade CSVs.
2. Confirm direction split and top-winner removal.
3. Compare V13 vs V4: is much higher active-day coverage worth lower PF, lower net, and worse month stability over four years?
4. Compare V13 vs V12: did directional blocking genuinely improve quality, or did it overfit?
5. Check whether the short-only blocked hours are too post-hoc.
6. Check month stability and worst-month risk.
7. Check if the V13 both-direction lane should forward-test beside V4 or instead remain only shadow.
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
general blocked hours
long-only blocked hours
short-only blocked hours
direction mode
H1/H4 filter state
RR
cost cap
minimum sample
pass rule
kill rule
what must not change during test
```

Owner-level question:

```text
Should V13 be rejected because the four-year result is weaker than V4, or is it still worth running as a separate companion/shadow lane because it gives 668 active days vs V4's 383?
```

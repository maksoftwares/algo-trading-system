# A1 XAU M5 Momentum Frequency-First V13 Directional-Mask Verdict

Generated: 2026-07-02  
Scope: analysis/backtest only; no demo runtime changes; no MT5 chart or preset changes.

## Why this test exists

V12 finally produced the project shape we wanted: high win rate, higher frequency, positive net, and robustness after top-winner removal. But the V12 direction/session split showed weak pockets:

```text
SHORT afternoon: PF 0.98
SHORT evening: PF 1.03
LONG morning: PF 1.04
```

V13 added default-off direction-specific blocked-hour inputs so we can test those weak pockets without bluntly blocking the same hours for both long and short entries.

Default behavior remains unchanged when the new inputs are blank:

```text
InpBlockedLongEntryHoursCsv=""
InpBlockedShortEntryHoursCsv=""
```

## Test window and method

```text
Symbol: XAUUSD
Timeframe: M5
Model: MT5 Strategy Tester exact run from project runner
Window: 2024-07-01 through 2026-06-30
Deposit: 1000 USD
Runtime touched: no
Current default signal mode changed: no
```

Artifacts:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_TWO_YEAR_2024_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_TWO_YEAR_2024_07_2026_06.json
xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_freq_first_v13_directional_mask_two_year_2024_07_2026_06_20260701/
```

## Result table

| Variant | Trades | WR % | Net | PF | Active days | Trades / active day | +months | -months | Top 10 removed | Top 25 removed | Worst month | Best month |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V4 control: `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 612 | 66.67 | +732.83 | 1.47 | 204 | 3.00 | 19 | 5 | +604.50 | +430.71 | -21.67 | +194.58 |
| V12 both 0.6R, block bad hours | 1078 | 67.63 | +775.94 | 1.25 | 324 | 3.33 | 17 | 7 | +668.86 | +513.68 | -118.26 | +227.92 |
| V13 both 0.6R, no weak shorts | 982 | 68.13 | +780.60 | 1.29 | 306 | 3.21 | 17 | 7 | +673.79 | +520.17 | -65.01 | +227.92 |
| V13 both 0.6R, no weak shorts / no long morning | 797 | 69.01 | +761.43 | 1.36 | 300 | 2.66 | 17 | 7 | +654.91 | +502.68 | -38.11 | +187.67 |
| **V13 both 0.7R, no weak shorts** | **908** | **65.09** | **+861.16** | **1.32** | **306** | **2.97** | **18** | **6** | **+732.73** | **+553.62** | **-57.42** | **+246.07** |
| V13 short-only core 0.6R | 162 | 72.22 | +283.54 | 1.67 | 72 | 2.25 | 10 | 6 | +179.77 | +42.21 | -29.23 | +139.09 |
| V13 long-only no morning 0.6R | 635 | 68.19 | +477.89 | 1.28 | 228 | 2.79 | 15 | 9 | +373.13 | +225.66 | -41.40 | +111.93 |

## Leading candidate

```text
v13_ema_trend_h1h4_both_rr0p7_no_weak_short
```

Inputs:

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

| Direction | Trades | WR % | Net | PF |
|---|---:|---:|---:|---:|
| LONG | 754 | 64.1 | +547 | 1.24 |
| SHORT | 154 | 70.1 | +315 | 1.72 |

## Verdict

```text
V13 directional-mask: COMPANION_REVIEW_CANDIDATE_NOT_ATTACHED
```

This is the strongest frequency-first companion candidate produced in the V10-V13 sequence, but it is not a replacement for V4 after four-year validation.

Compared with V4:

```text
V4 has higher PF: 1.47 vs 1.32
V13 has more trades: 908 vs 612
V13 has more active days: 306 vs 204
V13 has higher net: +861.16 vs +732.83
V13 remains positive after top-25 winner removal: +553.62
```

Compared with V12:

```text
V13 reduces trades from 1078 to 908 but improves PF from 1.25 to 1.32.
V13 improves net from +775.94 to +861.16.
V13 improves worst month from -118.26 to -57.42.
V13 improves month count from 17/7 to 18/6.
```

## Why this matters

The owner wants:

```text
multiple trades on active days
win rate above 50%
positive net result
enough active days to support a daily-profit style system
```

V13 is not perfect, but it satisfies this shape better than any prior candidate:

```text
908 two-year trades
306 active days
2.97 trades per active day
65.09% win rate
PF 1.32
```

## Concerns

```text
1. Hour masks are still derived from the same diagnostic family, so forward-test discipline is mandatory.
2. V13 PF is lower than V4, even though total net and frequency are better.
3. It uses both directions; shorts are high-quality but lower-frequency.
4. It needs independent review before demo attachment.
5. It should not replace V4 blindly; the sensible forward test is side-by-side with separate magic numbers.
```

## Recommended next action

Ask for independent review and prepare a frozen forward-test spec if accepted.

Recommended forward-test structure:

```text
Run V4 and V13 side-by-side on demo with separate magic numbers.
Keep fixed 0.01 lot.
No mid-test parameter changes.
Judge after at least 100 V13 trades or 4 full trading weeks, whichever comes later.
Pass only if V13 stays positive, WR > 55%, PF >= 1.20, and no single day dominates net.
Kill if rolling 40-trade PF < 0.90, or drawdown breaches pre-set demo limit.
```

No V13 demo attachment is authorized yet.

## Four-year validation addendum

After the two-year V13 diagnostic result, the leading candidate was tested against the longer four-year window used for V4:

```text
Window: 2022-07-01 through 2026-06-30
Variants: V4 control vs V13 leading candidate only
Runtime touched: no
```

Artifacts:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_FOUR_YEAR_2022_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_DIRECTIONAL_MASK_FOUR_YEAR_2022_07_2026_06.json
```

Four-year comparison:

| Variant | Trades | WR % | Net | PF | Active days | Trades / active day | +months | -months | Top 10 removed | Top 25 removed | Worst month | Best month |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V4 control | 1132 | 65.90 | +1042.07 | 1.45 | 383 | 2.96 | 36 | 11 | +899.51 | +724.76 | -21.67 | +194.58 |
| V13 leading candidate | 1786 | 61.53 | +862.93 | 1.20 | 668 | 2.67 | 25 | 23 | +734.50 | +555.39 | -57.42 | +246.07 |

Four-year interpretation:

```text
V13 gives far more active-day coverage: 668 active days vs 383.
V13 does not beat V4 on net, PF, win rate, month stability, or worst month.
V13 remains robust after top-winner removal, but it is lower quality than V4.
```

Updated recommendation:

```text
V4 remains the primary candidate.
V13 should not replace V4.
V13 may be reviewed as a separate companion/shadow lane if the owner values coverage more than PF.
```

## Four-year alternative validation addendum

After the owner clarified that sparse strategies do not satisfy the project goal, the cleaner V13 alternatives were also tested across the same four-year window.

Artifacts:

```text
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_ALT_FOUR_YEAR_2022_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V13_ALT_FOUR_YEAR_2022_07_2026_06.json
```

| Variant | Trades | WR % | Net USD | PF | Active days | Trades / active day | +months | -months | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| V4 control | 1132 | 65.90 | +1042.07 | 1.45 | 383 | 2.96 | 36 | 11 | Remains primary |
| V13 both 0.6R, no weak shorts | 1921 | 64.97 | +775.18 | 1.18 | 668 | 2.88 | 24 | 24 | Too noisy |
| V13 both 0.6R, no weak shorts / no long morning | 1596 | 65.54 | +778.77 | 1.23 | 651 | 2.45 | 27 | 21 | Coverage candidate only |
| V13 short-only core | 496 | 63.91 | +225.36 | 1.24 | 230 | 2.16 | 20 | 17 | Too small / low net |
| V13 long-only no morning | 1100 | 66.27 | +553.41 | 1.22 | 422 | 2.61 | 28 | 19 | Weaker than V4 |

Conclusion:

```text
The V13 alternatives improve active-day coverage, but they do not solve the full business requirement.
More trades are available, but the extra trades reduce PF and monthly stability.
Do not replace V4 with V13 just to increase activity.
```

# A1 XAU M5 Momentum Frequency-First V12 EMA-Trend Hour-Mask Verdict

Generated: 2026-07-02  
Scope: analysis/backtest only; no demo runtime changes; no MT5 chart or preset changes.

## Why this test exists

V11 proved that M5 EMA-trend continuation can create the kind of trade frequency the owner wants, but raw V11 PF was too weak. V12 tests whether the weak result was caused by bad trading hours diluting a usable high-frequency signal.

The V12 masks were derived from exact V11 trade CSV hour-bucket diagnostics. They were then re-run in the MT5 Strategy Tester as explicit variants, not accepted from spreadsheet math alone.

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
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V12_EMA_TREND_MASK_TWO_YEAR_2024_07_2026_06.md
xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V12_EMA_TREND_MASK_TWO_YEAR_2024_07_2026_06.json
xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_freq_first_v12_ema_trend_mask_two_year_2024_07_2026_06_20260701/
```

## Result table

| Variant | Trades | WR % | Net | PF | Active days | Trades / active day | +months | -months | Top 10 removed | Top 25 removed | Worst month | Best month |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| V4 control: `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 612 | 66.67 | +732.83 | 1.47 | 204 | 3.00 | 19 | 5 | +604.50 | +430.71 | -21.67 | +194.58 |
| V12 H1+H4 long 0.7R, block bad hours | 710 | 65.49 | +682.39 | 1.33 | 234 | 3.03 | 17 | 7 | +550.70 | +373.14 | -45.23 | +176.46 |
| V12 H1+H4 long 0.6R, block bad hours | 810 | 68.15 | +569.03 | 1.26 | 237 | 3.42 | 13 | 11 | +455.29 | +302.96 | -38.45 | +141.26 |
| V12 H1+H4 both 0.6R, block bad hours | 1078 | 67.63 | +775.94 | 1.25 | 324 | 3.33 | 17 | 7 | +668.86 | +513.68 | -118.26 | +227.92 |
| V12 H1+H4 long 0.7R, keep strong hours | 628 | 66.08 | +633.54 | 1.35 | 228 | 2.75 | 14 | 10 | +506.92 | +334.19 | -32.09 | +170.29 |
| V12 H1+H4 long 0.6R, V4 mask plus bad hours | 667 | 67.17 | +341.18 | 1.18 | 224 | 2.98 | 14 | 10 | +228.10 | +79.36 | -41.21 | +138.25 |

## Verdict

```text
V12 EMA-trend hour-mask: REVIEW_CANDIDATE_NOT_ATTACHED
```

This is the first post-V4 candidate that materially improves the project shape:

```text
V12 both-direction:
- 1078 trades over two years
- 324 active days
- 3.33 trades per active day
- 67.63% win rate
- +775.94 USD net
- PF 1.25
- top-25 winners removed remains +513.68 USD
```

Compared with V4:

```text
V4 has better PF and fewer negative months.
V12 both-direction has more trades, more active days, higher net, and stronger fit to the owner's frequency goal.
```

## Why this matters

The previous experiments failed in two different ways:

```text
Sparse candidates: looked clean but did not trade enough.
Raw high-frequency candidates: traded enough but PF collapsed.
```

V12 is the first one that clears both rough screens:

```text
meaningful frequency
win rate above 50%
positive net
PF at the minimum review bar
not destroyed by top-winner removal
```

It should still not be promoted directly from this backtest. It needs independent review and a frozen forward-test spec because the hour mask was derived from prior V11 diagnostics.

## Direction and session split for the leading V12 candidate

Leading candidate:

```text
v12_ema_trend_h1h4_both_rr0p6_block_bad_hours
```

Direction:

| Direction | Trades | WR % | Net | PF |
|---|---:|---:|---:|---:|
| LONG | 820 | 67.32 | +497.06 | 1.22 |
| SHORT | 258 | 68.60 | +278.88 | 1.33 |

Session:

| Session | Trades | WR % | Net | PF |
|---|---:|---:|---:|---:|
| Morning | 261 | 67.05 | +203.32 | 1.28 |
| Afternoon | 317 | 67.19 | +205.40 | 1.18 |
| Evening | 107 | 66.36 | +63.32 | 1.20 |
| Night | 393 | 68.70 | +303.90 | 1.33 |

Direction/session:

| Bucket | Trades | WR % | Net | PF |
|---|---:|---:|---:|---:|
| LONG morning | 185 | 64.32 | +19.17 | 1.04 |
| LONG afternoon | 246 | 68.29 | +212.82 | 1.27 |
| LONG evening | 82 | 68.29 | +60.56 | 1.28 |
| LONG night | 307 | 68.08 | +204.51 | 1.30 |
| SHORT morning | 76 | 73.68 | +184.15 | 1.95 |
| SHORT afternoon | 71 | 63.38 | -7.42 | 0.98 |
| SHORT evening | 25 | 60.00 | +2.76 | 1.03 |
| SHORT night | 86 | 70.93 | +99.39 | 1.43 |

Interpretation:

```text
Both directions contribute.
Shorts are lower-frequency but higher-quality.
The weakest pocket is SHORT afternoon/evening, which should be watched before forward promotion.
```

## Concerns

```text
1. V12 both-direction PF is only 1.25, which is the lower edge of acceptability.
2. It has 7 negative months out of 24.
3. Worst month is -118.26 USD, larger than V4's worst month.
4. Hour masks were derived from the same two-year diagnostic data, so forward-test discipline is required.
5. It uses both directions, so direction-level attribution must be reviewed before demo attachment.
```

## Recommended next action

Ask for independent review of V12, especially:

```text
1. Is V12 both-direction a better demo candidate than V4 despite lower PF?
2. Is the higher frequency worth the lower PF?
3. Are the blocked hours defensible or too post-hoc?
4. Does direction-level performance support both-direction trading?
5. Should the forward test run V4 and V12 side-by-side with separate magic numbers?
```

No V12 demo attachment is authorized yet.

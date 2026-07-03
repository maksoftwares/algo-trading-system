# A1 XAU M5 Momentum Frequency-First V7 Pullback Verdict - 2026-07-02

## Purpose

The owner clarified that the target is not a sparse strategy with a clean equity curve. The target is a frequent intraday strategy with:

- Multiple trades on active days.
- Win rate above 50%.
- Positive expectancy.
- Enough opportunity to support daily profit goals.

V7 was built to test a genuinely different intraday signal family inside the existing default-safe `A1XauM5MomentumContinuationExecutor.mq5`:

```text
M5 EMA20 pullback continuation
```

This is different from the V4 break-and-run entry. The idea was to see whether waiting for pullbacks into M5 EMA20 could create more daily opportunities without losing the >50% win-rate profile.

No live/demo MT5 runtime was changed. The EA default remains:

```text
InpSignalMode = SIGNAL_BREAK_AND_RUN
```

The pullback mode only runs when explicitly selected in tester/preset inputs:

```text
InpSignalMode = SIGNAL_EMA_PULLBACK
```

## Test Setup

Period:

```text
2024-07-01 through 2026-06-30
```

Tester:

```text
MT5 every tick / isolated sandbox / 1000 USD deposit
```

Sandbox:

```text
C:\MT5A1M5MomentumBacktest
```

## Result

| Variant | Trades | Win Rate | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Negative Months |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 612 | 66.67% | +732.83 | 1.47 | 204 | 3.00 | 19 | 5 |
| `v7_pullback_h1h4_long_rr0p6_v4mask` | 811 | 64.00% | +88.02 | 1.04 | 230 | 3.53 | 13 | 11 |
| `v7_pullback_h1h4_both_rr0p6` | 1679 | 63.01% | +52.90 | 1.01 | 366 | 4.59 | 12 | 12 |
| `v7_pullback_h1h4_long_rr0p6_stop500` | 1135 | 63.61% | +30.08 | 1.01 | 253 | 4.49 | 12 | 12 |
| `v7_pullback_h1h4_long_rr0p5` | 1350 | 67.48% | +25.13 | 1.01 | 255 | 5.29 | 14 | 10 |
| `v7_pullback_h1h4_long_rr0p6` | 1212 | 63.12% | -21.32 | 0.99 | 253 | 4.79 | 12 | 12 |
| `v7_pullback_h1_long_rr0p6` | 1555 | 62.32% | -279.39 | 0.94 | 324 | 4.80 | 12 | 12 |

## Verdict

```text
REJECT_PULLBACK_FAMILY_FOR_NOW
```

The EMA pullback family does increase trade count and active-day coverage, but the expectancy is too weak. Most variants cluster around PF `1.00`, which means the extra trades are mostly churn.

This directly answers an important question:

```text
More trades alone will not make the system profitable.
```

The V4 break-and-run entry remains much stronger because it keeps similar or better win rate with far better PF and net profit.

## What We Learned

1. The pullback family can create the activity level we want.

   The both-direction pullback variant reached `1679` trades and `366` active days in two years, or `4.59` trades per active day.

2. The extra activity is low quality.

   PF was only `1.01` for the most active both-direction variant.

3. H1-only pullback is clearly worse.

   It produced `1555` trades but lost `-279.39 USD`, showing that H4 agreement still matters.

4. The V4 entry quality is real.

   V4 made `+732.83 USD` over the same period while the best pullback variant made only `+88.02 USD`.

5. The next EA should not simply loosen entry conditions.

   We need a different edge mechanism, not just more signals.

## Decision

Do not promote V7 pullback to demo.

Keep V4 as the current best frequency-first candidate and keep V6 max2 as a diagnostic optional upgrade. Continue the hunt with a different mechanism, such as:

- momentum continuation after compression expansion,
- trend day continuation after a shallow flag,
- volatility expansion with session confirmation,
- failed counter-move reversal after H1/H4 trend holds.

## Artifacts

| Artifact | Path |
|---|---|
| V7 MT5 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V7_PULLBACK_TWO_YEAR_2024_07_2026_06.md` |
| V7 JSON | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V7_PULLBACK_TWO_YEAR_2024_07_2026_06.json` |
| EA source | `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5` |
| Runner | `xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py` |

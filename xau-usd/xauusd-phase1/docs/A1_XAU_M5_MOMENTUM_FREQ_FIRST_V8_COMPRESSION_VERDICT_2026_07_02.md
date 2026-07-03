# A1 XAU M5 Momentum Frequency-First V8 Compression Verdict - 2026-07-02

## Purpose

V8 tested a genuinely different intraday mechanism:

```text
M5 compression -> directional expansion
```

The idea was to catch moves after a quiet range breaks, while still satisfying the owner goal:

- multiple trades on active days,
- win rate above 50%,
- positive expectancy,
- enough trade frequency to support daily profit objectives.

No live/demo MT5 runtime was changed. The EA default remains `SIGNAL_BREAK_AND_RUN`; compression-expansion is default-off and only runs when `InpSignalMode = SIGNAL_COMPRESSION_EXPANSION`.

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
| `v8_compress_h1_long_rr0p6` | 11 | 81.82% | +19.93 | 1.90 | 11 | 1.00 | 8 | 2 |
| `v8_compress_h1h4_long_rr0p6` | 9 | 77.78% | +15.64 | 1.70 | 9 | 1.00 | 6 | 2 |
| `v8_compress_h1h4_both_rr0p6` | 9 | 77.78% | +15.64 | 1.70 | 9 | 1.00 | 6 | 2 |
| `v8_compress_h1h4_long_rr0p5` | 9 | 77.78% | +9.36 | 1.42 | 9 | 1.00 | 6 | 2 |
| `v8_compress_h1h4_long_rr0p6_v4mask` | 7 | 71.43% | +6.24 | 1.28 | 7 | 1.00 | 5 | 2 |
| `v8_compress_h1h4_long_rr0p6_tight` | 0 | 0.00% | 0.00 | n/a | 0 | 0.00 | 0 | 0 |

## Verdict

```text
REJECT_COMPRESSION_EXPANSION_FOR_PRIMARY_GOAL
```

The compression-expansion idea is clean, but far too sparse. It produces only `7` to `11` trades over two years, so it fails the frequency requirement immediately.

The high win rate is not useful for the current business goal because the signal barely appears.

## What We Learned

1. Compression-expansion is the opposite of the V7 pullback problem.

   V7 produced enough trades but weak expectancy. V8 produced decent win rate but almost no trades.

2. The target lives between these extremes.

   We need the entry quality of V4 with either more active-day coverage or an additional independent family that trades regularly.

3. Do not over-tune compression.

   Loosening compression enough to create hundreds of trades would likely turn it into the same low-quality churn we saw in V7.

## Decision

Do not promote V8 to demo.

Keep V4 as the current best frequency-first candidate. Keep V6 max2 as a diagnostic optional upgrade. Continue the hunt with a different mechanism.

Next candidate family to test:

```text
M5 sweep-and-reclaim reversal in the direction of H1/H4 trend
```

This targets a different market behavior: a liquidity sweep below/above a recent range, followed by a strong reclaim candle.

## Artifacts

| Artifact | Path |
|---|---|
| V8 MT5 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V8_COMPRESSION_TWO_YEAR_2024_07_2026_06.md` |
| V8 JSON | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V8_COMPRESSION_TWO_YEAR_2024_07_2026_06.json` |
| EA source | `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5` |
| Runner | `xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py` |

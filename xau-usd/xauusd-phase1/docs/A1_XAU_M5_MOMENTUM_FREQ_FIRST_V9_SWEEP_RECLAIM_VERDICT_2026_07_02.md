# A1 XAU M5 Momentum Frequency-First V9 Sweep-Reclaim Verdict - 2026-07-02

## Purpose

V9 tested another distinct intraday mechanism:

```text
M5 sweep-and-reclaim reversal
```

This looks for price to sweep beyond a recent M5 high/low and then close strongly back through that level. The idea was to catch failed stop-hunts in the direction of higher-timeframe trend.

The target remains the owner goal:

- multiple trades on active days,
- win rate above 50%,
- positive expectancy,
- enough trade frequency to support daily profit objectives.

No live/demo MT5 runtime was changed. The EA default remains `SIGNAL_BREAK_AND_RUN`; sweep-reclaim is default-off and only runs when `InpSignalMode = SIGNAL_SWEEP_RECLAIM`.

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
| `v9_sweep_h1_long_rr0p6` | 401 | 63.84% | +142.50 | 1.13 | 214 | 1.87 | 14 | 10 |
| `v9_sweep_h1h4_long_rr0p6_v4mask` | 172 | 65.70% | +67.50 | 1.16 | 118 | 1.46 | 11 | 11 |
| `v9_sweep_h1h4_long_rr0p6_strict` | 203 | 63.05% | +55.68 | 1.11 | 140 | 1.45 | 14 | 8 |
| `v9_sweep_h1h4_long_rr0p6` | 308 | 62.34% | +48.91 | 1.06 | 170 | 1.81 | 15 | 8 |
| `v9_sweep_h1h4_long_rr0p5` | 310 | 66.45% | +46.70 | 1.07 | 170 | 1.82 | 14 | 9 |
| `v9_sweep_h1h4_both_rr0p6` | 408 | 61.27% | +38.70 | 1.03 | 236 | 1.73 | 14 | 10 |

## Verdict

```text
REJECT_SWEEP_RECLAIM_FOR_PROMOTION
```

Sweep-reclaim is better balanced than V7 and V8:

- It is not as sparse as compression-expansion.
- It is not as noisy as EMA pullback.
- It keeps win rate above 60%.

But it does not have enough expectancy. PF stays between `1.03` and `1.16`, and the better variants stay below `2` trades per active day.

It is a useful idea, but not strong enough to replace V4 or become the next demo lane.

## What We Learned

1. Failed-sweep logic has some signal.

   It is consistently positive in the tested variants, unlike the pullback family.

2. The signal is too weak.

   The best net result was only `+142.50 USD` over two years, versus V4 at `+732.83 USD`.

3. Both-direction sweep-reclaim is not the answer.

   It produced more active days but PF only `1.03`.

4. H1-only increased activity but still lacked edge.

   `v9_sweep_h1_long_rr0p6` had `401` trades and WR `63.84%`, but PF only `1.13`.

## Decision

Do not promote V9 to demo.

Keep V4 as the current best frequency-first candidate. Keep V6 max2 as an optional diagnostic upgrade only if owner/reviewer accept two-position exposure. Continue the hunt with a different mechanism.

Next candidate families worth testing:

- opening range continuation,
- London/New York session impulse continuation,
- volatility expansion after higher-timeframe trend day confirmation,
- micro pullback after break-and-run rather than EMA touch,
- ensemble of V4 plus a separate non-overlapping long-only filter if it improves active days without hurting PF.

## Artifacts

| Artifact | Path |
|---|---|
| V9 MT5 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V9_SWEEP_RECLAIM_TWO_YEAR_2024_07_2026_06.md` |
| V9 JSON | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V9_SWEEP_RECLAIM_TWO_YEAR_2024_07_2026_06.json` |
| EA source | `xau-usd/xauusd-phase1/mt5/Experts/A1XauM5MomentumContinuationExecutor.mq5` |
| Runner | `xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py` |

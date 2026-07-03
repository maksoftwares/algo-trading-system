# A1 XAU M5 Momentum Frequency-First V5 Diagnostic Verdict - 2026-07-02

Status: `V5_DIAGNOSTIC_COMPLETE_V4_STILL_PRIMARY`

## Purpose

The owner clarified that the goal is not a sparse, high-R tail strategy. The goal is:

```text
multiple trades on active days
win rate above 50%
positive expectancy
enough cadence to plausibly make money day by day
```

V4 currently fits that goal best. This V5 batch tested whether the V4 loss clusters could be repaired further without destroying trade frequency.

No live/demo MT5 runtime was touched. All tests were run in the isolated MT5 Strategy Tester sandbox:

```text
C:\MT5A1M5MomentumBacktest
```

## Baseline For Comparison

Current primary candidate:

| Variant | Trades | Win Rate | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Top-10 Removed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 1132 | 65.90% | +1042.07 | 1.45 | 383 | 2.96 | 36 | +899.51 |

## V5 Tests

Exact MT5 every-tick run:

```text
2022.07.01 -> 2026.06.30
tester deposit/currency: 1000 USD
history quality: 98%
```

| Variant | Change vs V4 | Trades | Win Rate | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Top-10 Removed |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `v5_v4_rr0p8` | Target `0.8R` instead of `0.7R` | 1075 | 61.86% | +958.92 | 1.39 | 378 | 2.84 | 33 | +802.20 |
| `v5_v4_move12` | Require `>=1.2 ATR` 3-bar move | 1017 | 65.59% | +926.67 | 1.46 | 366 | 2.78 | 38 | +788.63 |
| `v5_v4_atr15` | Require M5 ATR `>=1.5` | 692 | 67.49% | +919.31 | 1.52 | 273 | 2.53 | 28 | +776.75 |
| `v5_v4_stop500` | Raise stop floor to `500` points | 1051 | 65.18% | +991.94 | 1.40 | 386 | 2.72 | 31 | +849.38 |
| `v5_v4_atr15_move12` | ATR `>=1.5` plus `>=1.2 ATR` 3-bar move | 603 | 67.33% | +814.20 | 1.55 | 255 | 2.36 | 30 | +676.16 |

## Interpretation

The V5 batch confirms the loss-cluster diagnosis:

```text
low-volatility and weaker-momentum trades are lower quality
stricter filters lift PF and win rate
but stricter filters also cut too much frequency and total net
```

The best PF variant is `v5_v4_atr15_move12`, but it drops to `603` trades across four years. That still clears `2.0` trades per active day, but it gives up too much total opportunity relative to V4.

The highest-net V5 variant is `v5_v4_stop500`, but it still earns less than V4:

```text
V4:          +1042.07 USD, 1132 trades, PF 1.45
V5 stop500:  +991.94 USD, 1051 trades, PF 1.40
```

So V5 is useful diagnostically, but it does not dethrone V4.

## Decision

```text
Primary review/demo candidate remains:
freq_h1_h4_long_rr0p7_v4_combo_rank1
```

V5 fallback options:

```text
If reviewer/owner prioritizes smoother WR/PF over total net:
  v5_v4_atr15

If reviewer/owner wants a mild safety repair with similar cadence:
  v5_v4_stop500

If reviewer/owner wants maximum PF and accepts fewer trades:
  v5_v4_atr15_move12
```

But the current best fit for the project objective remains V4 because it has the best balance of:

```text
trade count
active-day cadence
win rate
net profit
profit factor
outlier resistance
```

## Artifacts

| Artifact | Path |
|---|---|
| V5 MT5 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V5_FOUR_YEAR_2022_07_2026_06.md` |
| V5 JSON | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V5_FOUR_YEAR_2022_07_2026_06.json` |
| V5 trade/order/signal CSVs | `xau-usd/xauusd-phase1/outputs/reports/mt5_backtests/a1_momentum_variants_freq_first_v5_four_year_2022_07_2026_06_20260701/` |
| V4 readiness doc | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_DEMO_REPLACEMENT_READINESS_2026_07_02.md` |

## Next Action

Send V4 plus the V5 diagnostic verdict for independent review. If the reviewer agrees, replace the sparse RR2 demo lane with V4 first. Do not replace V4 with a V5 variant unless the reviewer explicitly values PF/win-rate smoothness over total cadence and net.

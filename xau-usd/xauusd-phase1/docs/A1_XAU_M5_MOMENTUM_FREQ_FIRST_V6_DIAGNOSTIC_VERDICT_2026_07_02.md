# A1 XAU M5 Momentum Frequency-First V6 Diagnostic Verdict - 2026-07-02

## Purpose

The owner clarified that a candidate with only a few trades per month is not aligned with the project goal. The target remains:

- Multiple intraday trades on active days.
- Win rate above 50%.
- Positive long-term expectancy.
- Enough frequency to make daily profit possible.

V6 was therefore built as a frequency-first diagnostic batch. It tested smaller targets, looser triggers, H1-only/H4-only filters, both-direction re-entry, asymmetric sessions, stop-floor changes, profit-lock behavior, and a max-two-open-position version of the current V4 candidate.

No live/demo MT5 runtime was changed. All runs used the isolated MT5 Strategy Tester sandbox:

```text
C:\MT5A1M5MomentumBacktest
```

## Key Verdict

The best V6 result is:

```text
v6_freq_v4_rr0p7_max2
```

It slightly improves four-year net profit versus plain V4 while preserving the win-rate and frequency profile. However, the improvement is modest and comes from allowing up to two own open positions, so it should be treated as a diagnostic improvement, not an automatic replacement.

Plain V4 remains the cleaner default unless the owner explicitly accepts the extra two-position exposure.

## Four-Year Validation

Period:

```text
2022-07-01 through 2026-06-30
```

Tester:

```text
MT5 every tick / isolated sandbox / 1000 USD deposit
```

| Variant | Trades | Win Rate | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Negative Months | Top 10 Removed | Top 25 Removed | Best Day % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `v6_freq_v4_rr0p7_max2` | 1211 | 66.72% | +1139.72 | 1.47 | 387 | 3.13 | 34 | 13 | +997.16 | +822.41 | 5.9% |
| `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 1132 | 65.90% | +1042.07 | 1.45 | 383 | 2.96 | 36 | 11 | +899.51 | +724.76 | 5.4% |
| `v6_freq_h1_only_long_rr0p6_v4mask` | 1532 | 66.91% | +877.66 | 1.29 | 510 | 3.00 | 34 | 14 | +745.32 | +591.19 | 7.7% |
| `v6_freq_v4_rr0p6_stop500` | 1126 | 67.05% | +762.64 | 1.30 | 387 | 2.91 | 33 | 14 | +632.74 | +481.17 | 8.9% |

## Two-Year Exploration

Period:

```text
2024-07-01 through 2026-06-30
```

| Variant | Trades | Win Rate | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Negative Months | Top 10 Removed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `v6_freq_v4_rr0p7_max2` | 642 | 66.67% | +757.97 | 1.47 | 205 | 3.13 | 18 | 6 | +629.64 |
| `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 612 | 66.67% | +732.83 | 1.47 | 204 | 3.00 | 19 | 5 | +604.50 |
| `v6_freq_both_h1h4_rr0p6_v4mask` | 863 | 67.21% | +629.06 | 1.27 | 282 | 3.06 | 17 | 7 | +514.53 |
| `v6_freq_v4_rr0p6_stop500` | 633 | 69.04% | +608.37 | 1.38 | 204 | 3.10 | 17 | 7 | +494.35 |
| `v6_freq_h1_only_long_rr0p6_v4mask` | 796 | 67.59% | +604.63 | 1.30 | 250 | 3.18 | 17 | 7 | +490.39 |
| `v6_freq_v4_rr0p6` | 647 | 68.47% | +574.53 | 1.37 | 204 | 3.17 | 18 | 6 | +460.51 |
| `v6_freq_v4_rr0p6_relaxed_trigger` | 767 | 66.62% | +518.16 | 1.27 | 211 | 3.64 | 15 | 9 | +404.14 |
| `v6_freq_v4_rr0p5` | 694 | 70.89% | +410.44 | 1.27 | 205 | 3.39 | 16 | 8 | +318.52 |
| `v6_freq_v4_rr0p6_lock04_01` | 658 | 74.62% | +381.73 | 1.30 | 204 | 3.23 | 14 | 10 | +274.49 |
| `v6_freq_h1_only_long_rr0p6` | 1250 | 64.80% | +346.55 | 1.10 | 275 | 4.55 | 14 | 10 | +232.31 |
| `v6_freq_h4_only_long_rr0p6` | 1338 | 63.98% | +130.26 | 1.03 | 272 | 4.92 | 13 | 11 | +15.78 |
| `v6_freq_asym_sessions_rr0p6` | 610 | 63.44% | +67.10 | 1.04 | 248 | 2.46 | 14 | 9 | -37.64 |

## What We Learned

1. The frequency-first requirement is achievable.

   Both V4 and the V6 max-two variant produce roughly 3 trades per active day while keeping win rate near 66%.

2. More trades alone is not enough.

   H1-only and H4-only variants increase frequency, but PF and net profit weaken. This means the H1+H4 agreement is carrying real quality.

3. Smaller targets lift win rate but reduce net profit.

   The 0.5R and 0.6R tests achieve higher win rates, but they do not improve net expectancy enough to replace V4.

4. Profit-lock increases win rate but cuts profit.

   The 0.4R trigger / 0.1R lock variant reached 74.62% win rate in the two-year run, but net profit fell sharply. A high win rate alone is not enough.

5. Allowing two open positions is the only V6 idea that improves four-year net profit.

   This is promising, but it adds exposure and can drift toward the duplicate-stacking problem we have already seen. It requires explicit owner/reviewer approval before demo replacement.

## Current Ranking

### Best simple default

```text
freq_h1_h4_long_rr0p7_v4_combo_rank1
```

Reason:

- Simpler.
- One position at a time.
- 65.90% four-year win rate.
- 2.96 trades per active day.
- +1042.07 USD four-year net.
- Positive after top 25 winners removed.

### Best diagnostic upgrade

```text
v6_freq_v4_rr0p7_max2
```

Reason:

- 66.72% four-year win rate.
- 3.13 trades per active day.
- +1139.72 USD four-year net.
- Positive after top 25 winners removed.
- But requires acceptance of max-two-position exposure.

## Recommendation

Use plain V4 as the default demo-replacement candidate unless the owner explicitly wants to test max-two exposure.

If max-two is tested, it should be a separate demo lane or a clearly labeled variant, not silently replacing the one-position V4. The forward review should measure whether the extra positions improve net profit without reviving duplicate-stacking behavior.

## Artifacts

| Artifact | Path |
|---|---|
| Two-year V6 MT5 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V6_TWO_YEAR_2024_07_2026_06.md` |
| Two-year V6 JSON | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V6_TWO_YEAR_2024_07_2026_06.json` |
| Four-year V6 max2 report | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V6_MAX2_FOUR_YEAR_2022_07_2026_06.md` |
| Four-year V6 max2 JSON | `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_FREQ_FIRST_V6_MAX2_FOUR_YEAR_2022_07_2026_06.json` |
| V4 readiness doc | `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_DEMO_REPLACEMENT_READINESS_2026_07_02.md` |

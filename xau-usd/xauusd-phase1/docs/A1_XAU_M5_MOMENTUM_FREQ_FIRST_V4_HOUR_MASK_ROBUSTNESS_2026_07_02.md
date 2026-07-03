# A1 XAU M5 Momentum V4 Hour-Mask Robustness - 2026-07-02

Status: `ROBUSTNESS_DIAGNOSTIC_NOT_PROMOTED`

This note tests whether the V4 frequency-first candidate is fragile to one exact hour mask. The project target remains:

- multiple trades per active day,
- win rate above 50%,
- positive expectancy,
- XAUUSD M5 demo candidate first,
- no live/canonical promotion from backtest alone.

No live/demo MT5 runtime, chart, preset, order, or position was changed.

## Why This Test Matters

The primary V4 candidate came from an offline hour-combination search. That creates selection pressure: a single best hour mask can look good by chance. To reduce that risk, nearby top-ranked masks were rerun exactly in MT5 Strategy Tester over older OOS, recent/current, and full four-year windows.

If the result only worked for one exact mask, it would be fragile. If nearby masks also worked, the signal is more likely to reflect a real time-of-day / trend-alignment structure.

## Variants

All variants are:

- XAUUSD M5
- long only
- H1 + H4 EMA aligned
- target `0.70R`
- max estimated cost R `0.05`
- max trades/day `12`
- cooldown `5` minutes

| Rank | Variant | Blocked Server Hours | Comment |
|---:|---|---|---|
| 1 | `freq_h1_h4_long_rr0p7_v4_combo_rank1` | `2,9,10,11,12,13,17,19,21,23` | Primary V4 |
| 2 | `v4_rank2` | `2,9,10,11,12,13,17,19,21,22,23` | Rank 1 plus hour 22 blocked |
| 3 | `v4_rank3` | `2,8,9,10,11,12,13,17,19,21,23` | Rank 1 plus hour 8 blocked |
| 4 | `v4_rank4` | `2,8,9,10,11,12,13,17,19,21,22,23` | Rank 1 plus hours 8 and 22 blocked |

## Exact MT5 Results

### Older OOS: 2022.07-2024.06

| Variant | Trades | Win Rate | Net USD | PF |
|---|---:|---:|---:|---:|
| Rank 1 / plain V4 | 520 | 65.00% | +309.24 | 1.40 |
| Rank 2 | 497 | 65.19% | +305.23 | 1.42 |
| Rank 3 | 481 | 65.49% | +312.23 | 1.45 |
| Rank 4 | 458 | 65.72% | +308.22 | 1.46 |

### Current: 2024.07-2026.06

| Variant | Trades | Win Rate | Net USD | PF |
|---|---:|---:|---:|---:|
| Rank 1 / plain V4 | 612 | 66.67% | +732.83 | 1.47 |
| Rank 2 | 580 | 66.72% | +719.84 | 1.48 |
| Rank 3 | 559 | 66.91% | +704.97 | 1.50 |
| Rank 4 | 527 | 66.98% | +691.98 | 1.51 |

### Combined Four-Year: 2022.07-2026.06

| Variant | Trades | Win Rate | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Negative Months | Net after Top 10 Removed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Rank 1 / plain V4 | 1132 | 65.90% | +1042.07 | 1.45 | 383 | 2.96 | 36 | 11 | +899.51 |
| Rank 2 | 1077 | 66.02% | +1025.07 | 1.46 | 360 | 2.99 | 35 | 12 | +882.51 |
| Rank 3 | 1040 | 66.25% | +1017.20 | 1.48 | 375 | 2.77 | 35 | 12 | +874.64 |
| Rank 4 | 985 | 66.40% | +1000.20 | 1.50 | 351 | 2.81 | 34 | 13 | +857.64 |

## Interpretation

The V4 hour-mask signal is not dependent on one exact mask.

What survived:

- All nearby masks stayed profitable in older OOS and current windows.
- All nearby masks stayed above 65% win rate.
- All nearby masks kept roughly 2.8-3.0 trades per active day.
- All nearby masks stayed positive after removing the top 10 winners.
- Blocking hour 8 and/or 22 raises PF slightly but reduces trade count and total net.

Practical decision:

- Plain V4 remains the best owner-goal candidate because it has the highest four-year net and highest trade count.
- Rank 4 is the highest-PF alternative if the reviewer prefers quality over trade count.
- This robustness test reduces, but does not remove, hour-mask overfit risk. A forward demo is still required before trusting it.

## Current Candidate Ranking

| Preference | Candidate | Why |
|---|---|---|
| Primary | Plain V4 | Highest net, highest trade count, still 65.90% WR |
| Quality fallback | Rank 4 | Highest PF and WR, but fewer trades and lower net |
| Win-rate smoother alternate | `v4_lock06` | Highest WR at 68.60%, but lower net and requires SL modification |

## Source Artifacts

- Hour-combination search: `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_HOUR_COMBINATION_SEARCH_2026_07_02.md`
- Plain V4 verdict: `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md`
- OOS robustness MT5 report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_ROBUST_OOS_USD_2022_07_2024_06.md`
- Current robustness MT5 report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_ROBUST_CURRENT_USD_2024_07_2026_06.md`
- Four-year robustness MT5 report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_ROBUST_FOUR_YEAR_USD_2022_07_2026_06.md`
- Runner: `xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py`

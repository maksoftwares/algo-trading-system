# A1 XAU M5 Momentum V4 Exit Protection Diagnostic - 2026-07-02

Status: `DIAGNOSTIC_ONLY_NOT_PROMOTED`

This document records the V4-specific profit-protection test after the owner clarified that the project target is not a sparse strategy. The target shape remains:

- multiple trades per active day,
- win rate above 50%,
- positive expectancy,
- XAUUSD M5 demo candidate first,
- no live/canonical promotion from backtest alone.

No live/demo MT5 runtime, chart, preset, order, or position was changed by this test.

## Tester Correction

The first V4 exit-protection rerun returned zero bars because the runner defaulted to `AED` tester currency. MT5 then needed `USDAED` conversion history for 2022-2024, but Capital.com only had that conversion history from `2025-12-20`. The runner has been hardened so zero-bar / zero-tick MT5 reports now fail loudly instead of being summarized as zero-trade strategy results.

For multi-year MT5 Strategy Tester runs, this screen uses:

- deposit: `1000`
- currency: `USD`
- model: MT5 every tick / real tick history as reported by MT5

## Variants Tested

All variants use the same V4 entry:

- XAUUSD M5
- long only
- H1 + H4 trend aligned
- risk reward `0.70`
- max estimated cost R `0.05`
- blocked hours `2,9,10,11,12,13,17,19,21,23`
- max trades/day `12`
- cooldown `5` minutes

Exit variants:

| Variant | Rule |
|---|---|
| `v4_be05` | Move SL to breakeven after +0.50R |
| `v4_lock05` | Lock +0.15R after +0.50R |
| `v4_lock06` | Lock +0.20R after +0.60R |

## Split Results

| Window | Variant | Trades | Win Rate | Net USD | PF |
|---|---|---:|---:|---:|---:|
| 2022.07-2024.06 OOS | `v4_be05` | 527 | 52.18% | +236.52 | 1.36 |
| 2022.07-2024.06 OOS | `v4_lock05` | 529 | 70.32% | +239.05 | 1.37 |
| 2022.07-2024.06 OOS | `v4_lock06` | 522 | 68.20% | +292.10 | 1.42 |
| 2024.07-2026.06 Current | `v4_be05` | 617 | 54.62% | +556.74 | 1.41 |
| 2024.07-2026.06 Current | `v4_lock05` | 620 | 71.61% | +558.99 | 1.41 |
| 2024.07-2026.06 Current | `v4_lock06` | 615 | 68.94% | +674.74 | 1.46 |
| 2022.07-2026.06 Combined | `v4_lock06` | 1137 | 68.60% | +966.84 | 1.45 |

## Plain V4 vs Exit-Protected V4

| Candidate | Trades | Win Rate | Net USD | PF | Active Days | Trades / Active Day | Positive Months | Negative Months | Net after Top 10 Removed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Plain V4 `freq_h1_h4_long_rr0p7_v4_combo_rank1` | 1132 | 65.90% | +1042.07 | 1.45 | 383 | 2.96 | 36 | 11 | +899.51 |
| Exit V4 `v4_lock06` | 1137 | 68.60% | +966.84 | 1.45 | 383 | 2.97 | 35 | 12 | +824.61 |

## Interpretation

`v4_lock06` is useful, but it is not a clear upgrade over plain V4.

What improved:

- Win rate improved from `65.90%` to `68.60%`.
- Frequency stayed aligned with the owner goal: about `2.97` trades per active day.
- PF stayed about the same at `1.45`.
- OOS and current windows both stayed profitable.

What did not improve:

- Total net dropped from `+1042.07` to `+966.84`.
- Positive months dropped from `36` to `35`.
- Net after removing the top 10 winners dropped from `+899.51` to `+824.61`.
- Profit protection requires live SL modification behavior, which adds execution complexity versus plain fixed SL/TP.

## Decision

Plain V4 remains the primary frequency-first review candidate because it has the higher four-year net and simpler execution.

`v4_lock06` is a legitimate alternate if the owner prioritizes smoother win rate over maximum net profit, but it should not replace plain V4 without reviewer agreement.

Recommended next step:

1. Send the V4 review packet plus this exit-protection diagnostic to the reviewer.
2. Ask whether the forward demo should test:
   - plain V4 only,
   - `v4_lock06` only,
   - or both as separate demo lanes with separate magic numbers.
3. Do not attach either version to demo runtime until owner approval is recorded.

## Source Artifacts

- Plain V4 verdict: `xau-usd/xauusd-phase1/docs/A1_XAU_M5_MOMENTUM_FREQ_FIRST_V4_COMBO_RANK1_VERDICT_2026_07_02.md`
- OOS exit report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_EXIT_OOS_USD_2022_07_2024_06.md`
- Current exit report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_EXIT_CURRENT_USD_2024_07_2026_06.md`
- Four-year `v4_lock06` report: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_M5_MOMENTUM_VARIANT_BACKTEST_V4_LOCK06_FOUR_YEAR_USD_2022_07_2026_06.md`
- Runner: `xau-usd/xauusd-phase1/scripts/run_a1_xau_m5_momentum_backtest_variants.py`

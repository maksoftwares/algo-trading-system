# Phase 2 Demo Repair Last-Week Backtest

Overall status: REPAIR_LAST_WEEK_BACKTEST_READY

Retrospective shadow backtest on actual demo broker rows only. No MT5 charts, inputs, orders, positions, presets, canonical Phase 2 status, or live-capital permissions are changed.

Generated at UTC: `2026-06-09T07:26:53.956541Z`
Window: `2026-06-01 00:00:00` to `2026-06-08 18:45:00`
Source CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
Rules CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_REPAIR_CANDIDATE_RULES.csv`

## Portfolio Summary

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| All duplicate-hidden baseline | 225 | 220 | 5 | 85 | 135 | 38.64% | 9.04 | 16.32 | 25.36 | 1.00 | 28.43 | -17.84 |
| Target weak-EA baseline | 128 | 124 | 4 | 44 | 80 | 35.48% | -426.80 | 12.24 | -414.56 | 0.76 | 29.99 | -21.83 |
| Repair-rule v1 target keep | 55 | 51 | 4 | 24 | 27 | 47.06% | 168.29 | 12.24 | 180.53 | 1.33 | 28.48 | -19.08 |
| Strict quarantine target keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Whole portfolio after repair-rule v1 | 152 | 147 | 5 | 65 | 82 | 44.22% | 604.13 | 16.32 | 620.45 | 1.51 | 27.39 | -14.35 |
| Whole portfolio after strict quarantine | 97 | 96 | 1 | 41 | 55 | 42.71% | 435.84 | 4.08 | 439.92 | 1.66 | 26.76 | -12.02 |

Repair-rule v1 target PnL delta: `595.09` AED
Repair-rule v1 whole-portfolio PnL delta: `595.09` AED
Strict quarantine target PnL delta: `426.80` AED
Strict quarantine whole-portfolio PnL delta: `426.80` AED

## Per-Candidate Results

| Candidate | Baseline Closed | Baseline WR | Baseline PnL | Baseline PF | Repair Keep Closed | Repair WR | Repair PnL | Repair PF | Repair Delta | Quarantine Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| session_extreme_retest_v0 | 42 | 28.57% | -133.23 | 0.66 | 23 | 39.13% | 5.90 | 1.04 | 139.13 | 133.23 |
| symbol_normalized_round_retest_v0 | 82 | 39.02% | -293.57 | 0.78 | 28 | 53.57% | 162.39 | 1.46 | 455.96 | 293.57 |
| round_number_retest_v0 | 0 | n/a | 0.00 | n/a | 0 | n/a | 0.00 | n/a | 0.00 | 0.00 |

## Interpretation

- Repair-rule v1 is the best retrospective result, but it is still post-hoc shadow evidence.
- Strict quarantine improves account-level decision PnL by removing the weak candidates, but it also removes any positive repaired slices.
- Forward evidence is still required before enforcing any rule in demo runtime.

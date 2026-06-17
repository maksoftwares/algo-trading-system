# Phase 2 Demo Repair Forward Week Report

Overall status: FORWARD_CONFIRMATION_FAILED_REVIEW_REQUIRED

Forward-week report only. It does not authorize canonical Phase 2 or runtime promotion.

Generated at UTC: `2026-06-17T04:03:47.790981Z`
Policy ID: `phase2_demo_repair_policy_2026_06_12_v2`
Forward window starts: `2026-06-09 00:00:00`
Expected window end: `2026-06-16 00:00:00`
Latest post-start entry: `2026-06-16 10:25:00`
Elapsed days: `7.434` / `7.0`
Promotion decision: `NOT_ELIGIBLE_WEAK_FORWARD_RESULT`

## Required Comparison

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pre-repair baseline | 228 | 228 | 0 | 87 | 140 | 38.33% | -25.44 | 0.00 | -25.44 | 0.99 | 28.43 | -17.85 |
| Pre-repair target baseline | 129 | 129 | 0 | 45 | 83 | 35.16% | -444.36 | 0.00 | -444.36 | 0.76 | 30.46 | -21.87 |
| Post-repair actual | 742 | 738 | 4 | 238 | 469 | 33.66% | -2472.41 | -72.34 | -2544.75 | 0.80 | 41.12 | -26.14 |
| Post target baseline | 517 | 515 | 2 | 167 | 330 | 33.60% | -1977.06 | -47.36 | -2024.42 | 0.79 | 43.61 | -28.06 |
| Post repair-rule v1 would keep | 295 | 294 | 1 | 88 | 188 | 31.88% | -1298.42 | -41.33 | -1339.75 | 0.74 | 41.48 | -26.32 |
| Post repair-rule v1 would block | 222 | 221 | 1 | 79 | 142 | 35.75% | -678.64 | -6.03 | -684.67 | 0.84 | 45.98 | -30.36 |
| Post whole portfolio after repair-rule v1 | 520 | 517 | 3 | 159 | 327 | 32.72% | -1793.77 | -66.31 | -1860.08 | 0.77 | 38.71 | -24.31 |
| Post strict quarantine would keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Post strict quarantine would block | 517 | 515 | 2 | 167 | 330 | 33.60% | -1977.06 | -47.36 | -2024.42 | 0.79 | 43.61 | -28.06 |
| Shadow would keep | 290 | 288 | 2 | 101 | 174 | 35.07 | -94.01 | -24.98 | -118.99 | 0.97 | 31.25 | -18.68 |
| Shadow would block | 680 | 678 | 2 | 224 | 435 | 33.04 | -2403.84 | -47.36 | -2451.20 | 0.79 | 40.64 | -26.45 |

Post repair-rule target PnL delta: `678.64` AED
Post repair-rule whole-portfolio PnL delta: `678.64` AED
Post strict-quarantine target PnL delta: `1977.06` AED

## Confirmation Checks

| Check | Value |
|---|---:|
| fresh_week_elapsed | `True` |
| min_target_closed_trades | `True` |
| repair_closed_pnl_improves | `True` |
| repair_pf_preserved_or_improves | `False` |
| repair_win_rate_preserved_or_improves | `False` |
| retained_trade_pct | `57.09` |
| required_target_closed_trades | `30` |

## Promotion Requirement

- Duplicate-hidden PF and PnL improve.
- Win rate improves or is preserved.
- Enough trade count remains.
- One fresh forward week survives.
- Owner/reviewer approval is recorded.

No rule can be promoted from shadow to demo enforcement without owner/reviewer approval.

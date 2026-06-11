# Phase 2 Demo Repair Forward Week Report

Overall status: PENDING_FORWARD_WEEK_IN_PROGRESS

Forward-week report only. It does not authorize canonical Phase 2 or runtime promotion.

Generated at UTC: `2026-06-11T04:06:50.393894Z`
Policy ID: `phase2_demo_repair_policy_2026_06_09_v1`
Forward window starts: `2026-06-09 00:00:00`
Expected window end: `2026-06-16 00:00:00`
Latest post-start entry: `2026-06-10 00:45:00`
Elapsed days: `1.0312` / `7.0`
Promotion decision: `NOT_ELIGIBLE_FORWARD_WEEK_PENDING`

## Required Comparison

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pre-repair baseline | 228 | 228 | 0 | 87 | 140 | 38.33% | -25.44 | 0.00 | -25.44 | 0.99 | 28.43 | -17.85 |
| Pre-repair target baseline | 129 | 129 | 0 | 45 | 83 | 35.16% | -444.36 | 0.00 | -444.36 | 0.76 | 30.46 | -21.87 |
| Post-repair actual | 90 | 77 | 13 | 23 | 54 | 29.87% | -304.21 | -18.77 | -322.98 | 0.76 | 42.41 | -23.70 |
| Post target baseline | 67 | 57 | 10 | 15 | 42 | 26.32% | -394.62 | -2.09 | -396.71 | 0.61 | 41.58 | -24.24 |
| Post repair-rule v1 would keep | 42 | 34 | 8 | 9 | 25 | 26.47% | -123.27 | 3.50 | -119.77 | 0.76 | 43.60 | -20.63 |
| Post repair-rule v1 would block | 25 | 23 | 2 | 6 | 17 | 26.09% | -271.35 | -5.59 | -276.94 | 0.46 | 38.54 | -29.56 |
| Post whole portfolio after repair-rule v1 | 65 | 54 | 11 | 17 | 37 | 31.48% | -32.86 | -13.18 | -46.04 | 0.96 | 43.77 | -21.00 |
| Post strict quarantine would keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Post strict quarantine would block | 67 | 57 | 10 | 15 | 42 | 26.32% | -394.62 | -2.09 | -396.71 | 0.61 | 41.58 | -24.24 |
| Shadow would keep | 102 | 99 | 3 | 45 | 54 | 45.45 | 584.86 | -16.68 | 568.18 | 1.89 | 27.57 | -12.14 |
| Shadow would block | 216 | 206 | 10 | 65 | 140 | 31.55 | -914.51 | -2.09 | -916.60 | 0.71 | 33.97 | -22.30 |

Post repair-rule target PnL delta: `271.35` AED
Post repair-rule whole-portfolio PnL delta: `271.35` AED
Post strict-quarantine target PnL delta: `394.62` AED

## Confirmation Checks

| Check | Value |
|---|---:|
| fresh_week_elapsed | `False` |
| min_target_closed_trades | `True` |
| repair_closed_pnl_improves | `True` |
| repair_pf_preserved_or_improves | `True` |
| repair_win_rate_preserved_or_improves | `True` |
| retained_trade_pct | `59.65` |
| required_target_closed_trades | `30` |

## Promotion Requirement

- Duplicate-hidden PF and PnL improve.
- Win rate improves or is preserved.
- Enough trade count remains.
- One fresh forward week survives.
- Owner/reviewer approval is recorded.

No rule can be promoted from shadow to demo enforcement without owner/reviewer approval.

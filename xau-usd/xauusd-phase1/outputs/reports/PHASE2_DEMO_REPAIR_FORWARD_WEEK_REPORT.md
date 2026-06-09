# Phase 2 Demo Repair Forward Week Report

Overall status: PENDING_FORWARD_WEEK_IN_PROGRESS

Forward-week report only. It does not authorize canonical Phase 2 or runtime promotion.

Generated at UTC: `2026-06-09T08:07:38.843249Z`
Policy ID: `phase2_demo_repair_policy_2026_06_09_v1`
Forward window starts: `2026-06-09 00:00:00`
Expected window end: `2026-06-16 00:00:00`
Latest post-start entry: `2026-06-09 11:35:01`
Elapsed days: `0.4827` / `7.0`
Promotion decision: `NOT_ELIGIBLE_FORWARD_WEEK_PENDING`

## Required Comparison

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pre-repair baseline | 228 | 228 | 0 | 87 | 140 | 38.33% | -25.44 | 0.00 | -25.44 | 0.99 | 28.43 | -17.85 |
| Pre-repair target baseline | 129 | 129 | 0 | 45 | 83 | 35.16% | -444.36 | 0.00 | -444.36 | 0.76 | 30.46 | -21.87 |
| Post-repair actual | 17 | 17 | 0 | 7 | 10 | 41.18% | -7.29 | 0.00 | -7.29 | 0.96 | 27.92 | -20.27 |
| Post target baseline | 12 | 12 | 0 | 5 | 7 | 41.67% | 32.60 | 0.00 | 32.60 | 1.26 | 31.44 | -17.80 |
| Post repair-rule v1 would keep | 3 | 3 | 0 | 0 | 3 | 0.00% | -47.83 | 0.00 | -47.83 | 0.00 | n/a | -15.94 |
| Post repair-rule v1 would block | 9 | 9 | 0 | 5 | 4 | 55.56% | 80.43 | 0.00 | 80.43 | 2.05 | 31.44 | -19.20 |
| Post whole portfolio after repair-rule v1 | 8 | 8 | 0 | 2 | 6 | 25.00% | -87.72 | 0.00 | -87.72 | 0.30 | 19.11 | -20.99 |
| Post strict quarantine would keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Post strict quarantine would block | 12 | 12 | 0 | 5 | 7 | 41.67% | 32.60 | 0.00 | 32.60 | 1.26 | 31.44 | -17.80 |
| Shadow would keep | 85 | 85 | 0 | 39 | 46 | 45.88 | 440.67 | 0.00 | 440.67 | 1.91 | 23.77 | -10.57 |
| Shadow would block | 160 | 160 | 0 | 55 | 104 | 34.38 | -473.40 | 0.00 | -473.40 | 0.79 | 31.66 | -21.30 |

Post repair-rule target PnL delta: `-80.43` AED
Post repair-rule whole-portfolio PnL delta: `-80.43` AED
Post strict-quarantine target PnL delta: `-32.6` AED

## Confirmation Checks

| Check | Value |
|---|---:|
| fresh_week_elapsed | `False` |
| min_target_closed_trades | `False` |
| repair_closed_pnl_improves | `False` |
| repair_pf_preserved_or_improves | `False` |
| repair_win_rate_preserved_or_improves | `False` |
| retained_trade_pct | `25.0` |
| required_target_closed_trades | `30` |

## Promotion Requirement

- Duplicate-hidden PF and PnL improve.
- Win rate improves or is preserved.
- Enough trade count remains.
- One fresh forward week survives.
- Owner/reviewer approval is recorded.

No rule can be promoted from shadow to demo enforcement without owner/reviewer approval.

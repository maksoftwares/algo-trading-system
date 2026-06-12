# Phase 2 Demo Repair Forward Week Report

Overall status: PENDING_FORWARD_WEEK_IN_PROGRESS

Forward-week report only. It does not authorize canonical Phase 2 or runtime promotion.

Generated at UTC: `2026-06-12T04:03:30.868518Z`
Policy ID: `phase2_demo_repair_policy_2026_06_09_v1`
Forward window starts: `2026-06-09 00:00:00`
Expected window end: `2026-06-16 00:00:00`
Latest post-start entry: `2026-06-11 21:35:12`
Elapsed days: `2.8994` / `7.0`
Promotion decision: `NOT_ELIGIBLE_FORWARD_WEEK_PENDING`

## Required Comparison

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pre-repair baseline | 228 | 228 | 0 | 87 | 140 | 38.33% | -25.44 | 0.00 | -25.44 | 0.99 | 28.43 | -17.85 |
| Pre-repair target baseline | 129 | 129 | 0 | 45 | 83 | 35.16% | -444.36 | 0.00 | -444.36 | 0.76 | 30.46 | -21.87 |
| Post-repair actual | 400 | 399 | 1 | 131 | 253 | 34.11% | -1315.44 | 64.15 | -1251.29 | 0.82 | 44.25 | -28.11 |
| Post target baseline | 292 | 292 | 0 | 96 | 185 | 34.16% | -1117.27 | 0.00 | -1117.27 | 0.80 | 46.60 | -30.22 |
| Post repair-rule v1 would keep | 171 | 171 | 0 | 58 | 102 | 36.25% | -338.55 | 0.00 | -338.55 | 0.88 | 42.59 | -27.54 |
| Post repair-rule v1 would block | 121 | 121 | 0 | 38 | 83 | 31.40% | -778.72 | 0.00 | -778.72 | 0.72 | 52.72 | -33.52 |
| Post whole portfolio after repair-rule v1 | 279 | 278 | 1 | 93 | 170 | 35.36% | -536.72 | 64.15 | -472.57 | 0.88 | 40.79 | -25.47 |
| Post strict quarantine would keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Post strict quarantine would block | 292 | 292 | 0 | 96 | 185 | 34.16% | -1117.27 | 0.00 | -1117.27 | 0.80 | 46.60 | -30.22 |
| Shadow would keep | 178 | 177 | 1 | 68 | 105 | 38.42 | 275.70 | 64.15 | 339.85 | 1.15 | 30.63 | -17.21 |
| Shadow would block | 450 | 450 | 0 | 150 | 288 | 33.33 | -1616.58 | 0.00 | -1616.58 | 0.79 | 41.24 | -27.09 |

Post repair-rule target PnL delta: `778.72` AED
Post repair-rule whole-portfolio PnL delta: `778.72` AED
Post strict-quarantine target PnL delta: `1117.27` AED

## Confirmation Checks

| Check | Value |
|---|---:|
| fresh_week_elapsed | `False` |
| min_target_closed_trades | `True` |
| repair_closed_pnl_improves | `True` |
| repair_pf_preserved_or_improves | `True` |
| repair_win_rate_preserved_or_improves | `True` |
| retained_trade_pct | `58.56` |
| required_target_closed_trades | `30` |

## Promotion Requirement

- Duplicate-hidden PF and PnL improve.
- Win rate improves or is preserved.
- Enough trade count remains.
- One fresh forward week survives.
- Owner/reviewer approval is recorded.

No rule can be promoted from shadow to demo enforcement without owner/reviewer approval.

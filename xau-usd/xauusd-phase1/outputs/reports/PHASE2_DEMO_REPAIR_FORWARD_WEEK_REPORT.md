# Phase 2 Demo Repair Forward Week Report

Overall status: PENDING_FORWARD_WEEK_IN_PROGRESS

Forward-week report only. It does not authorize canonical Phase 2 or runtime promotion.

Generated at UTC: `2026-06-13T04:03:54.375063Z`
Policy ID: `phase2_demo_repair_policy_2026_06_12_v2`
Forward window starts: `2026-06-09 00:00:00`
Expected window end: `2026-06-16 00:00:00`
Latest post-start entry: `2026-06-13 00:15:01`
Elapsed days: `4.0104` / `7.0`
Promotion decision: `NOT_ELIGIBLE_FORWARD_WEEK_PENDING`

## Required Comparison

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pre-repair baseline | 228 | 228 | 0 | 87 | 140 | 38.33% | -25.44 | 0.00 | -25.44 | 0.99 | 28.43 | -17.85 |
| Pre-repair target baseline | 129 | 129 | 0 | 45 | 83 | 35.16% | -444.36 | 0.00 | -444.36 | 0.76 | 30.46 | -21.87 |
| Post-repair actual | 568 | 564 | 4 | 185 | 364 | 33.70% | -2131.14 | 24.04 | -2107.10 | 0.79 | 43.66 | -28.04 |
| Post target baseline | 418 | 417 | 1 | 141 | 265 | 34.73% | -1592.92 | 26.43 | -1566.49 | 0.80 | 45.48 | -30.21 |
| Post repair-rule v1 would keep | 245 | 245 | 0 | 80 | 154 | 34.19% | -882.73 | 0.00 | -882.73 | 0.79 | 42.50 | -27.81 |
| Post repair-rule v1 would block | 173 | 172 | 1 | 61 | 111 | 35.47% | -710.19 | 26.43 | -683.76 | 0.81 | 49.38 | -33.53 |
| Post whole portfolio after repair-rule v1 | 395 | 392 | 3 | 124 | 253 | 32.89% | -1420.95 | -2.39 | -1423.34 | 0.78 | 40.85 | -25.64 |
| Post strict quarantine would keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Post strict quarantine would block | 418 | 417 | 1 | 141 | 265 | 34.73% | -1592.92 | 26.43 | -1566.49 | 0.80 | 45.48 | -30.21 |
| Shadow would keep | 219 | 216 | 3 | 76 | 136 | 35.19 | -106.94 | -2.39 | -109.33 | 0.96 | 31.35 | -18.30 |
| Shadow would block | 577 | 576 | 1 | 196 | 368 | 34.03 | -2049.64 | 26.43 | -2023.21 | 0.80 | 41.67 | -27.76 |

Post repair-rule target PnL delta: `710.19` AED
Post repair-rule whole-portfolio PnL delta: `710.19` AED
Post strict-quarantine target PnL delta: `1592.92` AED

## Confirmation Checks

| Check | Value |
|---|---:|
| fresh_week_elapsed | `False` |
| min_target_closed_trades | `True` |
| repair_closed_pnl_improves | `True` |
| repair_pf_preserved_or_improves | `False` |
| repair_win_rate_preserved_or_improves | `False` |
| retained_trade_pct | `58.75` |
| required_target_closed_trades | `30` |

## Promotion Requirement

- Duplicate-hidden PF and PnL improve.
- Win rate improves or is preserved.
- Enough trade count remains.
- One fresh forward week survives.
- Owner/reviewer approval is recorded.

No rule can be promoted from shadow to demo enforcement without owner/reviewer approval.

# Phase 2 Demo Repair Forward Week Report

Overall status: FORWARD_CONFIRMATION_FAILED_REVIEW_REQUIRED

Forward-week report only. It does not authorize canonical Phase 2 or runtime promotion.

Generated at UTC: `2026-06-18T04:03:12.104484Z`
Policy ID: `phase2_demo_repair_policy_2026_06_12_v2`
Forward window starts: `2026-06-09 00:00:00`
Expected window end: `2026-06-16 00:00:00`
Latest post-start entry: `2026-06-18 02:15:01`
Elapsed days: `9.0938` / `7.0`
Promotion decision: `NOT_ELIGIBLE_WEAK_FORWARD_RESULT`

## Required Comparison

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pre-repair baseline | 228 | 228 | 0 | 87 | 140 | 38.33% | -25.44 | 0.00 | -25.44 | 0.99 | 28.43 | -17.85 |
| Pre-repair target baseline | 129 | 129 | 0 | 45 | 83 | 35.16% | -444.36 | 0.00 | -444.36 | 0.76 | 30.46 | -21.87 |
| Post-repair actual | 964 | 955 | 9 | 298 | 625 | 32.29% | -2928.58 | 22.31 | -2906.27 | 0.79 | 37.16 | -22.41 |
| Post target baseline | 651 | 643 | 8 | 211 | 413 | 33.81% | -1903.83 | 11.41 | -1892.42 | 0.81 | 39.40 | -24.74 |
| Post repair-rule v1 would keep | 367 | 359 | 8 | 107 | 233 | 31.47% | -1399.64 | 11.41 | -1388.23 | 0.74 | 36.34 | -22.69 |
| Post repair-rule v1 would block | 284 | 284 | 0 | 104 | 180 | 36.62% | -504.19 | 0.00 | -504.19 | 0.90 | 42.55 | -27.38 |
| Post whole portfolio after repair-rule v1 | 680 | 671 | 9 | 194 | 445 | 30.36% | -2424.39 | 22.31 | -2402.08 | 0.73 | 34.28 | -20.39 |
| Post strict quarantine would keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Post strict quarantine would block | 651 | 643 | 8 | 211 | 413 | 33.81% | -1903.83 | 11.41 | -1892.42 | 0.81 | 39.40 | -24.74 |
| Shadow would keep | 367 | 366 | 1 | 113 | 240 | 30.87 | -598.26 | 10.90 | -587.36 | 0.85 | 29.60 | -16.43 |
| Shadow would block | 825 | 817 | 8 | 272 | 525 | 33.29 | -2355.76 | 11.41 | -2344.35 | 0.81 | 37.51 | -23.92 |

Post repair-rule target PnL delta: `504.19` AED
Post repair-rule whole-portfolio PnL delta: `504.19` AED
Post strict-quarantine target PnL delta: `1903.83` AED

## Confirmation Checks

| Check | Value |
|---|---:|
| fresh_week_elapsed | `True` |
| min_target_closed_trades | `True` |
| repair_closed_pnl_improves | `True` |
| repair_pf_preserved_or_improves | `False` |
| repair_win_rate_preserved_or_improves | `False` |
| retained_trade_pct | `55.83` |
| required_target_closed_trades | `30` |

## Promotion Requirement

- Duplicate-hidden PF and PnL improve.
- Win rate improves or is preserved.
- Enough trade count remains.
- One fresh forward week survives.
- Owner/reviewer approval is recorded.

No rule can be promoted from shadow to demo enforcement without owner/reviewer approval.

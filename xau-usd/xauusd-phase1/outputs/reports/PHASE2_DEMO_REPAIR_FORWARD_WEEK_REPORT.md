# Phase 2 Demo Repair Forward Week Report

Overall status: FORWARD_CONFIRMATION_FAILED_REVIEW_REQUIRED

Forward-week report only. It does not authorize canonical Phase 2 or runtime promotion.

Generated at UTC: `2026-07-12T04:02:03.719573Z`
Policy ID: `phase2_demo_repair_policy_2026_06_12_v2`
Forward window starts: `2026-06-09 00:00:00`
Expected window end: `2026-06-16 00:00:00`
Latest post-start entry: `2026-06-19 18:05:01`
Elapsed days: `10.7535` / `7.0`
Promotion decision: `NOT_ELIGIBLE_WEAK_FORWARD_RESULT`

## Required Comparison

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Pre-repair baseline | 228 | 228 | 0 | 87 | 140 | 38.33% | -25.44 | 0.00 | -25.44 | 0.99 | 28.43 | -17.85 |
| Pre-repair target baseline | 129 | 129 | 0 | 45 | 83 | 35.16% | -444.36 | 0.00 | -444.36 | 0.76 | 30.46 | -21.87 |
| Post-repair actual | 1070 | 1070 | 0 | 340 | 680 | 33.33% | -3116.32 | 0.00 | -3116.32 | 0.79 | 33.60 | -21.38 |
| Post target baseline | 658 | 658 | 0 | 221 | 416 | 34.69% | -1838.50 | 0.00 | -1838.50 | 0.82 | 37.96 | -24.59 |
| Post repair-rule v1 would keep | 374 | 374 | 0 | 117 | 236 | 33.14% | -1334.31 | 0.00 | -1334.31 | 0.75 | 33.88 | -22.45 |
| Post repair-rule v1 would block | 284 | 284 | 0 | 104 | 180 | 36.62% | -504.19 | 0.00 | -504.19 | 0.90 | 42.55 | -27.38 |
| Post whole portfolio after repair-rule v1 | 786 | 786 | 0 | 236 | 500 | 32.07% | -2612.13 | 0.00 | -2612.13 | 0.73 | 29.65 | -19.22 |
| Post strict quarantine would keep | 0 | 0 | 0 | 0 | 0 | n/a | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a |
| Post strict quarantine would block | 658 | 658 | 0 | 221 | 416 | 34.69% | -1838.50 | 0.00 | -1838.50 | 0.82 | 37.96 | -24.59 |
| Shadow would keep | 460 | 460 | 0 | 144 | 287 | 31.30 | -782.32 | 0.00 | -782.32 | 0.82 | 24.97 | -15.26 |
| Shadow would block | 838 | 838 | 0 | 283 | 533 | 33.77 | -2359.44 | 0.00 | -2359.44 | 0.81 | 36.39 | -23.75 |

Post repair-rule target PnL delta: `504.19` AED
Post repair-rule whole-portfolio PnL delta: `504.19` AED
Post strict-quarantine target PnL delta: `1838.5` AED

## Confirmation Checks

| Check | Value |
|---|---:|
| fresh_week_elapsed | `True` |
| min_target_closed_trades | `True` |
| repair_closed_pnl_improves | `True` |
| repair_pf_preserved_or_improves | `False` |
| repair_win_rate_preserved_or_improves | `False` |
| retained_trade_pct | `56.84` |
| required_target_closed_trades | `30` |

## Promotion Requirement

- Duplicate-hidden PF and PnL improve.
- Win rate improves or is preserved.
- Enough trade count remains.
- One fresh forward week survives.
- Owner/reviewer approval is recorded.

No rule can be promoted from shadow to demo enforcement without owner/reviewer approval.

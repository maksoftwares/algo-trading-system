# Phase 2 Demo Loss Review Verdict - No Runtime Touch

```text
status: EXPERIMENTAL_LOSS_PATTERN_FOUND
runtime_change_authorized: false
current_demo_eas_touched: false
mt5_terminal_touched: false
mql5_source_touched: false
canonical_phase2_authority: false
router_change_authorized: false
shadow_filter_enforced: false
same_family_guard_implemented: false
future_owner_decision_required: true
```

## Boundary

This is a repo-only review of already committed CSV artifacts. It is experimental demo evidence only. It does not authorize canonical Phase 2, paper-mode execution, live trading, router/session-filter enforcement, touching currently running demo EAs, chart changes, EA input changes, position/order changes, attached-EA changes, or any broker-side action.

The shadow filter is a measurement only. It was not enforced. MT5, charts, inputs, positions, orders, and attached EAs were not modified by this review task.

## Source Artifacts

- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_ACTUAL_BROKER_TRADES_DIRECT_MT5_2026_06_04.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_DEMO_LOSS_CASE_STUDY_2026_06_04.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\PHASE2_DEMO_SHADOW_FILTER_REPORT_2026_06_04.md`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04.zip`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_LOSS_CASE_STUDY_TRADES_2026_06_04.csv`
- `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\docs\review_exports\PHASE2_DEMO_ACTUAL_TRADES_REVIEW_2026_06_04\PHASE2_DEMO_SHADOW_FILTER_TRADES.csv`

## Executive Summary

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | Floating AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw grouped actual trades | 202 | 197 | 5 | 72 | 125 | 36.55% | -299.67 | 25.02 | 0.87 | 28.37 | -18.74 |
| Duplicate-hidden decision view | 119 | 116 | 3 | 43 | 73 | 37.07% | -135.38 | 13.34 | 0.90 | 27.02 | -17.77 |
| Shadow would-keep subset | 59 | 57 | 2 | 27 | 30 | 47.37% | 279.86 | 6.80 | 1.55 | 29.26 | -17.01 |
| Shadow would-block subset | 60 | 59 | 1 | 16 | 43 | 27.12% | -415.24 | 6.54 | 0.47 | 23.23 | -18.30 |

- Duplicate-hidden baseline remains negative: 116 closed trades, 37.07% win rate, -135.38 AED closed PnL, PF 0.90.
- The measured shadow rule would keep 57 closed trades at 47.37% win rate and 279.86 AED closed PnL, while the would-block subset produced -415.24 AED.
- This is enough to identify a loss pattern, not enough to deploy a runtime filter.

## Main Loss Drivers

1. `symbol_normalized_round_retest_v0` loss concentration.
2. XAUUSD Morning/Afternoon weakness.
3. `session_extreme_retest_v0` weakness.
4. Same-family duplicate/correlated exposure.
5. Missing spread/slippage/cost_R decomposition in current trade rows.

### By Candidate

| candidate | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | 46 | 2 | 16 | 30 | 34.78% | -310.79 | 0.59 | 28.01 | -25.30 |
| session_extreme_retest_v0 | 31 | 0 | 10 | 21 | 32.26% | -66.47 | 0.76 | 21.07 | -13.20 |
| swing_breakout_retest_v0 | 2 | 0 | 1 | 1 | 50.00% | 61.95 | 32.45 | 63.92 | -1.97 |
| breakout_retest | 37 | 1 | 16 | 21 | 43.24% | 179.93 | 1.69 | 27.44 | -12.34 |

### By Symbol

| symbol | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| XAUUSD | 88 | 1 | 31 | 57 | 35.23% | -140.89 | 0.89 | 35.60 | -21.83 |
| USDJPY | 7 | 1 | 2 | 5 | 28.57% | -8.18 | 0.28 | 1.59 | -2.27 |
| EURUSD | 21 | 1 | 10 | 11 | 47.62% | 13.69 | 1.33 | 5.51 | -3.76 |

### By Time Bucket

| time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Morning 06:00-11:59 | 23 | 1 | 7 | 16 | 30.43% | -209.50 | 0.40 | 20.31 | -21.98 |
| Afternoon 12:00-15:59 | 29 | 1 | 8 | 21 | 27.59% | -157.08 | 0.44 | 15.20 | -13.27 |
| Night 20:00-05:59 | 45 | 0 | 18 | 27 | 40.00% | 58.26 | 1.13 | 28.89 | -17.10 |
| Evening 16:00-19:59 | 19 | 1 | 10 | 9 | 52.63% | 172.94 | 1.84 | 37.79 | -22.77 |

### Worst Candidate x Symbol x Time Clusters

| candidate | symbol | time_bucket | Closed | Open | Wins | Losses | Win Rate | Closed PnL AED | PF | Avg Win | Avg Loss |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | 17 | 1 | 4 | 13 | 23.53% | -213.80 | 0.34 | 26.94 | -24.74 |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | 5 | 0 | 1 | 4 | 20.00% | -80.50 | 0.35 | 43.65 | -31.04 |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 3 | 0 | 0 | 3 | 0.00% | -67.83 | 0.00 | n/a | -22.61 |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | 6 | 0 | 1 | 5 | 16.67% | -67.67 | 0.31 | 29.74 | -19.48 |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | 7 | 0 | 1 | 6 | 14.29% | -64.71 | 0.44 | 50.19 | -19.15 |
| session_extreme_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | 10 | 0 | 3 | 7 | 30.00% | -16.88 | 0.82 | 25.89 | -13.51 |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | 4 | 0 | 1 | 3 | 25.00% | -5.43 | 0.50 | 5.51 | -3.65 |
| breakout_retest | EURUSD | Night 20:00-05:59 | 6 | 0 | 2 | 4 | 33.33% | -4.52 | 0.71 | 5.51 | -3.88 |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | 1 | 0 | 0 | 1 | 0.00% | -3.64 | 0.00 | n/a | -3.64 |
| breakout_retest | USDJPY | Morning 06:00-11:59 | 1 | 0 | 0 | 1 | 0.00% | -3.50 | 0.00 | n/a | -3.50 |
| session_extreme_retest_v0 | USDJPY | Afternoon 12:00-15:59 | 3 | 0 | 1 | 2 | 33.33% | -2.58 | 0.40 | 1.72 | -2.15 |
| swing_breakout_retest_v0 | USDJPY | Evening 16:00-19:59 | 1 | 0 | 0 | 1 | 0.00% | -1.97 | 0.00 | n/a | -1.97 |

## Recommended Future Fixes

- Future family-level duplicate guard. Not implemented in this task; requires explicit owner authorization if it affects runtime.
- Future passive-only demotion for weak variants. Not implemented in this task; requires explicit owner authorization if it affects runtime.
- Future pre-registered shadow filter forward test. Not implemented in this task; requires explicit owner authorization if it affects runtime.
- Future enhanced trade ledger fields for spread, slippage, and cost_R decomposition. Not implemented in this task; requires explicit owner authorization if it affects runtime.
- Future Phase 0R lower-cost independent research. Not implemented in this task; requires explicit owner authorization if it affects runtime.

## Decision

`EXPERIMENTAL_LOSS_PATTERN_FOUND`. The review found a plausible selection/timing and same-family duplication problem. The fix remains future-only and owner-reviewed. No runtime change is authorized by this document.

- Keep current demo EAs untouched.
- Keep shadow filter as measurement only.
- Do not treat demo PnL as canonical evidence.
- Continue Phase 0R replacement research.

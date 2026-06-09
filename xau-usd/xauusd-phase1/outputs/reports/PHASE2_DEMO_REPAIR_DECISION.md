# Phase 2 Demo Repair Decision

Overall status: REPAIR_DECISION_READY_NO_RUNTIME_CHANGE

Decision report only. No MT5 charts, EA inputs, presets, orders, positions, or canonical Phase 2 status are changed.

Generated at UTC: `2026-06-09T07:15:09.031297Z`
Policy ID: `phase2_demo_repair_policy_2026_06_09_v1`
Trade source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv`
Weakness shadow source: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_EA_WEAKNESS_SHADOW_REPORT.json`
Canonical Phase 2 authorized: `false`
Live trading authorized: `false`

## Summary

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw broker view | 384 | 377 | 7 | 150 | 227 | 39.79% | 288.73 | 22.76 | 311.49 | 1.07 | 30.92 | -19.16 |
| Duplicate-hidden decision view | 225 | 220 | 5 | 85 | 135 | 38.64% | 9.04 | 16.32 | 25.36 | 1.00 | 28.43 | -17.84 |

## Shadow Policy Reference

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Combined shadow would keep | 79 | 78 | 1 | 36 | 42 | 46.15 | 483.04 | 4.08 | 487.12 | 2.21 | 24.54 | -9.53 |
| Combined shadow would block | 146 | 142 | 4 | 49 | 93 | 34.51 | -474.00 | 12.24 | -461.76 | 0.76 | 31.30 | -21.59 |

## Class Counts

| Class | Buckets |
|---|---:|
| DISABLED_SYMBOL | 9 |
| KEEP_DEMO | 3 |
| OBSERVER_ONLY | 2 |
| OWNER_REVIEW_REQUIRED | 7 |
| REDUCE_DEMO | 2 |
| SUSPEND_NO_NEW_ENTRIES | 14 |

## Candidate / Symbol / Time Decisions

| Candidate | Symbol | Time Bucket | Class | Closed | Win Rate | PnL | PF | Reason |
|---|---|---|---|---:|---:|---:|---:|---|
| WR50_BreakoutEvening_v0 | XAUUSD | Night 20:00-05:59 | OBSERVER_ONLY | 2 | 0.00% | -74.00 | 0.00 | WR50_BreakoutEvening_v0 is observer-only under the repair policy. |
| breakout_retest | EURUSD | Afternoon 12:00-15:59 | OWNER_REVIEW_REQUIRED | 10 | 30.00% | -10.25 | 0.62 | EURUSD experimental exposure is under owner lot-size review. |
| breakout_retest | EURUSD | Evening 16:00-19:59 | OWNER_REVIEW_REQUIRED | 4 | 100.00% | 22.10 | inf | EURUSD experimental exposure is under owner lot-size review. |
| breakout_retest | EURUSD | Morning 06:00-11:59 | OWNER_REVIEW_REQUIRED | 5 | 40.00% | -0.07 | 0.99 | EURUSD experimental exposure is under owner lot-size review. |
| breakout_retest | EURUSD | Night 20:00-05:59 | OWNER_REVIEW_REQUIRED | 11 | 36.36% | -5.37 | 0.80 | EURUSD experimental exposure is under owner lot-size review. |
| breakout_retest | GBPUSD | Evening 16:00-19:59 | KEEP_DEMO | 0 | n/a | 0.00 | n/a | breakout_retest remains controlled demo candidate. |
| breakout_retest | USDJPY | Afternoon 12:00-15:59 | DISABLED_SYMBOL | 3 | 66.67% | 13.80 | 4.85 | USDJPY is disabled by repair policy. |
| breakout_retest | USDJPY | Morning 06:00-11:59 | DISABLED_SYMBOL | 2 | 0.00% | -4.76 | 0.00 | USDJPY is disabled by repair policy. |
| breakout_retest | XAUUSD | Afternoon 12:00-15:59 | REDUCE_DEMO | 7 | 28.57% | -33.45 | 0.66 | XAUUSD morning/afternoon remains a shadow-forward block candidate. |
| breakout_retest | XAUUSD | Evening 16:00-19:59 | KEEP_DEMO | 9 | 88.89% | 323.39 | 14.19 | breakout_retest remains controlled demo candidate. |
| breakout_retest | XAUUSD | Morning 06:00-11:59 | REDUCE_DEMO | 11 | 27.27% | -13.75 | 0.92 | XAUUSD morning/afternoon remains a shadow-forward block candidate. |
| breakout_retest | XAUUSD | Night 20:00-05:59 | KEEP_DEMO | 20 | 45.00% | 166.01 | 1.81 | breakout_retest remains controlled demo candidate. |
| session_extreme_retest_v0 | EURUSD | Afternoon 12:00-15:59 | SUSPEND_NO_NEW_ENTRIES | 2 | 50.00% | 1.84 | 1.50 | session_extreme_retest_v0 is suspended for new demo entries. |
| session_extreme_retest_v0 | EURUSD | Evening 16:00-19:59 | SUSPEND_NO_NEW_ENTRIES | 1 | 0.00% | -3.64 | 0.00 | session_extreme_retest_v0 is suspended for new demo entries. |
| session_extreme_retest_v0 | EURUSD | Night 20:00-05:59 | SUSPEND_NO_NEW_ENTRIES | 4 | 75.00% | 12.66 | 4.31 | session_extreme_retest_v0 is suspended for new demo entries. |
| session_extreme_retest_v0 | USDJPY | Afternoon 12:00-15:59 | DISABLED_SYMBOL | 3 | 33.33% | -2.58 | 0.40 | USDJPY is disabled by repair policy. |
| session_extreme_retest_v0 | USDJPY | Evening 16:00-19:59 | DISABLED_SYMBOL | 3 | 0.00% | -10.35 | 0.00 | USDJPY is disabled by repair policy. |
| session_extreme_retest_v0 | USDJPY | Night 20:00-05:59 | DISABLED_SYMBOL | 2 | 0.00% | -5.76 | 0.00 | USDJPY is disabled by repair policy. |
| session_extreme_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | SUSPEND_NO_NEW_ENTRIES | 11 | 36.36% | 21.38 | 1.23 | session_extreme_retest_v0 is suspended for new demo entries. |
| session_extreme_retest_v0 | XAUUSD | Evening 16:00-19:59 | SUSPEND_NO_NEW_ENTRIES | 6 | 33.33% | -33.84 | 0.66 | session_extreme_retest_v0 is suspended for new demo entries. |
| session_extreme_retest_v0 | XAUUSD | Night 20:00-05:59 | SUSPEND_NO_NEW_ENTRIES | 10 | 10.00% | -112.94 | 0.31 | session_extreme_retest_v0 is suspended for new demo entries. |
| swing_breakout_retest_v0 | EURUSD | Afternoon 12:00-15:59 | OWNER_REVIEW_REQUIRED | 2 | 50.00% | 1.76 | 1.47 | EURUSD experimental exposure is under owner lot-size review. |
| swing_breakout_retest_v0 | EURUSD | Evening 16:00-19:59 | OWNER_REVIEW_REQUIRED | 1 | 100.00% | 5.47 | inf | EURUSD experimental exposure is under owner lot-size review. |
| swing_breakout_retest_v0 | EURUSD | Night 20:00-05:59 | OWNER_REVIEW_REQUIRED | 1 | 0.00% | -3.67 | 0.00 | EURUSD experimental exposure is under owner lot-size review. |
| swing_breakout_retest_v0 | USDJPY | Afternoon 12:00-15:59 | DISABLED_SYMBOL | 1 | 0.00% | -1.15 | 0.00 | USDJPY is disabled by repair policy. |
| swing_breakout_retest_v0 | USDJPY | Evening 16:00-19:59 | DISABLED_SYMBOL | 4 | 25.00% | -3.76 | 0.28 | USDJPY is disabled by repair policy. |
| swing_breakout_retest_v0 | USDJPY | Night 20:00-05:59 | DISABLED_SYMBOL | 2 | 0.00% | -10.38 | 0.00 | USDJPY is disabled by repair policy. |
| swing_breakout_retest_v0 | XAUUSD | Evening 16:00-19:59 | OBSERVER_ONLY | 1 | 100.00% | 63.92 | inf | swing_breakout_retest_v0 is observer-only under the repair policy. |
| symbol_normalized_round_retest_v0 | EURUSD | Afternoon 12:00-15:59 | SUSPEND_NO_NEW_ENTRIES | 1 | 100.00% | 5.47 | inf | symbol_normalized_round_retest_v0 is suspended for new demo entries. |
| symbol_normalized_round_retest_v0 | EURUSD | Evening 16:00-19:59 | SUSPEND_NO_NEW_ENTRIES | 3 | 66.67% | 6.97 | 2.91 | symbol_normalized_round_retest_v0 is suspended for new demo entries. |
| symbol_normalized_round_retest_v0 | EURUSD | Morning 06:00-11:59 | SUSPEND_NO_NEW_ENTRIES | 1 | 100.00% | 5.51 | inf | symbol_normalized_round_retest_v0 is suspended for new demo entries. |
| symbol_normalized_round_retest_v0 | GBPUSD | Evening 16:00-19:59 | SUSPEND_NO_NEW_ENTRIES | 0 | n/a | 0.00 | n/a | symbol_normalized_round_retest_v0 is suspended for new demo entries. |
| symbol_normalized_round_retest_v0 | USDJPY | Afternoon 12:00-15:59 | DISABLED_SYMBOL | 0 | n/a | 0.00 | n/a | USDJPY is disabled by repair policy. |
| symbol_normalized_round_retest_v0 | XAUUSD | Afternoon 12:00-15:59 | SUSPEND_NO_NEW_ENTRIES | 4 | 0.00% | -88.40 | 0.00 | symbol_normalized_round_retest_v0 is suspended for new demo entries. |
| symbol_normalized_round_retest_v0 | XAUUSD | Evening 16:00-19:59 | SUSPEND_NO_NEW_ENTRIES | 10 | 40.00% | -0.30 | 1.00 | symbol_normalized_round_retest_v0 is suspended for new demo entries. |
| symbol_normalized_round_retest_v0 | XAUUSD | Morning 06:00-11:59 | SUSPEND_NO_NEW_ENTRIES | 30 | 33.33% | -195.31 | 0.64 | symbol_normalized_round_retest_v0 is suspended for new demo entries. |
| symbol_normalized_round_retest_v0 | XAUUSD | Night 20:00-05:59 | SUSPEND_NO_NEW_ENTRIES | 33 | 42.42% | -27.51 | 0.94 | symbol_normalized_round_retest_v0 is suspended for new demo entries. |

## Operational Decision

- Prepare controlled demo-only quarantine for suspended weak variants.
- Do not enforce XAUUSD morning/afternoon filtering until a fresh forward week confirms the shadow result.
- Do not treat this report as canonical Phase 2 approval.
- Do not close open positions automatically.

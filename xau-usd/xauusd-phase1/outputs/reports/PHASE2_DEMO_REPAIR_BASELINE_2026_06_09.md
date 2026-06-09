# Phase 2 Demo Repair Baseline - 2026-06-09

Overall status: BASELINE_READY_NO_RUNTIME_CHANGE

Baseline before any repair enforcement. No runtime changes were made by the generator.

Generated at UTC: `2026-06-09T07:15:09.031297Z`
Policy ID: `phase2_demo_repair_policy_2026_06_09_v1`
Server: `Capital.ComMena-Demo`
Currency: `AED`
Profile backup path: `NOT_CREATED_DRY_RUN`
Profile backup exists: `false`

## Account / Trade Summary

| View | Total | Closed | Open | Wins | Losses | Win Rate | Closed PnL | Floating | Total PnL | PF | Avg Win | Avg Loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Raw broker view | 384 | 377 | 7 | 150 | 227 | 39.79% | 288.73 | 22.76 | 311.49 | 1.07 | 30.92 | -19.16 |
| Duplicate-hidden decision view | 225 | 220 | 5 | 85 | 135 | 38.64% | 9.04 | 16.32 | 25.36 | 1.00 | 28.43 | -17.84 |
| Open positions | 7 | 0 | 7 | 0 | 0 | n/a | 0.00 | 22.76 | 22.76 | n/a | n/a | n/a |

## Open Positions

| Candidate | Symbol | Direction | Volume | Floating PnL | Position | Magic |
|---|---|---|---:|---:|---|---|
| session_extreme_retest_v0 | XAUUSD | BUY | 0.01 | 10.61 | 3869613 | 920501 |
| session_extreme_retest_v0 | EURUSD | BUY | 0.05 | -1.65 | 3869280 | 920502 |
| symbol_normalized_round_retest_v0 | GBPUSD | SELL | 0.01 | 0.92 | 3868990 | 920304 |
| swing_breakout_retest_v0 | GBPUSD | SELL | 0.01 | 4.08 | 3868295 | 920204 |
| breakout_retest | GBPUSD | SELL | 0.01 | 4.08 | 3868298 | 920104 |
| round_number_retest_v0 | USDJPY | BUY | 0.01 | 2.36 | 3862984 | 920403 |
| symbol_normalized_round_retest_v0 | USDJPY | BUY | 0.01 | 2.36 | 3862985 | 920303 |

## Targets

- Suspend new entries: `symbol_normalized_round_retest_v0`
- Suspend new entries: `session_extreme_retest_v0`
- Disable symbol: `USDJPY`
- Observer-only: `swing_breakout_retest_v0`
- Observer-only: `round_number_retest_v0`
- Observer-only: `WR50_BreakoutEvening_v0`

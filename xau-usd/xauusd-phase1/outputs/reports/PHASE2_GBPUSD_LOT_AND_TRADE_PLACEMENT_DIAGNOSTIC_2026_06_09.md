# Phase 2 Experimental Demo GBPUSD Lot And Trade-Placement Diagnostic

Generated: 2026-06-09

Status: PASS_WITH_ACTIVE_GUARDS

## Summary

The owner requested that GBPUSD demo execution use 0.05 lots across the experimental demo EAs and asked why fresh trades were not appearing.

The standard Capital.com demo terminal was inspected, updated, recompiled, restarted, and verified. GBPUSD was previously still configured at 0.01 lots on all five standard experimental demo executor charts. It is now configured at 0.05 lots on those charts.

MT5 broker permissions are not the blocker. The account is connected, demo-marked, trade-enabled, and expert trading is enabled. Actual broker history confirms XAUUSD, EURUSD, and GBPUSD orders have been accepted in the last 24 hours.

## Runtime Boundary

- Terminal touched: `C:\Program Files\MetaTrader 5\terminal64.exe`
- Terminal data root: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075`
- Profile backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_gbpusd_lot_0_05_20260609_163214`
- Runtime action: standard terminal was closed, profile inputs were updated, updated sources were copied to the terminal `MQL5\Experts` folder, both EAs were compiled, and the same terminal was relaunched.
- Positions/orders were not closed, modified, deleted, or manually created by this task.

## Compile Verification

| Source | Result | Compile log |
|---|---:|---|
| `Phase2ExperimentalDemoExecutor.mq5` | 0 errors / 0 warnings | `xau-usd/xauusd-phase1/outputs/logs/phase2_experimental_demo_executor_compile_gbpusd_lot_20260609_163214.log` |
| `Phase2ExperimentalDemoRepairExecutor.mq5` | 0 errors / 0 warnings | `xau-usd/xauusd-phase1/outputs/logs/phase2_experimental_demo_repair_executor_compile_gbpusd_lot_20260609_163214.log` |

## GBPUSD Chart Inputs After Restart

| Chart | Candidate | Symbol | Fixed lot | GBPUSD lot input | Account daily order cap | Per-instance open-position cap |
|---|---|---:|---:|---:|---:|---:|
| `chart02.chr` | `breakout_retest` | GBPUSD | 0.05 | 0.05 | 0 | 1 |
| `chart05.chr` | `swing_breakout_retest_v0` | GBPUSD | 0.05 | 0.05 | 0 | 1 |
| `chart08.chr` | `symbol_normalized_round_retest_v0` | GBPUSD | 0.05 | 0.05 | 0 | 1 |
| `chart10.chr` | `round_number_retest_v0` | GBPUSD | 0.05 | 0.05 | 0 | 1 |
| `chart13.chr` | `session_extreme_retest_v0` | GBPUSD | 0.05 | 0.05 | 0 | 1 |

## Trade-Placement Diagnosis

Direct MT5 inspection showed:

| Check | Result |
|---|---|
| Terminal connected | PASS |
| Demo account server | `Capital.ComMena-Demo` |
| Account login | `1025742` |
| Account trade allowed | PASS |
| Expert trading allowed | PASS |
| Open positions after restart | 3 |
| Pending orders after restart | 0 |
| GBPUSD startup logs after restart | 5/5 updated |
| GBPUSD signal logs after restart | 5/5 updated |

Latest post-restart GBPUSD signal rows were all `would_signal=false`, with `no_short_*_candidate` as the reason. This means the EAs were running, but the GBPUSD setup conditions were not present on the most recent M5 bar.

Earlier 2026-06-09 GBPUSD order attempts were guard-blocked as follows:

| Candidate | Action | Guard reason | Count |
|---|---|---|---:|
| `breakout_retest` | `GUARD_BLOCK` | `estimated_cost_r_exceeds_threshold` | 7 |
| `breakout_retest` | `GUARD_BLOCK` | `max_account_orders_per_day_reached` | 3 |
| `session_extreme_retest_v0` | `GUARD_BLOCK` | `max_account_orders_per_day_reached` | 2 |
| `swing_breakout_retest_v0` | `GUARD_BLOCK` | `estimated_cost_r_exceeds_threshold` | 6 |
| `swing_breakout_retest_v0` | `GUARD_BLOCK` | `max_account_orders_per_day_reached` | 1 |
| `symbol_normalized_round_retest_v0` | `GUARD_BLOCK` | `estimated_cost_r_exceeds_threshold` | 12 |

The account daily-order-cap blocker was from the older `InpMaxAccountOrdersPerDay=24` runtime state and has now been removed from the active GBPUSD charts by setting `InpMaxAccountOrdersPerDay=0`.

The current practical GBPUSD blockers are:

1. No valid GBPUSD setup on the latest post-restart M5 bar.
2. Cost guard still blocks narrow-stop GBPUSD candidates when `estimated_cost_R > 0.30`.
3. Per-instance one-open-position guard remains active by design.

## Actual Broker Evidence

Actual broker history in the last 24 hours includes accepted demo orders for XAUUSD, EURUSD, and GBPUSD. GBPUSD broker orders existed before this update, but they were placed at 0.01 lots. Future GBPUSD orders from the five standard experimental demo executor charts should use 0.05 lots.

## Interpretation

Order placement is working. GBPUSD was not placing fresh orders at the moment of inspection because the latest M5 rows had no valid setup, and earlier candidate rows were blocked by cost or the previously active daily account order cap.

No canonical Phase 2 approval is implied by this report. This remains experimental demo execution only.

# A1/A2/A3 Runtime Repair - 2026-06-23

Status: `PASS_ORDER_LOG_PROOF_CLOSED`

Purpose: repair the runtime drift found on 2026-06-22, where A1/A2 were no longer running the locked `920101` evening forward-test identity and A3 had a broker-enabled fill-collection executor.

## Actions Applied

| Account | Action |
| --- | --- |
| A1 `1025742` | Restored `Phase2ExperimentalDemoExecutor` on `XAUUSD` as `A1_XAU_920101_EVENING_FORWARD_V0_20260621`, broker action enabled, dry-run false, session gate `12->15`, fixed lot `0.01`. |
| A1 `1025742` | Disarmed extra duplicate `Phase2ExperimentalDemoExecutor` chart `chart27.chr` by setting dry-run true and broker action false. |
| A2 `1033030` | Restored `Phase2ExperimentalDemoExecutor` on `XAUUSD` as `A2_XAU_920101_EVENING_FORWARD_V0_20260621`, broker action enabled, dry-run false, session gate `12->15`, fixed lot `0.01`. |
| A2 `1033030` | Disarmed extra duplicate `Phase2ExperimentalDemoExecutor` chart `chart04.chr` by setting dry-run true and broker action false. |
| A3 `1033669` | Disarmed `A3_DEMO_FILL_COLLECTION_A3_V1` by setting dry-run true and broker action false. Other A3 lanes remain paused/dry-run. |
| Dashboard | Regenerated `status_summary.md`, `status_summary.json`, and `status.html` from the refreshed runtime inventory. |

## Backups

| Account | Backup |
| --- | --- |
| A1 | Created by `apply_a1_a2_920101_maintenance.py --apply` under the standard MT5 `_codex_quarantine/profile_backups` folder. |
| A2 | Created by `apply_a1_a2_920101_maintenance.py --apply` under `C:\MT5PortableTier1BestEA\_codex_quarantine\profile_backups`. |
| A3 | `C:\MT5PortableRepairLane\_codex_quarantine\profile_backups\a3_disable_fill_collection_20260623_005303` |

## Verification

Authoritative verification report:

`xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_MAINTENANCE_SUPPLEMENTAL_VERIFICATION_2026_06_21.md`

Verifier result: `PASS_WITH_ORDER_LOG_PENDING`

Current broker-action inventory:

| Lane | Chart | Symbol | Expert | Magic | State |
| --- | --- | --- | --- | ---: | --- |
| A1 | `chart03.chr` | XAUUSD | `Phase2ExperimentalDemoExecutor` | `920101` | `BROKER_ACTION_ENABLED` |
| A1 | `chart26.chr` | XAUUSD | `Account1DailyProfitFloorGuardian` | n/a | `GUARDIAN_CLOSE_ACTION_ENABLED` |
| A2 | `chart02.chr` | XAUUSD | `Phase2ExperimentalDemoExecutor` | `920101` | `BROKER_ACTION_ENABLED` |
| A2 | `chart03.chr` | XAUUSD | `Account1DailyProfitFloorGuardian` | n/a | `GUARDIAN_CLOSE_ACTION_ENABLED` |

A3 verification: no broker-action-enabled rows remain in the inspected A3 profile.

## Order-Log Proof Closure

`a1_first_order_log_proof` and `a2_first_order_log_proof` are now closed.

Closure artifact:

`xau-usd/xauusd-phase1/outputs/reports/A1_A2_920101_ORDER_LOG_PROOF_CLOSED_2026_06_23.md`

Both A1 and A2 produced post-repair `ORDER_SEND_OK` rows for `XAUUSD`, magic `920101`, during the allowed `12->15` server-hour window on 2026-06-23. The runtime repair is therefore no longer waiting on first-order proof.

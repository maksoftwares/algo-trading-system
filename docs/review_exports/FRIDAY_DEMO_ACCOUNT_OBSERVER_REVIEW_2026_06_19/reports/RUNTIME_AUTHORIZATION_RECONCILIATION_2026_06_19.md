# Runtime Authorization Reconciliation - 2026-06-19

Status: `PASS_CURRENT`

Standing runtime-vs-authorized reconciliation across A1/A2/A3 demo terminals.

Boundary: read-only reconciliation report. It sends no orders, closes no positions, and changes no profile.

Decision: `CURRENT_RUNTIME_AUTHORIZED`

## Current Runtime Charts

| Account | Chart | Symbol | Expert | Magic | Candidate | Dry-run | Broker | Manage | Demo | Classification | Reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| A1 | chart01.chr | EURUSD | `Phase2ExperimentalDemoExecutor` | `` | `breakout_retest` | `false` | `true` | `` | `` | `AUTHORIZED` | A1 experimental demo entry lane; governed by A1 goal/session controls. |
| A1 | chart02.chr | GBPUSD | `Phase2ExperimentalDemoExecutor` | `` | `breakout_retest` | `false` | `true` | `` | `` | `AUTHORIZED` | A1 experimental demo entry lane; governed by A1 goal/session controls. |
| A1 | chart18.chr | XAUUSD | `Phase2ExperimentalDemoRepairExecutor` | `` | `symbol_normalized_round_retest_v0_repair_v1` | `false` | `true` | `` | `` | `AUTHORIZED` | A1 experimental demo entry lane; governed by A1 goal/session controls. |
| A1 | chart19.chr | XAUUSD | `Phase2ExperimentalDemoRepairExecutor` | `` | `session_extreme_retest_v0_repair_v1` | `false` | `true` | `` | `` | `AUTHORIZED` | A1 experimental demo entry lane; governed by A1 goal/session controls. |
| A1 | chart20.chr | EURUSD | `Phase2ExperimentalDemoRepairExecutor` | `` | `session_extreme_retest_v0_repair_v1` | `false` | `true` | `` | `` | `AUTHORIZED` | A1 experimental demo entry lane; governed by A1 goal/session controls. |
| A1 | chart21.chr | XAUUSD | `WR50_BreakoutWideStop_v0` | `930300` | `` | `` | `` | `` | `true` | `AUTHORIZED` | A1 experimental demo entry lane; governed by A1 goal/session controls. |
| A1 | chart24.chr | XAUUSD | `AccountEquityGuardianShadow` | `` | `` | `` | `` | `` | `` | `AUTHORIZED_SHADOW` | A1 support/guardian/observer lane. |
| A1 | chart26.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `` | `` | `false` | `` | `` | `` | `AUTHORIZED_SHADOW` | A1 support/guardian/observer lane. |
| A2 | chart01.chr | XAUUSD | `AccountEquityGuardianShadow` | `` | `` | `` | `` | `` | `` | `AUTHORIZED_SHADOW` | Non-entry support/observer lane. |
| A2 | chart02.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `` | `breakout_retest` | `false` | `true` | `` | `` | `AUTHORIZED` | A2 is the tier-1 breakout-only demo lane. |
| A2 | chart03.chr | XAUUSD | `DirectionStatePublisher` | `` | `` | `` | `` | `` | `` | `AUTHORIZED_SHADOW` | Non-entry support/observer lane. |
| A3 | chart01.chr | XAUUSD | `Account3BreakoutPlainExecutor` | `933200` | `` | `true` | `false` | `` | `` | `PAUSED` | A3 chart is disarmed as expected. |
| A3 | chart02.chr | XAUUSD | `Account3BreakoutImprovedExecutor` | `933300` | `` | `true` | `false` | `` | `` | `PAUSED` | A3 chart is disarmed as expected. |
| A3 | chart04.chr | XAUUSD | `Account3BreakoutTier1CompatExecutor` | `933400` | `` | `true` | `false` | `` | `` | `PAUSED` | A3 chart is disarmed as expected. |
| A3 | chart05.chr | XAUUSD | `Account3ProfitLockExitManager` | `` | `` | `true` | `` | `false` | `` | `PAUSED` | A3 chart is disarmed as expected. |
| A3 | chart06.chr | XAUUSD | `Account3SoftRetestExecutor` | `933500` | `` | `true` | `false` | `` | `` | `PAUSED` | SoftRetest 933500 was previously drifted into broker action; current chart is now paused. |

## Prior Drift Evidence

Evidence date: `2026_06_19`

| Account | Magic | Candidate | Trades | PnL AED_001 | Classification |
| --- | --- | --- | ---: | ---: | --- |
| n/a | n/a | n/a | 0 | 0.00 | `NO_PRIOR_DRIFT_IN_EVIDENCE_FILE` |

## Trade Evidence Summary

| Account | Magic | Candidate | Trades | PnL AED_001 |
| --- | --- | --- | ---: | ---: |
| 1025742 | 921101 | `symbol_normalized_round_retest_v0_repair_v1` | 3 | 90.3 |
| 1033030 | 920101 | `breakout_retest` | 2 | -23.47 |

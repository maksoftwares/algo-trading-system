# Runtime Authorization Reconciliation - 2026-06-19

Status: `PASS_CURRENT_PRIOR_DRIFT_REMEDIATED`

Standing runtime-vs-authorized reconciliation across A1/A2/A3 demo terminals.

Boundary: read-only reconciliation report. It sends no orders, closes no positions, and changes no profile.

Decision: `CURRENT_RUNTIME_SAFE; PRIOR_A3_DRIFT_REMEDIATED; KEEP_RECONCILIATION_STANDING`

## Current Runtime Charts

| Account | Chart | Symbol | Expert | Magic | Candidate | Dry-run | Broker | Manage | Demo | Classification | Reason |
| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| A1 | chart03.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `` | `breakout_retest` | `false` | `true` | `` | `` | `AUTHORIZED` | A1 experimental demo entry lane; governed by A1 goal/session controls. |
| A1 | chart24.chr | XAUUSD | `AccountEquityGuardianShadow` | `` | `` | `` | `` | `` | `` | `AUTHORIZED_SHADOW` | A1 support/guardian/observer lane. |
| A1 | chart26.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `` | `` | `false` | `` | `` | `` | `AUTHORIZED_SHADOW` | A1 support/guardian/observer lane. |
| A1 | chart27.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `` | `breakout_retest` | `true` | `false` | `` | `` | `AUTHORIZED_BUT_NOT_ARMED` | A1 experimental demo entry lane; governed by A1 goal/session controls. |
| A2 | chart01.chr | XAUUSD | `AccountEquityGuardianShadow` | `` | `` | `` | `` | `` | `` | `AUTHORIZED_SHADOW` | Non-entry support/observer lane. |
| A2 | chart02.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `` | `breakout_retest` | `false` | `true` | `` | `` | `AUTHORIZED` | A2 is the tier-1 breakout-only demo lane. |
| A2 | chart03.chr | XAUUSD | `Account1DailyProfitFloorGuardian` | `` | `` | `false` | `` | `` | `` | `AUTHORIZED_SHADOW` | Non-entry support/observer lane. |
| A2 | chart04.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `` | `breakout_retest` | `true` | `false` | `` | `` | `AUTHORIZED_BUT_NOT_ARMED` | A2 is the tier-1 breakout-only demo lane. |
| A3 | chart01.chr | XAUUSD | `Account3BreakoutPlainExecutor` | `933200` | `` | `true` | `false` | `` | `` | `PAUSED` | A3 chart is disarmed as expected. |
| A3 | chart02.chr | XAUUSD | `Account3BreakoutImprovedExecutor` | `933300` | `` | `true` | `false` | `` | `` | `PAUSED` | A3 chart is disarmed as expected. |
| A3 | chart04.chr | XAUUSD | `Account3BreakoutTier1CompatExecutor` | `933400` | `` | `true` | `false` | `` | `` | `PAUSED` | A3 chart is disarmed as expected. |
| A3 | chart05.chr | XAUUSD | `Account3ProfitLockExitManager` | `` | `` | `true` | `` | `false` | `` | `PAUSED` | A3 chart is disarmed as expected. |
| A3 | chart06.chr | XAUUSD | `Account3SoftRetestExecutor` | `933500` | `` | `true` | `false` | `` | `` | `PAUSED` | SoftRetest 933500 was previously drifted into broker action; current chart is now paused. |
| A3 | chart07.chr | XAUUSD | `Phase2ExperimentalDemoExecutor` | `` | `breakout_retest` | `true` | `false` | `` | `` | `PAUSED` | A3 chart is disarmed as expected. |

## Prior Drift Evidence

Evidence date: `2026_06_18`

| Account | Magic | Candidate | Trades | PnL AED_001 | Classification |
| --- | --- | --- | ---: | ---: | --- |
| 1033669 | 933200 | `a3_breakout_plain` | 5 | -203.32 | `PAUSED_BUT_TRADING_EVIDENCE` |
| 1033669 | 933300 | `a3_breakout_improved` | 6 | -120.29 | `PAUSED_BUT_TRADING_EVIDENCE` |
| 1033669 | 933500 | `A3_SOFT_RETEST_V2` | 1 | 23.64 | `PAUSED_BUT_TRADING_EVIDENCE` |

## Trade Evidence Summary

| Account | Magic | Candidate | Trades | PnL AED_001 |
| --- | --- | --- | ---: | ---: |
| 1025742 | 920101 | `breakout_retest` | 4 | -108.54 |
| 1025742 | 920201 | `swing_breakout_retest_v0` | 6 | -135.06 |
| 1025742 | 920501 | `session_extreme_retest_v0` | 1 | 59.44 |
| 1025742 | 921101 | `symbol_normalized_round_retest_v0_repair_v1` | 8 | -11.69 |
| 1025742 | 921201 | `session_extreme_retest_v0_repair_v1` | 3 | 57.02 |
| 1033030 | 920101 | `breakout_retest` | 1 | -44.12 |
| 1033669 | 933200 | `a3_breakout_plain` | 5 | -203.32 |
| 1033669 | 933300 | `a3_breakout_improved` | 6 | -120.29 |
| 1033669 | 933500 | `A3_SOFT_RETEST_V2` | 1 | 23.64 |

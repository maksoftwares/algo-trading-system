# Phase 2 Floor Decisions Applied

Overall status: PASS

Owner-approved Block A maintenance window: A3 family duplicate mutex, A6 USDJPY broker-action off, A7 AccountEquityGuardianShadow Stage A attach. Declined A1/A2/A4/A5 were not changed.

Demo only; no canonical Phase 2 approval; no live trading or real-capital authorization.

## Applied Items

| Item | Result | Evidence |
|---|---|---|
| A3 family duplicate mutex | APPLIED | Guard reason `WOULD_DUPLICATE_FAMILY_EVENT`; compile log `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_Phase2ExperimentalDemoExecutor_floor_decisions.log` |
| A6 USDJPY broker-action off | OFF | No USDJPY charts with broker action were found. |
| A7 guardian Stage A attach | ATTACHED | `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart24.chr`; compile log `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_AccountEquityGuardianShadow_floor_decisions.log` |

## Declined Items Preserved

- A1 weak-family quarantine: declined, not changed.
- A2 repair executor off: declined, not changed.
- A4 guard re-arm: declined, not changed.
- A5 lot revert: declined, not changed.

## Runtime Evidence

- Terminal: `C:\Program Files\MetaTrader 5\terminal64.exe`
- Profile backup: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\_codex_quarantine\profile_backups\default_profile_before_floor_decisions_20260612_111909`
- Closed before profile/source change: `True`
- Relaunched: `True`
- Guardian startup log: `C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\EQUITY_GUARDIAN_SHADOW_STARTUP.csv` exists=`True`
- Broker-action chart count after: `17`

## Checks

| Check | Status | Evidence |
|---|---|---|
| A3_family_mutex_source_deployed | PASS | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_Phase2ExperimentalDemoExecutor_floor_decisions.log |
| A7_guardian_source_deployed | PASS | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Logs\compile_AccountEquityGuardianShadow_floor_decisions.log |
| A6_usdjpy_broker_action_off | PASS | No USDJPY charts with broker action were found. |
| A7_guardian_stage_a_attached | PASS | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Profiles\Charts\Default\chart24.chr |
| guardian_startup_log | PASS | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\EQUITY_GUARDIAN_SHADOW_STARTUP.csv |
| declined_items_untouched | PASS | A1/A2/A4/A5 were not changed by this script. |

## Before Charts

| Chart | Symbol | Expert | Candidate | Broker Action | Dry Run | Lot | EUR Lot | GBP Lot |
|---|---|---|---|---:|---:|---:|---:|---:|
| chart01.chr | EURUSD | Phase2ExperimentalDemoExecutor | breakout_retest | true | false | 0.05 | 0.05 | 0.05 |
| chart02.chr | GBPUSD | Phase2ExperimentalDemoExecutor | breakout_retest | true | false | 0.05 | 0.05 | 0.05 |
| chart03.chr | XAUUSD | Phase2ExperimentalDemoExecutor | breakout_retest | true | false | 0.01 | 0.05 | 0.05 |
| chart04.chr | EURUSD | Phase2ExperimentalDemoExecutor | swing_breakout_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart05.chr | GBPUSD | Phase2ExperimentalDemoExecutor | swing_breakout_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart06.chr | XAUUSD | Phase2ExperimentalDemoExecutor | swing_breakout_retest_v0 | true | false | 0.01 | 0.05 | 0.05 |
| chart07.chr | EURUSD | Phase2ExperimentalDemoExecutor | symbol_normalized_round_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart08.chr | GBPUSD | Phase2ExperimentalDemoExecutor | symbol_normalized_round_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart09.chr | XAUUSD | Phase2ExperimentalDemoExecutor | symbol_normalized_round_retest_v0 | true | false | 0.01 | 0.05 | 0.05 |
| chart10.chr | GBPUSD | Phase2ExperimentalDemoExecutor | round_number_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart11.chr | XAUUSD | Phase2ExperimentalDemoExecutor | round_number_retest_v0 | true | false | 0.01 | 0.05 | 0.05 |
| chart12.chr | EURUSD | Phase2ExperimentalDemoExecutor | session_extreme_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart13.chr | GBPUSD | Phase2ExperimentalDemoExecutor | session_extreme_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart14.chr | XAUUSD | Phase2ExperimentalDemoExecutor | session_extreme_retest_v0 | true | false | 0.01 | 0.05 | 0.05 |
| chart15.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart16.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart17.chr | XAUUSD | WR50_BreakoutExit1R_v0 |  |  |  | 0.01 |  |  |
| chart18.chr | XAUUSD | Phase2ExperimentalDemoRepairExecutor | symbol_normalized_round_retest_v0_repair_v1 | true | false | 0.01 | 0.05 | 0.05 |
| chart19.chr | XAUUSD | Phase2ExperimentalDemoRepairExecutor | session_extreme_retest_v0_repair_v1 | true | false | 0.01 | 0.05 | 0.05 |
| chart20.chr | EURUSD | Phase2ExperimentalDemoRepairExecutor | session_extreme_retest_v0_repair_v1 | true | false | 0.05 | 0.05 | 0.05 |
| chart21.chr | XAUUSD | WR50_BreakoutWideStop_v0 |  |  |  | 0.01 |  |  |
| chart22.chr | XAUUSD | WR50_BreakoutWideStop_v0 |  |  |  | 0.01 |  |  |
| chart23.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart24.chr | XAUUSD | AccountEquityGuardianShadow |  |  |  |  |  |  |

## After Charts

| Chart | Symbol | Expert | Candidate | Broker Action | Dry Run | Lot | EUR Lot | GBP Lot |
|---|---|---|---|---:|---:|---:|---:|---:|
| chart01.chr | EURUSD | Phase2ExperimentalDemoExecutor | breakout_retest | true | false | 0.05 | 0.05 | 0.05 |
| chart02.chr | GBPUSD | Phase2ExperimentalDemoExecutor | breakout_retest | true | false | 0.05 | 0.05 | 0.05 |
| chart03.chr | XAUUSD | Phase2ExperimentalDemoExecutor | breakout_retest | true | false | 0.01 | 0.05 | 0.05 |
| chart04.chr | EURUSD | Phase2ExperimentalDemoExecutor | swing_breakout_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart05.chr | GBPUSD | Phase2ExperimentalDemoExecutor | swing_breakout_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart06.chr | XAUUSD | Phase2ExperimentalDemoExecutor | swing_breakout_retest_v0 | true | false | 0.01 | 0.05 | 0.05 |
| chart07.chr | EURUSD | Phase2ExperimentalDemoExecutor | symbol_normalized_round_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart08.chr | GBPUSD | Phase2ExperimentalDemoExecutor | symbol_normalized_round_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart09.chr | XAUUSD | Phase2ExperimentalDemoExecutor | symbol_normalized_round_retest_v0 | true | false | 0.01 | 0.05 | 0.05 |
| chart10.chr | GBPUSD | Phase2ExperimentalDemoExecutor | round_number_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart11.chr | XAUUSD | Phase2ExperimentalDemoExecutor | round_number_retest_v0 | true | false | 0.01 | 0.05 | 0.05 |
| chart12.chr | EURUSD | Phase2ExperimentalDemoExecutor | session_extreme_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart13.chr | GBPUSD | Phase2ExperimentalDemoExecutor | session_extreme_retest_v0 | true | false | 0.05 | 0.05 | 0.05 |
| chart14.chr | XAUUSD | Phase2ExperimentalDemoExecutor | session_extreme_retest_v0 | true | false | 0.01 | 0.05 | 0.05 |
| chart15.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart16.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart17.chr | XAUUSD | WR50_BreakoutExit1R_v0 |  |  |  | 0.01 |  |  |
| chart18.chr | XAUUSD | Phase2ExperimentalDemoRepairExecutor | symbol_normalized_round_retest_v0_repair_v1 | true | false | 0.01 | 0.05 | 0.05 |
| chart19.chr | XAUUSD | Phase2ExperimentalDemoRepairExecutor | session_extreme_retest_v0_repair_v1 | true | false | 0.01 | 0.05 | 0.05 |
| chart20.chr | EURUSD | Phase2ExperimentalDemoRepairExecutor | session_extreme_retest_v0_repair_v1 | true | false | 0.05 | 0.05 | 0.05 |
| chart21.chr | XAUUSD | WR50_BreakoutWideStop_v0 |  |  |  | 0.01 |  |  |
| chart22.chr | XAUUSD | WR50_BreakoutWideStop_v0 |  |  |  | 0.01 |  |  |
| chart23.chr | XAUUSD | NO_EA |  |  |  |  |  |  |
| chart24.chr | XAUUSD | AccountEquityGuardianShadow |  |  |  |  |  |  |

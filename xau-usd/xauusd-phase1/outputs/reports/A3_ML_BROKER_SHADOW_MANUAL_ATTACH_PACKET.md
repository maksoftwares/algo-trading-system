# A3 ML Broker Shadow Manual Attach Packet

Overall status: BROKER_SHADOW_RUNTIME_PRESENT_ALL_ACCOUNTS
Dataset version: xauusd_c02_multiacct_202606242335_g0a9823b0_c9221d066

## Authorization

- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Broker action authorized: false.

## Upstream Statuses

- C16 EA consumer readiness: BROKER_EXECUTOR_CONSUMERS_READY
- C17 broker shadow consumer deploy: DEPLOYED_COMPILED_SHADOW_CONSUMERS
- C20 runtime evidence: RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS
- C30 broker shadow preset deploy: DEPLOYED_SAFE_PASSIVE_PRESETS

## Account Runtime State

| Account | Login | Active ready | Expected EX5 | Safe presets | Broker tap |
| --- | --- | --- | --- | --- | --- |
| A1 | 1025742 | true | true | true | true |
| A2 | 1033030 | true | true | true | true |
| A3 | 1033669 | true | true | true | true |

## Manual Attach Steps

1. Open each MT5 terminal for A1, A2, and A3.
2. Use a separate XAUUSD M5 chart for the broker-shadow check when you do not want to disturb any existing chart.
3. Attach or reload the recommended broker-shadow expert for that account from the Account Details section.
4. Load the matching C30 safe preset for that account and expert before clicking OK.
5. Confirm InpDryRunOnly=true and InpBrokerActionAllowed=false before clicking OK.
6. Confirm InpMlShadowReadEnabled=true, InpMlHandoffFileName=A3_ML_EA_HANDOFF.csv, and InpMlShadowLogFileName=a3_ml_broker_shadow_tap.csv.
7. Wait for a3_ml_broker_shadow_tap.csv to appear in each account's MQL5/Files folder.
8. Run C28 with --timeout-seconds 300 to wait for observer logs and Python preview read-path proof, then rerun C24.

## Account Details

### A1 1025742

- Terminal: C:/Program Files/MetaTrader 5/terminal64.exe
- Files root: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files
- Recommended broker-shadow expert(s): Phase2ExperimentalDemoExecutor
- Safe preset(s): Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set, Phase2ExperimentalDemoRepairExecutor.A1.a3_ml_shadow_readonly.set
- Handoff file: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A3_ML_EA_HANDOFF.csv
- Shadow tap log to watch: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a3_ml_broker_shadow_tap.csv
- Shadow tap include: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\A3MlShadowTap.mqh
- Current active broker executor count: 1

### A2 1033030

- Terminal: C:/MT5PortableTier1BestEA/terminal64.exe
- Files root: C:\MT5PortableTier1BestEA\MQL5\Files
- Recommended broker-shadow expert(s): Phase2ExperimentalDemoExecutor
- Safe preset(s): Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set
- Handoff file: C:\MT5PortableTier1BestEA\MQL5\Files\A3_ML_EA_HANDOFF.csv
- Shadow tap log to watch: C:\MT5PortableTier1BestEA\MQL5\Files\a3_ml_broker_shadow_tap.csv
- Shadow tap include: C:\MT5PortableTier1BestEA\MQL5\Include\A3MlShadowTap.mqh
- Current active broker executor count: 1

### A3 1033669

- Terminal: C:/MT5PortableRepairLane/terminal64.exe
- Files root: C:\MT5PortableRepairLane\MQL5\Files
- Recommended broker-shadow expert(s): Account3BreakoutImprovedExecutor, Account3BreakoutPlainExecutor, Account3BreakoutTier1CompatExecutor, Account3SoftRetestExecutor, Phase2ExperimentalDemoExecutor
- Safe preset(s): Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set, Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set, Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set, Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set
- Handoff file: C:\MT5PortableRepairLane\MQL5\Files\A3_ML_EA_HANDOFF.csv
- Shadow tap log to watch: C:\MT5PortableRepairLane\MQL5\Files\a3_ml_broker_shadow_tap.csv
- Shadow tap include: C:\MT5PortableRepairLane\MQL5\Include\A3MlShadowTap.mqh
- Current active broker executor count: 5

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| c16_broker_executor_consumers_ready | true | BROKER_EXECUTOR_CONSUMERS_READY |
| c17_compiled_shadow_consumers_deployed | true | DEPLOYED_COMPILED_SHADOW_CONSUMERS |
| c30_safe_passive_presets_deployed | true | DEPLOYED_SAFE_PASSIVE_PRESETS |
| A1_files_root_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A1_files_root_safe | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A1_handoff_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A1_shadow_tap_include_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\A3MlShadowTap.mqh |
| A1_handoff_include_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Include\A3MlEaHandoff.mqh |
| A1_expected_compiled_ex5_exists | true | compiled broker-shadow EX5 files exist |
| A1_active_broker_executor_consumers_ready | true | active broker executors can consume ML handoff |
| A1_safe_broker_shadow_presets_deployed | true | safe C30 presets exist |
| A2_files_root_exists | true | C:\MT5PortableTier1BestEA\MQL5\Files |
| A2_files_root_safe | true | C:\MT5PortableTier1BestEA\MQL5\Files |
| A2_handoff_exists | true | C:\MT5PortableTier1BestEA\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A2_shadow_tap_include_exists | true | C:\MT5PortableTier1BestEA\MQL5\Include\A3MlShadowTap.mqh |
| A2_handoff_include_exists | true | C:\MT5PortableTier1BestEA\MQL5\Include\A3MlEaHandoff.mqh |
| A2_expected_compiled_ex5_exists | true | compiled broker-shadow EX5 files exist |
| A2_active_broker_executor_consumers_ready | true | active broker executors can consume ML handoff |
| A2_safe_broker_shadow_presets_deployed | true | safe C30 presets exist |
| A3_files_root_exists | true | C:\MT5PortableRepairLane\MQL5\Files |
| A3_files_root_safe | true | C:\MT5PortableRepairLane\MQL5\Files |
| A3_handoff_exists | true | C:\MT5PortableRepairLane\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A3_shadow_tap_include_exists | true | C:\MT5PortableRepairLane\MQL5\Include\A3MlShadowTap.mqh |
| A3_handoff_include_exists | true | C:\MT5PortableRepairLane\MQL5\Include\A3MlEaHandoff.mqh |
| A3_expected_compiled_ex5_exists | true | compiled broker-shadow EX5 files exist |
| A3_active_broker_executor_consumers_ready | true | active broker executors can consume ML handoff |
| A3_safe_broker_shadow_presets_deployed | true | safe C30 presets exist |
| broker_action_false | true | report-only; broker action remains false |

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime launch attempted: false.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Broker shadow-tap runtime evidence is present on all accounts. Keep broker action false and continue C28/C24 readiness checks.

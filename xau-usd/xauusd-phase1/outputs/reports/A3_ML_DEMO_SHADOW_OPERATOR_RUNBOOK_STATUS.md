# A3 ML Demo Shadow Operator Runbook

Overall status: DEMO_SHADOW_RUNTIME_CONFIRMED_WAITING_FOR_DATA
Dataset version: xauusd_c02_multiacct_202606242335_g0a9823b0_c9221d066

## Summary

| Item | Status |
| --- | --- |
| c11_readiness_gap | GAP_REMAINS |
| c15_observer_manual_attach | MANUAL_ATTACH_REQUIRED |
| c25_broker_shadow_manual_attach | BROKER_SHADOW_RUNTIME_PRESENT_ALL_ACCOUNTS |
| c26_research_preview_handoff | PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED |
| c28_demo_shadow_post_attach | DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS |
| c30_broker_shadow_preset_deploy | DEPLOYED_SAFE_PASSIVE_PRESETS |
| c31_demo_attach_watch | ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS |
| c32_demo_operator_launch_kit | READY_OPERATOR_ATTACH_KIT |

## Account State

| Account | Observer logs | Broker tap | Safe presets | Handoff | Terminal |
| --- | --- | --- | --- | --- | --- |
| A1 | false | true | true | true | C:/Program Files/MetaTrader 5/terminal64.exe |
| A2 | false | true | true | true | C:/MT5PortableTier1BestEA/terminal64.exe |
| A3 | false | true | true | true | C:/MT5PortableRepairLane/terminal64.exe |

## Exact Attach Matrix

### A1 1025742

- Terminal: C:/Program Files/MetaTrader 5/terminal64.exe
- Observer: A3MlPredictionObserver using C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Broker-shadow: Phase2ExperimentalDemoExecutor using Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set (C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set)
- Broker-shadow log to confirm: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a3_ml_broker_shadow_tap.csv

### A2 1033030

- Terminal: C:/MT5PortableTier1BestEA/terminal64.exe
- Observer: A3MlPredictionObserver using C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Broker-shadow: Phase2ExperimentalDemoExecutor using Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set (C:\MT5PortableTier1BestEA\MQL5\Presets\Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set)
- Broker-shadow log to confirm: C:\MT5PortableTier1BestEA\MQL5\Files\a3_ml_broker_shadow_tap.csv

### A3 1033669

- Terminal: C:/MT5PortableRepairLane/terminal64.exe
- Observer: A3MlPredictionObserver using C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Broker-shadow: Account3BreakoutImprovedExecutor using Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set (C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set), Account3BreakoutPlainExecutor using Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set (C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set), Account3BreakoutTier1CompatExecutor using Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set (C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set), Account3SoftRetestExecutor using Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set (C:\MT5PortableRepairLane\MQL5\Presets\Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set), Phase2ExperimentalDemoExecutor
- Broker-shadow log to confirm: C:\MT5PortableRepairLane\MQL5\Files\a3_ml_broker_shadow_tap.csv

## Operator Steps

1. Open MT5 terminal A1, A2, and A3.
2. On each account, open or select an XAUUSD M5 chart and attach A3MlPredictionObserver with the passive preset.
3. On each account, attach or reload the recommended broker-shadow expert from the account state/details.
4. For each broker-shadow expert, load the matching C30 safe preset before clicking OK.
5. Confirm all broker-shadow settings stay dry-run/passive: InpDryRunOnly=true, InpBrokerActionAllowed=false, InpMlShadowReadEnabled=true.
6. Run the C31 command while or after attaching to see which exact runtime files are still missing.
7. Run the C28 command and wait for DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS.
8. After C28 passes, keep collecting data and run the refresh command after market data advances.

## Commands

- generate_operator_launch_kit: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c32_generate_demo_operator_launch_kit.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- run_operator_launch_kit: `powershell -ExecutionPolicy Bypass -File 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_DEMO_OPERATOR_LAUNCH_KIT.ps1'`
- deploy_broker_shadow_safe_presets: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c30_deploy_broker_shadow_presets.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --deploy`
- broker_shadow_attach_packet: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c25_generate_broker_shadow_manual_attach_packet.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- demo_attach_watch: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c31_watch_demo_attach.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --timeout-seconds 300 --poll-seconds 5`
- post_attach_demo_shadow_wait: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c28_wait_for_demo_shadow_post_attach.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --timeout-seconds 300 --poll-seconds 5`
- check_action_packet: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c24_generate_demo_prediction_action_packet.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- refresh_after_market_data: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c23_run_demo_python_launch_controller.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --refresh-live-readonly --post-attach-timeout-seconds 300 --post-attach-poll-seconds 5`

## Pass Conditions

- C28 status is DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS.
- C30 status is DEPLOYED_SAFE_PASSIVE_PRESETS.
- C27 has confirmed ml_available=true, ml_action=ABSTAIN, and ml_broker_action_authorized=false on A1/A2/A3.
- C20 shows passive observer runtime and broker shadow tap runtime on all accounts.
- C24 still shows broker_action_authorized=false.

## Data Gaps

| Gate | Gap |
| --- | --- |
| dataset_status | needs different category/state |
| market_setup_groups | 18 |
| active_weeks | 4.22 weeks |
| at_least_two_regimes | needs different category/state |
| feature_budget | 6 |
| slippage_readiness | needs different category/state |

## Authorization

- Official model training authorized: false.
- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Broker action authorized: false.

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime launch attempted: false.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Demo-shadow runtime is confirmed. Continue collecting/exporting A1/A2/A3 data until C03/C05/C04/C06 authorize official demo-shadow predictions.

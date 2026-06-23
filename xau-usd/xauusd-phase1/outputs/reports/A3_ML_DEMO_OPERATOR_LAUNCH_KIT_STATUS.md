# A3 ML Demo Operator Launch Kit Status

Overall status: READY_OPERATOR_ATTACH_KIT
Dataset version: xauusd_c02_multiacct_202606212216_geffebb6d_c9221d066

## Summary

- C29 runbook: ACTION_REQUIRED_MANUAL_ATTACH.
- C31 attach watch: WAITING_FOR_MANUAL_ATTACH.
- Operator kit script: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_DEMO_OPERATOR_LAUNCH_KIT.ps1.

## Accounts

| Account | Login | Observer | Broker-shadow |
| --- | --- | --- | --- |
| A1 | 1025742 | A3MlPredictionObserver | Phase2ExperimentalDemoExecutor, Phase2ExperimentalDemoRepairExecutor |
| A2 | 1033030 | A3MlPredictionObserver | Phase2ExperimentalDemoExecutor |
| A3 | 1033669 | A3MlPredictionObserver | Account3BreakoutImprovedExecutor, Account3BreakoutPlainExecutor, Account3BreakoutTier1CompatExecutor, Account3SoftRetestExecutor |

## Commands

- regenerate_operator_launch_kit: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c32_generate_demo_operator_launch_kit.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- run_operator_launch_kit: `powershell -ExecutionPolicy Bypass -File 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_DEMO_OPERATOR_LAUNCH_KIT.ps1'`
- demo_attach_watch: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c31_watch_demo_attach.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --timeout-seconds 300 --poll-seconds 5`
- post_attach_demo_shadow_wait: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c28_wait_for_demo_shadow_post_attach.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --timeout-seconds 300 --poll-seconds 5`

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| accounts_present | true | accounts=3 |
| kit_script_target_safe | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_DEMO_OPERATOR_LAUNCH_KIT.ps1 |
| script_contains_c31_watch | true | C31 watcher command |
| script_contains_c28_proof_command | true | C28 proof command |
| script_has_no_broker_action_tokens | true | ok |

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
- Operator script generated: true.
- Operator script executed: false.
- Broker action authorized: false.

## Next

Run the generated operator kit while attaching/reloading MT5 EAs, then run C28 after C31 passes.

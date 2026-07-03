# A3 ML Demo Prediction Action Packet

Overall status: WAITING_FOR_DATA
Dataset version: xauusd_c02_multiacct_202606242335_g0a9823b0_c9221d066

## Summary

| Item | Status |
| --- | --- |
| c23_status | WAITING_FOR_DATA |
| c11_status | GAP_REMAINS |
| c15_status | MANUAL_ATTACH_REQUIRED |
| c18_status | REHEARSED_RESEARCH_ONLY |
| c20_status | RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS |
| c22_status | RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS |
| c25_status | BROKER_SHADOW_RUNTIME_PRESENT_ALL_ACCOUNTS |
| c26_status | PUBLISHED_RESEARCH_PREVIEW_FAIL_CLOSED |
| c27_status | RESEARCH_PREVIEW_READ_PATH_CONFIRMED_ALL_ACCOUNTS |
| c28_status | DEMO_SHADOW_RUNTIME_CONFIRMED_ALL_ACCOUNTS |
| c29_status | DEMO_SHADOW_RUNTIME_CONFIRMED_WAITING_FOR_DATA |
| c30_status | DEPLOYED_SAFE_PASSIVE_PRESETS |
| c31_status | ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS |
| c32_status | READY_OPERATOR_ATTACH_KIT |

## Data Gaps

| Gate | Observed | Required | Gap |
| --- | --- | --- | --- |
| dataset_status | PIPELINE_ONLY | EXPLORATORY_MODEL or higher | needs different category/state |
| market_setup_groups | 282 | >=300 | 18 |
| active_weeks | 3.78 | >=8 | 4.22 weeks |
| at_least_two_regimes | FALLING | >=2 non-UNKNOWN regimes | needs different category/state |
| feature_budget | 0 | >=6 | 6 |
| slippage_readiness | INSUFFICIENT | ADEQUATE | needs different category/state |

## Manual Attach State

| Account | Expert | Preset | Startup log | Prediction log |
| --- | --- | --- | --- | --- |
| A1 | true | true | false | false |
| A2 | true | true | false | false |
| A3 | true | true | false | false |

## Broker Shadow State

| Account | Active ready | Expected EX5 | Broker tap |
| --- | --- | --- | --- |
| A1 | true | true | true |
| A2 | true | true | true |
| A3 | true | true | true |

## Operator Actions

1. Attach A3MlPredictionObserver on XAUUSD M5 for A1, A2, and A3 using the passive preset.
2. C26 research-preview ABSTAIN handoff is published; after attach, broker-shadow taps should log ml_available=true.
3. Keep A1/A2/A3 terminals collecting passive observer data and rerun C10 with --refresh-live-readonly after new market sessions.
4. Need about 4.22 more active weeks unless older compatible decisions are imported.
5. Need about 18 more market setup groups.

## Commands

- check_now: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c24_generate_demo_prediction_action_packet.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- operator_runbook: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c29_generate_demo_shadow_operator_runbook.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- generate_operator_launch_kit: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c32_generate_demo_operator_launch_kit.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- run_operator_launch_kit: `powershell -ExecutionPolicy Bypass -File 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_DEMO_OPERATOR_LAUNCH_KIT.ps1'`
- broker_shadow_preset_deploy: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c30_deploy_broker_shadow_presets.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --deploy`
- broker_shadow_attach_packet: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c25_generate_broker_shadow_manual_attach_packet.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- demo_attach_watch: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c31_watch_demo_attach.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --timeout-seconds 300 --poll-seconds 5`
- research_preview_handoff_publish: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c26_publish_research_preview_handoff_rehearsal.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --publish`
- research_preview_runtime_verify: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c27_verify_research_preview_runtime_read_path.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1'`
- demo_shadow_post_attach_wait: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c28_wait_for_demo_shadow_post_attach.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --timeout-seconds 300 --poll-seconds 5`
- post_attach_wait: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c23_run_demo_python_launch_controller.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --post-attach-timeout-seconds 300 --post-attach-poll-seconds 5`
- refresh_after_market_data: `'C:\Users\ZHAO ZHU INFORMATION\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\scripts\c23_run_demo_python_launch_controller.py' --root 'C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1' --refresh-live-readonly --post-attach-timeout-seconds 300 --post-attach-poll-seconds 5`

## Authorization

- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Broker action authorized: false.

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime launch attempted: false.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- Model training authorized: false.
- Broker action authorized: false.

## Next

Continue collecting/exporting A1/A2/A3 data and rerun C24 after new market sessions.

# A3 ML Demo Prediction Activation Status

Overall status: WAITING_FOR_DATA
Dataset version: xauusd_c02_multiacct_202606242335_g0a9823b0_c9221d066

## Stage Summary

| Stage | Status |
| --- | --- |
| C03 readiness | NO_GO |
| C05 training | REFUSED_NOT_READY |
| C04 shadow bridge | DISABLED_FAIL_CLOSED |
| C06 EA handoff | REFUSED_NOT_READY |
| C09 observer deploy | DEPLOYED_PASSIVE_OBSERVER |
| C13 fail-closed rehearsal | PUBLISHED_FAIL_CLOSED_REHEARSAL |
| C14 observer runtime | RUNTIME_LOGS_DETECTED_ALL_ACCOUNTS |
| C15 manual attach packet | MANUAL_ATTACH_REQUIRED |
| C16 EA consumer readiness | BROKER_EXECUTOR_CONSUMERS_READY |
| C17 broker shadow consumer deploy | DEPLOYED_COMPILED_SHADOW_CONSUMERS |
| C18 exploratory training rehearsal | REHEARSED_RESEARCH_ONLY |
| C20 runtime evidence | RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS |
| C21 runtime launch diagnostic | RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS |
| C22 post-attach runtime monitor | RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS |

## Actions

No actions ran.

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| c03_readiness_pass | false | dataset_status observed PIPELINE_ONLY required EXPLORATORY_MODEL or higher; market_setup_groups observed 282 required >=300; active_weeks observed 3.78 required >=8; at_least_two_regimes observed FALLING required >=2 non-UNKNOWN regimes; feature_budget observed 0 required >=6; slippage_readiness observed INSUFFICIENT required ADEQUATE |
| c05_model_trained | false | observed=REFUSED_NOT_READY required=TRAINED_SHADOW_ONLY |
| c04_shadow_bridge_ready | false | observed=DISABLED_FAIL_CLOSED required=READY_SHADOW_ONLY |
| c04_python_predictions_authorized | false | observed=False required=true |
| c06_ea_handoff_ready_or_published | false | observed=REFUSED_NOT_READY required=READY_DRY_RUN or PUBLISHED_TO_MT5_FILES |
| c09_observer_deployed | true | observed=DEPLOYED_PASSIVE_OBSERVER required=DEPLOYED_PASSIVE_OBSERVER |
| observer_files_exist_all_accounts | true | all observer artifacts exist |
| c16_passive_ea_consumer_ready | true | observed=True c16_status=BROKER_EXECUTOR_CONSUMERS_READY required=true |
| c16_active_broker_executor_consumers_ready | true | observed=True c16_status=BROKER_EXECUTOR_CONSUMERS_READY required=true |
| handoff_files_published_all_accounts | false | c06_status=REFUSED_NOT_READY not published |
| c20_runtime_evidence_all_accounts | true | observed=RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS required=RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS |
| c21_runtime_launch_diagnostic_all_accounts | true | observed=RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS required=RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS |
| broker_action_false_everywhere | true | broker action false in all checked reports |

## Blockers

- c03_readiness_pass: dataset_status observed PIPELINE_ONLY required EXPLORATORY_MODEL or higher; market_setup_groups observed 282 required >=300; active_weeks observed 3.78 required >=8; at_least_two_regimes observed FALLING required >=2 non-UNKNOWN regimes; feature_budget observed 0 required >=6; slippage_readiness observed INSUFFICIENT required ADEQUATE
- c05_model_trained: observed=REFUSED_NOT_READY required=TRAINED_SHADOW_ONLY
- c04_shadow_bridge_ready: observed=DISABLED_FAIL_CLOSED required=READY_SHADOW_ONLY
- c04_python_predictions_authorized: observed=False required=true
- c06_ea_handoff_ready_or_published: observed=REFUSED_NOT_READY required=READY_DRY_RUN or PUBLISHED_TO_MT5_FILES
- handoff_files_published_all_accounts: c06_status=REFUSED_NOT_READY not published

## Authorization

- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Handoff publish requested: false.
- Broker action authorized: false.

## Boundary

- MT5 connection attempted: false.
- Data export attempted: false.
- Terminal runtime change authorized: false.
- Profile or chart change authorized: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Collect/export more A1/A2/A3 data, rerun C18 for research-only Python training rehearsal as needed, then rerun C10 with --refresh-live-readonly when MT5 terminals and market data are available.

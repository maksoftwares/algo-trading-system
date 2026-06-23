# A3 ML Broker Shadow Preset Deploy Status

Overall status: DEPLOYED_SAFE_PASSIVE_PRESETS
Mode: DEPLOY
Dataset version: xauusd_c02_multiacct_202606211549_geffebb6d_c9221d066

## Authorization

- Broker-shadow preset deploy requested: true.
- Broker-shadow preset deploy attempted: true.
- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Broker action authorized: false.

## Targets

| Account | Expert | Preset | Safe |
| --- | --- | --- | --- |
| A1 | Phase2ExperimentalDemoExecutor | Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set | true |
| A1 | Phase2ExperimentalDemoRepairExecutor | Phase2ExperimentalDemoRepairExecutor.A1.a3_ml_shadow_readonly.set | true |
| A2 | Phase2ExperimentalDemoExecutor | Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set | true |
| A3 | Account3BreakoutImprovedExecutor | Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set | true |
| A3 | Account3BreakoutPlainExecutor | Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set | true |
| A3 | Account3BreakoutTier1CompatExecutor | Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set | true |
| A3 | Account3SoftRetestExecutor | Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set | true |

## Deployed Presets

- A1 Phase2ExperimentalDemoExecutor: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set
- A1 Phase2ExperimentalDemoRepairExecutor: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\Phase2ExperimentalDemoRepairExecutor.A1.a3_ml_shadow_readonly.set
- A2 Phase2ExperimentalDemoExecutor: C:\MT5PortableTier1BestEA\MQL5\Presets\Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set
- A3 Account3BreakoutImprovedExecutor: C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set
- A3 Account3BreakoutPlainExecutor: C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set
- A3 Account3BreakoutTier1CompatExecutor: C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set
- A3 Account3SoftRetestExecutor: C:\MT5PortableRepairLane\MQL5\Presets\Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| registry_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\config\ml\mt5_accounts.yaml |
| registry_parses | true | A1,A2,A3 |
| c17_compiled_shadow_consumers_deployed | true | DEPLOYED_COMPILED_SHADOW_CONSUMERS |
| repo_experts_dir_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts |
| repo_include_dir_exists | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Include |
| source_exists_Account3BreakoutImprovedExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Account3BreakoutImprovedExecutor.mq5 |
| source_supports_safe_inputs_Account3BreakoutImprovedExecutor.mq5 | true | ok |
| source_exists_Account3BreakoutPlainExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Account3BreakoutPlainExecutor.mq5 |
| source_supports_safe_inputs_Account3BreakoutPlainExecutor.mq5 | true | ok |
| source_exists_Account3BreakoutTier1CompatExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Account3BreakoutTier1CompatExecutor.mq5 |
| source_supports_safe_inputs_Account3BreakoutTier1CompatExecutor.mq5 | true | ok |
| source_exists_Account3SoftRetestExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Account3SoftRetestExecutor.mq5 |
| source_supports_safe_inputs_Account3SoftRetestExecutor.mq5 | true | ok |
| source_exists_Phase2ExperimentalDemoExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoExecutor.mq5 |
| source_supports_safe_inputs_Phase2ExperimentalDemoExecutor.mq5 | true | ok |
| source_exists_Phase2ExperimentalDemoRepairExecutor.mq5 | true | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\mt5\Experts\Phase2ExperimentalDemoRepairExecutor.mq5 |
| source_supports_safe_inputs_Phase2ExperimentalDemoRepairExecutor.mq5 | true | ok |
| all_target_paths_safe | true | A1=True; A2=True; A3=True |
| preset_content_safe_A1_Phase2ExperimentalDemoExecutor | true | Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set |
| preset_content_safe_A1_Phase2ExperimentalDemoRepairExecutor | true | Phase2ExperimentalDemoRepairExecutor.A1.a3_ml_shadow_readonly.set |
| preset_content_safe_A2_Phase2ExperimentalDemoExecutor | true | Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set |
| preset_content_safe_A3_Account3BreakoutImprovedExecutor | true | Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set |
| preset_content_safe_A3_Account3BreakoutPlainExecutor | true | Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set |
| preset_content_safe_A3_Account3BreakoutTier1CompatExecutor | true | Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set |
| preset_content_safe_A3_Account3SoftRetestExecutor | true | Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set |

## Boundary

- MT5 connection attempted: false.
- Terminal runtime launch attempted: false.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- Preset file deploy attempted: true.
- Broker action authorized: false.

## Next

Safe broker-shadow presets are deployed. In MT5, load the account-specific preset for the attached broker-shadow expert, then run C28.

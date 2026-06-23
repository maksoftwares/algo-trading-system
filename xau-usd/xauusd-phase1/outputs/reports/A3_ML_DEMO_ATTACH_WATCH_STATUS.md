# A3 ML Demo Attach Watch Status

Overall status: ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS
Dataset version: xauusd_c02_multiacct_202606212216_geffebb6d_c9221d066

## Monitor

- Timeout seconds: 5.
- Poll seconds: 1.
- Elapsed seconds: 0.0.
- Attempt count: 1.
- Timed out: false.

## Account Evidence

| Account | Observer | Broker tap | Handoff | Missing |
| --- | --- | --- | --- | --- |
| A1 | true | true | true | - |
| A2 | true | true | true | - |
| A3 | true | true | true | - |

## Exact Missing Paths

### A1 1025742

- Terminal: C:/Program Files/MetaTrader 5/terminal64.exe
- Observer preset: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Missing observer startup log: -
- Missing observer prediction log: -
- Missing broker-shadow tap: -
- Broker-shadow presets: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\Phase2ExperimentalDemoExecutor.A1.a3_ml_shadow_readonly.set, C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\Phase2ExperimentalDemoRepairExecutor.A1.a3_ml_shadow_readonly.set

### A2 1033030

- Terminal: C:/MT5PortableTier1BestEA/terminal64.exe
- Observer preset: C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Missing observer startup log: -
- Missing observer prediction log: -
- Missing broker-shadow tap: -
- Broker-shadow presets: C:\MT5PortableTier1BestEA\MQL5\Presets\Phase2ExperimentalDemoExecutor.A2.a3_ml_shadow_readonly.set

### A3 1033669

- Terminal: C:/MT5PortableRepairLane/terminal64.exe
- Observer preset: C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Missing observer startup log: -
- Missing observer prediction log: -
- Missing broker-shadow tap: -
- Broker-shadow presets: C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutImprovedExecutor.A3.a3_ml_shadow_readonly.set, C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutPlainExecutor.A3.a3_ml_shadow_readonly.set, C:\MT5PortableRepairLane\MQL5\Presets\Account3BreakoutTier1CompatExecutor.A3.a3_ml_shadow_readonly.set, C:\MT5PortableRepairLane\MQL5\Presets\Account3SoftRetestExecutor.A3.a3_ml_shadow_readonly.set

## Attempts

| Attempt | Elapsed | Ready accounts | Missing | Status |
| --- | --- | --- | --- | --- |
| 1 | 0.0 | 3 | A1:none; A2:none; A3:none | ATTACH_RUNTIME_FILES_PRESENT_ALL_ACCOUNTS |

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| c30_safe_passive_presets_deployed | true | DEPLOYED_SAFE_PASSIVE_PRESETS |
| A1_observer_preset_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A1_safe_broker_shadow_presets_exist | true | safe presets exist |
| A1_handoff_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A2_observer_preset_exists | true | C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A2_safe_broker_shadow_presets_exist | true | safe presets exist |
| A2_handoff_exists | true | C:\MT5PortableTier1BestEA\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A3_observer_preset_exists | true | C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A3_safe_broker_shadow_presets_exist | true | safe presets exist |
| A3_handoff_exists | true | C:\MT5PortableRepairLane\MQL5\Files\A3_ML_EA_HANDOFF.csv |

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

Attach files are present on all accounts. Run C28 to confirm the full Python preview read path.

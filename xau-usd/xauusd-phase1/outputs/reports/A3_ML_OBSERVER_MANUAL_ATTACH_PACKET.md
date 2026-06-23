# A3 ML Observer Manual Attach Packet

Overall status: MANUAL_ATTACH_REQUIRED
Dataset version: xauusd_c02_multiacct_202606211549_geffebb6d_c9221d066

## Authorization

- Python demo predictions authorized: false
- EA consumption authorized: false
- Broker action authorized: false

## Upstream Statuses

- C09 observer deploy: DEPLOYED_PASSIVE_OBSERVER
- C13 fail-closed handoff: PUBLISHED_FAIL_CLOSED_REHEARSAL
- C14 runtime attach: LAUNCH_SENT_WAITING_FOR_LOGS

## Account Runtime State

| Account | Login | Terminal | Startup log | Prediction log |
| --- | --- | --- | --- | --- |
| A1 | 1025742 | C:/Program Files/MetaTrader 5/terminal64.exe | false | false |
| A2 | 1033030 | C:/MT5PortableTier1BestEA/terminal64.exe | false | false |
| A3 | 1033669 | C:/MT5PortableRepairLane/terminal64.exe | false | false |

## Manual Attach Steps

1. Open each MT5 terminal for A1, A2, and A3.
2. Open or select an XAUUSD M5 chart.
3. Attach the Expert Advisor named A3MlPredictionObserver.
4. Load preset A3MlPredictionObserver.passive_xauusd.set.
5. Confirm InpDryRunOnly=true, InpTargetSymbol=XAUUSD, and InpHandoffFileName=A3_ML_EA_HANDOFF.csv.
6. Click OK only with those passive settings.
7. Wait for a tick or new M5 bar, then run C28 to wait for observer logs and demo-shadow read-path evidence.

## Account Details

### A1 1025742

- Terminal: C:/Program Files/MetaTrader 5/terminal64.exe
- Files root: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files
- Expert: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\A3MlPredictionObserver.ex5
- Preset: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Handoff file: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A3_ML_EA_HANDOFF.csv
- Startup log: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a3_ml_prediction_observer_startup.csv
- Prediction log: C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\a3_ml_prediction_observer_log.csv

### A2 1033030

- Terminal: C:/MT5PortableTier1BestEA/terminal64.exe
- Files root: C:\MT5PortableTier1BestEA\MQL5\Files
- Expert: C:\MT5PortableTier1BestEA\MQL5\Experts\A3MlPredictionObserver.ex5
- Preset: C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Handoff file: C:\MT5PortableTier1BestEA\MQL5\Files\A3_ML_EA_HANDOFF.csv
- Startup log: C:\MT5PortableTier1BestEA\MQL5\Files\a3_ml_prediction_observer_startup.csv
- Prediction log: C:\MT5PortableTier1BestEA\MQL5\Files\a3_ml_prediction_observer_log.csv

### A3 1033669

- Terminal: C:/MT5PortableRepairLane/terminal64.exe
- Files root: C:\MT5PortableRepairLane\MQL5\Files
- Expert: C:\MT5PortableRepairLane\MQL5\Experts\A3MlPredictionObserver.ex5
- Preset: C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set
- Handoff file: C:\MT5PortableRepairLane\MQL5\Files\A3_ML_EA_HANDOFF.csv
- Startup log: C:\MT5PortableRepairLane\MQL5\Files\a3_ml_prediction_observer_startup.csv
- Prediction log: C:\MT5PortableRepairLane\MQL5\Files\a3_ml_prediction_observer_log.csv

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| c09_observer_deployed | true | DEPLOYED_PASSIVE_OBSERVER |
| c13_fail_closed_handoff_published | true | PUBLISHED_FAIL_CLOSED_REHEARSAL |
| A1_expert_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\A3MlPredictionObserver.ex5 |
| A1_preset_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A1_handoff_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A2_expert_exists | true | C:\MT5PortableTier1BestEA\MQL5\Experts\A3MlPredictionObserver.ex5 |
| A2_preset_exists | true | C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A2_handoff_exists | true | C:\MT5PortableTier1BestEA\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A3_expert_exists | true | C:\MT5PortableRepairLane\MQL5\Experts\A3MlPredictionObserver.ex5 |
| A3_preset_exists | true | C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A3_handoff_exists | true | C:\MT5PortableRepairLane\MQL5\Files\A3_ML_EA_HANDOFF.csv |

## Boundary

- MT5 connection attempted: false.
- Terminal runtime launch attempted: false.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- Broker action authorized: false.

## Next

Attach A3MlPredictionObserver manually on XAUUSD M5 for A1, A2, and A3, then run C28 to wait for demo-shadow runtime evidence.

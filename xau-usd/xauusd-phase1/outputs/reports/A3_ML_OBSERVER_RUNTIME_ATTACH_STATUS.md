# A3 ML Observer Runtime Attach Status

Overall status: RUNTIME_LOGS_DETECTED_ALL_ACCOUNTS
Dataset version: xauusd_c02_multiacct_202606212216_geffebb6d_c9221d066

## Authorization

- Runtime launch requested: true
- Runtime launch attempted: true
- Python demo predictions authorized: false
- EA consumption authorized: false
- Broker action authorized: false

## Accounts

| Account | Login | Config | Files |
| --- | --- | --- | --- |
| A1 | 1025742 | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\Config\a3_ml_prediction_observer_startup.ini | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A2 | 1033030 | C:\MT5PortableTier1BestEA\Config\a3_ml_prediction_observer_startup.ini | C:\MT5PortableTier1BestEA\MQL5\Files |
| A3 | 1033669 | C:\MT5PortableRepairLane\Config\a3_ml_prediction_observer_startup.ini | C:\MT5PortableRepairLane\MQL5\Files |

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| A1_terminal_exe_exists | true | C:\Program Files\MetaTrader 5\terminal64.exe |
| A1_data_root_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075 |
| A1_observer_ex5_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\A3MlPredictionObserver.ex5 |
| A1_passive_preset_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A1_handoff_file_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A1_files_root_safe | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files |
| A2_terminal_exe_exists | true | C:\MT5PortableTier1BestEA\terminal64.exe |
| A2_data_root_exists | true | C:\MT5PortableTier1BestEA |
| A2_observer_ex5_exists | true | C:\MT5PortableTier1BestEA\MQL5\Experts\A3MlPredictionObserver.ex5 |
| A2_passive_preset_exists | true | C:\MT5PortableTier1BestEA\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A2_handoff_file_exists | true | C:\MT5PortableTier1BestEA\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A2_files_root_safe | true | C:\MT5PortableTier1BestEA\MQL5\Files |
| A3_terminal_exe_exists | true | C:\MT5PortableRepairLane\terminal64.exe |
| A3_data_root_exists | true | C:\MT5PortableRepairLane |
| A3_observer_ex5_exists | true | C:\MT5PortableRepairLane\MQL5\Experts\A3MlPredictionObserver.ex5 |
| A3_passive_preset_exists | true | C:\MT5PortableRepairLane\MQL5\Presets\A3MlPredictionObserver.passive_xauusd.set |
| A3_handoff_file_exists | true | C:\MT5PortableRepairLane\MQL5\Files\A3_ML_EA_HANDOFF.csv |
| A3_files_root_safe | true | C:\MT5PortableRepairLane\MQL5\Files |

## Runtime Logs

| Account | Startup | Prediction | Fresh startup | Fresh prediction |
| --- | --- | --- | --- | --- |
| A1 | true | true | true | true |
| A2 | true | true | true | true |
| A3 | true | true | true | true |

## Boundary

- MT5 connection attempted: false.
- Terminal runtime launch attempted: true.
- Terminal shutdown attempted: false.
- Profile or chart file write attempted: false.
- Startup config write attempted: true.
- Startup config allows live trading: false.
- Broker action authorized: false.

## Next

Passive observer runtime is logging on all three accounts. Keep collecting data; real Python predictions still require C03 PASS and C05/C04/C06 readiness.

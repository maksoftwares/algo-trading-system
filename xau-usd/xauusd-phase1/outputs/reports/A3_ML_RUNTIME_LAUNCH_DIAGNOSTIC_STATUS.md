# A3 ML Runtime Launch Diagnostic Status

Overall status: RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS
Dataset version: xauusd_c02_multiacct_202606242335_g0a9823b0_c9221d066

## Upstream Statuses

- C14 observer runtime attach: RUNTIME_LOGS_DETECTED_ALL_ACCOUNTS
- C20 runtime evidence: RUNTIME_EVIDENCE_PRESENT_ALL_ACCOUNTS

## Diagnostic Summary

- Startup configs safe all accounts: true.
- Observer log mentions all accounts: false.
- Observer log mentions any account: false.
- Error mentions any account: false.

## Account Diagnostics

| Account | Config safe | Observer mentions | Error mentions | Files checked |
| --- | --- | --- | --- | --- |
| A1 | true | 0 | 0 | 10 |
| A2 | true | 0 | 0 | 10 |
| A3 | true | 0 | 0 | 10 |

## Validations

| Check | Passed | Detail |
| --- | --- | --- |
| A1_startup_config_exists | true | C:\Users\ZHAO ZHU INFORMATION\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\Config\a3_ml_prediction_observer_startup.ini |
| A1_startup_config_safe_passive | true | {"allow_live_trading_disabled": true, "observer_expert_set": true, "passive_preset_set": true, "period_m5": true, "symbol_xauusd": true} |
| A2_startup_config_exists | true | C:\MT5PortableTier1BestEA\Config\a3_ml_prediction_observer_startup.ini |
| A2_startup_config_safe_passive | true | {"allow_live_trading_disabled": true, "observer_expert_set": true, "passive_preset_set": true, "period_m5": true, "symbol_xauusd": true} |
| A3_startup_config_exists | true | C:\MT5PortableRepairLane\Config\a3_ml_prediction_observer_startup.ini |
| A3_startup_config_safe_passive | true | {"allow_live_trading_disabled": true, "observer_expert_set": true, "passive_preset_set": true, "period_m5": true, "symbol_xauusd": true} |

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
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Runtime evidence is present. Continue data collection and rerun C19 after market data advances.

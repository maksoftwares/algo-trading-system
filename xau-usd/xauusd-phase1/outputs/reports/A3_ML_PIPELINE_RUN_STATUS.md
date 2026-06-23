# A3 ML Pipeline Run Status

Overall status: NOT_READY
Dataset version: xauusd_c02_multiacct_202606220547_geffebb6d_c9221d066
Publish requested: false

## Stage Summary

| Stage | Status |
| --- | --- |
| C01 data audit | PIPELINE_ONLY |
| C03 readiness | NO_GO |
| C05 training | REFUSED_NOT_READY |
| C04 shadow bridge | DISABLED_FAIL_CLOSED |
| C06 EA handoff | REFUSED_NOT_READY |

## Pipeline Steps

| Step | Status | Output |
| --- | --- | --- |
| C02-04 normalize snapshots | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_NORMALIZATION_REPORT.json |
| C02-05 grouping audit | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_SIGNAL_GROUPING_AUDIT.json |
| C02-05 final verdict | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_FINAL_VERDICT.json |
| C02-06 diagnostic labels | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_LABEL_AUDIT.json |
| C01 feature/data audit | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_C01_DATA_AUDIT.json |
| C03 readiness | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C03_TRAINING_READINESS_REPORT.json |
| C05 train or refuse | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_TRAINING_STATUS.json |
| C04 shadow bridge | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_SHADOW_BRIDGE_STATUS.json |
| C06 EA handoff | PASS | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_EA_HANDOFF_STATUS.json |

## Current Blocker

C03 readiness is not PASS: dataset_status observed PIPELINE_ONLY required EXPLORATORY_MODEL or higher; market_setup_groups observed 223 required >=300; active_weeks observed 3.37 required >=8; at_least_two_regimes observed FALLING required >=2 non-UNKNOWN regimes; feature_budget observed 0 required >=6; slippage_readiness observed INSUFFICIENT required ADEQUATE

## Failed C03 Gates

- dataset_status observed PIPELINE_ONLY required EXPLORATORY_MODEL or higher
- market_setup_groups observed 223 required >=300
- active_weeks observed 3.37 required >=8
- at_least_two_regimes observed FALLING required >=2 non-UNKNOWN regimes
- feature_budget observed 0 required >=6
- slippage_readiness observed INSUFFICIENT required ADEQUATE

## Boundary

- MT5 connection attempted: false.
- Terminal runtime change authorized: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Collect more live data on A1/A2/A3, rerun C02 live export when market data advances, then rerun C07.

# A3 ML Exploratory Training Rehearsal Status

Overall status: REHEARSED_RESEARCH_ONLY

## Meaning

This is a quarantined research rehearsal only. It does not create the official C05 model artifact and it does not authorize Python demo predictions, EA consumption, or broker action.

## Population

| Metric | Value |
| --- | --- |
| snapshot_rows | 512 |
| diagnostic_labeled_rows | 512 |
| official_candidate_trainable_rows | 0 |
| positive | 149 |
| negative | 363 |
| minority | 149 |

## Inputs

- Readiness report: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C03_TRAINING_READINESS_REPORT.json
- Data audit: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_C01_DATA_AUDIT.json
- Snapshot CSV: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_C01_SNAPSHOT_ROWS.csv

## Outputs

- Rehearsal artifact: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_EXPLORATORY_MODEL_REHEARSAL_ARTIFACT.json
- Artifact SHA256: 96d3aa3f88d946fc5b00559c509384c107d8910ac0d613993b7e692244fcfb42
- Shadow preview CSV: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_EXPLORATORY_SHADOW_PREVIEW.csv
- Shadow preview rows: 512

## Official Gate Blockers

- dataset_status observed PIPELINE_ONLY required EXPLORATORY_MODEL or higher
- market_setup_groups observed 282 required >=300
- active_weeks observed 3.78 required >=8
- at_least_two_regimes observed FALLING required >=2 non-UNKNOWN regimes
- feature_budget observed 0 required >=6
- slippage_readiness observed INSUFFICIENT required ADEQUATE
- C01 supervised_training_allowed=false: global_feature_budget=0 is below the contract minimum of 5

## Refusal Reasons

- none

## Authorization

- Official model training authorized: false.
- Python demo predictions authorized: false.
- EA consumption authorized: false.
- Broker action authorized: false.

## Boundary

- MT5 connection attempted: false.
- Terminal runtime change authorized: false.
- EA file drop authorized: false.
- Official model artifact written: false.
- Broker action authorized: false.

## Next

Use this only to verify Python training/scoring mechanics. Continue A1/A2/A3 data collection, rerun C03, then let C05 create the official model only after readiness passes.

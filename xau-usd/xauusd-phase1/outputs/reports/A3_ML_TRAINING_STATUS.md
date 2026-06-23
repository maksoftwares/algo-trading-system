# A3 ML Training Status

Overall status: REFUSED_NOT_READY

## Authorization

- Training authorized: false
- Python demo predictions authorized: false
- EA consumption authorized: false
- Broker action authorized: false

## Inputs

- Readiness report: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C03_TRAINING_READINESS_REPORT.json
- Data audit: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\C02_C01_DATA_AUDIT.json
- Snapshot CSV: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_C01_SNAPSHOT_ROWS.csv

## Outputs

- Model artifact: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_MODEL_ARTIFACT.json
- Artifact SHA256: 

## Refusal Reasons

- C03 readiness is NO_GO, required PASS
- C01 supervised training is false: global_feature_budget=0 is below the contract minimum of 5
- selected_features=0, required >= 5
- candidate training rows=0, required >= 120
- minority labels=0, required >= 60

## Boundary

- MT5 connection attempted: false.
- Terminal runtime change authorized: false.
- EA file drop authorized: false.
- Broker action authorized: false.

## Next

Continue data collection, rerun C01/C02/C03, then rerun C05.

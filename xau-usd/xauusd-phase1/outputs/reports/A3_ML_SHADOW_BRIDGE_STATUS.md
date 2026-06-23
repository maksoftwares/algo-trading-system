# A3 ML Shadow Bridge Status

Overall status: DISABLED_FAIL_CLOSED

## Authorization

- Training authorized: false
- Python demo predictions authorized: false
- EA consumption authorized: false
- Broker action authorized: false

## Output

- Predictions CSV: C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\A3_ML_SHADOW_PREDICTIONS.csv
- Rows: 349
- SHA256: ef4560a069ee9a280e133251b331208b3f8d681a973694ebe032bb3ac3f1eed7

## Readiness Failures

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

Generate real TAKE/SKIP shadow scores only after C03 PASS and a locked reviewed model artifact exists.

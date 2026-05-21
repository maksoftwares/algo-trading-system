# Phase 0 Data Readiness

Status: PASS
Required timeframe sets: 25
Ready timeframe sets: 25
Blocked timeframe sets: 0

## Required Broker/Symbol Inputs

| Broker | Symbol | Raw CSV candidates | Required processed timeframes |
| --- | --- | --- | --- |
| capital_com | EURUSD | 5 | M5, M15, H1, H4, D1 |
| capital_com | USDJPY | 5 | M5, M15, H1, H4, D1 |
| capital_com | XAUUSD | 5 | M5, M15, H1, H4, D1 |
| dukascopy | XAUUSD | 42 | M5, M15, H1, H4, D1 |
| pepperstone | XAUUSD | 5 | M5, M15, H1, H4, D1 |

## Blocked Processed Bar Sets

None.

## Next Action

Add raw broker CSVs, run import-required-bars for direct bar exports or normalize-data/build-bars for tick exports, then rerun check-data-availability.

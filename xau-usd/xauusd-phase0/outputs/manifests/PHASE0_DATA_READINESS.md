# Phase 0 Data Readiness

Status: BLOCKED
Required timeframe sets: 15
Ready timeframe sets: 12
Blocked timeframe sets: 3

## Required Broker/Symbol Inputs

| Broker | Symbol | Raw CSV candidates | Required processed timeframes |
| --- | --- | --- | --- |
| capital_com | XAUUSD | 5 | M5, M15, H1, H4, D1 |
| dukascopy | XAUUSD | 58 | M5, M15, H1, H4, D1 |
| pepperstone | XAUUSD | 5 | M5, M15, H1, H4, D1 |

## Blocked Processed Bar Sets

| Broker | Symbol | Timeframe | Required Start | Required End | Coverage Start | Coverage End | Valid CSVs | Candidate CSVs | Directory | First issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dukascopy | XAUUSD | M15 | 2022-01-01T00:00:00Z | 2024-12-31T23:59:59Z | 2016-01-01T00:00:00Z | 2025-07-01T00:00:00Z | 8 | 8 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\data\processed\bars\dukascopy\XAUUSD\M15 | largest timestamp gap 10d 00:15:00 exceeds allowed 7d 00:00:00 for M15 |
| dukascopy | XAUUSD | H1 | 2022-01-01T00:00:00Z | 2024-12-31T23:59:59Z | 2016-01-01T00:00:00Z | 2025-07-01T00:00:00Z | 4 | 4 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\data\processed\bars\dukascopy\XAUUSD\H1 | largest timestamp gap 121d 01:00:00 exceeds allowed 7d 00:00:00 for H1 |
| dukascopy | XAUUSD | H4 | 2022-01-01T00:00:00Z | 2024-12-31T23:59:59Z | 2016-01-01T00:00:00Z | 2025-07-01T00:00:00Z | 3 | 3 | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\data\processed\bars\dukascopy\XAUUSD\H4 | largest timestamp gap 123d 04:00:00 exceeds allowed 10d 00:00:00 for H4 |

## Suggested Direct Bar Import Commands

```powershell
python -m phase0 normalize-bars --broker dukascopy --symbol XAUUSD --timeframe M15
python -m phase0 normalize-bars --broker dukascopy --symbol XAUUSD --timeframe H1
python -m phase0 normalize-bars --broker dukascopy --symbol XAUUSD --timeframe H4
```

## Next Action

Add raw broker CSVs, run import-required-bars for direct bar exports or normalize-data/build-bars for tick exports, then rerun check-data-availability.

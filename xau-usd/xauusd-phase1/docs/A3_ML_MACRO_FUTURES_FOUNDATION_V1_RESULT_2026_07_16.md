# A3 ML Macro/Futures Foundation V1 Result

## Result

Iteration 1 passed its data-integrity and causality checks.

- Five official Federal Reserve/FRED daily series were archived: 5-year and 10-year real yields, 2-year and 10-year nominal yields, and the broad-dollar index.
- Seven annual CFTC disaggregated futures archives were stored for 2018 through 2024 and filtered to COMEX Gold contract `088691`.
- The daily event timeline contains 2,141 point-in-time availability rows.
- The enriched Dukascopy cache contains 424,942 M5 rows and 119 columns.
- Macro features joined to 424,918 rows; CFTC features joined to 424,918 rows.
- Future-visible macro joins: zero.
- Future-visible CFTC joins: zero.

## Frozen artifacts

- Daily feature SHA-256: `3d0368412ec41702586ebd57e9af90a0f3ae8ec6f21644d618a8f175c0835c82`.
- Enriched M5 SHA-256: `4ed79c7456519a3c1b8995c2667e60304b5cf457af96c76356db8f9475dcfee7`.
- Base Dukascopy feature SHA-256: `74ca74f2f6f5b3eaa8bca687fc2cced8dc20140a54506f3a25cb22920b53031b`.

## Important limitation

This foundation has official daily/weekly regime information, not licensed intraday COMEX order flow. CME depth/trade history, consensus macro forecasts, and exact ICE DXY intraday history remain absent and are explicitly prohibited from being inferred or mislabeled.

## Decision

Proceed to frozen macro-repricing and CFTC-positioning specialist tests. This result authorizes research only, not demo or live trading.

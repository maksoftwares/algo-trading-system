# A3 ML Broker Cost Calibration V1 Report

Classification: `BROKER_COST_CALIBRATION_VALID`

## Canonical Broker Feed

- Tick rows: `7616882`
- Active UTC files: `18`
- Spread median: `0.500000`
- Spread 90th percentile: `0.750000`
- Spread 99th percentile: `0.750000`
- Spread maximum: `1.800000`

## Dukascopy Overlap

- Matched M5 bars: `4092`
- Broker M5 median-spread median: `0.500000`
- Dukascopy mean-spread median: `0.605336`
- Broker p90 spread/ATR median: `0.123311`
- Dukascopy open spread/ATR median: `0.105892`

## Locked Cost Geometry

- Broker spread floor: `0.750000`
- Additional execution cost in price: `0.300000`
- Total stressed entry cost in price: `1.050000`
- Maximum cost/R: `0.1500`
- Minimum initial stop distance: `7.000000`

## Quality Gates

- c02_report_and_manifest_hashes_match: `PASS`
- account_identity_and_counts_match: `PASS`
- canonical_file_hashes_match: `PASS`
- canonical_rows_chronological: `PASS`
- canonical_bid_ask_valid: `PASS`
- canonical_spread_reconciles: `PASS`
- cross_account_boundary_quotes_match: `PASS`
- dukascopy_source_hash_and_rows_match: `PASS`
- minimum_overlap_m5_bars_met: `PASS`

## Authorization

- Strategy authorization: `false`
- Model training authorization: `false`
- Demo or live authorization: `false`

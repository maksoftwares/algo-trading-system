# Phase 0 Data Manifest

Prepared by: phase0
Prepared date UTC: 2026-06-11T05:43:07+00:00
Data source: Dukascopy
Broker: dukascopy
Symbol: EURUSD

## Raw Files

| path | sha256 | row_count | start_timestamp_utc | end_timestamp_utc |
| --- | --- | --- | --- | --- |
| data/raw/dukascopy/EURUSD_H1_20220101_20241231_dukascopy.csv | 9a86c3ca11d772c418b6364fa2e0cae4f8a5bf53a2d429f83a91c7dbc94cbf00 | 18685 | 2022-01-03T00:00:00+00:00 | 2024-12-31T21:00:00+00:00 |
| data/raw/dukascopy/EURUSD_M5_20160101_20250701_dukascopy.csv | 0880c32f95c4df4347075bbf2b38c85070baa60ba84823bb75ec3de016413aec | 997056 | 2016-01-01T00:00:00+00:00 | 2025-06-29T23:55:00+00:00 |

## Processed Files

| path | sha256 | row_count | start_timestamp_utc | end_timestamp_utc |
| --- | --- | --- | --- | --- |
| data/processed/bars/dukascopy/EURUSD/H1/EURUSD_dukascopy_H1_20220103_20241231.csv | 2c6b19e9fab4dff8ae2ed24618ae926ee8e259924532c8b825ace19e37cc9846 | 18685 | 2022-01-03T01:00:00+00:00 | 2024-12-31T22:00:00+00:00 |
| data/processed/bars/dukascopy/EURUSD/M5/EURUSD_dukascopy_M5_20160101_20250630.csv | eba6a3785aca069f311f9a6892591daa88fdf2e3bd9b2bac1092ac7c65c70add | 997056 | 2016-01-01T00:05:00+00:00 | 2025-06-30T00:00:00+00:00 |

## Known Gaps

Not automatically detected. Review validation artifacts and broker coverage manually.

## Known Quality Warnings

None recorded.

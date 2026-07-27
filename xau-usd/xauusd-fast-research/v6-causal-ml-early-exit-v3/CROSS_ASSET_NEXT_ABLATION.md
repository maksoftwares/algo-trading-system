# Cross-Asset Inputs for the Next Entry-Filter Ablation

This inventory is not part of the V3 post-entry model. It locks the smallest
defensible input set for a separate future experiment.

## Audited Sources

| Input | Coverage | SHA-256 |
|---|---|---|
| `D:/AlgoTradingData/C_DRIVE/DukascopyTickDataFoundationV1/research/xau-intraday-macro-source-v1/m5_bidask_features_v1.parquet` | 2019-01-02 to 2026-06-30 | `3982a3bb56741a5c5139f0381696d4ec4f50d7b1be7588a0efa2664bbf51ffa4` |
| `D:/AlgoTradingData/research/fx-multipair-portfolio-v1/bars/EURUSD_M5_BIDASK.parquet` | 2016-07-01 to 2026-06-30 | `8281d96ccbc3488f98586894fe58f6988eaa5376601a0bfaec874fd9f08f1f45` |
| `D:/AlgoTradingData/research/fx-multipair-portfolio-v1/bars/GBPUSD_M5_BIDASK.parquet` | 2016-07-01 to 2026-06-30 | `4e855855978964958d255ca69b47c6452909ebe2b991bf27b5c537ea9ac765fd` |
| `D:/AlgoTradingData/research/fx-multipair-portfolio-v1/bars/USDJPY_M5_BIDASK.parquet` | 2016-07-01 to 2026-06-30 | `b112d958b52ab5650fb790129184608c54268138025ea04d2322ea2f06e231b2` |

The first source contains DXY and US Treasury total-return M5 bars with
independent availability flags. The three FX sources are sorted, duplicate-free
M5 bid/ask histories.

## First Ablation Only

1. DXY trailing mid returns over one and four hours.
2. Treasury total-return changes over one and four hours.
3. A 60-minute common-dollar factor from `-EURUSD`, `-GBPUSD`, and `+USDJPY`.
4. Per-source availability and staleness features.

At decision time `T`, a source bar is eligible only when
`source_timestamp + 5 minutes <= T`. Use a backward join with a maximum
ten-minute age. Missing or closed-session values stay missing; do not
forward-fill across market closures.

## Exclusions

- Do not use the synthetic `4000`-price placeholder CSVs under `D:/DXY`,
  `D:/EURUSD`, and similar directories.
- Do not use unmanifested EURGBP, EURJPY, or GBPJPY Parquets.
- Do not use a US500 proxy; no valid historical source was found.
- Keep XAG, daily real yields, and CFTC positioning for separate later
  ablations so their incremental value remains identifiable.

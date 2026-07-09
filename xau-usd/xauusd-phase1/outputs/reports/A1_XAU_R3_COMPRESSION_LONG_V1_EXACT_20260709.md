# A1 XAU R3 Compression Long V1 Exact-MT5

Generated UTC: `2026-07-09T06:55:50Z`
Status: `R3_COMPRESSION_LONG_V1_REVIEW_CANDIDATE`

Scope: exact-MT5 run using the existing D1-compression/H4-expansion signal. Research-only.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_PREREG_2026_07_09.md`
Preregistration SHA256: `2d60e1d926942698f543cb6821657bbbb5ee6fec3240ba07e94b94b7900a1c9e`

## Results

| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r3_compression_long_v1_broad_box3_atr60_range125_body035` | 215 | 61.40 | 2.3120 | 3.6769 | 12194.08 | 2.2940 | 3.6482 | 1 | -204.70 | 856.09 | 9115.15 | 9267.09 | True |
| `current_r1_plus_r3_compression_long_v1_broad_box3_atr60_range125_body035` | 663 | 50.98 | 2.8586 | 2.9730 | 13921.91 | 2.8060 | 2.9183 | 1 | -204.70 | 1076.56 | 10845.33 | 11290.31 | True |

## April-May-June 2026

| Book | April trades/net | May trades/net | June trades/net |
| --- | ---: | ---: | ---: |
| `r3_compression_long_v1_broad_box3_atr60_range125_body035` | 0 / 0.00 | 1 / -204.70 | 0 / 0.00 |
| `current_r1_plus_r3_compression_long_v1_broad_box3_atr60_range125_body035` | 0 / 0.00 | 1 / -204.70 | 0 / 0.00 |

## Current R1 Baseline

Current R1 book: 558 trades, WR 50.18%, W/L 2.7028, PF 2.7223, net 8716.36, recent3 trades 0, recent3 net 0.00, max DD 889.69.

## Failed Checks

- `r3_compression_long_v1_broad_box3_atr60_range125_body035`: none
- `current_r1_plus_r3_compression_long_v1_broad_box3_atr60_range125_body035`: none

## Guard Notes

- `direction_mode_block`: 142

## Interpretation

The R3 compression long specialist passed standalone and combined gates. It is still research-only and needs reviewer approval.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_COMBINED.csv`
- normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_r3_compression_long_v1_broad_box3_atr60_range125_body035_NORMALIZED_TRADES.csv`
- combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_current_r1_plus_r3_compression_long_v1_broad_box3_atr60_range125_body035_KEPT.csv`
- combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_current_r1_plus_r3_compression_long_v1_broad_box3_atr60_range125_body035_DROPPED.csv`
- mt5_report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_MT5.md`
- mt5_report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_EXACT_20260709_MT5.json`

# A1 XAU R3 Compression Long V1 Router-Alignment Audit

Generated UTC: `2026-07-09T08:38:14Z`
Status: `R3_MIXED_REGIME_LONG_EXPANSION_SHADOW`

Scope: exact-MT5 EA-router snapshot attribution plus recomposition of existing exact-MT5 R3 and current R1+R2 ledgers. Research-only.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_PREREG_2026_07_09.md`
Preregistration SHA256: `1bb89221ec005a2b9aa74d24b5ee938d34b6c0bce5e39b142be9d480784ce212`
Snapshot signal CSV SHA256: `34acae8900e7df84392df27f95602c96e18a89cc399a0fa3ad7d8f1d86022065`

## Router Attribution

| EA router regime | Trades | WR% | W/L | PF | Net | Stress PF | Recent3 trades | Recent3 net | Max DD | Top10 rem | Top3 days rem | 2023-2024 net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `shock` | 8 | 100.00 | 0.0000 | 0.0000 | 584.16 | 0.0000 | 0 | 0.00 | 0.00 | 0.00 | 47.52 | 584.16 |
| `uptrend` | 139 | 68.35 | 2.0342 | 4.3921 | 10534.09 | 4.3644 | 0 | 0.00 | 856.09 | 7455.16 | 7607.10 | 2037.97 |
| `compression` | 45 | 44.44 | 2.6899 | 2.1519 | 915.92 | 2.1244 | 0 | 0.00 | 635.38 | -174.99 | 106.92 | -60.06 |
| `chop` | 23 | 39.13 | 1.9355 | 1.2442 | 159.91 | 1.2322 | 1 | -204.70 | 300.01 | -654.74 | -347.84 | 578.05 |

## Portfolio Books

| Book | Trades | WR% | W/L | PF | Net | Stress net | Recent3 trades | Recent3 net | Max DD | Best month share% | Top10 rem | Top3 days rem |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_r1_r2_baseline` | 678 | 51.03 | 2.6082 | 2.7182 | 9640.05 | 9436.65 | 59 | 764.92 | 889.69 | 27.96 | 6731.40 | 7275.75 |
| `r3_all` | 215 | 61.40 | 2.3120 | 3.6769 | 12194.08 | 12129.58 | 1 | -204.70 | 856.09 | 23.99 | 9115.15 | 9267.09 |
| `r3_compression_only` | 45 | 44.44 | 2.6899 | 2.1519 | 915.92 | 902.42 | 0 | 0.00 | 635.38 | 84.75 | -174.99 | 106.92 |
| `r3_noncompression_only` | 170 | 65.88 | 2.0711 | 3.9993 | 11278.16 | 11227.16 | 1 | -204.70 | 856.09 | 23.05 | 8199.23 | 8351.17 |
| `current_r1_r2_plus_r3_all` | 783 | 51.60 | 2.7692 | 2.9519 | 14845.60 | 14610.70 | 60 | 560.22 | 1076.56 | 21.16 | 11769.02 | 12214.00 |
| `current_r1_r2_plus_r3_compression_only` | 723 | 50.62 | 2.5828 | 2.6479 | 10555.97 | 10339.07 | 59 | 764.92 | 889.69 | 25.53 | 7647.32 | 8191.67 |
| `current_r1_r2_plus_r3_noncompression_only` | 738 | 52.03 | 2.8073 | 3.0452 | 13929.68 | 13708.28 | 60 | 560.22 | 1076.56 | 20.21 | 10853.10 | 11298.08 |

## Checks

### `full_r3_strong_checks`
- `trades_ge_150`: `True`
- `wr_ge_50`: `True`
- `wl_ge_2`: `True`
- `pf_ge_2p50`: `True`
- `stress_pf_ge_2`: `True`
- `top10_removed_net_gt_0`: `True`
- `top3_days_removed_net_gt_0`: `True`

### `true_compression_checks`
- `compression_trades_ge_100`: `False`
- `wr_ge_50`: `False`
- `wl_ge_2`: `True`
- `pf_ge_2`: `True`
- `stress_pf_ge_1p50`: `True`
- `net_gt_0`: `True`
- `top10_removed_net_gt_0`: `False`
- `top3_days_removed_net_gt_0`: `True`
- `net_2023_2024_ge_0`: `False`
- `max_dd_lte_baseline`: `True`

### `portfolio_checks`
- `net_gt_baseline`: `True`
- `stress_net_gt_baseline`: `True`
- `wr_ge_50`: `True`
- `wl_ge_2`: `True`
- `pf_ge_2`: `True`
- `max_dd_lte_115pct_baseline`: `False`
- `recent3_net_ge_baseline_minus_100`: `False`
- `top10_removed_net_gt_0`: `True`
- `top3_days_removed_net_gt_0`: `True`
- `best_month_share_lte_35`: `True`

### `freeze_checks`
- `r3_top10_removed_net_lte_0`: `False`
- `r3_top3_days_removed_net_lte_0`: `False`
- `r3_2023_2024_net_lt_0`: `False`
- `combined_dd_gt_125pct_baseline`: `False`
- `combined_wr_lt_50`: `False`
- `combined_pf_lt_2`: `False`

## Snapshot Coverage

- Snapshot rows: `282641`
- Tagged R3 rows: `215`
- Missing/no-snapshot R3 rows: `0`
- Max snapshot lag seconds: `0.0`

## Interpretation

R3 remains strong as a full source, but the EA-router attribution does not prove it is a clean compression specialist.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709.json`
- router_tagged_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709_ROUTER_TAGGED_TRADES.csv`
- regime_rows_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709_REGIME_ROWS.csv`
- combined_portfolios_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709_COMBINED_PORTFOLIOS.csv`
- monthly_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709_MONTHLY.csv`
- yearly_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709_YEARLY.csv`
- mt5_report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709_MT5.md`
- mt5_report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R3_COMPRESSION_LONG_V1_ROUTER_ALIGNMENT_AUDIT_20260709_MT5.json`
- mt5_signal_csv: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\mt5_backtests\a1_momentum_variants_owner_goal_r3_router_alignment_audit_202207_202606_20260701\A1XauM5Momentum_OWNER_GOAL_R3_ROUTER_ALIGNMENT_AUDIT_202207_202606_XAUUSD_M5_r3_alignment_full_window_regime_snapshot_m5_signals.csv`

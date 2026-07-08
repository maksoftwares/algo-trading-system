# A1 XAU Short Downside Impulse Retest Exact MT5 Probe

Generated UTC: `2026-07-08T11:58:05Z`
Status: `SHORT_IMPULSE_RETEST_NO_STANDALONE_SURVIVOR`

Scope: standalone short-specialist test from the TradingView chart idea: downside impulse, failed retest, short-only, fixed 2R. No hour/session/day/month masks were used.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_PREREG_2026_07_08.md`
Preregistration SHA256: `cb4e441618e349d009397364afc7d7623a10fb0f452694063ea8938a1c3ba6d4`

## Result

| Variant | Trades | WR% | W/L | PF | Net | Stress PF | Stress net | Q2-2026 | Recent3 | 2023+2024 | Year+ | Top10-removed | Top3-days-removed | Pos weeks% | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `short_v4_impulse_retest_d1_nonup_h1h4` | 287 | 32.75 | 2.7744 | 1.3513 | 367.41 | 1.2548 | 281.31 | 282.10 | 282.10 | -172.72 | 3 | 15.79 | 157.75 | 39.24 | FAIL |
| `short_v4_impulse_retest_d1_structural_h1h4` | 180 | 40.00 | 2.6773 | 1.7848 | 452.16 | 1.6543 | 398.16 | 282.10 | 282.10 | -6.90 | 3 | 131.67 | 228.49 | 51.11 | FAIL |
| `short_v4_impulse_retest_d1_nonup_h1_only` | 307 | 32.57 | 2.6788 | 1.2941 | 333.44 | 1.2018 | 241.34 | 282.10 | 282.10 | -167.72 | 3 | -18.18 | 123.78 | 40.00 | FAIL |

## Gate Failures

- `short_v4_impulse_retest_d1_nonup_h1h4`: wr_ge_50, y2023_2024_net_ge_0
- `short_v4_impulse_retest_d1_structural_h1h4`: wr_ge_50, y2023_2024_net_ge_0
- `short_v4_impulse_retest_d1_nonup_h1_only`: wr_ge_50, y2023_2024_net_ge_0, top10_removed_net_gt_0

## By Year

| Variant | Year | Trades | WR% | W/L | PF | Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `short_v4_impulse_retest_d1_nonup_h1h4` | 2022 | 65 | 36.92 | 2.1586 | 1.2636 | 42.71 |
| `short_v4_impulse_retest_d1_nonup_h1h4` | 2023 | 92 | 28.26 | 2.0306 | 0.7999 | -48.38 |
| `short_v4_impulse_retest_d1_nonup_h1h4` | 2024 | 50 | 12.00 | 2.7467 | 0.3745 | -124.34 |
| `short_v4_impulse_retest_d1_nonup_h1h4` | 2025 | 40 | 35.00 | 2.2345 | 1.2032 | 43.36 |
| `short_v4_impulse_retest_d1_nonup_h1h4` | 2026 | 40 | 60.00 | 1.9830 | 2.9745 | 454.06 |
| `short_v4_impulse_retest_d1_structural_h1h4` | 2022 | 64 | 35.94 | 2.1755 | 1.2204 | 35.71 |
| `short_v4_impulse_retest_d1_structural_h1h4` | 2023 | 64 | 34.38 | 2.0234 | 1.0599 | 9.34 |
| `short_v4_impulse_retest_d1_structural_h1h4` | 2024 | 14 | 28.57 | 1.7145 | 0.6858 | -16.24 |
| `short_v4_impulse_retest_d1_structural_h1h4` | 2025 | 1 | 0.00 | 0.0000 | 0.0000 | -3.52 |
| `short_v4_impulse_retest_d1_structural_h1h4` | 2026 | 37 | 62.16 | 1.8890 | 3.1033 | 426.87 |
| `short_v4_impulse_retest_d1_nonup_h1_only` | 2022 | 67 | 35.82 | 2.1699 | 1.2111 | 35.69 |
| `short_v4_impulse_retest_d1_nonup_h1_only` | 2023 | 95 | 29.47 | 2.0234 | 0.8456 | -37.87 |
| `short_v4_impulse_retest_d1_nonup_h1_only` | 2024 | 57 | 14.04 | 2.5408 | 0.4148 | -129.85 |
| `short_v4_impulse_retest_d1_nonup_h1_only` | 2025 | 46 | 34.78 | 2.1100 | 1.1253 | 31.06 |
| `short_v4_impulse_retest_d1_nonup_h1_only` | 2026 | 42 | 57.14 | 2.0553 | 2.7404 | 434.41 |

## Interpretation

No downside-impulse retest variant reached the standalone short objective. Best WR was `short_v4_impulse_retest_d1_structural_h1h4` at 40.00% with W/L 2.6773. The TradingView idea is useful as a visual hypothesis, but this exact-MT5 pass did not prove it as a standalone short expert.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708.json`
- summary_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708_SUMMARY.csv`
- year_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708_YEAR.csv`
- block_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708_BLOCK.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708_MT5_COMPONENTS.json`
- short_v4_impulse_retest_d1_nonup_h1h4_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708_short_v4_impulse_retest_d1_nonup_h1h4_NORMALIZED_TRADES.csv`
- short_v4_impulse_retest_d1_structural_h1h4_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708_short_v4_impulse_retest_d1_structural_h1h4_NORMALIZED_TRADES.csv`
- short_v4_impulse_retest_d1_nonup_h1_only_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_DOWNSIDE_IMPULSE_RETEST_20260708_short_v4_impulse_retest_d1_nonup_h1_only_NORMALIZED_TRADES.csv`

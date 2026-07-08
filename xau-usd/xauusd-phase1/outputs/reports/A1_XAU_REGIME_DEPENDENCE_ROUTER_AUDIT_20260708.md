# A1 XAU Regime-Dependence Router Audit

Generated UTC: `2026-07-08T12:38:59Z`
Status: `REGIME_DEPENDENCE_CONFIRMED_SHADOW_ONLY`

Scope: source/time attribution over the current exact-MT5 chart-context blend ledger. PnL and shape are manually recomputed from trade rows. No MT5 launch, live/demo runtime, chart, preset, order, position, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_PREREG_2026_07_08.md`
Preregistration SHA256: `703264bc0e236d5537c54dbf3eab8207c70fc0f91c77c58c14127b88589da7d4`
Input SHA256: `84878b6dd5e1ed1a6f326180f3958baa4bf95a22e9ee648cdcfe77f3aedb3369`

## Current Blend

| Period | Signals | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Worst week |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Full | 3794 | 50.03 | 2.1328 | 2.0084 | 86.58 | 20882.42 | 958.86 | 31 | 17 | 58.57 | -878.18 |
| Q2-2026 | 166 | 46.99 | 1.5073 | n/a | n/a | 514.04 | n/a | n/a | n/a | n/a | n/a |

## Full-Window Source Concentration

| Source | Signals | Net | Net share |
| --- | ---: | ---: | ---: |
| `freq_step3_frontier` | 3416 | 6134.72 | 29.38% |
| `h4_d1_long_best_box2_atr80` | 208 | 14349.57 | 68.72% |
| `short_v4_impulse_retest_d1_structural_h1h4` | 170 | 398.13 | 1.91% |

## Q2-2026 Source Contribution

| Source | Signals | Wins | Losses | WR% | W/L | Net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `freq_step3_frontier` | 139 | 63 | 75 | 45.32 | 1.4481 | 279.22 |
| `short_v4_impulse_retest_d1_structural_h1h4` | 27 | 15 | 12 | 55.56 | 1.8872 | 234.82 |
| `h4_d1_long_best_box2_atr80` | 0 | 0 | 0 | 0.00 | 0.0000 | 0.00 |

## Diagnostic Portfolios

| Portfolio | Core gate | Signals | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | Q2 signals | Q2 WR% | Q2 W/L | Q2 net |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_blend` | `True` | 3794 | 50.03 | 2.1328 | 2.0084 | 86.58 | 20882.42 | 958.86 | 31 | 166 | 46.99 | 1.5073 | 514.04 |
| `h4_long_only` | `False` | 208 | 67.31 | 2.4948 | 2.4744 | 11.60 | 14349.57 | 866.37 | 18 | 0 | 0.00 | 0.0000 | 0.00 |
| `freq_only` | `False` | 3416 | 49.47 | 1.4531 | 1.3307 | 85.04 | 6134.72 | 365.80 | 34 | 139 | 45.32 | 1.4481 | 279.22 |
| `short_v4_only` | `False` | 170 | 40.00 | 2.5760 | 2.3891 | 9.49 | 398.13 | 65.17 | 12 | 27 | 55.56 | 1.8872 | 234.82 |
| `freq_plus_short_no_h4` | `False` | 3586 | 49.02 | 1.4912 | 1.3662 | 86.00 | 6532.85 | 327.52 | 35 | 166 | 46.99 | 1.5073 | 514.04 |

## Top H4/D1 Long Months

| Exit month | Net |
| --- | ---: |
| `2025-10` | 3622.34 |
| `2026-01` | 3182.27 |
| `2025-09` | 2384.85 |
| `2023-01` | 1115.63 |
| `2024-10` | 1063.57 |
| `2025-02` | 745.31 |
| `2025-03` | 599.86 |
| `2025-01` | 553.42 |

## Period/Source Snapshot

| Period | Source | Signals | WR% | W/L | Net | Active% |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `pre_2025_202207_202412` | `ALL` | 2320 | 48.02 | 1.7933 | 5171.46 | 88.36 |
| `pre_2025_202207_202412` | `h4_d1_long_best_box2_atr80` | 111 | 57.66 | 2.2062 | 3504.91 | 11.03 |
| `pre_2025_202207_202412` | `freq_step3_frontier` | 2074 | 48.31 | 1.3658 | 1623.64 | 86.52 |
| `pre_2025_202207_202412` | `short_v4_impulse_retest_d1_structural_h1h4` | 135 | 35.56 | 2.0356 | 42.91 | 12.56 |
| `bull_harvest_202501_202601` | `ALL` | 1224 | 54.58 | 2.3209 | 14834.97 | 84.10 |
| `bull_harvest_202501_202601` | `h4_d1_long_best_box2_atr80` | 97 | 78.35 | 2.0182 | 10844.66 | 17.31 |
| `bull_harvest_202501_202601` | `freq_step3_frontier` | 1126 | 52.58 | 1.4487 | 3993.83 | 83.39 |
| `bull_harvest_202501_202601` | `short_v4_impulse_retest_d1_structural_h1h4` | 1 | 0.00 | 0.0000 | -3.52 | 0.35 |
| `q2_recent_202604_202606` | `ALL` | 166 | 46.99 | 1.5073 | 514.04 | 87.69 |
| `q2_recent_202604_202606` | `h4_d1_long_best_box2_atr80` | 0 | 0.00 | 0.0000 | 0.00 | 0.00 |
| `q2_recent_202604_202606` | `freq_step3_frontier` | 139 | 45.32 | 1.4481 | 279.22 | 86.15 |
| `q2_recent_202604_202606` | `short_v4_impulse_retest_d1_structural_h1h4` | 27 | 55.56 | 1.8872 | 234.82 | 21.54 |
| `last12_202507_202606` | `ALL` | 843 | 53.14 | 2.4218 | 12737.51 | 79.69 |
| `last12_202507_202606` | `h4_d1_long_best_box2_atr80` | 65 | 83.08 | 1.9381 | 9209.08 | 11.49 |
| `last12_202507_202606` | `freq_step3_frontier` | 744 | 50.27 | 1.5066 | 3169.69 | 78.16 |
| `last12_202507_202606` | `short_v4_impulse_retest_d1_structural_h1h4` | 34 | 58.82 | 1.9373 | 358.74 | 6.13 |

## Interpretation

The user's concern is confirmed. The full-window book is mostly carried by the H4/D1 long source, but Q2-2026 survival came from frequency plus short rows while the H4/D1 long source had no Q2 trades. Removing the long source leaves no viable full-window book. Treat this as a regime-routed research candidate, not demo-ready.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_20260708.json`
- period_source_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_20260708_PERIOD_SOURCE.csv`
- monthly_source_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_20260708_MONTHLY_SOURCE.csv`
- diagnostic_portfolios_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_20260708_DIAGNOSTIC_PORTFOLIOS.csv`
- q2_rows_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_DEPENDENCE_ROUTER_AUDIT_20260708_Q2_ROWS.csv`

# A1 XAU Regime Router V1 Exact-MT5

Generated UTC: `2026-07-08T13:34:33Z`
Status: `ROUTER_V1_SHADOW_ONLY`

Scope: exact-MT5 component rerun with the EA-side completed-bar regime router. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_REGIME_ROUTER_V1_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `600416dbb57d19b64540f22b38902bf85b9de1f6c80bc451a22df40f66de0381`

## Component Results

| Component | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Q2 trades | Q2 net | Router blocks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `router_v1_r1_long_box2_prevhealth` | 145 | 59.31 | 2.1804 | 3.1782 | 7050.42 | 2.1631 | 3.1530 | 0 | 0.00 | 171 |
| `router_v1_r2_short_v4_structural` | 0 | 0.00 | 0.0000 | 0.0000 | 0.00 | 0.0000 | 0.0000 | 0 | 0.00 | 4307 |

## Portfolio Diagnostics

| Portfolio | Trades | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Pos weeks% | Q2 trades | Q2 net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `router_long_short_no_freq` | 145 | 59.31 | 2.1804 | 2.1631 | 7.96 | 7050.42 | 866.37 | 15 | 10 | 13.33 | 0 | 0.00 |
| `router_long_short_with_freq_observer` | 3555 | 49.90 | 1.7547 | 1.6425 | 85.33 | 13067.88 | 958.86 | 32 | 16 | 56.67 | 139 | 279.22 |

## Router Block Reasons

### `router_v1_r1_long_box2_prevhealth`
- `regime_router_block_long_r1_uptrend_only_state_chop`: 87
- `regime_router_block_long_r1_uptrend_only_state_compression`: 53
- `regime_router_block_long_r1_uptrend_only_state_downtrend`: 1
- `regime_router_block_long_r1_uptrend_only_state_shock`: 30

### `router_v1_r2_short_v4_structural`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 1851
- `regime_router_block_short_r2_downtrend_only_state_compression`: 515
- `regime_router_block_short_r2_downtrend_only_state_shock`: 843
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 1098

## Source Contributions

### `router_long_short_no_freq`

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `h4_d1_long_best_box2_atr80` | 145 | 7050.42 |

### `router_long_short_with_freq_observer`

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3416 | 6134.72 |
| `h4_d1_long_best_box2_atr80` | 139 | 6933.16 |

## Interpretation

Router V1 is useful as a shadow architecture, but the current result still relies on frequency or lacks enough routed standalone coverage. Do not promote; use this to guide the next specialist.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708.json`
- component_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_COMPONENTS.csv`
- portfolio_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_PORTFOLIOS.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_MT5_COMPONENTS.json`
- router_v1_r1_long_box2_prevhealth_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_router_v1_r1_long_box2_prevhealth_NORMALIZED_TRADES.csv`
- router_v1_r2_short_v4_structural_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_router_v1_r2_short_v4_structural_NORMALIZED_TRADES.csv`
- router_long_short_no_freq_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_router_long_short_no_freq_KEPT.csv`
- router_long_short_no_freq_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_router_long_short_no_freq_DROPPED.csv`
- router_long_short_with_freq_observer_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_router_long_short_with_freq_observer_KEPT.csv`
- router_long_short_with_freq_observer_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_REGIME_ROUTER_V1_EXACT_20260708_router_long_short_with_freq_observer_DROPPED.csv`

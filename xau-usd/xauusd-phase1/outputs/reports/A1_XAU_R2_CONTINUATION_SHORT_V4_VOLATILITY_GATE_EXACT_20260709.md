# A1 XAU R2 Continuation Short V4 Volatility Gate Exact-MT5

Generated UTC: `2026-07-09T05:59:31Z`
Status: `R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_QUALITY_REPAIR_BELOW_V1_NET`

Scope: exact-MT5 research-only volatility participation layer over the strict-R2 V1 continuation short. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_PREREG_2026_07_09.md`
Preregistration SHA256: `5b3bbdf5fedd54f41192155a8885807869bd0a5fcca803df18d4c77212996d6f`
MT5 component evidence: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_MT5_COMPONENTS.md`

## Reference

| Book | Full net | Recent3 net | Note |
| --- | ---: | ---: | --- |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` | 9750.48 | 818.35 | V1 profit leader |

## Standalone V4

| Variant | Trades | WR% | W/L | PF | Net | Stress net | Apr net | May net | Jun trades | Jun WR% | Jun net | Recent3 net | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r2_impulse_body45_atr45` | 59 | 55.93 | 2.1450 | 2.7226 | 568.41 | 550.71 | 71.35 | 12.98 | 47 | 59.57 | 511.06 | 595.39 | True |
| `r2_impulse_body45_atr50` | 55 | 58.18 | 2.0566 | 2.8614 | 565.91 | 549.41 | 71.35 | 12.98 | 43 | 62.79 | 508.56 | 592.89 | True |
| `r2_impulse_body45_atr45_daily_loss10` | 57 | 57.89 | 2.1150 | 2.9081 | 589.46 | 572.36 | 71.35 | 12.98 | 45 | 62.22 | 532.11 | 616.44 | True |

## Combined With Current R1 Plus Best R2 Pullback

| Book | Trades | WR% | W/L | PF | Net | Stress net | Apr net | May net | Jun trades | Jun WR% | Jun net | Recent3 net | Max DD | Dropped | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45` | 680 | 50.88 | 2.6141 | 2.7081 | 9619.00 | 9415.00 | 145.37 | 55.74 | 48 | 60.42 | 542.76 | 743.87 | 889.69 | 0 | True |
| `current_r1_best_r2_pullback_plus_r2_impulse_body45_atr50` | 676 | 51.04 | 2.6053 | 2.7155 | 9616.50 | 9413.70 | 145.37 | 55.74 | 44 | 63.64 | 540.26 | 741.37 | 889.69 | 0 | True |
| `current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10` | 678 | 51.03 | 2.6082 | 2.7182 | 9640.05 | 9436.65 | 145.37 | 55.74 | 46 | 63.04 | 563.81 | 764.92 | 889.69 | 0 | True |

## Guard Summary

### `r2_impulse_body45_atr45`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 232
- `regime_router_block_short_r2_downtrend_only_state_shock`: 183
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 76
- `stop_ceiling_exceeded`: 20

### `r2_impulse_body45_atr50`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 196
- `regime_router_block_short_r2_downtrend_only_state_shock`: 154
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 57
- `stop_ceiling_exceeded`: 20

### `r2_impulse_body45_atr45_daily_loss10`
- `portfolio_daily_loss_stop_reached`: 2
- `regime_router_block_short_r2_downtrend_only_state_chop`: 232
- `regime_router_block_short_r2_downtrend_only_state_shock`: 183
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 76
- `stop_ceiling_exceeded`: 20

## Failed Checks

- `r2_impulse_body45_atr45` standalone: none
- `r2_impulse_body45_atr50` standalone: none
- `r2_impulse_body45_atr45_daily_loss10` standalone: none
- `current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45` combined: none
- `current_r1_best_r2_pullback_plus_r2_impulse_body45_atr50` combined: none
- `current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10` combined: none

## Interpretation

`current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10` improved R2 quality and neutralized May-style damage, but it did not beat V1 full-window profit.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_COMBINED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_MT5_COMPONENTS.json`
- r2_impulse_body45_atr45_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_r2_impulse_body45_atr45_NORMALIZED_TRADES.csv`
- r2_impulse_body45_atr50_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_r2_impulse_body45_atr50_NORMALIZED_TRADES.csv`
- r2_impulse_body45_atr45_daily_loss10_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_r2_impulse_body45_atr45_daily_loss10_NORMALIZED_TRADES.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_DROPPED.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_atr50_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr50_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_atr50_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr50_DROPPED.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_DROPPED.csv`

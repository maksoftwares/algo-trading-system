# A1 XAU R2 Continuation Short V3 Profit Guard Exact-MT5

Generated UTC: `2026-07-08T22:17:34Z`
Status: `R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_USEFUL_BUT_BELOW_V1`

Scope: exact-MT5 research-only profit-guard pass over the strict-R2 V1 continuation short. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_PREREG_2026_07_09.md`
Preregistration SHA256: `52aac5fbcd19736342e2970c1588f8f2d0ee29bf54b928f6fd362b533e33ed25`
MT5 component evidence: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_MT5_COMPONENTS.md`

## Reference

| Book | Trades | WR% | PF | Net | Recent3 trades | Recent3 WR% | Recent3 net | Max DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_r1_best_r2_pullback_plus_r2_impulse_retest_body45` | 1060 | 44.72 | 2.4634 | 9750.48 | 88 | 55.68 | 818.35 | 889.69 |

## Standalone Full Window

| Variant | Trades | Wins | Losses | WR% | W/L | PF | Net | Stress net | Recent3 trades | Recent3 WR% | Recent3 net | June net | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r2_impulse_body45_daily_loss7` | 340 | 117 | 223 | 34.41 | 2.7420 | 1.4386 | 505.41 | 403.41 | 80 | 56.25 | 718.12 | 677.04 | True |
| `r2_impulse_body45_daily_loss10` | 387 | 134 | 253 | 34.63 | 2.7523 | 1.4578 | 575.54 | 459.44 | 80 | 56.25 | 718.12 | 677.04 | True |
| `r2_impulse_body45_loss_cooldown240` | 372 | 136 | 236 | 36.56 | 2.6961 | 1.5537 | 660.83 | 549.23 | 77 | 55.84 | 668.57 | 627.49 | True |

## Combined With Current R1 Plus Best R2 Pullback

| Book | Trades | WR% | W/L | PF | Net | Stress net | Recent3 trades | Recent3 WR% | Recent3 net | June net | Max DD | Dropped | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss7` | 949 | 44.89 | 3.0609 | 2.4932 | 9567.98 | 9283.28 | 84 | 58.33 | 866.60 | 708.74 | 889.69 | 12 | True |
| `current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss10` | 993 | 44.61 | 3.0899 | 2.4888 | 9659.59 | 9361.69 | 84 | 58.33 | 866.60 | 708.74 | 889.69 | 15 | True |
| `current_r1_best_r2_pullback_plus_r2_impulse_body45_loss_cooldown240` | 983 | 45.37 | 3.0191 | 2.5075 | 9726.87 | 9431.97 | 81 | 58.02 | 817.05 | 659.19 | 889.69 | 10 | True |

## Guard Summary

### `r2_impulse_body45_daily_loss7`
- `daily_trade_cap_reached`: 2
- `max_open_positions_reached`: 2
- `portfolio_daily_loss_stop_reached`: 117
- `regime_router_block_short_r2_downtrend_only_state_chop`: 1463
- `regime_router_block_short_r2_downtrend_only_state_compression`: 409
- `regime_router_block_short_r2_downtrend_only_state_shock`: 653
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 875

### `r2_impulse_body45_daily_loss10`
- `daily_trade_cap_reached`: 4
- `max_open_positions_reached`: 3
- `portfolio_daily_loss_stop_reached`: 67
- `regime_router_block_short_r2_downtrend_only_state_chop`: 1463
- `regime_router_block_short_r2_downtrend_only_state_compression`: 409
- `regime_router_block_short_r2_downtrend_only_state_shock`: 653
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 875

### `r2_impulse_body45_loss_cooldown240`
- `daily_trade_cap_reached`: 2
- `portfolio_cooldown_after_loss_active`: 87
- `regime_router_block_short_r2_downtrend_only_state_chop`: 1463
- `regime_router_block_short_r2_downtrend_only_state_compression`: 409
- `regime_router_block_short_r2_downtrend_only_state_shock`: 653
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 875

## Failed Checks

- `r2_impulse_body45_daily_loss7` standalone: none
- `r2_impulse_body45_daily_loss10` standalone: none
- `r2_impulse_body45_loss_cooldown240` standalone: none
- `current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss7` combined: none
- `current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss10` combined: none
- `current_r1_best_r2_pullback_plus_r2_impulse_body45_loss_cooldown240` combined: none

## Interpretation

`current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss10` preserved useful recent profit but did not beat the ungated V1 continuation reference.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_COMBINED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_MT5_COMPONENTS.json`
- r2_impulse_body45_daily_loss7_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_r2_impulse_body45_daily_loss7_NORMALIZED_TRADES.csv`
- r2_impulse_body45_daily_loss10_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_r2_impulse_body45_daily_loss10_NORMALIZED_TRADES.csv`
- r2_impulse_body45_loss_cooldown240_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_r2_impulse_body45_loss_cooldown240_NORMALIZED_TRADES.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss7_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss7_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss7_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss7_DROPPED.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss10_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss10_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss10_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_daily_loss10_DROPPED.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_loss_cooldown240_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_loss_cooldown240_KEPT.csv`
- current_r1_best_r2_pullback_plus_r2_impulse_body45_loss_cooldown240_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V3_PROFIT_GUARD_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_loss_cooldown240_DROPPED.csv`

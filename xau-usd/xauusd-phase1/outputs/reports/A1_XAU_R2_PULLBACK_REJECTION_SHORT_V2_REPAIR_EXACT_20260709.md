# A1 XAU R2 Pullback-Rejection Short V2 Repair Exact-MT5

Generated UTC: `2026-07-08T21:26:47Z`
Status: `R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_SHADOW_LOW_SAMPLE`

Scope: exact-MT5 research-only repair of the strict R2 H1 short specialist. No demo/live runtime, chart, preset, order, position, account, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_PREREG_2026_07_09.md`
Preregistration SHA256: `a25fa27071ff5e86dfdd4611c1d7cf5b167cb47de2da6b81a9aecd1743420da6`
Current R1 book: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_KEPT.csv`
MT5 component evidence: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_MT5_COMPONENTS.md`

## Standalone Full Window

| Variant | Trades | Wins | Losses | WR% | W/L | PF | Net | Stress W/L | Stress PF | Max DD | Top10 rem | Top3 days rem | Best month% | Repair status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r2_h1_m5_body58` | 86 | 40 | 46 | 46.51 | 2.1213 | 1.8446 | 303.39 | 2.0058 | 1.7442 | 56.91 | 13.74 | 152.91 | 24.40 | `FAIL_WR` |
| `r2_h1_m5_body58_hours05_18` | 63 | 33 | 30 | 52.38 | 2.1721 | 2.3893 | 334.23 | 2.0577 | 2.2634 | 37.21 | 44.58 | 203.21 | 22.15 | `LOW_SAMPLE_WR_REPAIRED` |

## Standalone Last Three Months

| Variant | Recent3 trades | Recent3 WR% | Recent3 W/L | Recent3 PF | Recent3 net | June trades | June WR% | June PF | June net |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `r2_h1_m5_body58` | 5 | 80.00 | 1.7427 | 6.9709 | 127.18 | 2 | 50.00 | 1.4883 | 10.40 |
| `r2_h1_m5_body58_hours05_18` | 4 | 100.00 | 0.0000 | 0.0000 | 148.48 | 1 | 100.00 | 0.0000 | 31.70 |

## Combined With Current R1 Book

| Book | Trades | WR% | W/L | PF | Net | Recent3 trades | Recent3 net | Max DD | Combined pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_plus_r2_h1_m5_body58` | 644 | 49.69 | 2.6974 | 2.6641 | 9019.75 | 5 | 127.18 | 889.69 | False |
| `current_r1_plus_r2_h1_m5_body58_hours05_18` | 621 | 50.40 | 2.6639 | 2.7072 | 9050.59 | 4 | 148.48 | 889.69 | True |

## Failed Checks

- `r2_h1_m5_body58` standalone: wr_ge_50, pf_ge_2
- `r2_h1_m5_body58_hours05_18` standalone: trades_ge_80_review_candidate
- `current_r1_plus_r2_h1_m5_body58` combined: wr_ge_50
- `current_r1_plus_r2_h1_m5_body58_hours05_18` combined: none

## Guard Summary

### `r2_h1_m5_body58`
- `regime_router_block_short_r2_downtrend_only_state_chop`: 211
- `regime_router_block_short_r2_downtrend_only_state_compression`: 43
- `regime_router_block_short_r2_downtrend_only_state_shock`: 69
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 3
- `stop_ceiling_exceeded`: 32

### `r2_h1_m5_body58_hours05_18`
- `directional_session_filter_block`: 137
- `regime_router_block_short_r2_downtrend_only_state_chop`: 136
- `regime_router_block_short_r2_downtrend_only_state_compression`: 35
- `regime_router_block_short_r2_downtrend_only_state_shock`: 47
- `regime_router_block_short_r2_downtrend_only_state_uptrend`: 3
- `stop_ceiling_exceeded`: 23

## Interpretation

A V2 repair variant repaired WR and payoff quality, but sample remains below the 80-trade review-candidate gate.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_COMBINED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_MT5_COMPONENTS.json`
- r2_h1_m5_body58_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_r2_h1_m5_body58_NORMALIZED_TRADES.csv`
- r2_h1_m5_body58_hours05_18_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_r2_h1_m5_body58_hours05_18_NORMALIZED_TRADES.csv`
- current_r1_plus_r2_h1_m5_body58_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_plus_r2_h1_m5_body58_KEPT.csv`
- current_r1_plus_r2_h1_m5_body58_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_plus_r2_h1_m5_body58_DROPPED.csv`
- current_r1_plus_r2_h1_m5_body58_hours05_18_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_plus_r2_h1_m5_body58_hours05_18_KEPT.csv`
- current_r1_plus_r2_h1_m5_body58_hours05_18_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_PULLBACK_REJECTION_SHORT_V2_REPAIR_EXACT_20260709_current_r1_plus_r2_h1_m5_body58_hours05_18_DROPPED.csv`

# A1 XAU R1 Pullback Long V2 Session Exact-MT5

Generated UTC: `2026-07-08T16:30:30Z`
Status: `R1_PULLBACK_LONG_V2_SESSION_SHADOW_ONLY`

Scope: exact-MT5 component rerun using the EA-side R1 router and one preregistered session repair. Research-only.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_PREREG_2026_07_08.md`
Preregistration SHA256: `de8de045e60a7955cc4c7d52b5bbf284b4b4aa557c0e9164cb52f939362b377e`

## Standalone Result

| Variant | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Active% | Max DD | +Years | Q2 trades | Q2 net | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `r1_pullback_long_v2_m15_session_09_15` | 413 | 46.97 | 2.1598 | 1.9133 | 1665.94 | 2.0500 | 1.8160 | 12.37 | 171.62 | 4 | 0 | 0.00 | 1268.88 | 1186.49 | False |

## Combined With Routed R1 Box

| Book | Trades | WR% | W/L | PF | Net | Stress W/L | Stress PF | Active% | Max DD | +Months | -Months | Best month share% | Dropped | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `box_plus_r1_pullback_long_v2_m15_session_09_15` | 558 | 50.18 | 2.7028 | 2.7223 | 8716.36 | 2.6428 | 2.6618 | 16.11 | 889.69 | 18 | 17 | 30.92 | 0 | False |

## Baseline

Routed R1 box baseline: 145 trades, WR 59.31%, W/L 2.1804, PF 3.1782, net 7050.42, active 7.96%, max DD 866.37.

## Failed Checks

- `r1_pullback_long_v2_m15_session_09_15`: wr_ge_50
- `box_plus_r1_pullback_long_v2_m15_session_09_15`: best_month_share_lte_30pct

## Router / Guard Notes

### `r1_pullback_long_v2_m15_session_09_15`
- `directional_session_filter_block`: 2265
- `regime_router_block_long_r1_uptrend_only_state_chop`: 254
- `regime_router_block_long_r1_uptrend_only_state_compression`: 110
- `regime_router_block_long_r1_uptrend_only_state_downtrend`: 7
- `regime_router_block_long_r1_uptrend_only_state_shock`: 234

## Interpretation

The session repair stayed positive but did not clear every promotion gate. Do not add it to the deployable R1 book without review.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_COMBINED.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_MT5_COMPONENTS.json`
- r1_pullback_long_v2_m15_session_09_15_normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_r1_pullback_long_v2_m15_session_09_15_NORMALIZED_TRADES.csv`
- box_plus_r1_pullback_long_v2_m15_session_09_15_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_KEPT.csv`
- box_plus_r1_pullback_long_v2_m15_session_09_15_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_PULLBACK_LONG_V2_SESSION_EXACT_20260708_box_plus_r1_pullback_long_v2_m15_session_09_15_DROPPED.csv`

# A1 XAU R1 Long Expansion R3 Reclass Exact-MT5

Generated UTC: `2026-07-09T10:43:02Z`
Status: `R1_LONG_EXPANSION_R3_RECLASS_SHADOW_ONLY`

Scope: exact-MT5 strict R1-router execution of the frozen R3 D1-compression/H4-expansion long source. Research-only.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_PREREG_2026_07_09.md`
Preregistration SHA256: `f4aaddf0e88d404f5ff667817769bf4968e0afb6efdcd6b48257ae4b6b964841`
Current R1+R2 baseline: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R2_CONTINUATION_SHORT_V4_VOLATILITY_GATE_EXACT_20260709_current_r1_best_r2_pullback_plus_r2_impulse_body45_atr45_daily_loss10_KEPT.csv`
Current R1+R2 baseline SHA256: `47cbe6a562ba2874d93a97255affbde613566ed06340a149ed2795d69a5dae52`

## Result Table

| Book | Trades | WR% | W/L | PF | Net | Stress net | Stress PF | Recent3 trades | Recent3 net | Max DD | +Months | Best month share% | Top10 rem | Top3 days rem | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `current_r1_r2_baseline` | 678 | 51.03 | 2.6082 | 2.7182 | 9640.05 | 9436.65 | 2.6526 | 59 | 764.92 | 889.69 | 26 | 27.96 | 6731.40 | 7275.75 | n/a |
| `r1_long_expansion_r3_reclass_strict_r1` | 139 | 67.63 | 2.0312 | 4.2430 | 10142.72 | 10101.02 | 4.2158 | 0 | 0.00 | 856.09 | 14 | 25.23 | 7063.79 | 7215.73 | True |
| `current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1` | 707 | 51.91 | 2.9075 | 3.1384 | 13163.85 | 12951.75 | 3.0696 | 59 | 764.92 | 1076.56 | 27 | 21.39 | 10087.27 | 10532.25 | False |

## April-May-June 2026

| Book | April trades/net | May trades/net | June trades/net |
| --- | ---: | ---: | ---: |
| `r1_long_expansion_r3_reclass_strict_r1` | 0 / 0.00 | 0 / 0.00 | 0 / 0.00 |
| `current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1` | 8 / 145.37 | 5 / 55.74 | 46 / 563.81 |

## Gate Thresholds From Baseline

- Combined net minimum: `11640.05`
- Combined stress net minimum: `11436.65`
- Combined max DD cap: `1023.14`
- Combined recent3 minimum: `714.92`
- Positive months minimum: `26`

## Failed Checks

- `static`: none
- `r1_long_expansion_r3_reclass_strict_r1`: none
- `current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1`: dd_lte_115pct_baseline

## Router / Guard Notes

- `regime_router_block_long_r1_uptrend_only_state_chop`: 23
- `regime_router_block_long_r1_uptrend_only_state_compression`: 45
- `regime_router_block_long_r1_uptrend_only_state_shock`: 8
- `ORDER_SEND_OK`: 139

## Interpretation

The strict R1-routed R3 reclassification has usable evidence but did not clear every combined promotion gate. Keep as shadow-only.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709.json`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_STANDALONE.csv`
- combined_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_COMBINED.csv`
- normalized_trades_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_r1_long_expansion_r3_reclass_strict_r1_NORMALIZED_TRADES.csv`
- combined_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1_KEPT.csv`
- combined_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_current_r1_r2_plus_r1_long_expansion_r3_reclass_strict_r1_DROPPED.csv`
- mt5_report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_MT5.md`
- mt5_report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_R1_LONG_EXPANSION_R3_RECLASS_EXACT_20260709_MT5.json`

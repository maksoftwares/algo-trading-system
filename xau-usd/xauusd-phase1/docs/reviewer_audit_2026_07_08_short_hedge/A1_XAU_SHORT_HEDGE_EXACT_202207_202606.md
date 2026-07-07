# A1 XAU Short Hedge Exact MT5 Probe

Generated UTC: `2026-07-07T20:42:28Z`
Status: `SHORT_HEDGE_COMBINED_REVIEW_CANDIDATE`

Scope: exact-MT5 short hedge work order. The prior bear-continuation family is frozen as a control; V2 and V3 are structural hedge tests. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_SHORT_HEDGE_PREREG_2026_07_08.md`
Preregistration SHA256: `0424d92efb758e483773f90c08332cb59c9fddbaae628ec71c720f3bc4d374af`
Freeze note: `xau-usd/xauusd-phase1/docs/A1_XAU_BEAR_CONTINUATION_FAMILY_FREEZE_2026_07_08.md`
Freeze note SHA256: `75abf16442d5f175e5c25e55a0d91ea0fa5df765ead06246adc6fc18a20a0ac9`

## Standalone Short Hedge

| Variant | Trades | WR% | W/L | Active% | PF | Net | Stress PF | Stress W/L | Stress net | Pos weeks% | Q2 net | Top1% | Top day% | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `short_hedge_v1_break_run_control` | 445 | 32.13 | 2.3536 | 17.55 | 1.1144 | 208.00 | 1.0390 | 2.1943 | 74.50 | 38.67 | 182.17 | 17.30 | 39.68 | `REJECT_COST_STRESS` |
| `short_hedge_v2_breakdown_retest` | 329 | 32.83 | 2.8332 | 16.68 | 1.3846 | 441.42 | 1.2823 | 2.6239 | 342.72 | 36.99 | 283.39 | 8.06 | 28.42 | `SHORT_HEDGE_STANDALONE_REVIEW_CANDIDATE` |
| `short_hedge_v3_prior_high_sweep_reclaim` | 350 | 33.43 | 2.0495 | 19.18 | 1.0292 | 43.37 | 0.9604 | 1.9126 | -61.63 | 44.79 | 178.03 | 89.49 | 114.80 | `REJECT_COST_STRESS` |

## Combined With Supportive-Guard Book

Q2 repair note: the current guarded long-box baseline has no Q2-2026 long-box loss, so the original loss-reduction test is not applicable. The substitute defense check requires positive short Q2 addition and improved combined recent-three-month net.

| Combo | Signals | WR% | W/L | Active% | PF | Net | Stress W/L | Pos weeks% | Delta pp | Recent3 | New kept | New net | Red flipped | Red worsened | Long-box Q2 base | Long-box Q2 with short | Q2 repair% | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `baseline_supportive_guard` | 3645 | 50.40 | 2.0895 | 85.71 | 2.1395 | 20701.41 | 1.9720 | 57.69 | 0.00 | 279.22 | 0 | 0.00 | 0 | 0 | 0.00 | 0.00 | 0.00 | `BASELINE` |
| `short_hedge_v1_break_run_control` | 4064 | 48.45 | 2.1638 | 87.82 | 2.0474 | 20837.00 | 2.0390 | 58.17 | 0.48 | 369.06 | 420 | 138.06 | 5 | 25 | 0.00 | 182.17 | 0.00 | `SHORT_HEDGE_COMBINED_REVIEW_CANDIDATE` |
| `short_hedge_v2_breakdown_retest` | 3953 | 49.00 | 2.1637 | 87.54 | 2.0934 | 21064.67 | 2.0390 | 58.17 | 0.48 | 494.57 | 309 | 381.00 | 6 | 25 | 0.00 | 283.39 | 0.00 | `SHORT_HEDGE_COMBINED_REVIEW_CANDIDATE` |
| `short_hedge_v3_prior_high_sweep_reclaim` | 3984 | 48.97 | 2.1327 | 88.30 | 2.0609 | 20770.64 | 2.0104 | 56.25 | -1.44 | 462.53 | 340 | 63.64 | 8 | 22 | 0.00 | 178.03 | 0.00 | `REJECT_COMBINED_WEEKLY_SHAPE` |

## Interpretation

`short_hedge_v2_breakdown_retest` passed both the standalone hedge gate and the combined book gate. Keep it research-only until reviewer approval; do not draft a demo spec from this single pass.

## Artifacts

- md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606.md`
- json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_RESULTS.csv`
- standalone_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_STANDALONE.csv`
- mt5_components_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_MT5_COMPONENTS.md`
- mt5_components_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_MT5_COMPONENTS.json`
- short_hedge_v1_break_run_control_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v1_break_run_control_KEPT.csv`
- short_hedge_v1_break_run_control_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v1_break_run_control_DROPPED.csv`
- short_hedge_v1_break_run_control_long_box_plus_short_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v1_break_run_control_LONG_BOX_PLUS_SHORT.csv`
- short_hedge_v2_breakdown_retest_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_KEPT.csv`
- short_hedge_v2_breakdown_retest_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_DROPPED.csv`
- short_hedge_v2_breakdown_retest_long_box_plus_short_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v2_breakdown_retest_LONG_BOX_PLUS_SHORT.csv`
- short_hedge_v3_prior_high_sweep_reclaim_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v3_prior_high_sweep_reclaim_KEPT.csv`
- short_hedge_v3_prior_high_sweep_reclaim_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v3_prior_high_sweep_reclaim_DROPPED.csv`
- short_hedge_v3_prior_high_sweep_reclaim_long_box_plus_short_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_SHORT_HEDGE_EXACT_202207_202606_short_hedge_v3_prior_high_sweep_reclaim_LONG_BOX_PLUS_SHORT.csv`

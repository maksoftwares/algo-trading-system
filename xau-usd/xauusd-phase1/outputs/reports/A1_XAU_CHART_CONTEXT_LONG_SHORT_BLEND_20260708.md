# A1 XAU Chart-Context Long/Short Blend

Generated UTC: `2026-07-08T12:05:49Z`
Status: `CHART_CONTEXT_BLEND_REVIEW_CANDIDATE`

Scope: recomposition of exact-MT5 ledgers only. The chart-context V4 downside-impulse short is tested as a hedge overlay inside the current H4 box2 health/broad-quarantine book. No live/demo runtime, chart, preset, order, position, or broker state was changed.

Preregistration: `xau-usd/xauusd-phase1/docs/A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_PREREG_2026_07_08.md`
Preregistration SHA256: `4e2ff9e388a9d38c9e38697d3fb60cfa70f7002224c5aa4dc24c92c21c03f0e8`

## Baseline

| Row | Signals | WR% | W/L | Stress W/L | Active% | Net | Max DD | +Months | -Months | Q2-2026 | Recent3 | Pos weeks% | Worst week |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `current_prevhealth_box2_broad_quarantined` | 3934 | 49.08 | 2.1793 | 2.0507 | 87.44 | 20858.29 | 958.86 | 31 | 17 | 494.57 | 494.57 | 58.10 | -878.18 |

## Blend Results

| Row | Decision | Mode | Short kept | Short net | V2 kept | WR% | W/L | Stress W/L | Net | Net delta | Max DD | DD delta | +Months | Q2 delta | Recent3 delta | Pos weeks% | Worst week |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `long_book_without_short_v2` | `REJECT_BLEND_GATE` | `diagnostic_remove_v2` | 0 | 0.00 | 0 | 50.48 | 2.1058 | 1.9844 | 20477.29 | -381.00 | 958.86 | 0.00 | 30 | -215.35 | -215.35 | 57.14 | -878.18 |
| `add_short_v4_impulse_retest_d1_nonup_h1h4` | `REJECT_BLEND_GATE` | `add` | 97 | -54.05 | 309 | 48.59 | 2.1952 | 2.0651 | 20811.24 | -47.05 | 965.00 | 6.14 | 31 | -5.68 | -5.68 | 58.10 | -896.04 |
| `replace_v2_with_short_v4_impulse_retest_d1_nonup_h1h4` | `REJECT_BLEND_GATE` | `replace_v2` | 273 | 352.37 | 0 | 49.29 | 2.1657 | 2.0386 | 20836.66 | -21.63 | 965.00 | 6.14 | 30 | 19.47 | 19.47 | 58.10 | -896.04 |
| `add_short_v4_impulse_retest_d1_structural_h1h4` | `REJECT_BLEND_GATE` | `add` | 38 | 35.24 | 309 | 48.98 | 2.1822 | 2.0533 | 20900.53 | 42.24 | 958.86 | 0.00 | 31 | -5.68 | -5.68 | 57.62 | -878.18 |
| `replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4` | `CHART_CONTEXT_BLEND_REVIEW_CANDIDATE` | `replace_v2` | 170 | 398.13 | 0 | 50.03 | 2.1328 | 2.0084 | 20882.42 | 24.13 | 958.86 | 0.00 | 31 | 19.47 | 19.47 | 58.57 | -878.18 |
| `add_short_v4_impulse_retest_d1_nonup_h1_only` | `REJECT_BLEND_GATE` | `add` | 117 | -88.02 | 309 | 48.49 | 2.1962 | 2.0659 | 20777.27 | -81.02 | 980.81 | 21.95 | 31 | -5.68 | -5.68 | 57.14 | -911.85 |
| `replace_v2_with_short_v4_impulse_retest_d1_nonup_h1_only` | `REJECT_BLEND_GATE` | `replace_v2` | 293 | 318.40 | 0 | 49.20 | 2.1671 | 2.0397 | 20802.69 | -55.60 | 980.81 | 21.95 | 30 | 19.47 | 19.47 | 58.10 | -911.85 |

## Gate Failures

- `long_book_without_short_v2`: positive_months_not_worse, negative_months_not_worse, q2_improved, recent3_improved
- `add_short_v4_impulse_retest_d1_nonup_h1h4`: dd_not_worse, q2_improved, recent3_improved
- `replace_v2_with_short_v4_impulse_retest_d1_nonup_h1h4`: dd_not_worse, positive_months_not_worse, negative_months_not_worse
- `add_short_v4_impulse_retest_d1_structural_h1h4`: q2_improved, recent3_improved
- `replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4`: none
- `add_short_v4_impulse_retest_d1_nonup_h1_only`: dd_not_worse, q2_improved, recent3_improved
- `replace_v2_with_short_v4_impulse_retest_d1_nonup_h1_only`: dd_not_worse, positive_months_not_worse, negative_months_not_worse

## Best Source Contributions

| Source | Signals | Net USD |
| --- | ---: | ---: |
| `freq_step3_frontier` | 3416 | 6134.72 |
| `h4_d1_long_best_box2_atr80` | 208 | 14349.57 |
| `short_v4_impulse_retest_d1_structural_h1h4` | 170 | 398.13 |

## Interpretation

`replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4` passed the fixed combined-book gate. Keep research-only until reviewer sign-off.

## Artifacts

- report_md: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708.md`
- report_json: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708.json`
- results_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708_RESULTS.csv`
- best_kept_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708_replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4_KEPT.csv`
- best_dropped_csv: `xau-usd/xauusd-phase1/outputs/reports/A1_XAU_CHART_CONTEXT_LONG_SHORT_BLEND_20260708_replace_v2_with_short_v4_impulse_retest_d1_structural_h1h4_DROPPED.csv`

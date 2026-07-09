# A1 XAU Current Candidate Regime Attribution

Generated UTC: `2026-07-09T07:35:08Z`

Scope: recomposition/audit of existing exact-MT5 trade ledgers against the 10-year D1 regime map. This is not a fresh MT5 backtest and does not prove a deployable filter by itself.

Causal filter tests use `prev_d1_regime`, the most recent completed D1 regime strictly before entry date. This avoids same-day close lookahead.

## Book Summary

| Book | Trades | WR% | W/L | PF | Net | Stress Net | Recent3 Trades | Recent3 Net | Max DD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `R1_current_long_book` | 558 | 50.18 | 2.7028 | 2.7223 | 8716.36 | 8548.96 | 0 | 0.00 | 889.69 |
| `R2_pullback_short_v2_hours05_18` | 63 | 52.38 | 2.1721 | 2.3893 | 334.23 | 315.33 | 4 | 148.48 | 37.21 |
| `R2_continuation_short_v4_atr45_daily_loss10` | 57 | 57.89 | 2.1150 | 2.9081 | 589.46 | 572.36 | 55 | 616.44 | 41.85 |
| `R2_combined_current_best` | 678 | 51.03 | 2.6082 | 2.7182 | 9640.05 | 9436.65 | 59 | 764.92 | 889.69 |
| `R3_compression_long_v1` | 215 | 61.40 | 2.3120 | 3.6769 | 12194.08 | 12129.58 | 1 | -204.70 | 856.09 |
| `R3_combined_with_R1` | 663 | 50.98 | 2.8586 | 2.9730 | 13921.91 | 13723.01 | 1 | -204.70 | 1076.56 |
| `R4_chop_prior_day_reclaim_both` | 526 | 33.84 | 2.0740 | 1.0608 | 95.06 | -62.74 | 24 | -26.73 | 134.56 |
| `R4_combined_with_R1` | 1084 | 42.25 | 3.1851 | 2.3303 | 8811.42 | 8486.22 | 24 | -26.73 | 880.88 |

## Regime Attribution By Book

| Book | Prev D1 Regime | Trades | WR% | PF | Net | Recent3 Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `R1_current_long_book` | `uptrend` | 412 | 49.51 | 2.3574 | 6003.83 | 0.00 |
| `R1_current_long_book` | `chop` | 49 | 30.61 | 2.5540 | 488.12 | 0.00 |
| `R1_current_long_book` | `compression` | 55 | 63.64 | 9.4631 | 1647.25 | 0.00 |
| `R1_current_long_book` | `shock` | 19 | 57.89 | 2.9865 | 72.21 | 0.00 |
| `R1_current_long_book` | `transition` | 23 | 65.22 | 6.4337 | 504.95 | 0.00 |
| `R2_pullback_short_v2_hours05_18` | `downtrend` | 31 | 41.94 | 1.5507 | 76.43 | 31.70 |
| `R2_pullback_short_v2_hours05_18` | `chop` | 6 | 66.67 | 3.1296 | 68.83 | 74.02 |
| `R2_pullback_short_v2_hours05_18` | `compression` | 24 | 62.50 | 3.4008 | 152.26 | 0.00 |
| `R2_pullback_short_v2_hours05_18` | `transition` | 2 | 50.00 | 7.0678 | 36.71 | 42.76 |
| `R2_continuation_short_v4_atr45_daily_loss10` | `downtrend` | 14 | 71.43 | 4.5321 | 203.66 | 203.66 |
| `R2_continuation_short_v4_atr45_daily_loss10` | `chop` | 6 | 66.67 | 3.1974 | 71.35 | 71.35 |
| `R2_continuation_short_v4_atr45_daily_loss10` | `shock` | 7 | 28.57 | 0.6610 | -25.11 | 1.87 |
| `R2_continuation_short_v4_atr45_daily_loss10` | `transition` | 30 | 56.67 | 3.3462 | 339.56 | 339.56 |
| `R2_combined_current_best` | `uptrend` | 412 | 49.51 | 2.3574 | 6003.83 | 0.00 |
| `R2_combined_current_best` | `downtrend` | 45 | 51.11 | 2.4258 | 280.09 | 235.36 |
| `R2_combined_current_best` | `chop` | 61 | 37.70 | 2.6583 | 628.30 | 145.37 |
| `R2_combined_current_best` | `compression` | 79 | 63.29 | 7.9732 | 1799.51 | 0.00 |
| `R2_combined_current_best` | `shock` | 26 | 50.00 | 1.4266 | 47.10 | 1.87 |
| `R2_combined_current_best` | `transition` | 55 | 60.00 | 4.6159 | 881.22 | 382.32 |
| `R3_compression_long_v1` | `uptrend` | 103 | 63.11 | 3.9369 | 7984.07 | 0.00 |
| `R3_compression_long_v1` | `downtrend` | 17 | 47.06 | 1.9285 | 281.25 | 0.00 |
| `R3_compression_long_v1` | `chop` | 35 | 48.57 | 1.3955 | 369.17 | -204.70 |
| `R3_compression_long_v1` | `compression` | 54 | 68.52 | 6.6995 | 3288.68 | 0.00 |
| `R3_compression_long_v1` | `transition` | 6 | 83.33 | 12.5428 | 270.91 | 0.00 |
| `R3_combined_with_R1` | `uptrend` | 436 | 51.15 | 3.0192 | 9507.07 | 0.00 |
| `R3_combined_with_R1` | `downtrend` | 17 | 47.06 | 1.9285 | 281.25 | 0.00 |
| `R3_combined_with_R1` | `chop` | 76 | 34.21 | 1.3377 | 389.83 | -204.70 |
| `R3_combined_with_R1` | `compression` | 91 | 60.44 | 5.3229 | 3190.07 | 0.00 |
| `R3_combined_with_R1` | `shock` | 19 | 57.89 | 2.9865 | 72.21 | 0.00 |
| `R3_combined_with_R1` | `transition` | 24 | 62.50 | 5.1364 | 481.48 | 0.00 |
| `R4_chop_prior_day_reclaim_both` | `uptrend` | 232 | 38.79 | 1.3829 | 253.21 | 0.00 |
| `R4_chop_prior_day_reclaim_both` | `downtrend` | 42 | 28.57 | 0.9095 | -8.16 | -5.01 |
| `R4_chop_prior_day_reclaim_both` | `chop` | 164 | 30.49 | 0.8494 | -60.53 | -43.89 |
| `R4_chop_prior_day_reclaim_both` | `compression` | 2 | 0.00 | 0.0000 | -8.71 | 0.00 |
| `R4_chop_prior_day_reclaim_both` | `shock` | 45 | 28.89 | 0.6203 | -88.50 | -3.33 |
| `R4_chop_prior_day_reclaim_both` | `transition` | 41 | 31.71 | 1.0463 | 7.75 | 25.50 |
| `R4_combined_with_R1` | `uptrend` | 644 | 45.65 | 2.2307 | 6257.04 | 0.00 |
| `R4_combined_with_R1` | `downtrend` | 42 | 28.57 | 0.9095 | -8.16 | -5.01 |
| `R4_combined_with_R1` | `chop` | 213 | 30.52 | 1.5972 | 427.59 | -43.89 |
| `R4_combined_with_R1` | `compression` | 57 | 61.40 | 9.0577 | 1638.54 | 0.00 |
| `R4_combined_with_R1` | `shock` | 64 | 37.50 | 0.9395 | -16.29 | -3.33 |
| `R4_combined_with_R1` | `transition` | 64 | 43.75 | 2.9686 | 512.70 | 25.50 |

## Causal Regime Filter Tests

| Test | Allowed Prev D1 Regimes | Kept / Base | WR% | PF | Net | Net Delta | Recent3 Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `R1_prev_uptrend_only` | `uptrend` | 412 / 558 | 49.51 | 2.3574 | 6003.83 | -2712.53 | 0.00 |
| `R1_prev_uptrend_or_shock` | `shock,uptrend` | 431 / 558 | 49.88 | 2.3626 | 6076.04 | -2640.32 | 0.00 |
| `R2_pullback_prev_downtrend_only` | `downtrend` | 31 / 63 | 41.94 | 1.5507 | 76.43 | -257.80 | 31.70 |
| `R2_pullback_prev_downtrend_or_transition` | `downtrend,transition` | 33 / 63 | 42.42 | 1.7811 | 113.14 | -221.09 | 74.46 |
| `R2_cont_prev_downtrend_only` | `downtrend` | 14 / 57 | 71.43 | 4.5321 | 203.66 | -385.80 | 203.66 |
| `R2_cont_prev_downtrend_or_transition` | `downtrend,transition` | 44 / 57 | 61.36 | 3.6840 | 543.22 | -46.24 | 543.22 |
| `R3_prev_compression_only` | `compression` | 54 / 215 | 68.52 | 6.6995 | 3288.68 | -8905.40 | 0.00 |
| `R3_prev_compression_or_chop` | `chop,compression` | 89 / 215 | 60.67 | 3.4218 | 3657.85 | -8536.23 | -204.70 |
| `R4_prev_chop_only` | `chop` | 164 / 526 | 30.49 | 0.8494 | -60.53 | -155.59 | -43.89 |
| `R4_prev_chop_or_compression` | `chop,compression` | 166 / 526 | 30.12 | 0.8313 | -69.24 | -164.30 | -43.89 |

## Router Overlay Portfolios

| Portfolio | Components | Trades | WR% | W/L | PF | Net | Stress Net | Recent3 Trades | Recent3 Net |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `baseline_R1_plus_R2_current_best` | existing exact-MT5 combined R1+R2 pullback+R2 continuation | 678 | 51.03 | 2.6082 | 2.7182 | 9640.05 | 9436.65 | 59 | 764.92 |
| `overlay_strict_named_regimes` | R1 uptrend + R2 downtrend + R3 compression + R4 chop | 675 | 46.52 | 3.1031 | 2.6991 | 9512.07 | 9309.57 | 21 | 191.47 |
| `overlay_transition_tolerant` | R1 uptrend + R2 downtrend/transition + R3 compression/chop + R4 chop | 742 | 47.04 | 2.8546 | 2.5350 | 10257.51 | 10034.91 | 53 | 369.09 |
| `overlay_no_R4_transition_tolerant` | R1 uptrend + R2 downtrend/transition + R3 compression/chop | 578 | 51.73 | 2.4661 | 2.6429 | 10318.04 | 10144.64 | 47 | 412.98 |

## Decision

The D1 regime map helps diagnostically, but the naive previous-D1 overlay is not yet a deployable improvement. R1 remains strongest in uptrend but loses too much full-window profit if filtered by the coarse D1 label alone; R2's recent defense is real and is concentrated in transition/downtrend; R3 is strong historically but not active enough recently; R4 prior-day reclaim still does not earn its keep even inside chop. Next improvement should be a router audit using the EA's native intraday regime snapshot at each entry, then repair R4/chop rather than tightening R1 with this coarse daily classifier.

## Artifacts

- report_md: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709.md`
- report_json: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709.json`
- book_csv: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709_BOOKS.csv`
- regime_by_book_csv: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709_REGIME_BY_BOOK.csv`
- filter_tests_csv: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709_FILTER_TESTS.csv`
- portfolio_csv: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709_PORTFOLIOS.csv`
- tagged_trades_csv: `xau-usd\xauusd-phase1\outputs\reports\A1_XAU_CURRENT_CANDIDATE_REGIME_ATTRIBUTION_20260709_TAGGED_TRADES.csv`

# XAUUSD Canonical Loss-Avoidance Analysis - 2026-06-17

Status: `PASS`

Analysis only. Reads exported CSV artifacts and writes reports. Does not touch MT5 runtime, EAs, presets, orders, positions, charts, profiles, or accounts.

This report implements the post-Claude correction: family, session, duplicate, protected-cluster, and cost views are all tied back to the same canonical 586-row deduped XAUUSD universe. Cost conclusions use only the cost-known subset of that same universe.

## Source Files

| file | path |
| --- | --- |
| canonical_rows_csv | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\XAUUSD_DEDUPED_REAL_FILL_EVIDENCE_2026_06_16_ROWS.csv |
| actual_trades_csv | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\PHASE2_DEMO_ACTUAL_BROKER_TRADES.csv |
| cost_trades_csv | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\COST_GATE_REAL_FILL_TRADES_2026_06_16.csv |

Enriched canonical rows CSV: `C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase1\outputs\reports\XAUUSD_CANONICAL_LOSS_AVOIDANCE_2026_06_17_ROWS.csv`

## Universe

| canonical_rows | ticket_matched_rows | cost_matched_rows | cost_known_rows | cost_missing_rows |
| --- | --- | --- | --- | --- |
| 586 | 586 | 586 | 435 | 151 |

## Baseline

| rows | wins | losses | flats | win_rate_pct | pnl_aed | profit_factor | avg_win_aed | avg_loss_aed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 586 | 220 | 362 | 4 | 37.80% | -554.52 | 0.95 | 45.10 | -28.94 |

## Family View

| group | rows | win_rate_pct | pnl_aed | pf | best_day_removed_pnl_aed | best_two_days_removed_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- |
| round_family | 432 | 36.60% | -1359.41 | 0.84 | -1424.53 | -1484.72 |
| session_extreme | 38 | 26.32% | -143.78 | 0.71 | -192.68 | -215.40 |
| wr50 | 2 | 0.00% | -74.00 | 0.00 | -52.87 | 0.00 |
| repair | 1 | 0.00% | -22.23 | 0.00 | 0.00 | 0.00 |
| p2weakness | 1 | 0.00% | -14.44 | 0.00 | 0.00 | 0.00 |
| breakout_core | 112 | 47.75% | 1059.34 | 1.82 | 772.49 | 506.22 |

## Candidate View

| group | rows | win_rate_pct | pnl_aed | pf | best_day_removed_pnl_aed | best_two_days_removed_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- |
| symbol_normalized_round_retest_v0 | 410 | 36.61% | -1270.55 | 0.85 | -1335.67 | -1395.86 |
| session_extreme_retest_v0 | 38 | 26.32% | -143.78 | 0.71 | -192.68 | -215.40 |
| round_number_retest_v0 | 22 | 36.36% | -88.86 | 0.67 | -77.88 | -58.11 |
| WR50_BreakoutEvening_v0 | 2 | 0.00% | -74.00 | 0.00 | -52.87 | 0.00 |
| symbol_normalized_round_retest_v0_repair_v1 | 1 | 0.00% | -22.23 | 0.00 | 0.00 | 0.00 |
| p2weakness_br_v1 | 1 | 0.00% | -14.44 | 0.00 | 0.00 | 0.00 |
| swing_breakout_retest_v0 | 11 | 54.55% | 166.45 | 3.07 | -3.02 | -66.94 |
| breakout_retest | 101 | 47.00% | 892.89 | 1.74 | 606.04 | 468.63 |

## Session View

| group | rows | win_rate_pct | pnl_aed | pf | best_day_removed_pnl_aed | best_two_days_removed_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- |
| Afternoon 12:00-15:59 | 82 | 28.05% | -523.03 | 0.62 | -595.51 | -639.45 |
| Morning 06:00-11:59 | 136 | 36.03% | -210.96 | 0.90 | -425.64 | -514.64 |
| Night 20:00-05:59 | 241 | 39.17% | -159.99 | 0.96 | -393.53 | -569.86 |
| Evening 16:00-19:59 | 127 | 43.55% | 339.46 | 1.13 | 117.25 | -64.24 |

## Afternoon Round-Family Diagnosis

This is the focused decision view requested after the Review 12/Claude correction. It tests whether the afternoon loss is truly an afternoon problem, or mostly a round-family problem that happens to cluster in the afternoon.

| session | dedup_universe_rows | afternoon_rows | afternoon_pnl_aed | round_family_afternoon_rows | round_family_afternoon_pnl_aed | round_family_loss_share_of_afternoon_loss_pct | residual_after_round_quarantine_rows | residual_after_round_quarantine_pnl_aed | protected_evening_night_rows_removed | protected_evening_night_pnl_removed_aed | runtime_authorized |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Afternoon 12:00-15:59 | 586 | 82 | -523.03 | 55 | -452.13 | 86.44% | 27 | -70.90 | 0 | 0.00 | False |

| segment | rows | win_rate_pct | pnl_aed | pf | loss_share_of_afternoon_loss_pct | best_day_removed_pnl_aed | best_two_days_removed_pnl_aed | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all_afternoon | 82 | 28.05% | -523.03 | 0.62 | 100.00% | -595.51 | -639.45 | Baseline afternoon exposure. |
| round_family_afternoon | 55 | 27.27% | -452.13 | 0.58 | 86.44% | -501.82 | -483.67 | Primary loss source to quarantine first. |
| non_round_residual_after_round_quarantine | 27 | 29.63% | -70.90 | 0.77 | 13.56% | -143.38 | -162.99 | Remaining afternoon exposure after removing round-family rows. |
| breakout_core_afternoon | 11 | 27.27% | -53.09 | 0.63 | 10.15% | -87.31 | -81.56 | Small residual; do not block breakout core solely because it is afternoon. |
| session_extreme_afternoon | 16 | 31.25% | -17.81 | 0.89 | 3.41% | -56.07 | -81.45 | Residual weak-family slice; keep measuring separately. |

Decision: Round-family quarantine is the first measurable fix. Avoid a broad afternoon ban until the non-round residual has more evidence.

## Cost View On The Same Universe

Cost rows below are the cost-known subset of the canonical 586-row universe. Missing-cost rows are not silently mixed into threshold claims.

### Cost Buckets

| bucket | rows | win_rate_pct | pnl_aed | pf | median_cost_r | mean_cost_r | best_day_removed_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| <=0.05 | 100 | 39.58% | -96.22 | 0.97 | 0.04 | 0.04 | -270.05 |
| 0.05-0.07 | 101 | 42.57% | 35.73 | 1.02 | 0.06 | 0.06 | -327.91 |
| 0.07-0.09 | 82 | 42.68% | 128.45 | 1.11 | 0.08 | 0.08 | 46.73 |
| 0.09-0.11 | 56 | 32.14% | -196.06 | 0.76 | 0.10 | 0.10 | -262.45 |
| 0.11-0.13 | 32 | 34.38% | -117.51 | 0.72 | 0.12 | 0.12 | -168.62 |
| >0.13 | 64 | 28.12% | -315.52 | 0.54 | 0.16 | 0.17 | -348.45 |

### Cost Cutoffs

| cutoff | kept_rows | kept_wr | kept_pnl_aed | blocked_rows | blocked_pnl_aed | kept_best_day_removed_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- |
| 0.04 | 53 | 42.00% | 193.18 | 382 | -754.31 | -21.41 |
| 0.05 | 100 | 39.58% | -96.22 | 335 | -464.91 | -270.05 |
| 0.06 | 155 | 39.07% | -309.56 | 280 | -251.57 | -600.66 |
| 0.07 | 201 | 41.12% | -60.49 | 234 | -500.64 | -426.45 |
| 0.08 | 241 | 42.19% | 129.93 | 194 | -691.06 | -227.37 |
| 0.09 | 283 | 41.58% | 67.96 | 152 | -629.09 | -332.05 |
| 0.10 | 315 | 41.16% | 41.67 | 120 | -602.80 | -400.18 |
| 0.11 | 339 | 40.00% | -128.10 | 96 | -433.03 | -479.59 |
| 0.12 | 361 | 39.50% | -242.15 | 74 | -318.98 | -560.30 |
| 0.13 | 371 | 39.51% | -245.61 | 64 | -315.52 | -563.76 |
| 0.15 | 394 | 38.97% | -358.98 | 41 | -202.15 | -606.37 |

### Cost By Family

| group | rows | win_rate_pct | pnl_aed | pf | median_cost_r | mean_cost_r |
| --- | --- | --- | --- | --- | --- | --- |
| round_family | 357 | 36.72% | -1025.95 | 0.86 | 0.07 | 0.08 |
| session_extreme | 13 | 23.08% | -66.17 | 0.64 | 0.10 | 0.10 |
| repair | 1 | 0.00% | -22.23 | 0.00 | 0.08 | 0.08 |
| breakout_core | 64 | 47.62% | 553.22 | 1.69 | 0.09 | 0.09 |

## Account Focus: Lab vs Production-Style

A1 is treated as a broad/noisy lab account. A2 and A3 are treated as the production-style evidence lane. In this canonical XAU export, A2 has no closed XAU rows, so A2+A3 currently equals A3 only.

| view | rows | win_rate_pct | pnl_aed | pf | no_round_rows | no_round_pnl_aed | breakout_core_rows | breakout_core_pnl_aed | protected_breakout_en_rows | protected_breakout_en_pnl_aed | no_afternoon_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 lab observation | 586 | 37.80% | -554.52 | 0.95 | 154 | 804.89 | 112 | 1059.34 | 79 | 1027.32 | -31.49 |
| A2+A3 production-style | 0 | n/a | 0.00 | n/a | 0 | 0.00 | 0 | 0.00 | 0 | 0.00 | 0.00 |
| A2 clean account | 0 | n/a | 0.00 | n/a | 0 | 0.00 | 0 | 0.00 | 0 | 0.00 | 0.00 |
| A3 experiment account | 0 | n/a | 0.00 | n/a | 0 | 0.00 | 0 | 0.00 | 0 | 0.00 | 0.00 |

### By Account

| group | rows | win_rate_pct | pnl_aed | pf | best_day_removed_pnl_aed | best_two_days_removed_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- |
| 1025742 | 586 | 37.80% | -554.52 | 0.95 | -737.02 | -839.47 |

### By Account And Family

| group | rows | win_rate_pct | pnl_aed | pf | best_day_removed_pnl_aed | best_two_days_removed_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- |
| 1025742 | round_family | 432 | 36.60% | -1359.41 | 0.84 | -1424.53 | -1484.72 |
| 1025742 | session_extreme | 38 | 26.32% | -143.78 | 0.71 | -192.68 | -215.40 |
| 1025742 | wr50 | 2 | 0.00% | -74.00 | 0.00 | -52.87 | 0.00 |
| 1025742 | repair | 1 | 0.00% | -22.23 | 0.00 | 0.00 | 0.00 |
| 1025742 | p2weakness | 1 | 0.00% | -14.44 | 0.00 | 0.00 | 0.00 |
| 1025742 | breakout_core | 112 | 47.75% | 1059.34 | 1.82 | 772.49 | 506.22 |

## Rule Scorecard

Positive `delta_vs_baseline_aed` means the retrospective filter improved the canonical duplicate-hidden baseline. This is not permission to change runtime; it is a review packet.

| scenario | kept_rows | kept_wr | kept_pnl_aed | delta_vs_baseline_aed | blocked_rows | blocked_winners | blocked_losses | blocked_pnl_aed | kept_best_day_removed_pnl_aed | protected_rows_removed | protected_pnl_removed_aed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| round_family_quarantine | 154 | 41.18% | 804.89 | 1359.41 | 432 | 157 | 272 | -1359.41 | 534.54 | 0 | 0.00 |
| breakout_core_only | 112 | 47.75% | 1059.34 | 1613.86 | 474 | 167 | 304 | -1613.86 | 772.49 | 0 | 0.00 |
| protect_breakout_evening_night_cluster | 79 | 52.56% | 1027.32 | 1581.84 | 507 | 179 | 325 | -1581.84 | 708.28 | 0 | 0.00 |
| no_afternoon | 504 | 39.40% | -31.49 | 523.03 | 82 | 23 | 59 | -523.03 | -411.47 | 0 | 0.00 |
| no_morning_afternoon | 368 | 40.66% | 179.47 | 733.99 | 218 | 72 | 146 | -733.99 | -219.07 | 0 | 0.00 |
| cost_known_keep_lte_0_13 | 522 | 39.00% | -239.00 | 315.52 | 64 | 18 | 46 | -315.52 | -557.15 | 11 | -21.49 |
| round_quarantine_plus_cost_gt_0_13 | 139 | 42.03% | 834.75 | 1389.27 | 447 | 162 | 282 | -1389.27 | 550.84 | 11 | -21.49 |

## Protected Cluster

| definition | rows | win_rate_pct | pnl_aed | pf | best_day_removed_pnl_aed | best_two_days_removed_pnl_aed |
| --- | --- | --- | --- | --- | --- | --- |
| selected breakout_retest or swing_breakout_retest_v0 in Evening/Night | 79 | 52.56% | 1027.32 | 2.17 | 708.28 | 483.97 |

## Duplicate Exposure

| multirow_groups | multirow_group_pnl_aed | mixed_family_groups | mixed_family_pnl_aed | breakout_round_mixed_groups | breakout_round_mixed_pnl_aed | note |
| --- | --- | --- | --- | --- | --- | --- |
| 461 | -356.95 | 81 | 500.88 | 26 | 290.46 | Canonical rows already collapse same-minute symbol/direction/volume duplicates. Runtime exposure guard should still catch cross-family and adjacent-bar stacks before order send. |

## Conclusions

- Round-family quarantine remains the strongest first promotion candidate.
- Evening/night breakout should be protected, but not converted into evening/night-only routing yet.
- Cost is useful as a worst-tier veto, but the exact threshold remains fragile and should stay shadow-only.
- Exposure control should use symbol + direction + bar + level band; family should remain an attribution field, not the exposure key.
- Hard short-block is still unproven until a down or range day is observed.

## Boundary

Review only. No MT5 runtime, EA, preset, order, chart, profile, or account change is authorized by this report.

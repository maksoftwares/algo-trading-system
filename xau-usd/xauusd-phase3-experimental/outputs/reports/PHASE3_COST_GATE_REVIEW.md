# Phase 3 Cost Gate Review

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Summary

| Field | Value |
| --- | --- |
| Raw ledger rows | 89 |
| Family unique events | 49 |
| Primary rows | 49 |
| Spread median points | 50.0 |
| Spread P95 points | 75.0 |

## Cost-In-R Gate Prototypes

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| proxy_cost_gt_0.20R | proxy_cost_r > 0.20 | 61 | 34 | 34 | 27 | 0.287 | 0.2246 | 417.23 | 50.0 | 38 | 3 | 20 |
| proxy_cost_gt_0.25R | proxy_cost_r > 0.25 | 50 | 28 | 28 | 22 | 0.3054 | 0.2061 | 399.46 | 50.0 | 27 | 3 | 20 |
| proxy_cost_gt_0.30R | proxy_cost_r > 0.30 | 27 | 15 | 15 | 12 | 0.4801 | 0.0315 | 312.02 | 50.0 | 4 | 3 | 20 |
| proxy_cost_gt_0.35R | proxy_cost_r > 0.35 | 23 | 13 | 13 | 10 | 0.4804 | 0.0312 | 283.09 | 50.0 | 0 | 3 | 20 |

## Stop-Distance Survival Buckets

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0_to_249 | 0_to_249 | 11 | 6 | 6 | 5 | 0.5197 | -0.0081 | 211.67 | 50.0 | 0 | 0 | 11 |
| 250_to_499 | 250_to_499 | 41 | 23 | 23 | 18 | 0.2689 | 0.2427 | 417.54 | 50.0 | 29 | 3 | 9 |
| 500_to_749 | 500_to_749 | 29 | 15 | 15 | 14 | 0.1838 | 0.3278 | 614.72 | 50.0 | 29 | 0 | 0 |
| 750_plus | 750_plus | 8 | 5 | 5 | 3 | 0.1514 | 0.3602 | 880.43 | 62.5 | 8 | 0 | 0 |

## Spread-Regime Buckets

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spread_lte_median_50_0 | spread_lte_median_50_0 | 70 | 38 | 38 | 32 | 0.2529 | 0.2587 | 434.91 | 50.0 | 57 | 2 | 11 |
| spread_median_to_p95_50_0_75_0 | spread_median_to_p95_50_0_75_0 | 19 | 11 | 11 | 8 | 0.361 | 0.1506 | 443.17 | 75.0 | 9 | 1 | 9 |
| spread_gt_p95_75_0 | spread_gt_p95_75_0 | 0 | 0 | 0 | 0 | None | None | None | None | 0 | 0 | 0 |

## Family Kill-State Summary

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COST_WATCH | kill_rule_state | 3 | 2 | 2 | 1 | 0.3525 | 0.1591 | 312.02 | 50.0 | 0 | 3 | 0 |
| NORMAL | kill_rule_state | 66 | 36 | 36 | 30 | 0.2252 | 0.2864 | 537.825 | 50.0 | 66 | 0 | 0 |
| SUSPEND_FAMILY | kill_rule_state | 20 | 11 | 11 | 9 | 0.4822 | 0.0294 | 229.12 | 50.0 | 0 | 0 | 20 |

## Reviewer Annotation Template

| Field | Value |
| --- | --- |
| COST_ISSUE | Spread/slippage proxy dominates an otherwise mechanically valid event. |
| TIGHT_STOP_ISSUE | Stop distance is so small that normal cost consumes the edge. |
| TIMING_ISSUE | Event timing appears structurally poor even before cost. |
| DUPLICATED_OBSERVER_ISSUE | Suspension belongs to a duplicate observer row, not a primary event. |
| UNKNOWN | Reviewer could not classify the suspension with current evidence. |

Use these annotations on suspend-family rows only as review labels. They do not authorize paper-mode execution or change the real Phase 2 gate state.

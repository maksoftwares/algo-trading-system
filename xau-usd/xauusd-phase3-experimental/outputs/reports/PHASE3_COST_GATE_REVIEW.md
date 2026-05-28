# Phase 3 Cost Gate Review

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Summary

| Field | Value |
| --- | --- |
| Raw ledger rows | 108 |
| Family unique events | 61 |
| Primary rows | 61 |
| Spread median points | 50.0 |
| Spread P95 points | 75.0 |

## Cost-In-R Gate Prototypes

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| proxy_cost_gt_0.20R | proxy_cost_r > 0.20 | 67 | 38 | 38 | 29 | 0.287 | 0.2246 | 417.54 | 50.0 | 42 | 3 | 22 |
| proxy_cost_gt_0.25R | proxy_cost_r > 0.25 | 53 | 30 | 30 | 23 | 0.3082 | 0.2034 | 399.46 | 50.0 | 28 | 3 | 22 |
| proxy_cost_gt_0.30R | proxy_cost_r > 0.30 | 30 | 17 | 17 | 13 | 0.472 | 0.0396 | 322.53 | 50.0 | 5 | 3 | 22 |
| proxy_cost_gt_0.35R | proxy_cost_r > 0.35 | 25 | 14 | 14 | 11 | 0.4804 | 0.0312 | 283.09 | 50.0 | 0 | 3 | 22 |

## Stop-Distance Survival Buckets

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0_to_249 | 0_to_249 | 11 | 6 | 6 | 5 | 0.5197 | -0.0081 | 211.67 | 50.0 | 0 | 0 | 11 |
| 250_to_499 | 250_to_499 | 45 | 26 | 26 | 19 | 0.2754 | 0.2362 | 417.54 | 50.0 | 31 | 3 | 11 |
| 500_to_749 | 500_to_749 | 38 | 20 | 20 | 18 | 0.1761 | 0.3355 | 635.57 | 50.0 | 38 | 0 | 0 |
| 750_plus | 750_plus | 14 | 9 | 9 | 5 | 0.1343 | 0.3774 | 991.805 | 50.0 | 14 | 0 | 0 |

## Spread-Regime Buckets

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spread_lte_median_50_0 | spread_lte_median_50_0 | 85 | 48 | 48 | 37 | 0.2252 | 0.2864 | 488.54 | 50.0 | 72 | 2 | 11 |
| spread_median_to_p95_50_0_75_0 | spread_median_to_p95_50_0_75_0 | 23 | 13 | 13 | 10 | 0.361 | 0.1506 | 443.17 | 75.0 | 11 | 1 | 11 |
| spread_gt_p95_75_0 | spread_gt_p95_75_0 | 0 | 0 | 0 | 0 | None | None | None | None | 0 | 0 | 0 |

## Family Kill-State Summary

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COST_WATCH | kill_rule_state | 3 | 2 | 2 | 1 | 0.3525 | 0.1591 | 312.02 | 50.0 | 0 | 3 | 0 |
| NORMAL | kill_rule_state | 83 | 47 | 47 | 36 | 0.2026 | 0.309 | 590.46 | 50.0 | 83 | 0 | 0 |
| SUSPEND_FAMILY | kill_rule_state | 22 | 12 | 12 | 10 | 0.4813 | 0.0303 | 256.105 | 62.5 | 0 | 0 | 22 |

## Reviewer Annotation Template

| Field | Value |
| --- | --- |
| COST_ISSUE | Spread/slippage proxy dominates an otherwise mechanically valid event. |
| TIGHT_STOP_ISSUE | Stop distance is so small that normal cost consumes the edge. |
| TIMING_ISSUE | Event timing appears structurally poor even before cost. |
| DUPLICATED_OBSERVER_ISSUE | Suspension belongs to a duplicate observer row, not a primary event. |
| UNKNOWN | Reviewer could not classify the suspension with current evidence. |

Use these annotations on suspend-family rows only as review labels. They do not authorize paper-mode execution or change the real Phase 2 gate state.

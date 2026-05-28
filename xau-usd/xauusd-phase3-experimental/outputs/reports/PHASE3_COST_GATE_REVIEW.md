# Phase 3 Cost Gate Review

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Summary

| Field | Value |
| --- | --- |
| Raw ledger rows | 116 |
| Family unique events | 65 |
| Primary rows | 65 |
| Spread median points | 50.0 |
| Spread P95 points | 75.0 |

## Cost-In-R Gate Prototypes

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| proxy_cost_gt_0.20R | proxy_cost_r > 0.20 | 71 | 40 | 40 | 31 | 0.276 | 0.2356 | 417.78 | 50.0 | 46 | 3 | 22 |
| proxy_cost_gt_0.25R | proxy_cost_r > 0.25 | 53 | 30 | 30 | 23 | 0.3082 | 0.2034 | 399.46 | 50.0 | 28 | 3 | 22 |
| proxy_cost_gt_0.30R | proxy_cost_r > 0.30 | 30 | 17 | 17 | 13 | 0.472 | 0.0396 | 322.53 | 50.0 | 5 | 3 | 22 |
| proxy_cost_gt_0.35R | proxy_cost_r > 0.35 | 25 | 14 | 14 | 11 | 0.4804 | 0.0312 | 283.09 | 50.0 | 0 | 3 | 22 |

## Stop-Distance Survival Buckets

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0_to_249 | 0_to_249 | 11 | 6 | 6 | 5 | 0.5197 | -0.0081 | 211.67 | 50.0 | 0 | 0 | 11 |
| 250_to_499 | 250_to_499 | 47 | 27 | 27 | 20 | 0.2689 | 0.2427 | 417.78 | 50.0 | 33 | 3 | 11 |
| 500_to_749 | 500_to_749 | 44 | 23 | 23 | 21 | 0.1838 | 0.3278 | 624.815 | 50.0 | 44 | 0 | 0 |
| 750_plus | 750_plus | 14 | 9 | 9 | 5 | 0.1343 | 0.3774 | 991.805 | 50.0 | 14 | 0 | 0 |

## Spread-Regime Buckets

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| spread_lte_median_50_0 | spread_lte_median_50_0 | 93 | 52 | 52 | 41 | 0.2179 | 0.2937 | 504.76 | 50.0 | 80 | 2 | 11 |
| spread_median_to_p95_50_0_75_0 | spread_median_to_p95_50_0_75_0 | 23 | 13 | 13 | 10 | 0.361 | 0.1506 | 443.17 | 75.0 | 11 | 1 | 11 |
| spread_gt_p95_75_0 | spread_gt_p95_75_0 | 0 | 0 | 0 | 0 | None | None | None | None | 0 | 0 | 0 |

## Family Kill-State Summary

| bucket | rule | raw_rows | family_unique_events | primary_rows | observer_duplicate_rows | median_proxy_cost_r | median_net_after_proxy_r | median_stop_distance_points | median_spread_points | normal_count | cost_watch_count | suspend_family_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COST_WATCH | kill_rule_state | 3 | 2 | 2 | 1 | 0.3525 | 0.1591 | 312.02 | 50.0 | 0 | 3 | 0 |
| NORMAL | kill_rule_state | 91 | 51 | 51 | 40 | 0.2026 | 0.309 | 575.4 | 50.0 | 91 | 0 | 0 |
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

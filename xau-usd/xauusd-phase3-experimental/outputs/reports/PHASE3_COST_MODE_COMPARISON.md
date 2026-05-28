# Phase 3 Cost Mode Comparison

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Comparison

| cost_mode | family_unique_events | primary_stream_allowed | median_proxy_cost_r | mean_proxy_cost_r | median_net_after_proxy_cost_r | mean_net_after_proxy_cost_r | baseline_assumed_cost_r | baseline_net_expectancy_r | median_net_delta_vs_assumed_baseline_r | normal_count | cost_watch_count | suspend_family_count | suspend_family_unique_events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only_proxy | 61 | 61 | 0.1226 | 0.1339 | 0.389 | 0.3777 | 0.3228 | 0.1888 | 0.2002 | 108 | 0 | 0 | 0 |
| entry_exit_proxy | 61 | 61 | 0.2452 | 0.2678 | 0.2664 | 0.2438 | 0.3228 | 0.1888 | 0.0776 | 83 | 3 | 22 | 12 |
| p95_fresh_proxy | 61 | 61 | 0.3287 | 0.3571 | 0.1829 | 0.1545 | 0.3228 | 0.1888 | -0.006 | 52 | 8 | 48 | 27 |
| stress_2x_p95_proxy | 61 | 61 | 0.6369 | 0.692 | -0.1253 | -0.1804 | 0.3228 | 0.1888 | -0.3141 | 8 | 2 | 98 | 55 |

## Cost Semantics

Baseline net expectancy is the Phase 0 fixed-notional net after the originally assumed cost model. Net after proxy cost is baseline gross expectancy minus the offline Phase 3 proxy cost; the delta columns show how far that proxy result sits above or below the assumed baseline net.

## Interpretation

This report compares offline cost assumptions only. It does not authorize Phase 2, paper-mode execution, or broker-side order logic.

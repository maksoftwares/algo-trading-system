# Phase 3 Cost Mode Comparison

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Comparison

| cost_mode | family_unique_events | primary_stream_allowed | median_proxy_cost_r | mean_proxy_cost_r | median_net_after_proxy_cost_r | mean_net_after_proxy_cost_r | baseline_assumed_cost_r | baseline_net_expectancy_r | median_net_delta_vs_assumed_baseline_r | normal_count | cost_watch_count | suspend_family_count | suspend_family_unique_events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only_proxy | 49 | 49 | 0.1277 | 0.1434 | 0.3839 | 0.3682 | 0.3228 | 0.1888 | 0.1951 | 89 | 0 | 0 | 0 |
| entry_exit_proxy | 49 | 49 | 0.2554 | 0.2867 | 0.2562 | 0.2249 | 0.3228 | 0.1888 | 0.0674 | 66 | 3 | 20 | 11 |
| p95_fresh_proxy | 49 | 49 | 0.3679 | 0.3836 | 0.1437 | 0.128 | 0.3228 | 0.1888 | -0.0451 | 37 | 7 | 45 | 25 |
| stress_2x_p95_proxy | 49 | 49 | 0.7128 | 0.7433 | -0.2012 | -0.2317 | 0.3228 | 0.1888 | -0.39 | 3 | 2 | 84 | 46 |

## Cost Semantics

Baseline net expectancy is the Phase 0 fixed-notional net after the originally assumed cost model. Net after proxy cost is baseline gross expectancy minus the offline Phase 3 proxy cost; the delta columns show how far that proxy result sits above or below the assumed baseline net.

## Interpretation

This report compares offline cost assumptions only. It does not authorize Phase 2, paper-mode execution, or broker-side order logic.

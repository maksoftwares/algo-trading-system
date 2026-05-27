# Phase 3 Cost Mode Comparison

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Comparison

| cost_mode | family_unique_events | primary_stream_allowed | median_proxy_cost_r | mean_proxy_cost_r | median_net_after_proxy_cost_r | mean_net_after_proxy_cost_r | normal_count | cost_watch_count | suspend_family_count | suspend_family_unique_events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only_proxy | 47 | 47 | 0.1277 | 0.1416 | 0.3839 | 0.37 | 87 | 0 | 0 | 0 |
| entry_exit_proxy | 47 | 47 | 0.2554 | 0.2831 | 0.2562 | 0.2285 | 66 | 2 | 19 | 10 |
| p95_fresh_proxy | 47 | 47 | 0.3679 | 0.3796 | 0.1437 | 0.132 | 37 | 6 | 44 | 24 |
| stress_2x_p95_proxy | 47 | 47 | 0.7128 | 0.7354 | -0.2012 | -0.2238 | 3 | 2 | 82 | 44 |

## Interpretation

This report compares offline cost assumptions only. It does not authorize Phase 2, paper-mode execution, or broker-side order logic.

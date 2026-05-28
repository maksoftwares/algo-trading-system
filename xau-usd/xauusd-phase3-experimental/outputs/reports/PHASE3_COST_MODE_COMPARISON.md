# Phase 3 Cost Mode Comparison

This report has no authority over Phase 2 readiness. PHASE2_READINESS_REPORT.md remains the sole real readiness authority.

Overall status: REVIEW_READY

## Comparison

| cost_mode | family_unique_events | primary_stream_allowed | median_proxy_cost_r | mean_proxy_cost_r | median_net_after_proxy_cost_r | mean_net_after_proxy_cost_r | baseline_assumed_cost_r | baseline_net_expectancy_r | median_net_delta_vs_assumed_baseline_r | normal_count | cost_watch_count | suspend_family_count | suspend_family_unique_events |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| entry_only_proxy | 65 | 65 | 0.1155 | 0.1318 | 0.3961 | 0.3798 | 0.3228 | 0.1888 | 0.2073 | 116 | 0 | 0 | 0 |
| entry_exit_proxy | 65 | 65 | 0.2311 | 0.2636 | 0.2805 | 0.248 | 0.3228 | 0.1888 | 0.0917 | 91 | 3 | 22 | 12 |
| p95_fresh_proxy | 65 | 65 | 0.3223 | 0.3532 | 0.1894 | 0.1584 | 0.3228 | 0.1888 | 0.0005 | 58 | 10 | 48 | 27 |
| stress_2x_p95_proxy | 65 | 65 | 0.6243 | 0.6843 | -0.1127 | -0.1727 | 0.3228 | 0.1888 | -0.3015 | 8 | 2 | 106 | 59 |

## Cost Semantics

Baseline net expectancy is the Phase 0 fixed-notional net after the originally assumed cost model. Net after proxy cost is baseline gross expectancy minus the offline Phase 3 proxy cost; the delta columns show how far that proxy result sits above or below the assumed baseline net.

## Interpretation

This report compares offline cost assumptions only. It does not authorize Phase 2, paper-mode execution, or broker-side order logic.

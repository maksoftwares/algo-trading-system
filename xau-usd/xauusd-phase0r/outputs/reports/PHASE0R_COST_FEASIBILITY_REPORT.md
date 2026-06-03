# Phase 0R Cost Feasibility Report

Overall status: PASS

Measured spread assumptions:

- measured_median_spread_points: 50
- measured_p95_spread_points: 75
- measured_max_spread_points: 180

Hard rule: measured P95 spread divided by expected median stop points must be <= 0.30R.

| candidate_id | expected_median_stop_points | median_cost_R | p95_cost_R | max_cost_R | status | block_reason |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| d1_compression_h4_expansion_v0 | 500 | 0.100 | 0.150 | 0.360 | PASS_PREFERRED | none |
| h4_trend_pullback_d1_bias_v0 | 375 | 0.133 | 0.200 | 0.480 | PASS_PREFERRED | none |
| weekly_level_h4_rejection_v0 | 425 | 0.118 | 0.176 | 0.424 | PASS_PREFERRED | none |
| session_extreme_retest_v1_htf_confirmed | 500 | 0.100 | 0.150 | 0.360 | PASS_PREFERRED | none |

No candidate has passed Phase 0R. This report is a structural precheck only.

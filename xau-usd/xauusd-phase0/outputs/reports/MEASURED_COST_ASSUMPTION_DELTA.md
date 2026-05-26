# Measured-Cost Assumption Delta

Overall status: FAIL

## Decision

Measured spread assumptions materially exceed the configured model and block Phase 2 execution eligibility.

## Delta Table

| Metric | Configured | Measured | Delta |
| --- | --- | --- | --- |
| configured_median_spread_points | 20.0000 | 50.0000 | 30.0000 |
| configured_p95_spread_points | 35.0000 | 75.0000 | 40.0000 |
| modeled_cost_R vs measured_cost_R | 0.3228 | 1.4384 | 1.1156 |
| modeled_net_R vs measured_net_R | 0.1888 | -0.9268 | -1.1156 |

## Boundary

This report compares configured spread assumptions against the passive-spread measured model and the measured-cost revalidation output.

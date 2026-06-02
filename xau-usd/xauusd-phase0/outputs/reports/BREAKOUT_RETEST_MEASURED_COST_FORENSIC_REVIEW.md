# Breakout-Retest Measured-Cost Forensic Review

Overall status: CALCULATION_CONFIRMED
Generated at UTC: 2026-06-02T11:45:08Z

## Decision Boundary

This forensic review checks whether the measured-cost failure looks reproducible. It does not authorize Phase 2, demo execution, broker execution, or live capital.

## Evidence Summary

| Field | Value |
| --- | --- |
| Expert | breakout_retest |
| Trades audited | 66759 |
| Baseline PF | 1.3625 |
| Measured PF | 0.4125 |
| Baseline net expectancy R | 0.1888 |
| Measured net expectancy R | -0.6150 |
| Baseline mean cost R | 0.3228 |
| Measured mean cost R | 1.1265 |

## Checks

| Check | Status | Evidence |
| --- | --- | --- |
| Unit conversion | PASS | max_abs_error=0.000000000000; formula=spread_points * point_size / risk_price |
| Spread replacement | PASS | max_abs_error=0.000000000000; measured spread replaces modeled entry spread. |
| Point size and digits | PASS | ledger_point_sizes=[0.01]; logger_point_sizes=[0.01]; logger_digits=['2'] |
| Stop distance distribution | PASS | median_stop_points=109.7939; p75_all_in_cost_R=1.1092 |
| Freshness and closed-market filtering | PASS | tick_fresh_reported=True; weekend_buckets_present=False |
| Broker source policy | PASS | measured_brokers=['all']; conservative source documented=True |

## Decision

No canonical Phase 2 execution may reopen from this report alone. If these checks remain confirmed, the correct action is Phase 0R replacement research.

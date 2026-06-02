# Hypothesis Draft: breakout_retest_cost_aware_v2

Status: DRAFT - NOT HASH LOCKED

Do not run this candidate through Phase 0 until humans review and finalize this draft. This document exists to convert measured-cost and passive-observer lessons into a new candidate, not to rescue `breakout_retest_v1.0`.

## 1. Why v1.0 Is Cost-Suspended

`breakout_retest_v1.0` failed measured-cost revalidation after the fresh measured spread model passed. The current controlling interpretation is:

```text
Measured P95 cost kills the historical v1.0 evidence package.
The failure is treated as real because the sanity check confirmed the cost conversion path.
```

Therefore, v1.0 remains `COST_SUSPENDED_CANONICAL` and cannot be made execution-eligible by adding a late filter.

## 2. What New Behavior v2 Tests

This draft tests whether breakout-retest behavior remains viable when the setup is cost-aware at birth:

- wider stop distances,
- explicit cost_R cap,
- explicit spread-regime cap,
- same-family lifecycle labelling,
- measured-cost revalidation before any Phase 2 reconsideration.

## 3. Why v2 Is Not A Parameter Patch

v2 is not a modified v1.0 result set. It is a new hypothesis because the cost gate changes the event universe before testing. All evidence must be regenerated after hypothesis lock.

## 4. Required Stop-Distance Gate

Draft constraints:

```text
preferred_stop_distance_points >= 375
absolute_min_stop_distance_points >= 250
```

Rationale: the latest cost review suggests tight stops below roughly 250 points are too fragile under measured XAUUSD spread.

## 5. Required Cost_R Gate

Draft constraints:

```text
preferred_estimated_total_cost_R <= 0.20
absolute_max_estimated_total_cost_R <= 0.30
```

Rows above the absolute maximum are blocked before candidate scoring.

## 6. Required Spread-Regime Gate

Draft constraints:

```text
preferred_spread_points <= measured_median_spread_points
absolute_max_spread_points <= measured_p95_spread_points
```

The measured model currently records median spread near 50 points and P95 near 75 points. These values must be regenerated from the current broker sample before final locking.

## 7. Expected Trade Count

Draft expectation:

```text
>= 40 trades per matrix cell after cost gates
```

If the cost-aware gates reduce trade count below this threshold, v2 fails as insufficiently evidenced for this framework.

## 8. Expected Median Hold Time

Draft expectation:

```text
median_hold_time >= 20 minutes
```

The goal is to move away from tight M5 micro-scalp behavior and toward event structures that can survive retail spread.

## 9. Expected Cost_R Distribution

Draft expectation:

```text
median_estimated_total_cost_R <= 0.20
p75_estimated_total_cost_R <= 0.30
p95_estimated_total_cost_R documented, not ignored
```

## 10. Falsification Criteria

The hypothesis is falsified if any of the following occur:

- measured-cost revalidation fails,
- fewer than 7 of 9 matrix cells pass PF and risk gates,
- cost_R distribution exceeds the absolute gate in normal spread regimes,
- zero-trade or low-trade cells dominate after cost filtering,
- adversarial review finds logic gaps above the allowed threshold,
- Phase 2B passive observer evidence contradicts the expected stop-distance or cost_R profile.

## 11. Explicit Same-Family Classification

```text
candidate_family = breakout_retest_family
diversification_credit = none
inherits_same_family_risk = true
```

This candidate, if later approved, does not solve diversification risk by itself.

## 12. Full Phase 0 Rerun Requirement

Required:

```text
new hypothesis lock
new 9-cell matrix
new decile persistence report
new multisymbol report
new adversarial review
new D2 / family-clustered reality check review
new review bundle
```

## 13. Measured-Cost Revalidation Requirement

Required before any canonical Phase 2 reconsideration:

```text
measured-cost model: PASS
measured-cost revalidation: PASS
measured-cost assumption delta: PASS
net expectancy after measured cost >= +0.15R
```

This draft cannot authorize demo execution, paper-mode execution, or live trading.

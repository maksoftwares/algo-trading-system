# Phase 0R Cost Feasibility Rules

The default measured spread assumptions are:

| metric | points |
| --- | ---: |
| measured_median_spread_points | 50 |
| measured_p95_spread_points | 75 |
| measured_max_spread_points | 180 |

Reject or mark `STRUCTURAL_COST_RISK` when:

```text
measured_p95_spread_points / expected_median_stop_points > 0.30
```

Preferred candidates satisfy:

```text
measured_p95_spread_points / expected_median_stop_points <= 0.20
```

Hard targets:

- median projected cost_R <= 0.30R
- P95 projected cost_R <= 0.50R
- net expectancy after measured cost >= +0.15R before any promotion

This lane should generally avoid expected median stops below 250 points, prefer 375+ points, and treat 500+ points as structurally stronger.

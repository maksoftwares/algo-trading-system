# Breakout-Retest Cost Break-Even Analysis

Overall status: BLOCKED_BY_MEASURED_COST
Generated at UTC: 2026-06-02T11:45:07Z

## Current Evidence

| Field | Value |
| --- | --- |
| Measured P95 spread points | 75.0000 |
| Median stop distance points | 109.7939 |
| P75 stop distance points | 179.0084 |
| Baseline gross expectancy R | 0.5115 |
| Measured net expectancy R | -0.6150 |
| Measured PF | 0.4125 |

## Required Stop Distance

| Target cost_R | Required stop points | Interpretation |
| --- | --- | --- |
| 0.1500 | 500.00 | Strong cost discipline target. |
| 0.2000 | 375.00 | Preferred candidate screening target. |
| 0.3000 | 250.00 | Hard upper tolerance for pre-screening. |
| 0.5000 | 150.00 | Too expensive for modest-edge systems. |
| 0.5115 | 146.61 | Approximate zero-edge cost ceiling from baseline gross expectancy; current measured net=-0.6150R. |

This analysis explains why current M5 retest stops are cost-fragile. It is not a filter proposal for the failed v1.0 candidate.

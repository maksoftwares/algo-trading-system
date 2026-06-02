# Candidate Cost Feasibility Requirements

Status: ACTIVE

Future Phase 0R candidates must pass a structural cost feasibility screen before full matrix work is prioritized.

## Measured-Cost Inputs

Current XAUUSD measured-cost reference:

| Metric | Value |
| --- | ---: |
| Measured median spread | 50 points |
| Measured P95 spread | 75 points |
| XAUUSD point size | 0.0100 |

## Stop-Distance Rules

| Class | Requirement |
| --- | --- |
| Hard minimum median stop distance | >= 250 points |
| Preferred median stop distance | >= 375 points |
| Ideal median stop distance | >= 500 points |
| Hard max P95 cost_R | <= 0.30R |
| Preferred median cost_R | <= 0.20R |
| Ideal median cost_R | <= 0.15R |

## Required Hypothesis Fields

Each new candidate must document:

- mechanic family
- entry / decision timeframe
- expected median hold bars M5-equivalent
- expected median hold hours
- expected decisions per week
- expected trades per year
- expected median stop distance points
- expected measured cost_R
- cost feasibility class
- why measured spread should not dominate the edge
- whether it qualifies as timeframe diversification
- falsification criteria

A D1/W1 reference level with M5 entries does not qualify as timeframe diversification.

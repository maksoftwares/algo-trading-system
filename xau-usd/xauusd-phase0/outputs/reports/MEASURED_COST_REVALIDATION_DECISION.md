# Measured-Cost Revalidation Decision

Overall status: FAIL

Decision: CALCULATION_CONFIRMED_COST_FAILURE

## Load-Bearing Result

| Metric | Value |
| --- | --- |
| Required passing cells | 7/9 |
| Observed passing cells | 0/9 |
| Trades | 66,759 |
| Overall PF | 0.4125 |
| Net expectancy | -0.6150R |
| Mean cost | 1.1265R |
| Fixed PnL | -2,052,677.40 |

## Cost Staircase

| Scenario | PF | Net R | Gate |
| --- | --- | --- | --- |
| Configured matrix as run | 1.3625 | +0.1888R | PASS |
| Configured P95 35 points | 0.9619 | -0.0251R | FAIL |
| Measured median 50 points | 0.6906 | -0.2479R | FAIL |
| Measured P95 75 points | 0.4097 | -0.6194R | FAIL |
| Measured stress 180 points | 0.0627 | -2.1793R | FAIL |

## Decision Rule

Because `MEASURED_COST_REVALIDATION_SANITY_CHECK.md` is `CALCULATION_CONFIRMED`, the measured-cost failure is treated as real. Do not lower the +0.15R floor, tune the old strategy, or use demo spreads to override the canonical live-spread gate.

## Required Next Step

Continue Phase 0R replacement research for lower-cost, lower-frequency, wider-stop, preferably H1/H4/D1 candidates.

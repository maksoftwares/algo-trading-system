# Profit Policy V12 Post-Outcome Audit

## Decision

`PROFIT_POLICY_V12_HISTORICAL_GATE_FAIL`

V12 retained 2,285 of 2,368 out-of-time candidates. It raised pooled stressed
normalized 0.01-lot P&L from $8,828.69 to $8,856.57, an improvement of only
$27.88. It exceeded V11 by $481.65 because V11's stronger veto removed profitable
volume along with losing candidates.

The pooled result is not statistically reliable. The 95% weekly-block bootstrap
interval for V12 minus non-ML normalized P&L was -$242.59 to +$268.13.

| Window | Non-ML | V11 | V12 |
|---|---:|---:|---:|
| 3 months | $441.65 | $354.08 | $328.59 |
| 6 months | $2,214.11 | $2,137.83 | $2,169.69 |
| 12 months | $3,250.58 | $3,040.92 | $3,238.62 |

V12 did not beat non-ML in any recent window. It beat V11 over six and twelve
months, but lost to V11 over three months.

The final forward research calibration selected quantile zero, which means
retain all candidates. Therefore V12 provides no evidence for enabling an ML
profit filter now. V11 remains the stronger quality/drawdown filter, while
non-ML remains the stronger recent total-profit baseline.

No runtime, MT5, shadow, demo, live, or broker authorization changed.

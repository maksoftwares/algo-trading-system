# Measured-Cost Revalidation Sanity Check

Overall status: CALCULATION_CONFIRMED

Decision: CALCULATION_CONFIRMED

## Scope And Data Sources

| Field | Value |
| --- | --- |
| Measured cost model | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\reports\MEASURED_COST_MODEL.md |
| Measured cost csv | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\reports\cost_model_measured.csv |
| Measured revalidation | C:\Users\ZHAO ZHU INFORMATION\Downloads\algo-trading-system\xau-usd\xauusd-phase0\outputs\reports\BREAKOUT_RETEST_MEASURED_COST_REVALIDATION.md |
| Measured model status | PASS |
| Measured revalidation status | FAIL |
| Configured median spread | 20 points |
| Configured P95 spread | 35 points |
| Measured median spread | 50 points |
| Measured P95 spread | 75 points |
| Measured stress spread | 180 points |

## Calculation Sanity Questions

| Question | Status | Evidence |
| --- | --- | --- |
| 1. Spread points converted to price correctly | PASS | point_size is positive for all rows; unique point sizes: 0.0100. |
| 2. XAUUSD point/digit handling | PASS | Phase 0 fixed-risk ledgers use XAUUSD point_size=0.0100. |
| 3. Spread applied once, not double-counted | PASS | all_in_cost_R = pre_measured_all_in_cost_R - entry_spread_R + measured_entry_spread_R. |
| 4. Entry and exit costs modeled consistently | PASS | net_R is reduced by the same spread replacement used in all_in_cost_R; exit/slippage terms are preserved. |
| 5. Slippage added on top of spread correctly | PASS | Measured spread replacement leaves entry/exit slippage_R unchanged; mean slippage contribution is 0.0167R. |
| 6. cost_R denominator | PASS | measured_entry_spread_R = measured_p95_spread_points * point_size / abs(entry_price - stop_loss). |
| 7. Manual sample recomputation | PASS | See sample table below; rows recompute measured_cost_R and net_R from raw ledger fields. |
| 8. Median measured-cost revalidation | PASS | Median, P95, and stress scenarios are listed below. Median also fails the formal cell gate in the current ledger. |
| 9. Live-server spreads vs demo execution | PASS | Measured model source is Capital.ComMena-Live; this remains the conservative canonical cost gate, not demo-spread cherry-picking. |
| 10. Broker commission assumption | PASS | Mean commission_R in the adjusted ledger is 0.0000; broker commission remains zero in this evidence surface. |
| Revalidation status integrity | PASS | Current measured-cost revalidation report status is FAIL. |

## Sample-Trade Manual Recomputations

| Cell | Broker | Entry UTC | Risk Price | Point | Spread Pts | Manual Cost R | Script Cost R | Manual Net R | Script Net R | Match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | capital_com | 2016-01-04 04:40:00+00:00 | 0.7624 | 0.0100 | 75.0000 | 0.9838 | 0.9838 | 0.6340 | 0.6340 | PASS |
| 5 | pepperstone | 2019-01-02 06:45:00+00:00 | 0.9065 | 0.0100 | 75.0000 | 0.8274 | 0.8274 | 0.8889 | 0.8889 | PASS |
| 9 | dukascopy | 2022-01-02 23:05:00+00:00 | 0.0300 | 0.0100 | 75.0000 | 25.0000 | 25.0000 | -14.1663 | -14.1663 | PASS |

## Median, P95, And Stress Results

| Scenario | Trades | PF | Net R | Cost R | Passing Cells | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| configured_matrix_as_run | 66759 | 1.3625 | 0.1888 | 0.3228 | 7/9; required 7 | PASS |
| configured_p95_fixed_35_points | 66759 | 0.9619 | -0.0251 | 0.5366 | 1/9; required 7 | FAIL |
| measured_median_fixed_50_points | 66759 | 0.6906 | -0.2479 | 0.7595 | 0/9; required 7 | FAIL |
| measured_p95_fixed_75_points | 66759 | 0.4097 | -0.6194 | 1.1309 | 0/9; required 7 | FAIL |
| measured_stress_fixed_180_points | 66759 | 0.0627 | -2.1793 | 2.6909 | 0/9; required 7 | FAIL |

## Decision Rule

- `BUG_FOUND`: fix the cost script, regenerate measured-cost model, revalidation, assumption delta, and Phase 2 readiness, then request reviewer sign-off.
- `CALCULATION_CONFIRMED`: keep the breakout-retest family cost-suspended for canonical execution and continue research for lower-cost independent candidates.

## Boundary

This report does not authorize Phase 2, paper-mode execution, demo execution, or live trading. It only checks whether the measured-cost failure looks like a unit/model defect.

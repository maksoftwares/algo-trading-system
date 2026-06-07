# H4 BTC Risk Pressure Gold Reversal v3 First Pass

Generated: 2026-06-07

Expert: `h4_btc_risk_pressure_gold_reversal_v3`
Hypothesis SHA256: `a97241808c796acf305ecc4418f38ce3ba3005eb825232710d5a24e6b1529ae2`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v3 without tuning.

The clustered BTC-pressure definition did not rescue the BTC reversal lane. It stayed sparse, failed the 40-trade floor in all 9 matrix cells, and only produced a Pepperstone-only PF pocket. Capital.com and Dukascopy were negative across costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 15 | 33.33% | 0.7111 | -0.95% | 1.60% | 22.22% | 8 |
| 2 | capital_com | median | 15 | 33.33% | 0.7111 | -0.95% | 1.60% | 22.22% | 8 |
| 3 | capital_com | p95 | 15 | 33.33% | 0.7049 | -0.97% | 1.60% | 22.22% | 8 |
| 4 | pepperstone | best_case | 9 | 66.67% | 1.3190 | 0.37% | 0.58% | 8.33% | 13 |
| 5 | pepperstone | median | 9 | 66.67% | 1.3190 | 0.37% | 0.58% | 8.33% | 13 |
| 6 | pepperstone | p95 | 9 | 66.67% | 1.3688 | 0.41% | 0.58% | 8.33% | 13 |
| 7 | dukascopy | best_case | 6 | 33.33% | 0.7577 | -0.30% | 0.78% | 8.33% | 10 |
| 8 | dukascopy | median | 6 | 33.33% | 0.8069 | -0.22% | 0.68% | 8.33% | 10 |
| 9 | dukascopy | p95 | 6 | 33.33% | 0.7806 | -0.25% | 0.70% | 8.33% | 10 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 3/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 13 |
| Cross-broker persistence | FAIL, only Pepperstone is positive/PF-threshold |
| Concentration | FAIL context, largest/top-5 trade concentration is meaningless with 6-15 trades per cell |

## Interpretation

The v3 change was directionally different from v1/v2 because it required same-sign BTC 5-day and 20-day pressure clusters. The result still did not produce enough observations, and the small positive pocket was broker-fragmented. This means the BTC stress-reversal idea remains a clue, not a worthy BTC EA.

Do not tune v3. Any future BTC attempt needs a materially different data class or mechanism, not another small threshold adjustment around shifted Yahoo BTC daily pressure.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_risk_pressure_gold_reversal_v3.md`
- Registration: `outputs/reports/h4_btc_risk_pressure_gold_reversal_v3_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_btc_risk_pressure_gold_reversal_v3_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_risk_pressure_gold_reversal_v3/`

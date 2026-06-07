# H1 BTC Risk Pressure Gold Followthrough v2 First Pass

Generated: 2026-06-07

Expert: `h1_btc_risk_pressure_gold_followthrough_v2`
Hypothesis SHA256: `6daa607e3798cddd1d6b128da96b953b795cb9b645e2e74e19066878befbb74e`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v2 without tuning.

This broader H1 BTC pressure follow-through variant fixed the sparse-sample problem, but the edge did not survive the broker/cost matrix. Capital.com was positive but below the PF threshold, Pepperstone was negative, and Dukascopy was materially negative across costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 111 | 46.85% | 1.1591 | 4.01% | 8.37% | 38.89% | 4 |
| 2 | capital_com | median | 111 | 46.85% | 1.1591 | 4.01% | 8.37% | 38.89% | 4 |
| 3 | capital_com | p95 | 111 | 46.85% | 1.1256 | 3.18% | 8.61% | 38.89% | 4 |
| 4 | pepperstone | best_case | 128 | 38.28% | 0.8622 | -4.42% | 8.29% | 38.89% | 3 |
| 5 | pepperstone | median | 128 | 38.28% | 0.8622 | -4.42% | 8.29% | 38.89% | 3 |
| 6 | pepperstone | p95 | 128 | 38.28% | 0.8394 | -5.18% | 8.63% | 38.89% | 3 |
| 7 | dukascopy | best_case | 105 | 31.43% | 0.7388 | -7.16% | 8.50% | 52.78% | 2 |
| 8 | dukascopy | median | 105 | 31.43% | 0.6546 | -9.74% | 10.67% | 55.56% | 2 |
| 9 | dukascopy | p95 | 105 | 31.43% | 0.6010 | -11.36% | 11.94% | 61.11% | 2 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | PASS, 9/9 |
| Max zero-trade months <= 3 | FAIL, max 4 |
| Cross-broker persistence | FAIL, Capital.com-only positive drift below threshold |
| Concentration | FAIL context, all non-Capital.com broker windows lose money |

## Interpretation

The v2 broadening shows that BTC pressure can be made active enough for H1 trading, but the activity dilutes into negative cross-broker expectancy. This closes the simple BTC daily-return pressure follow-through path as an approval candidate.

Do not tune v2. A future BTC attempt needs a materially different mechanism, likely one that separates crypto-liquidity regime from same-day XAU execution state instead of using BTC return pressure alone.

## Evidence

- Hypothesis: `docs/hypothesis_h1_btc_risk_pressure_gold_followthrough_v2.md`
- Registration: `outputs/reports/h1_btc_risk_pressure_gold_followthrough_v2_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h1_btc_risk_pressure_gold_followthrough_v2_research_smoke.md`
- Matrix: `outputs/matrix_results/h1_btc_risk_pressure_gold_followthrough_v2/`

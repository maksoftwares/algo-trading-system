# H4 GLD BTC Vol Flow Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h4_gld_btc_vol_flow_reversal_v0`
Hypothesis SHA256: `6ecdb4a291bef338c13fcc62cd6a8302475c1c2db22bfc4ea2c2037a48f1fa49`
Status: `REJECTED_FIRST_PASS_SPARSE_PF_LEAD`

## Verdict

Reject v0 without tuning.

The combined GLD-flow plus BTC-volatility filter created a real PF clue in Pepperstone and Dukascopy, but it collapsed activity and failed Capital.com badly. This is not a worthy EA. It is a sparse research clue: the overlap may isolate better events than either source alone, but not enough and not cross-broker enough for approval.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 6 | 33.33% | 0.1786 | -1.10% | 1.33% | 11.11% | 10 |
| 2 | capital_com | median | 6 | 33.33% | 0.1786 | -1.10% | 1.33% | 11.11% | 10 |
| 3 | capital_com | p95 | 6 | 33.33% | 0.1740 | -1.11% | 1.34% | 11.11% | 10 |
| 4 | pepperstone | best_case | 13 | 53.85% | 1.6075 | 1.09% | 0.98% | 5.56% | 11 |
| 5 | pepperstone | median | 13 | 53.85% | 1.6075 | 1.09% | 0.98% | 5.56% | 11 |
| 6 | pepperstone | p95 | 13 | 53.85% | 1.5949 | 1.07% | 0.98% | 5.56% | 11 |
| 7 | dukascopy | best_case | 12 | 58.33% | 1.6744 | 1.11% | 0.49% | 11.11% | 7 |
| 8 | dukascopy | median | 12 | 58.33% | 1.6348 | 1.02% | 0.53% | 11.11% | 7 |
| 9 | dukascopy | p95 | 12 | 50.00% | 1.5736 | 0.93% | 0.55% | 11.11% | 7 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 6/9 |
| At least 40 trades per cell | FAIL, 0/9 |
| Max zero-trade months <= 3 | FAIL, max 11 |
| Cross-broker persistence | FAIL, Capital.com is materially negative |
| Concentration | FAIL, sample is too sparse and top-trade concentration is high |

## Interpretation

This is the most interesting independent clue from the latest run because Pepperstone and Dukascopy both preserved PF above 1.30 across costs. The failure is just as important: Capital.com rejects the behavior and the event overlap is too rare.

Do not tune v0. A future version would need a broader but mechanically different event definition, not simple threshold loosening. The problem to solve is activity and Capital.com transfer without destroying the two-broker PF clue.

## Evidence

- Hypothesis: `docs/hypothesis_h4_gld_btc_vol_flow_reversal_v0.md`
- Registration: `outputs/reports/h4_gld_btc_vol_flow_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_gld_btc_vol_flow_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_gld_btc_vol_flow_reversal_v0/`

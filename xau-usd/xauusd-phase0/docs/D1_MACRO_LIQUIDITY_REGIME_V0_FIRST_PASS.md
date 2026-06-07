# D1 Macro Liquidity Regime v0 First Pass

Generated: 2026-06-07

Expert: `d1_macro_liquidity_regime_v0`
Hypothesis SHA256: `fec127f1a73af394e362908fab2d38e9e52436eca7cebe2144a6600a7ad12bee`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The official-FRED liquidity regime idea did not produce cross-broker edge. It used slower D1 macro conditions with H4 confirmation and generated enough trades for Dukascopy, but every broker/cost cell finished below PF 1.0. Capital.com was nearly flat but negative, Pepperstone was clearly negative, and Dukascopy weakened further as costs increased.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 25 | 40.00% | 0.9927 | -0.05% | 3.36% | 8.33% | 26 |
| 2 | capital_com | median | 25 | 40.00% | 0.9927 | -0.05% | 3.36% | 8.33% | 26 |
| 3 | capital_com | p95 | 25 | 40.00% | 0.9907 | -0.06% | 3.38% | 8.33% | 26 |
| 4 | pepperstone | best_case | 30 | 30.00% | 0.5267 | -4.18% | 5.09% | 25.00% | 17 |
| 5 | pepperstone | median | 30 | 30.00% | 0.5267 | -4.18% | 5.09% | 25.00% | 17 |
| 6 | pepperstone | p95 | 30 | 30.00% | 0.5219 | -4.24% | 5.14% | 25.00% | 17 |
| 7 | dukascopy | best_case | 44 | 34.09% | 0.9235 | -0.96% | 3.49% | 27.78% | 8 |
| 8 | dukascopy | median | 44 | 34.09% | 0.8881 | -1.38% | 3.82% | 27.78% | 8 |
| 9 | dukascopy | p95 | 44 | 34.09% | 0.8451 | -1.92% | 4.30% | 27.78% | 8 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 3/9 |
| Max zero-trade months <= 3 | FAIL, max 26 |
| Cross-broker persistence | FAIL, no broker reached PF 1.0 across costs |
| Concentration | FAIL context, net losing ledgers show 100% largest/top-5 concentration |

## Interpretation

The macro-liquidity regime was worth testing because it was slower, data-class independent, and not another retail-spread-sensitive M5 retest variant. The result says the official WALCL plus broad-dollar regime is not enough to define a tradable XAU behavior with H4 confirmation.

Do not tune v0. Any revisit needs a materially different mechanism, such as a distinct liquidity source, explicit BTC/crypto liquidity stress, or separate event-window definition, not minor threshold edits around this WALCL/DTWEXBGS regime.

## Evidence

- Hypothesis: `docs/hypothesis_d1_macro_liquidity_regime_v0.md`
- Registration: `outputs/reports/d1_macro_liquidity_regime_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/d1_macro_liquidity_regime_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/d1_macro_liquidity_regime_v0/`

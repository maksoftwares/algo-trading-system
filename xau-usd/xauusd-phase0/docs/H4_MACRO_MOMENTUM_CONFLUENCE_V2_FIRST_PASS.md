# H4 Macro Momentum Confluence v2 First Pass

Generated: 2026-06-07

Expert: `h4_macro_momentum_confluence_v2`
Hypothesis SHA256: `42786e87e558d7f73438fd7d63bd667d67be38423e631a2a14b322b0ac0494db`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v2 without tuning.

v2 preserved stricter macro evidence and broadened only H4 execution, but it did not become a worthy EA. It improved activity versus v0, yet still produced only 20 to 55 trades per cell and only one cell reached PF above 1.30.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 26 | 46.15% | 1.0713 | 0.37% | 1.30% | 11.11% | 7 |
| 2 | capital_com | median | 26 | 46.15% | 1.0713 | 0.37% | 1.30% | 11.11% | 7 |
| 3 | capital_com | p95 | 26 | 46.15% | 1.0825 | 0.43% | 1.30% | 11.11% | 7 |
| 4 | pepperstone | best_case | 20 | 50.00% | 1.2811 | 1.21% | 2.26% | 11.11% | 6 |
| 5 | pepperstone | median | 20 | 50.00% | 1.2811 | 1.21% | 2.26% | 11.11% | 6 |
| 6 | pepperstone | p95 | 20 | 50.00% | 1.2746 | 1.18% | 2.27% | 11.11% | 6 |
| 7 | dukascopy | best_case | 55 | 49.09% | 1.4242 | 4.70% | 2.71% | 25.00% | 5 |
| 8 | dukascopy | median | 55 | 49.09% | 1.2962 | 3.27% | 2.61% | 25.00% | 5 |
| 9 | dukascopy | p95 | 55 | 49.09% | 1.2627 | 2.78% | 2.67% | 27.78% | 5 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 1/9 |
| At least 40 trades per cell | FAIL, 3/9 |
| Max zero-trade months <= 3 | FAIL, max 7 |
| Cross-broker persistence | FAIL, only Dukascopy best-case reached PF threshold |
| Concentration | FAIL, Capital.com/Pepperstone concentration remains extreme |

## Interpretation

v2 confirms that broadening H4 execution while keeping strict macro evidence is less destructive than v1, but still not enough. The v0 sparse PF clue remains the cleanest signal; v2 does not earn deeper gates.

Do not tune v2. A separate hypothesis can test whether the D1 confirmation layer is over-filtering otherwise useful strict-macro H4 pullback/reclaim signals.

## Evidence

- Hypothesis: `docs/hypothesis_h4_macro_momentum_confluence_v2.md`
- Registration: `outputs/reports/h4_macro_momentum_confluence_v2_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_macro_momentum_confluence_v2_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_macro_momentum_confluence_v2/`

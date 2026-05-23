# Symbol-Normalized Round Retest v0 Research Result

Status: `PROVISIONAL_PASS_PENDING_GATE9`

Generated: 2026-05-23

## Decision

`symbol_normalized_round_retest_v0` passed the automated research gates run so far and improves the prior `round_number_retest_v0` weakness by producing non-zero EURUSD and USDJPY transfer evidence.

It is not an approved EA yet.

Reasons:

- Manual Gate 9 adversarial review is still pending: 0/120 sampled losing trades reviewed.
- The candidate remains same-family with `breakout_retest`; it is a symbol-scaled breakout-retest variant, not true diversification.
- `breakout_retest` remains the D2 Reality Check family winner.

## Hypothesis Lock

| Field | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_symbol_normalized_round_retest_v0.md` |
| Registration report | `outputs/reports/symbol_normalized_round_retest_v0_research_hypothesis_registration.md` |
| SHA256 | `49578289ffd65ce6974d3581ce309646d0232fc6ea36d156b450e9a64f3033f2` |
| Research smoke | PASS |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 3,837 | 1.486 | 8,870.90 | 10.52 | 49.57% |
| 2 | capital_com | median | 3,837 | 1.486 | 8,870.90 | 10.52 | 49.57% |
| 3 | capital_com | p95 | 3,837 | 1.351 | 3,142.42 | 11.81 | 49.57% |
| 4 | pepperstone | best_case | 5,497 | 1.560 | 52,007.03 | 10.12 | 49.30% |
| 5 | pepperstone | median | 5,497 | 1.560 | 52,007.03 | 10.12 | 49.30% |
| 6 | pepperstone | p95 | 5,497 | 1.472 | 21,093.97 | 11.13 | 49.30% |
| 7 | dukascopy | best_case | 6,462 | 1.469 | 240,669.03 | 9.01 | 49.83% |
| 8 | dukascopy | median | 6,462 | 1.469 | 240,669.03 | 9.01 | 49.83% |
| 9 | dukascopy | p95 | 6,462 | 1.421 | 94,796.53 | 11.21 | 49.83% |

Matrix gate summary:

| Gate | Observed | Status |
| --- | --- | --- |
| PF >= 1.30 cells | 9/9 | PASS |
| Minimum cell trades | 3,837 | PASS |
| Max drawdown | 11.81% | PASS |
| Cost sensitivity | P95 cells remain above PF threshold | PASS |

## Decile Persistence

| Metric | Value |
| --- | ---: |
| Deciles passed | 10/10 |
| PF range | 1.371 to 1.558 |
| Min decile trades | 1,030 |
| Max decile trades | 3,127 |

## Multisymbol Transfer

| Symbol | Trades | PF | Total Return % | Max DD % |
| --- | ---: | ---: | ---: | ---: |
| EURUSD | 12,260 | 1.298 | 7,225,025.75 | 12.72 |
| USDJPY | 14,380 | 1.559 | 214,357,758.92 | 12.00 |

This is materially better than `round_number_retest_v0`, which produced 0 EURUSD trades. The candidate still remains same-family because the edge mechanism is breakout-retest through public levels.

## Intrabar Ambiguity

| Metric | Value |
| --- | ---: |
| Matrix trades inspected | 47,388 |
| Ambiguous exits | 198 |
| Ambiguous exit rate | 0.42% |
| Same-timestamp entry/exit trades | 0 |
| Adverse-first PF | 1.47287 |

## Gate 9

| Metric | Value |
| --- | --- |
| Review packet | `outputs/adversarial_review/symbol_normalized_round_retest_v0_losing_trades_review.csv` |
| Sampled losing trades | 120 |
| Reviewed trades | 0 |
| Logic gaps | n/a |
| Status | PENDING |

## Reality Check Context

After adding this candidate, the full-universe D2 rerun remained PASS:

| Metric | Value |
| --- | --- |
| Winner | `breakout_retest` |
| White Reality Check p-value | 0.0200 |
| Max pairwise SPA p-value | 0.0326 |
| Candidate panel | 24 non-empty matrix-ledger candidates |

## Next Action

Complete Gate 9 manual adversarial review before treating this candidate as approved. In parallel, continue searching for a more independent non-breakout-retest behavior family.

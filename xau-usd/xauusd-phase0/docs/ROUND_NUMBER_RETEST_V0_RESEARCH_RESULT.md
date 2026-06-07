# Round Number Retest v0 Research Result

Date: 2026-05-23

## Current Verdict

`round_number_retest_v0` is `APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY`.

It is the first new candidate after `swing_breakout_retest_v0` to pass the 9-cell matrix and decile persistence gates. Gate 9 now scores PASS with 120 / 120 sampled losing trades reviewed and 0 logic gaps.

This candidate should be treated as same-family with `breakout_retest` until correlation and paper-mode evidence prove otherwise. It is a different level source, not a different execution premise.

## Gate Summary

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 9 of 9 cells | PASS |
| Minimum trade count | At least 40 trades per matrix cell | 3837 to 6462 trades | PASS |
| Drawdown/return safety | DD <= 30%, total return >= -25% | All cells inside limits | PASS |
| Decile persistence | PF > 1.0 in at least 8 of 10 deciles | 10 of 10 deciles | PASS |
| Multisymbol consistency | EURUSD and USDJPY PF >= 0.90, or XAU-specific defense | EURUSD 0 trades, USDJPY PF 1.435 | PASS_WITH_XAU_SPECIFIC_NOTE |
| Intrabar ambiguity | Low material ambiguity under adverse-first | 198 / 47,388 trades, 0.42% | PASS |
| Gate 9 adversarial review | Logic-gap losses <= 25% | 120 / 120 reviewed, 0 logic gaps | PASS |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 3837 | 1.486 | 8870.900 | 10.515 | 49.57% |
| 2 | capital_com | median | 3837 | 1.486 | 8870.900 | 10.515 | 49.57% |
| 3 | capital_com | p95 | 3837 | 1.351 | 3142.422 | 11.810 | 49.57% |
| 4 | pepperstone | best_case | 5497 | 1.560 | 52007.032 | 10.117 | 49.30% |
| 5 | pepperstone | median | 5497 | 1.560 | 52007.032 | 10.117 | 49.30% |
| 6 | pepperstone | p95 | 5497 | 1.472 | 21093.970 | 11.126 | 49.30% |
| 7 | dukascopy | best_case | 6462 | 1.469 | 240669.027 | 9.008 | 49.83% |
| 8 | dukascopy | median | 6462 | 1.469 | 240669.027 | 9.008 | 49.83% |
| 9 | dukascopy | p95 | 6462 | 1.421 | 94796.527 | 11.213 | 49.83% |

## Decile Summary

| Decile | Trades | Profit Factor | Status |
| ---: | ---: | ---: | --- |
| 1 | 1515 | 1.489 | PASS |
| 2 | 1120 | 1.384 | PASS |
| 3 | 1030 | 1.437 | PASS |
| 4 | 1191 | 1.543 | PASS |
| 5 | 2145 | 1.467 | PASS |
| 6 | 1997 | 1.371 | PASS |
| 7 | 1856 | 1.484 | PASS |
| 8 | 1922 | 1.407 | PASS |
| 9 | 2034 | 1.557 | PASS |
| 10 | 3127 | 1.558 | PASS |

## Multisymbol Note

The EURUSD multisymbol run produced zero trades because the v0 definition uses XAU-style absolute 10/25/50 dollar handles. That is not a valid universal FX round-number definition. USDJPY did pass with PF 1.435.

This means the candidate is XAU-specific unless a future v1 hypothesis pre-registers symbol-normalized handle increments before testing. Do not count this result as cross-asset diversification.

## Intrabar Note

Adverse-first intrabar ambiguity is low:

| Metric | Value |
| --- | ---: |
| Total trades inspected | 47,388 |
| Ambiguous exit trades | 198 |
| Ambiguous exit rate | 0.42% |
| Same-timestamp entry/exit trades | 0 |
| PF under adverse-first | 1.47287 |

## Decision

Gate 9 passed for `round_number_retest_v0`.

The Gate 9 review was completed as a Codex packet-level mechanical review on 2026-06-07. The CSV notes explicitly state this was not owner chart-by-chart attestation.

The candidate is now `APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY`, not independent diversification. Do not add it to execution planning while the family remains cost-suspended. It does not authorize live execution, paper execution, `OrderSend`, `CTrade`, or position management.

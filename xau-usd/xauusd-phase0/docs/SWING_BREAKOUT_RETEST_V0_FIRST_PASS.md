# Swing Breakout Retest v0 First-Pass Result

Date: 2026-05-22

## Verdict

`swing_breakout_retest_v0` is `DEEP_GATES_PASS_PENDING_MANUAL_ADVERSARIAL_REVIEW`.

This is the first extended-bench candidate after `breakout_retest` to survive the real 9-cell matrix, decile persistence, multisymbol consistency, and intrabar ambiguity checks. It is not an approved future expert yet because the adversarial losing-trade packet still needs manual review.

Important qualification: this candidate is same-family with the already approved `breakout_retest` expert. It reduces concentration risk inside the breakout-retest family, but it does not provide fully independent behavior.

## Gate Result

| Gate | Required | Observed | Status |
| --- | --- | --- | --- |
| Matrix PF coverage | PF >= 1.30 in at least 7 of 9 cells | 7 of 9 cells | PASS |
| Minimum trade count | At least 40 trades per matrix cell | 6,281 to 6,600 trades | PASS |
| Decile persistence | PF > 1.0 in at least 8 of 10 deciles | 10 of 10 deciles | PASS |
| Decile concentration | No decile PF above 2x median | Max/median PF = 1.09x | PASS |
| Multisymbol consistency | EURUSD and USDJPY PF >= 0.90 | EURUSD 1.375, USDJPY 1.668 | PASS |
| Intrabar ambiguity | Must not be material enough to explain the edge | 342 of 57,897 trades, 0.59% | PASS_REVIEW_NOTE |
| Adversarial review | Logic-gap losses <= 25% | 0 of 120 reviewed | PENDING |
| Approval status | Full Phase 0 pass required | Manual adversarial pending | NOT_APPROVED |

## Matrix Summary

| Cell | Broker | Cost Model | Trades | Profit Factor | Total Return % | Max DD % | Win Rate |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 6,281 | 1.433 | 70,304.042 | 9.887 | 48.53% |
| 2 | capital_com | median | 6,281 | 1.433 | 70,304.042 | 9.887 | 48.53% |
| 3 | capital_com | p95 | 6,281 | 1.268 | 8,610.584 | 11.682 | 48.53% |
| 4 | pepperstone | best_case | 6,418 | 1.316 | 27,573.693 | 13.454 | 47.18% |
| 5 | pepperstone | median | 6,418 | 1.316 | 27,573.693 | 13.454 | 47.18% |
| 6 | pepperstone | p95 | 6,418 | 1.240 | 6,261.092 | 16.274 | 47.18% |
| 7 | dukascopy | best_case | 6,600 | 1.493 | 131,375.106 | 8.480 | 48.89% |
| 8 | dukascopy | median | 6,600 | 1.493 | 131,368.415 | 8.480 | 48.89% |
| 9 | dukascopy | p95 | 6,600 | 1.423 | 38,949.793 | 9.595 | 48.89% |

## Deep-Gate Summary

| Check | Output | Key Result |
| --- | --- | --- |
| Deciles | `outputs/decile_results/swing_breakout_retest_v0_decile_results.csv` | 10/10 deciles passed; median PF 1.450 |
| Multisymbol | `outputs/multisymbol_results/swing_breakout_retest_v0_multisymbol_summary.csv` | EURUSD PF 1.375; USDJPY PF 1.668 |
| Intrabar | `outputs/reports/swing_breakout_retest_v0_intrabar_ambiguity_report.md` | 0.59% ambiguous exits; adverse-first PF 1.433 |
| Adversarial packet | `outputs/adversarial_review/swing_breakout_retest_v0_losing_trades_review.csv` | 120 sampled losing trades selected from 29,988 losses |
| Adversarial score | `outputs/adversarial_review/swing_breakout_retest_v0_adversarial_score.md` | PENDING; 0/120 manually reviewed |

## Decision

Keep `swing_breakout_retest_v0` as the next valid research candidate, but do not promote it to approved future expert until Gate 9 manual adversarial review is complete.

Next required manual step:

1. Review `outputs/adversarial_review/swing_breakout_retest_v0_losing_trades_review.csv`.
2. Fill `manual_failure_class`, `manual_notes`, `reviewer`, and `reviewed_at_utc` for all 120 rows.
3. Run `phase0 score-research-adversarial-review --expert swing_breakout_retest_v0 --hypothesis-file docs/hypothesis_swing_breakout_retest_v0.md`.
4. Promote only if logic-gap failures are <= 25%.

Do not tune `swing_breakout_retest_v0` in place. Any change to breakout distance, retest tolerance, stop offset, target, session, volatility, or news filters requires a new versioned hypothesis and fresh hash registration.

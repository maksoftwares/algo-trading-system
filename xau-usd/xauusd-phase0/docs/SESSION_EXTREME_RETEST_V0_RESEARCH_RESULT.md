# Session Extreme Retest v0 Research Result

Status: APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY
Generated: 2026-05-23

## Summary

`session_extreme_retest_v0` was registered, hash-locked, smoke-tested, and run through the real research matrix, decile persistence, multisymbol check, intrabar ambiguity report, and adversarial packet generation.

This is an approved future expert candidate in the same-family level-and-pullback group after Gate 9 scored PASS with 120 / 120 sampled losing trades reviewed and 0 logic gaps.

## Classification

| Field | Value |
| --- | --- |
| Candidate | `session_extreme_retest_v0` |
| Family | Same-family breakout/retest variant |
| Diversification value | Not true independent diversification |
| Current status | `APPROVED_FUTURE_EXPERT_CANDIDATE_SAME_FAMILY` |
| Approval boundary | Same-family and cost-suspended; not authorized for live/paper execution |

## Matrix Result

| Metric | Result |
| --- | ---: |
| Matrix cells completed | 9 / 9 |
| PF passing cells >= 1.30 | 9 / 9 |
| Total trades across cells | 23,727 |
| Min cell trades | 2,331 |
| Max cell trades | 2,898 |
| PF range | 1.328 to 1.596 |

## Decile Result

| Metric | Result |
| --- | ---: |
| Passing deciles | 10 / 10 |
| Decile PF range | 1.321 to 1.657 |
| Decile trade-count range | 643 to 805 |

## Multisymbol Result

| Symbol | Trades | PF | Total Return | Max DD |
| --- | ---: | ---: | ---: | ---: |
| EURUSD | 8,354 | 1.181 | 6,920.37% | 23.28% |
| USDJPY | 7,095 | 1.236 | 1,595.35% | 14.12% |

## Intrabar Ambiguity

| Metric | Result |
| --- | ---: |
| Matrix trades inspected | 23,727 |
| Ambiguous exit trades | 240 |
| Ambiguous exit rate | 1.01% |
| Same-timestamp entry/exit trades | 0 |
| Adverse-first PF | 1.514 |

## Gate 9

| Metric | Result |
| --- | ---: |
| Sampled losing trades | 120 |
| Reviewed trades | 120 |
| Logic gaps | 0 |
| Logic-gap pct | 0% |
| Status | PASS |

## Verdict

This candidate is approved as a future expert candidate in the same-family level-and-pullback group. It passed automated evidence gates strongly and Gate 9 now scores PASS.

The Gate 9 review was completed as a Codex packet-level mechanical review on 2026-06-07. The CSV notes explicitly state this was not owner chart-by-chart attestation.

Because its mechanics are still breakout/retest-based, it should not be used to claim true portfolio diversification. It also remains cost-suspended with the family and does not authorize live execution, paper execution, `OrderSend`, `CTrade`, or position management.

## Artifacts

- Hypothesis: `docs/hypothesis_session_extreme_retest_v0.md`
- Smoke report: `outputs/reports/session_extreme_retest_v0_research_smoke.md`
- Matrix folder: `outputs/matrix_results/session_extreme_retest_v0/`
- Deciles: `outputs/decile_results/session_extreme_retest_v0_decile_results.csv`
- Multisymbol: `outputs/multisymbol_results/session_extreme_retest_v0_multisymbol_summary.csv`
- Intrabar: `outputs/reports/session_extreme_retest_v0_intrabar_ambiguity_report.md`
- Gate 9 packet: `outputs/adversarial_review/session_extreme_retest_v0_losing_trades_review.csv`
- Gate 9 score: `outputs/adversarial_review/session_extreme_retest_v0_adversarial_score.md`
- Gate 9 review note: `docs/SESSION_EXTREME_RETEST_V0_GATE9_REVIEW.md`

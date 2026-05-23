# Session Extreme Retest v0 Research Result

Status: PROVISIONAL_PASS_PENDING_GATE9
Generated: 2026-05-23

## Summary

`session_extreme_retest_v0` was registered, hash-locked, smoke-tested, and run through the real research matrix, decile persistence, multisymbol check, intrabar ambiguity report, and adversarial packet generation.

This is a promising new candidate, but it is not approved yet. Gate 9 manual adversarial review is still pending with 0 / 120 sampled losing trades reviewed.

## Classification

| Field | Value |
| --- | --- |
| Candidate | `session_extreme_retest_v0` |
| Family | Same-family breakout/retest variant |
| Diversification value | Not true independent diversification |
| Current status | `PROVISIONAL_PASS_PENDING_GATE9` |
| Approval boundary | Not approved for Phase 1/Phase 2 until Gate 9 passes |

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
| Reviewed trades | 0 |
| Logic gaps | 0 |
| Logic-gap pct | n/a |
| Status | PENDING |

## Verdict

This candidate is found as a provisional candidate. It passed automated evidence gates strongly, but it must remain blocked from approval until manual Gate 9 review is completed. Because its mechanics are still breakout/retest-based, it should not be used to claim true portfolio diversification.

## Artifacts

- Hypothesis: `docs/hypothesis_session_extreme_retest_v0.md`
- Smoke report: `outputs/reports/session_extreme_retest_v0_research_smoke.md`
- Matrix folder: `outputs/matrix_results/session_extreme_retest_v0/`
- Deciles: `outputs/decile_results/session_extreme_retest_v0_decile_results.csv`
- Multisymbol: `outputs/multisymbol_results/session_extreme_retest_v0_multisymbol_summary.csv`
- Intrabar: `outputs/reports/session_extreme_retest_v0_intrabar_ambiguity_report.md`
- Gate 9 packet: `outputs/adversarial_review/session_extreme_retest_v0_losing_trades_review.csv`
- Gate 9 score: `outputs/adversarial_review/session_extreme_retest_v0_adversarial_score.md`

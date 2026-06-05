# WR50 Reporting Policy

Document date: 2026-06-04

WR50 reporting is research-only. Reports must not describe WR50 results as canonical Phase 2 evidence, live trading evidence, or diversification evidence.

## Minimum Review Gates

Do not judge an EA before enough closed trades exist:

| Gate | Required value |
| --- | ---: |
| Minimum closed trades | 100 |
| Preferred closed trades | 200+ |
| Win rate | >= 50% |
| Profit factor | >= 1.20 |
| Net expectancy after measured cost | >= +0.15R |
| Single trade contribution | <= 10% of net PnL |
| Top 5 trade contribution | <= 40% of net PnL |

Every report must include attribution by EA, magic, comment, experiment id, run id, symbol, and session bucket.

## Status Labels

| Outcome | Label |
| --- | --- |
| Sample too small | `REVIEW_READY_LOW_SAMPLE` |
| Gates pass after minimum sample | `CANDIDATE_FOR_PHASE0R_REVALIDATION` |
| Gates fail | `REJECTED_EXPERIMENTAL` |
| Logs incomplete | `INVALID_ATTRIBUTION` |

Passing WR50 demo gates only allows a future Phase 0R hypothesis discussion. It does not authorize canonical inclusion or live trading.


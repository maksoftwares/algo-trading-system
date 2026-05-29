# H1 XLP/XLY Consumer Rotation Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_xlp_xly_consumer_rotation_followthrough_v0`
Hypothesis: `docs/hypothesis_h1_xlp_xly_consumer_rotation_followthrough_v0.md`
Registered SHA256: `b6b76e153469132a3593dc9ab4e58f9b37a6078a297876579da9ef73df023c2b`

## Decision

Reject v0 without tuning.

The candidate reached the minimum trade-count floor in all 9 cells, but 0/9 cells reached PF >= 1.30. Capital.com was positive but below threshold, Pepperstone was roughly flat to slightly negative under P95 cost, and Dukascopy was materially negative. This is a cross-venue expectancy failure.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Max zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 163 | 48.47% | 1.2564 | 10.73% | 2 | 4.16% |
| 2 | capital_com | median | 163 | 48.47% | 1.2564 | 10.73% | 2 | 4.16% |
| 3 | capital_com | p95 | 163 | 48.47% | 1.2256 | 9.45% | 2 | 4.39% |
| 4 | pepperstone | best_case | 142 | 42.25% | 1.0092 | 0.34% | 3 | 4.72% |
| 5 | pepperstone | median | 142 | 42.25% | 1.0092 | 0.34% | 3 | 4.72% |
| 6 | pepperstone | p95 | 142 | 42.25% | 0.9930 | -0.26% | 3 | 4.89% |
| 7 | dukascopy | best_case | 158 | 36.08% | 0.7176 | -11.85% | 1 | 16.20% |
| 8 | dukascopy | median | 158 | 36.08% | 0.6896 | -12.93% | 1 | 16.76% |
| 9 | dukascopy | p95 | 158 | 35.44% | 0.6558 | -14.36% | 1 | 17.95% |

## Gate Snapshot

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total cost-cell trades | 1,389 | Review context | PASS |

## Interpretation

This tested whether shifted public XLP/XLY consumer defensive-versus-discretionary rotation could identify XAU H1 follow-through. The effect did not persist across broker windows, and the negative Dukascopy block rejects the thesis for v0.

Do not tune this v0. A future consumer-rotation lane would need a new versioned hypothesis and a materially different input thesis.

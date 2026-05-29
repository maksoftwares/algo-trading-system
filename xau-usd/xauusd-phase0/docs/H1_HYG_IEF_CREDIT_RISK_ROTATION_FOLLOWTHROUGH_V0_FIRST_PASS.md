# H1 HYG/IEF Credit-Risk Rotation Follow-Through v0 First Pass

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Expert: `h1_hyg_ief_credit_risk_rotation_followthrough_v0`
Hypothesis: `docs/hypothesis_h1_hyg_ief_credit_risk_rotation_followthrough_v0.md`
Registered SHA256: `f9b1c6af4ea2a060affeb841bf8abc3bd5e8e85234f5c3387e671246ebb6d039`

## Decision

Reject v0 without tuning.

The candidate reached the minimum trade-count floor in all 9 cells, but 0/9 cells reached PF >= 1.30. Capital.com was positive but below threshold, Pepperstone was weakly positive below threshold, and Dukascopy was negative across cost models. This is a cross-venue expectancy failure.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return | Max zero months | Max DD |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 153 | 47.06% | 1.2212 | 8.87% | 2 | 4.12% |
| 2 | capital_com | median | 153 | 47.06% | 1.2212 | 8.87% | 2 | 4.12% |
| 3 | capital_com | p95 | 153 | 47.06% | 1.1886 | 7.60% | 2 | 4.35% |
| 4 | pepperstone | best_case | 118 | 42.37% | 1.0862 | 2.71% | 1 | 5.58% |
| 5 | pepperstone | median | 118 | 42.37% | 1.0862 | 2.71% | 1 | 5.58% |
| 6 | pepperstone | p95 | 118 | 42.37% | 1.0609 | 1.92% | 1 | 5.66% |
| 7 | dukascopy | best_case | 158 | 38.61% | 0.8320 | -7.16% | 1 | 7.90% |
| 8 | dukascopy | median | 158 | 38.61% | 0.8122 | -8.01% | 1 | 8.58% |
| 9 | dukascopy | p95 | 158 | 38.61% | 0.7769 | -9.47% | 1 | 9.83% |

## Gate Snapshot

| Gate | Observed | Required | Result |
| --- | ---: | ---: | --- |
| PF >= 1.30 cells | 0/9 | 7/9 | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total cost-cell trades | 1,287 | Review context | PASS |

## Interpretation

This tested whether shifted public HYG/IEF credit-risk rotation could identify XAU H1 follow-through during risk-off or risk-on credit pressure. The effect was not persistent across broker windows, and the negative Dukascopy block rejects the thesis for v0.

Do not tune this v0. Any future credit-risk lane must use a new versioned hypothesis and a better credit input, such as primary credit-spread, CDS, futures, or intraday rates/credit data.

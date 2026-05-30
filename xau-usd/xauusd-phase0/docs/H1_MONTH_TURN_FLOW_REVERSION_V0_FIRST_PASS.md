# H1 Month-Turn Flow Reversion v0 First Pass

Status: REJECTED_FIRST_PASS
Hypothesis: `docs/hypothesis_h1_month_turn_flow_reversion_v0.md`
Research hash: `9aa8927fc329888740ec5b64f7c4e7062386c5b1d727ff16b5887a08427d7e55`
Data source: H1 XAUUSD broker bars with month-end / month-start calendar filters

## Decision

Reject v0 without tuning.

This candidate tested whether month-end and month-start pressure in XAU tends to unwind after an overextended H1 move. It generated enough trades in every broker and cost cell, but failed the first hard expectancy gate with 0/9 PF cells >= 1.30. Dukascopy was positive, but not strong enough, and Capital.com/Pepperstone were negative or near flat after costs.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Capital.com | best | 79 | 41.77% | 0.8692 | -2.75% | 5.31% | 1 | FAIL |
| 2 | Capital.com | median | 79 | 41.77% | 0.8692 | -2.75% | 5.31% | 1 | FAIL |
| 3 | Capital.com | p95 | 79 | 41.77% | 0.8359 | -3.48% | 5.83% | 1 | FAIL |
| 4 | Pepperstone | best | 94 | 45.74% | 0.9928 | -0.18% | 6.52% | 2 | FAIL |
| 5 | Pepperstone | median | 94 | 45.74% | 0.9928 | -0.18% | 6.52% | 2 | FAIL |
| 6 | Pepperstone | p95 | 94 | 45.74% | 0.9758 | -0.59% | 6.62% | 2 | FAIL |
| 7 | Dukascopy | best | 87 | 51.72% | 1.2208 | +4.23% | 3.24% | 1 | FAIL |
| 8 | Dukascopy | median | 87 | 50.57% | 1.1933 | +3.71% | 3.45% | 1 | FAIL |
| 9 | Dukascopy | p95 | 87 | 50.57% | 1.1198 | +2.31% | 3.76% | 1 | FAIL |

## Gate Read

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| Matrix PF cells | 0/9 | >= 7/9 | FAIL |
| Trade-count cells | 9/9 | 9/9 with >= 40 trades | PASS |
| Total matrix trades | 780 | Informational | PASS |
| Max zero-trade months | 2 | <= 3 | PASS |
| Cross-broker portability | Dukascopy-only positive pocket, Capital.com/Pepperstone non-viable | Robust across windows | FAIL |
| Cost sensitivity | P95 cells remain below threshold | P95 should not break the edge | FAIL |

## Interpretation

The month-turn reversion idea has a small broker-specific positive pocket, but not enough strength or portability to justify promotion. This is useful negative evidence: the paired month-turn continuation and reversion hypotheses both failed first-pass, so the current H1 calendar-flow lane should be retired unless a new data source or materially different mechanism is pre-registered.

## Next Action

Do not tune this v0 candidate. Continue the independent search in a different mechanism. This result does not alter approved/provisional EA status, Phase 1 dry-run permissions, Phase 2 readiness, demo observer authority, or trade permissions.

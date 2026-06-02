# H4/D1 Contraction Trend Continuation v0 First Pass

Generated: 2026-06-02
Status: `REJECTED_FIRST_PASS`

## Decision

Reject `h4_d1_contraction_trend_continuation_v0` without tuning.

This was a fresh Phase 0R lower-cost candidate, not a breakout-retest variant. It was SHA256-locked before implementation, passed the measured-cost structural precheck, passed synthetic smoke, and produced enough trades in all 9 real-data matrix cells. It failed because every matrix cell had PF below 1.0, so there is no edge-quality basis for deciles, multisymbol validation, adversarial review, demo observation, or EA coding.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Single Trade | Top 5 | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | capital_com | best_case | 82 | 35.37% | 0.8970 | -2.49% | 3.99% | 3 | 100.00% | 100.00% | FAIL |
| 2 | capital_com | median | 82 | 35.37% | 0.8970 | -2.49% | 3.99% | 3 | 100.00% | 100.00% | FAIL |
| 3 | capital_com | p95 | 82 | 35.37% | 0.8856 | -2.77% | 4.19% | 3 | 100.00% | 100.00% | FAIL |
| 4 | pepperstone | best_case | 50 | 28.00% | 0.6294 | -5.49% | 7.70% | 5 | 100.00% | 100.00% | FAIL |
| 5 | pepperstone | median | 50 | 28.00% | 0.6294 | -5.49% | 7.70% | 5 | 100.00% | 100.00% | FAIL |
| 6 | pepperstone | p95 | 50 | 28.00% | 0.6280 | -5.51% | 7.69% | 5 | 100.00% | 100.00% | FAIL |
| 7 | dukascopy | best_case | 87 | 33.33% | 0.8804 | -2.94% | 9.65% | 3 | 100.00% | 100.00% | FAIL |
| 8 | dukascopy | median | 87 | 33.33% | 0.8444 | -3.85% | 10.05% | 3 | 100.00% | 100.00% | FAIL |
| 9 | dukascopy | p95 | 87 | 33.33% | 0.8356 | -4.03% | 9.90% | 3 | 100.00% | 100.00% | FAIL |

## Gate Snapshot

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| PF cells >= 1.30 | 0/9 | >= 7/9 | FAIL |
| PF cells > 1.00 | 0/9 | Informational | FAIL |
| Trade-count cells >= 40 | 9/9 | 9/9 | PASS |
| Total matrix trades | 657 | Informational | PASS |
| Max zero-trade months | 5 | <= 3 | FAIL |
| Max drawdown | 10.05% | <= 30.00% | PASS |
| Worst total return | -5.51% | >= -25.00% | PASS |
| Largest single trade contribution | 100.00% | <= 10.00% | FAIL |
| Top-5 trade contribution | 100.00% | <= 40.00% | FAIL |
| Cost structure | P95 cost_R precheck 0.1765R | <= 0.3000R | PASS |

## Interpretation

The candidate did meet the wider-stop, lower-cost research objective structurally, but the market evidence was plainly negative. All broker/cost windows were unprofitable after costs. This is an edge failure, not a cost-budget or sample-size failure.

## Next Action

Do not proceed to deciles, multisymbol validation, intrabar review, adversarial review, EA coding, or demo observation for this version.

Do not tune `h4_d1_contraction_trend_continuation_v0` in place. Any future revisit needs a new versioned hypothesis, a new SHA256 lock, and a fresh first pass.

The next Phase 0R search should prefer a genuinely new information source. Two consecutive lower-cost OHLC-only H4/D1 contraction ideas have now failed first pass.

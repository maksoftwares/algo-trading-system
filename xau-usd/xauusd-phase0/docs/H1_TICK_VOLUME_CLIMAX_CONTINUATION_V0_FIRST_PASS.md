# H1 Tick-Volume Climax Continuation v0 First Pass

Status: REJECTED_FIRST_PASS
Hypothesis: `docs/hypothesis_h1_tick_volume_climax_continuation_v0.md`
Research hash: `d0a65532af37b6d93565142f6a95db374e0fbcd61827dae95d1b2ede255eb0b4`
Data source: H1 XAUUSD bar tick-count / volume fields from the normalized broker bar data

## Decision

Reject v0 without tuning.

This candidate tested whether the rejected tick-volume climax reversal should instead be interpreted as continuation. It generated enough trades in Capital.com and Pepperstone, but failed the hard matrix expectancy gate with 0/9 PF cells >= 1.30. Dukascopy produced zero qualifying trades, so the mechanism is not broker-portable in the current normalized data.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win Rate | PF | Return | Max DD | Zero Months | Result |
|---:|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Capital.com | best | 362 | 45.30% | 0.9195 | -5.83% | 10.71% | 0 | FAIL |
| 2 | Capital.com | median | 362 | 45.30% | 0.9195 | -5.83% | 10.71% | 0 | FAIL |
| 3 | Capital.com | p95 | 362 | 45.03% | 0.8991 | -7.33% | 11.88% | 0 | FAIL |
| 4 | Pepperstone | best | 371 | 45.55% | 1.0095 | +0.67% | 11.31% | 0 | FAIL |
| 5 | Pepperstone | median | 371 | 45.55% | 1.0095 | +0.67% | 11.31% | 0 | FAIL |
| 6 | Pepperstone | p95 | 371 | 45.55% | 1.0042 | +0.30% | 11.42% | 0 | FAIL |
| 7 | Dukascopy | best | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |
| 8 | Dukascopy | median | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |
| 9 | Dukascopy | p95 | 0 | 0.00% | 0.0000 | +0.00% | 0.00% | 36 | FAIL |

## Gate Read

| Gate | Observed | Required | Status |
|---|---:|---:|---|
| Matrix PF cells | 0/9 | >= 7/9 | FAIL |
| Trade-count cells | 6/9 | 9/9 with >= 40 trades | FAIL |
| Total matrix trades | 2,199 | Informational | PASS |
| Max zero-trade months | 36 | <= 3 | FAIL |
| Cross-broker portability | Dukascopy produced zero qualifying trades | Robust across windows | FAIL |
| Cost sensitivity | All PF values remain below threshold | P95 should not break the edge | FAIL |

## Interpretation

Participation-flow continuation is not a viable v0 independent EA candidate under the current bar/tick-count data. The idea was useful because it tested the opposite side of the failed participation-reversal thesis, but neither side produced a portable Phase 0 first pass.

## Next Action

Do not tune this v0 candidate. Continue the independent search in a different mechanism or with a materially higher-quality participation/order-flow data class. This result does not alter approved/provisional EA status, Phase 1 dry-run permissions, Phase 2 readiness, demo observer authority, or trade permissions.

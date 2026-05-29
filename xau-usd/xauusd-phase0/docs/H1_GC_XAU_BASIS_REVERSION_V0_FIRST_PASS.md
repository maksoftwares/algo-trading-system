# H1 GC/XAU Basis Reversion v0 First-Pass Result

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Hypothesis SHA256: eb901cea1eb18fb2ad1a57bb847729db3fe35ddc314756381d6f08521ace2ec2

## Summary

`h1_gc_xau_basis_reversion_v0` was registered, hash-locked, synthetic-smoke tested, and run through the real 9-cell research matrix without tuning.

This was an independent, non-level hypothesis using a shifted Yahoo `GC=F` daily futures proxy against broker XAUUSD D1/H1 bars. It tested whether prior-day GC/XAU divergence creates short-term H1 convergence pressure. The candidate produced enough trades, but it failed the core expectancy gate.

## Matrix Result

| Cell | Broker | Cost Model | Trades | Profit Factor | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 218 | 0.8700 | -7.94% | 11.63% | 5 |
| 2 | capital_com | median | 218 | 0.8700 | -7.94% | 11.63% | 5 |
| 3 | capital_com | p95 | 218 | 0.8443 | -9.53% | 12.28% | 5 |
| 4 | pepperstone | best_case | 238 | 1.0098 | 0.66% | 6.10% | 6 |
| 5 | pepperstone | median | 238 | 1.0098 | 0.66% | 6.10% | 6 |
| 6 | pepperstone | p95 | 238 | 0.9988 | -0.08% | 6.04% | 6 |
| 7 | dukascopy | best_case | 243 | 1.2626 | 16.80% | 5.38% | 4 |
| 8 | dukascopy | median | 243 | 1.2369 | 14.95% | 5.35% | 4 |
| 9 | dukascopy | p95 | 243 | 1.1614 | 10.06% | 5.95% | 4 |

## Gate Notes

| Gate | Result | Observed |
| --- | --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL | 0/9 cells |
| Trade count >= 40 per cell | PASS | 9/9 cells |
| Max zero-trade months <= 3 | FAIL | Max 6 |
| P95 / best-case PF >= 0.50 | PASS | 0.67 |
| Cross-broker persistence | FAIL | Dukascopy-only strength; Capital.com negative and Pepperstone flat |

## Verdict

Reject v0 without tuning.

The GC futures proxy remains a useful independent data class, but this specific convergence rule is not approved and must not be promoted into Phase 1, Phase 2, or demo attachment. Any future GC/XAU attempt must be a new versioned hypothesis with a clearly distinct mechanic and fresh SHA256 registration.

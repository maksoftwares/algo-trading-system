# H1 GC Momentum Pullback v0 First-Pass Result

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Hypothesis SHA256: a228055c8e5ee8fae1dc295a29ac98579d99fbffacc16a8356799d6df26aa6a1

## Summary

`h1_gc_momentum_pullback_v0` was registered, hash-locked, synthetic-smoke tested, and run through the real 9-cell research matrix without tuning.

This was an independent, non-level hypothesis using shifted Yahoo `GC=F` daily futures-proxy momentum to define direction, with XAUUSD H1 pullback candles used only for timing. It produced enough trades and acceptable activity, but failed the core expectancy gate decisively.

## Matrix Result

| Cell | Broker | Cost Model | Trades | Profit Factor | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 119 | 0.7814 | -6.96% | 8.61% | 1 |
| 2 | capital_com | median | 119 | 0.7814 | -6.96% | 8.61% | 1 |
| 3 | capital_com | p95 | 119 | 0.7638 | -7.55% | 9.10% | 1 |
| 4 | pepperstone | best_case | 117 | 1.1467 | 4.71% | 5.02% | 2 |
| 5 | pepperstone | median | 117 | 1.1467 | 4.71% | 5.02% | 2 |
| 6 | pepperstone | p95 | 117 | 1.1178 | 3.79% | 5.19% | 2 |
| 7 | dukascopy | best_case | 129 | 0.7863 | -7.49% | 8.58% | 1 |
| 8 | dukascopy | median | 129 | 0.7711 | -8.02% | 9.10% | 1 |
| 9 | dukascopy | p95 | 129 | 0.7209 | -9.81% | 10.64% | 1 |

## Gate Notes

| Gate | Result | Observed |
| --- | --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL | 0/9 cells |
| Trade count >= 40 per cell | PASS | 9/9 cells |
| Max zero-trade months <= 3 | PASS | Max 2 |
| P95 / best-case PF >= 0.50 | PASS | 0.63 |
| Cross-broker persistence | FAIL | Pepperstone-only positive PF below threshold; Capital.com and Dukascopy negative |

## Verdict

Reject v0 without tuning.

The GC futures proxy remains a useful independent data class, but this specific momentum-pullback expression is not approved and must not be promoted into Phase 1, Phase 2, or demo attachment. Any future GC momentum attempt must be a new versioned hypothesis with a clearly distinct mechanic and fresh SHA256 registration.

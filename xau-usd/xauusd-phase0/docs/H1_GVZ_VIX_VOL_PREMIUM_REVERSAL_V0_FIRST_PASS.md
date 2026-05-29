# H1 GVZ/VIX Vol-Premium Reversal v0 First-Pass Result

Date: 2026-05-29
Status: REJECTED_FIRST_PASS
Hypothesis SHA256: c4287838788c0e7a9859075e68cdbaa186407957226dadcc3b67be2773dc685b

## Summary

`h1_gvz_vix_vol_premium_reversal_v0` was registered, hash-locked, synthetic-smoke tested, and run through the real 9-cell research matrix without tuning.

This was an independent, non-level hypothesis using shifted FRED GVZCLS and VIXCLS data. It tested whether gold implied-volatility premium expansion versus broad equity implied volatility marks local XAUUSD H1 exhaustion. The candidate produced enough trades, but it failed the core expectancy gate decisively.

## Matrix Result

| Cell | Broker | Cost Model | Trades | Profit Factor | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 123 | 0.9550 | -1.50% | 8.99% | 6 |
| 2 | capital_com | median | 123 | 0.9550 | -1.50% | 8.99% | 6 |
| 3 | capital_com | p95 | 123 | 0.9362 | -2.13% | 9.37% | 6 |
| 4 | pepperstone | best_case | 187 | 1.2101 | 10.35% | 5.79% | 4 |
| 5 | pepperstone | median | 187 | 1.2101 | 10.35% | 5.79% | 4 |
| 6 | pepperstone | p95 | 187 | 1.1947 | 9.57% | 5.96% | 4 |
| 7 | dukascopy | best_case | 169 | 0.7909 | -9.53% | 10.83% | 6 |
| 8 | dukascopy | median | 169 | 0.7810 | -9.95% | 11.10% | 6 |
| 9 | dukascopy | p95 | 169 | 0.7376 | -11.83% | 12.07% | 6 |

## Gate Notes

| Gate | Result | Observed |
| --- | --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL | 0/9 cells |
| Trade count >= 40 per cell | PASS | 9/9 cells |
| Max zero-trade months <= 3 | FAIL | Max 6 |
| P95 / best-case PF >= 0.50 | PASS | 0.61 |
| Cross-broker persistence | FAIL | Pepperstone-only strength, Capital.com and Dukascopy negative |

## Verdict

Reject v0 without tuning.

The volatility-premium data class remains useful, but this reversal expression is not approved and must not be promoted into Phase 1, Phase 2, or demo attachment. Any future GVZ/VIX attempt must be a new versioned hypothesis with a clearly distinct mechanic and fresh SHA256 registration.

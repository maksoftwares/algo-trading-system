# H1 MOVE/VIX Bond-Vol Shock Reversal v0 First-Pass Result

Date: 2026-05-30
Status: REJECTED_FIRST_PASS
Hypothesis SHA256: 2b4db7b2163d79e90c841115c73c3a3db6805ac449f477b0940118cc1cb6ccfb
MOVE data SHA256: 1f86da62fbec6850b829bca2d7239b8fafbb2fa6c916f2a3337b1381979d267b

## Summary

`h1_move_vix_bond_vol_shock_reversal_v0` was registered, hash-locked, synthetic-smoke tested, and run through the real 9-cell research matrix without tuning.

This was an independent, non-level hypothesis using public Yahoo `^MOVE` bond-volatility data and shifted FRED VIXCLS data. It tested whether rates-volatility shocks relative to equity volatility mark local XAUUSD H1 exhaustion. The candidate did not reach enough trade frequency in all cells and failed the primary cross-cell PF gate.

## Matrix Result

| Cell | Broker | Cost Model | Trades | Win Rate | Profit Factor | Return | Max DD | Zero-Trade Months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 23 | 43.48% | 1.0297 | 0.18% | 2.35% | 14 |
| 2 | capital_com | median | 23 | 43.48% | 1.0297 | 0.18% | 2.35% | 14 |
| 3 | capital_com | p95 | 23 | 43.48% | 0.9937 | -0.04% | 2.38% | 14 |
| 4 | pepperstone | best_case | 70 | 42.86% | 1.0369 | 0.68% | 3.70% | 11 |
| 5 | pepperstone | median | 70 | 42.86% | 1.0369 | 0.68% | 3.70% | 11 |
| 6 | pepperstone | p95 | 70 | 42.86% | 1.0166 | 0.31% | 3.82% | 11 |
| 7 | dukascopy | best_case | 84 | 41.67% | 0.9851 | -0.32% | 5.43% | 5 |
| 8 | dukascopy | median | 84 | 41.67% | 0.9607 | -0.84% | 5.53% | 5 |
| 9 | dukascopy | p95 | 84 | 41.67% | 0.9144 | -1.85% | 5.89% | 5 |

## Gate Notes

| Gate | Result | Observed |
| --- | --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL | 0/9 cells |
| Trade count >= 40 per cell | FAIL | 6/9 cells |
| Max zero-trade months <= 3 | FAIL | Max 14 |
| Cross-broker persistence | FAIL | Pepperstone and Capital.com mildly positive below threshold; Dukascopy negative |
| Concentration | FAIL | Positive cells are dominated by a small number of trades |

## Verdict

Reject v0 without tuning.

The MOVE/VIX rates-volatility data class is now tested as a standalone reversal expression. The first pass does not justify Phase 1, Phase 2, or demo attachment. Any future rates-volatility attempt must be a new versioned hypothesis with a clearly distinct mechanic and fresh SHA256 registration.

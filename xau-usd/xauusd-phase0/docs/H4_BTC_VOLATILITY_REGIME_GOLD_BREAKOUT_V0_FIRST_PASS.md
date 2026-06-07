# H4 BTC Volatility Regime Gold Breakout v0 First Pass

Generated: 2026-06-07

Expert: `h4_btc_volatility_regime_gold_breakout_v0`
Hypothesis SHA256: `813bc9a8374bfc18d28343de557487d1666fd69acf89491f60d5746df7b8bec8`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The BTC volatility-regime hypothesis is a better clue than the raw BTC return-pressure family, but it is still not a worthy EA. Pepperstone passed PF in all three cost cells with low drawdown, while Capital.com was flat-negative and Dukascopy was negative across costs. This is broker-fragmented, not cross-broker persistent.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 56 | 48.21% | 0.9918 | -0.09% | 3.13% | 25.00% | 8 |
| 2 | capital_com | median | 56 | 48.21% | 0.9918 | -0.09% | 3.13% | 25.00% | 8 |
| 3 | capital_com | p95 | 56 | 48.21% | 0.9869 | -0.14% | 3.14% | 22.22% | 8 |
| 4 | pepperstone | best_case | 52 | 51.92% | 1.6783 | 4.16% | 1.10% | 19.44% | 3 |
| 5 | pepperstone | median | 52 | 51.92% | 1.6783 | 4.16% | 1.10% | 19.44% | 3 |
| 6 | pepperstone | p95 | 52 | 51.92% | 1.6604 | 4.08% | 1.10% | 19.44% | 3 |
| 7 | dukascopy | best_case | 40 | 35.00% | 0.7492 | -2.20% | 5.13% | 27.78% | 4 |
| 8 | dukascopy | median | 40 | 35.00% | 0.7277 | -2.40% | 5.36% | 27.78% | 4 |
| 9 | dukascopy | p95 | 40 | 35.00% | 0.7117 | -2.51% | 5.28% | 27.78% | 4 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| PF >= 1.30 in at least 7/9 cells | FAIL, 3/9 |
| At least 40 trades per cell | PASS, 9/9 |
| Max zero-trade months <= 3 | FAIL, max 8 |
| Cross-broker persistence | FAIL, Pepperstone-only PF threshold strength |
| Concentration | FAIL context, Capital.com and Dukascopy are net losing ledgers |

## Interpretation

This was materially different from the prior BTC attempts because BTC return direction was not the signal. The result suggests BTC volatility transitions can mark a real local XAU opportunity in one broker window, but the behavior does not transfer across broker histories.

Do not tune v0. If BTC is revisited, the next version should not lower these same thresholds. A materially different path would need additional crypto-market structure, such as BTC volatility plus funding/liquidity breadth, or a broker-robust XAU execution filter that explains why Dukascopy fails.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_volatility_regime_gold_breakout_v0.md`
- Registration: `outputs/reports/h4_btc_volatility_regime_gold_breakout_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_btc_volatility_regime_gold_breakout_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_volatility_regime_gold_breakout_v0/`

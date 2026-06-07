# H4 BTC Volatility Regime Gold Reversal v0 First Pass

Generated: 2026-06-07

Expert: `h4_btc_volatility_regime_gold_reversal_v0`
Hypothesis SHA256: `388fc20db0d5ba9f9c6c14729047a07ee387fb39292db93020e1b0939d2ddb2a`
Status: `REJECTED_FIRST_PASS`

## Verdict

Reject v0 without tuning.

The candidate passed the measured-cost structural precheck, focused unit test, hypothesis registration, and research smoke, but the real-data matrix did not produce an approval-worthy BTC EA. Capital.com was mildly positive below threshold, while Pepperstone and Dukascopy were negative across all cost cases.

## Matrix Summary

| Cell | Broker | Cost | Trades | Win rate | PF | Return % | Max DD % | Losing months % | Max zero months |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | capital_com | best_case | 38 | 47.37% | 1.1112 | 0.77% | 1.83% | 19.44% | 6 |
| 2 | capital_com | median | 38 | 47.37% | 1.1112 | 0.77% | 1.83% | 19.44% | 6 |
| 3 | capital_com | p95 | 38 | 47.37% | 1.0975 | 0.68% | 1.86% | 19.44% | 6 |
| 4 | pepperstone | best_case | 43 | 41.86% | 0.6196 | -2.94% | 3.61% | 30.56% | 4 |
| 5 | pepperstone | median | 43 | 41.86% | 0.6196 | -2.94% | 3.61% | 30.56% | 4 |
| 6 | pepperstone | p95 | 43 | 41.86% | 0.6146 | -2.98% | 3.66% | 30.56% | 4 |
| 7 | dukascopy | best_case | 35 | 45.71% | 0.8305 | -0.93% | 2.57% | 19.44% | 4 |
| 8 | dukascopy | median | 35 | 45.71% | 0.7847 | -1.17% | 2.58% | 19.44% | 4 |
| 9 | dukascopy | p95 | 35 | 45.71% | 0.7401 | -1.45% | 2.65% | 19.44% | 4 |

## Gate Snapshot

| Gate | Result |
| --- | --- |
| Measured-cost structural precheck | PASS, P95 cost_R 0.1875 |
| Focused unit test | PASS |
| Research candidate smoke | PASS, 1 synthetic signal |
| PF >= 1.30 in at least 7/9 cells | FAIL, 0/9 |
| At least 40 trades per cell | FAIL, 3/9 |
| Positive PnL persistence | FAIL, 3/9 and Capital.com-only |
| Max zero-trade months <= 3 | FAIL, max 6 |
| Cross-broker persistence | FAIL, Pepperstone and Dukascopy negative |
| Concentration | FAIL, top-trade concentration remains extreme |

## Interpretation

High BTC volatility as a regime filter is not enough to make H4 XAU exhaustion reversal robust. The result is cleaner than the fully negative compression-expansion branch, but it still fails PF, activity, concentration, and broker-transfer gates.

Do not tune v0. A future BTC path likely needs a better crypto data class or a non-BTC primary signal rather than another OHLCV-derived BTC regime variant.

## Evidence

- Hypothesis: `docs/hypothesis_h4_btc_volatility_regime_gold_reversal_v0.md`
- Cost precheck: `PASS`, median stop 400 points, P95 cost_R 0.1875
- Registration: `outputs/reports/h4_btc_volatility_regime_gold_reversal_v0_research_hypothesis_registration.md`
- Smoke: `outputs/reports/h4_btc_volatility_regime_gold_reversal_v0_research_smoke.md`
- Matrix: `outputs/matrix_results/h4_btc_volatility_regime_gold_reversal_v0/`

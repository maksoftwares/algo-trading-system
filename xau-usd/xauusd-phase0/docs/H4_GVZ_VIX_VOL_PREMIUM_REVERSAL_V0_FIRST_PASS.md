# H4 GVZ/VIX Vol Premium Reversal v0 First Pass

Date: 2026-06-01

`h4_gvz_vix_vol_premium_reversal_v0` was tested as a higher-timeframe, non-level, gold-specific implied-volatility premium reversal candidate. The hypothesis was SHA256-locked before the real matrix run.

## Verdict

REJECTED_FIRST_PASS

Do not tune this v0 in place. Any future GVZ/VIX volatility-premium revisit needs a new versioned hypothesis and fresh SHA256 registration before result-producing runs.

## Registration

| Item | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_h4_gvz_vix_vol_premium_reversal_v0.md` |
| SHA256 | `6e0f84b2e7099cd4406e9a5f2c0f495e9f0761366c61a11fa94c5945b3ec26db` |
| Synthetic smoke | PASS |
| Real matrix | COMPLETE |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | PnL USD |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | capital_com | best_case | 43 | 1.7313 | 586.86 |
| 2 | capital_com | median | 43 | 1.7313 | 586.86 |
| 3 | capital_com | p95 | 43 | 1.7139 | 575.98 |
| 4 | pepperstone | best_case | 61 | 1.1313 | 160.83 |
| 5 | pepperstone | median | 61 | 1.1313 | 160.83 |
| 6 | pepperstone | p95 | 61 | 1.1225 | 150.79 |
| 7 | dukascopy | best_case | 63 | 1.1642 | 229.33 |
| 8 | dukascopy | median | 63 | 1.1462 | 205.62 |
| 9 | dukascopy | p95 | 63 | 1.0983 | 139.81 |

## Gate Read

| Gate | Observed | Required | Status |
| --- | ---: | ---: | --- |
| Total cost-cell trades | 501 | n/a | INFO |
| Cells with >=40 trades | 9/9 | >=7/9 | PASS |
| Cells with PF >=1.30 | 3/9 | >=7/9 | FAIL |
| Positive-PnL cells | 9/9 | robust across brokers | PASS |
| Max zero-trade months | 8 | <=3 | FAIL |
| Largest single-trade concentration | 53.73% | <=10% | FAIL |
| Top-5 trade concentration | 263.48% | <=40% | FAIL |
| Best PF | 1.7313 | >=1.30 | PASS |

## Interpretation

This was a better H4 result than the recent ETF-rotation reversals because every broker/cost cell was profitable. It still failed first pass because the edge was concentrated in Capital.com and did not persist strongly enough through Pepperstone and Dukascopy. Activity and concentration also fail. The correct action is to reject v0 without tuning, preserve the evidence, and keep searching for a genuinely independent higher-timeframe candidate.

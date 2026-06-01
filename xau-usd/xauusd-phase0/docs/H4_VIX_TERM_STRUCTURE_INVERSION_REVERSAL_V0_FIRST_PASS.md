# H4 VIX Term Structure Inversion Reversal v0 First Pass

Date: 2026-06-01

`h4_vix_term_structure_inversion_reversal_v0` was tested as a higher-timeframe, non-level, equity-volatility term-structure reversal candidate. The hypothesis was SHA256-locked before the real matrix run.

## Verdict

REJECTED_FIRST_PASS

Do not tune this v0 in place. Any future VIX/VXV term-structure revisit needs a new versioned hypothesis and fresh SHA256 registration before result-producing runs.

## Registration

| Item | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_h4_vix_term_structure_inversion_reversal_v0.md` |
| SHA256 | `7f7fe5c2b5a01bbaa81a1ddc39d539ef402122e74b572c3d54b986cd532813e7` |
| Synthetic smoke | PASS |
| Real matrix | COMPLETE |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | PnL USD |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | capital_com | best_case | 48 | 1.5476 | 493.74 |
| 2 | capital_com | median | 48 | 1.5476 | 493.74 |
| 3 | capital_com | p95 | 48 | 1.5066 | 458.19 |
| 4 | pepperstone | best_case | 43 | 1.1409 | 111.98 |
| 5 | pepperstone | median | 43 | 1.1409 | 111.98 |
| 6 | pepperstone | p95 | 43 | 1.1294 | 103.38 |
| 7 | dukascopy | best_case | 24 | 0.9948 | -2.84 |
| 8 | dukascopy | median | 24 | 0.9816 | -10.09 |
| 9 | dukascopy | p95 | 24 | 0.9736 | -14.42 |

## Gate Read

| Gate | Observed | Required | Status |
| --- | ---: | ---: | --- |
| Total cost-cell trades | 345 | n/a | INFO |
| Cells with >=40 trades | 6/9 | >=7/9 | FAIL |
| Cells with PF >=1.30 | 3/9 | >=7/9 | FAIL |
| Positive-PnL cells | 6/9 | robust across brokers | FAIL |
| Max zero-trade months | 3 | <=3 | PASS |
| Largest single-trade concentration | 100.00% | <=10% | FAIL |
| Top-5 trade concentration | 354.55% | <=40% | FAIL |
| Best PF | 1.5476 | >=1.30 | PASS |

## Interpretation

This lane produced a real Capital.com pocket and mild Pepperstone profitability, but it failed to generalize. Dukascopy generated too few trades and negative returns, and the overall profile failed PF persistence, sample-size, and concentration gates. The correct action is to reject v0 without tuning and keep searching for an independent higher-timeframe edge.

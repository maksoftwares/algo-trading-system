# H4 SLV/GLD Precious-Beta Reversal v0 First Pass

Date: 2026-06-01

`h4_slv_gld_precious_beta_reversal_v0` was tested as a higher-timeframe, non-level, precious-metals beta rotation reversal candidate. The hypothesis was SHA256-locked before the real matrix run.

## Verdict

REJECTED_FIRST_PASS

Do not tune this v0 in place. Any future SLV/GLD precious-beta revisit needs a new versioned hypothesis and fresh SHA256 registration before result-producing runs.

## Registration

| Item | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_h4_slv_gld_precious_beta_reversal_v0.md` |
| SHA256 | `7580b26105964bc4f184b54c623f0f05a2589545392bd1885b9dcebc0540df23` |
| Synthetic smoke | PASS |
| Real matrix | COMPLETE |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | PnL USD |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | capital_com | best_case | 34 | 0.6573 | -347.53 |
| 2 | capital_com | median | 34 | 0.6573 | -347.53 |
| 3 | capital_com | p95 | 34 | 0.6598 | -342.06 |
| 4 | pepperstone | best_case | 49 | 1.0827 | 97.86 |
| 5 | pepperstone | median | 49 | 1.0827 | 97.86 |
| 6 | pepperstone | p95 | 49 | 1.0841 | 99.12 |
| 7 | dukascopy | best_case | 46 | 0.8312 | -209.15 |
| 8 | dukascopy | median | 46 | 0.8255 | -214.92 |
| 9 | dukascopy | p95 | 46 | 0.8247 | -214.30 |

## Gate Read

| Gate | Observed | Required | Status |
| --- | ---: | ---: | --- |
| Total cost-cell trades | 387 | n/a | INFO |
| Cells with >=40 trades | 6/9 | >=7/9 | FAIL |
| Cells with PF >=1.30 | 0/9 | >=7/9 | FAIL |
| Positive-PnL cells | 3/9 | robust across brokers | FAIL |
| Max zero-trade months | 6 | <=3 | FAIL |
| Largest single-trade concentration | 100.00% | <=10% | FAIL |
| Top-5 trade concentration | 378.47% | <=40% | FAIL |
| Best PF | 1.0841 | >=1.30 | FAIL |

## Interpretation

The H4 reversal expression did not rescue the rejected H1 SLV/GLD precious-beta follow-through lane. Pepperstone had a mild positive pocket below threshold, Capital.com and Dukascopy were negative, and the candidate failed sample-size, PF, activity, and concentration gates. The correct action is to reject v0 without tuning and keep searching for a genuinely independent higher-timeframe mechanism.

# H4 MOVE/VIX Bond-Vol Shock Reversal v0 First Pass

Date: 2026-06-01

`h4_move_vix_bond_vol_shock_reversal_v0` was tested as a higher-timeframe, non-level, rates-volatility versus equity-volatility shock reversal candidate. The hypothesis was SHA256-locked before the real matrix run.

## Verdict

REJECTED_FIRST_PASS

Do not tune this v0 in place. Any future MOVE/VIX bond-volatility revisit needs a new versioned hypothesis and fresh SHA256 registration before result-producing runs.

## Registration

| Item | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_h4_move_vix_bond_vol_shock_reversal_v0.md` |
| SHA256 | `1e48509add7580fcea6bf9470ed34fd88cd81e1c6251a5736822f614cf73f938` |
| Synthetic smoke | PASS |
| Real matrix | COMPLETE |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | PnL USD |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | capital_com | best_case | 6 | 0.2912 | -104.98 |
| 2 | capital_com | median | 6 | 0.2912 | -104.98 |
| 3 | capital_com | p95 | 6 | 0.2861 | -106.30 |
| 4 | pepperstone | best_case | 27 | 0.6263 | -252.57 |
| 5 | pepperstone | median | 27 | 0.6263 | -252.57 |
| 6 | pepperstone | p95 | 27 | 0.6208 | -257.49 |
| 7 | dukascopy | best_case | 28 | 1.4215 | 176.41 |
| 8 | dukascopy | median | 28 | 1.3999 | 168.44 |
| 9 | dukascopy | p95 | 28 | 1.3163 | 133.54 |

## Gate Read

| Gate | Observed | Required | Status |
| --- | ---: | ---: | --- |
| Total cost-cell trades | 183 | n/a | INFO |
| Cells with >=40 trades | 0/9 | >=7/9 | FAIL |
| Cells with PF >=1.30 | 3/9 | >=7/9 | FAIL |
| Positive-PnL cells | 3/9 | robust across brokers | FAIL |
| Max zero-trade months | 14 | <=3 | FAIL |
| Largest single-trade concentration | 100.00% | <=10% | FAIL |
| Top-5 trade concentration | 260.48% | <=40% | FAIL |
| Best PF | 1.4215 | >=1.30 | PASS |

## Interpretation

The H4 MOVE/VIX expression did not rescue the rejected H1 MOVE/VIX lane. The only PF-threshold cells were sparse Dukascopy cells below the trade-count floor, while Capital.com and Pepperstone were negative. The correct action is to reject v0 without tuning and keep searching for a materially different higher-timeframe mechanism or a better primary rates/order-flow data source.

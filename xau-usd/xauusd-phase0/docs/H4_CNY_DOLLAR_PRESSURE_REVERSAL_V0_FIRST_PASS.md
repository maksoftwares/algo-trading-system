# H4 CNY-Dollar Pressure Reversal v0 First Pass

Date: 2026-06-01

`h4_cny_dollar_pressure_reversal_v0` was tested as a higher-timeframe, non-level, official CNY-dollar macro/FX pressure reversal candidate. The hypothesis was SHA256-locked before the real matrix run.

## Verdict

REJECTED_FIRST_PASS

Do not tune this v0 in place. Any future CNY-dollar pressure revisit needs a new versioned hypothesis and fresh SHA256 registration before result-producing runs.

## Registration

| Item | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_h4_cny_dollar_pressure_reversal_v0.md` |
| SHA256 | `8677209cd4c0c35180e2ee9efc76c6ce1bace67867531be567516136ff193e4a` |
| Synthetic smoke | PASS |
| Real matrix | COMPLETE |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | PnL USD |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | capital_com | best_case | 30 | 1.0023 | 1.75 |
| 2 | capital_com | median | 30 | 1.0023 | 1.75 |
| 3 | capital_com | p95 | 30 | 0.9903 | -7.57 |
| 4 | pepperstone | best_case | 48 | 0.6850 | -421.65 |
| 5 | pepperstone | median | 48 | 0.6850 | -421.65 |
| 6 | pepperstone | p95 | 48 | 0.6803 | -429.73 |
| 7 | dukascopy | best_case | 39 | 1.0592 | 58.35 |
| 8 | dukascopy | median | 39 | 1.0580 | 56.15 |
| 9 | dukascopy | p95 | 39 | 1.0400 | 39.05 |

## Gate Read

| Gate | Observed | Required | Status |
| --- | ---: | ---: | --- |
| Total cost-cell trades | 351 | n/a | INFO |
| Cells with >=40 trades | 3/9 | >=7/9 | FAIL |
| Cells with PF >=1.30 | 0/9 | >=7/9 | FAIL |
| Positive-PnL cells | 5/9 | robust across brokers | FAIL |
| Max zero-trade months | 6 | <=3 | FAIL |
| Largest single-trade concentration | 4274.74% | <=10% | FAIL |
| Top-5 trade concentration | 20488.90% | <=40% | FAIL |
| Best PF | 1.0592 | >=1.30 | FAIL |

## Interpretation

The H4 timing did not rescue the rejected H1 CNY-dollar pressure reversion lane. Capital.com was roughly flat and below the trade-count floor, Pepperstone was clearly negative despite enough trades, and Dukascopy was positive but still below PF threshold and below trade-count minimum. The correct action is to reject v0 without tuning and keep searching for a higher-timeframe mechanism that can survive cross-broker and cost-cell pressure.

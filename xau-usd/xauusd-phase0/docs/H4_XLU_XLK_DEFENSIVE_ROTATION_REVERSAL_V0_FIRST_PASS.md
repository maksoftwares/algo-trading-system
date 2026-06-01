# H4 XLU/XLK Defensive Rotation Reversal v0 First Pass

Date: 2026-06-01

`h4_xlu_xlk_defensive_rotation_reversal_v0` was tested as a higher-timeframe, non-level, intermarket defensive-sector reversal candidate. The hypothesis was SHA256-locked before the real matrix run.

## Verdict

REJECTED_FIRST_PASS

Do not tune this v0 in place. Any future XLU/XLK revisit needs a new versioned hypothesis and fresh SHA256 registration before result-producing runs.

## Registration

| Item | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_h4_xlu_xlk_defensive_rotation_reversal_v0.md` |
| SHA256 | `8ffbcc18c87e34599b6b1f935ee5d0384a411d2396ff0d5d794e01e240e1b2e1` |
| Synthetic smoke | PASS |
| Real matrix | COMPLETE |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF | PnL USD |
| ---: | --- | --- | ---: | ---: | ---: |
| 1 | capital_com | best_case | 47 | 0.8174 | -199.69 |
| 2 | capital_com | median | 47 | 0.8174 | -199.69 |
| 3 | capital_com | p95 | 47 | 0.8088 | -209.93 |
| 4 | pepperstone | best_case | 47 | 0.5304 | -523.74 |
| 5 | pepperstone | median | 47 | 0.5304 | -523.74 |
| 6 | pepperstone | p95 | 47 | 0.5274 | -527.45 |
| 7 | dukascopy | best_case | 57 | 0.8025 | -270.33 |
| 8 | dukascopy | median | 57 | 0.7940 | -283.03 |
| 9 | dukascopy | p95 | 57 | 0.7634 | -326.81 |

## Gate Read

| Gate | Observed | Required | Status |
| --- | ---: | ---: | --- |
| Total cost-cell trades | 453 | n/a | INFO |
| Cells with >=40 trades | 9/9 | >=7/9 | PASS |
| Cells with PF >=1.30 | 0/9 | >=7/9 | FAIL |
| Positive-PnL cells | 0/9 | robust across brokers | FAIL |
| Best PF | 0.8174 | >=1.30 | FAIL |

## Interpretation

The lane produced enough H4 sample size, so this was not primarily a frequency failure. It failed because expectancy was negative across every broker and cost model. This rejects the defensive-sector H4 reversal expression and keeps the project without an approved independent higher-timeframe EA.

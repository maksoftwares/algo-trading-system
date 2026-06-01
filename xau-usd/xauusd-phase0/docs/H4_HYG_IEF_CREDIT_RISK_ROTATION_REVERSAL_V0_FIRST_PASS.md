# H4 HYG/IEF Credit-Risk Rotation Reversal v0 First Pass

Date: 2026-06-01

`h4_hyg_ief_credit_risk_rotation_reversal_v0` was tested as a higher-timeframe, non-level, intermarket credit-risk reversal candidate. The hypothesis was SHA256-locked before the real matrix run.

## Verdict

REJECTED_FIRST_PASS

Do not tune this v0 in place. Any future HYG/IEF revisit needs a new versioned hypothesis and fresh SHA256 registration before result-producing runs.

## Registration

| Item | Value |
| --- | --- |
| Hypothesis file | `docs/hypothesis_h4_hyg_ief_credit_risk_rotation_reversal_v0.md` |
| SHA256 | `12f3e288ae8c2e266c1df7b46a128c5b4ba9c952d36c0f59538c9fd840022a26` |
| Synthetic smoke | PASS |
| Real matrix | COMPLETE |

## Matrix Summary

| Cell | Broker | Cost | Trades | PF |
| ---: | --- | --- | ---: | ---: |
| 1 | capital_com | best_case | 47 | 1.0471 |
| 2 | capital_com | median | 47 | 1.0471 |
| 3 | capital_com | p95 | 47 | 1.0418 |
| 4 | pepperstone | best_case | 50 | 0.7451 |
| 5 | pepperstone | median | 50 | 0.7451 |
| 6 | pepperstone | p95 | 50 | 0.7378 |
| 7 | dukascopy | best_case | 48 | 0.8334 |
| 8 | dukascopy | median | 48 | 0.8199 |
| 9 | dukascopy | p95 | 48 | 0.7869 |

## Gate Read

| Gate | Observed | Required | Status |
| --- | ---: | ---: | --- |
| Total cost-cell trades | 435 | n/a | INFO |
| Cells with >=40 trades | 9/9 | >=7/9 | PASS |
| Cells with PF >=1.30 | 0/9 | >=7/9 | FAIL |
| Best PF | 1.0471 | >=1.30 | FAIL |
| Cross-broker persistence | Capital.com mildly positive only | robust across brokers | FAIL |

## Interpretation

The lane produced enough higher-timeframe sample size, which is useful evidence. The edge did not survive the actual matrix: Capital.com was only mildly positive and stayed below threshold, while Pepperstone and Dukascopy were negative across all cost models.

This rejects the H4 credit-risk reversal expression. It also confirms that the broader HYG/IEF data class has now failed in both H1 follow-through and H4 reversal forms under the current discipline.

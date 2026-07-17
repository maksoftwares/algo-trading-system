# XAUUSD ML Candidate Rankers V1 Result

Decision: **NO_ML_RANKER_SURVIVOR**

Research only. No model score is authorized for Python prediction, EA consumption, demo, or live execution.

| Family | Stage | Eligible | Trades | Trades/day | Stress PF | Avg R | Drawdown R | Gate |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `ML_M15_MOMENTUM_RANKER_V1` | train | True | 235 | 0.376 | 0.481 | -0.410 | 107.972 | FAIL |
| `ML_M15_MOMENTUM_RANKER_V1` | validation | False | 168 | 0.271 | 0.832 | -0.119 | 33.435 | INELIGIBLE |
| `ML_M15_MOMENTUM_RANKER_V1` | internal_test | False | 2 | 0.003 | 1.564 | 0.333 | 0.000 | INELIGIBLE |
| `ML_M15_MOMENTUM_RANKER_V1` | exam | False | 0 | 0.000 | nan | 0.000 | 0.000 | INELIGIBLE |
| `ML_M15_MOMENTUM_RANKER_V1` | recent_tail | False | 0 | 0.000 | nan | 0.000 | 0.000 | INELIGIBLE |
| `ML_M15_REVERSION_RANKER_V1` | train | True | 181 | 0.290 | 0.776 | -0.148 | 34.148 | FAIL |
| `ML_M15_REVERSION_RANKER_V1` | validation | False | 174 | 0.280 | 0.715 | -0.200 | 46.954 | INELIGIBLE |
| `ML_M15_REVERSION_RANKER_V1` | internal_test | False | 154 | 0.248 | 0.620 | -0.268 | 40.068 | INELIGIBLE |
| `ML_M15_REVERSION_RANKER_V1` | exam | False | 219 | 0.351 | 0.667 | -0.238 | 52.384 | INELIGIBLE |
| `ML_M15_REVERSION_RANKER_V1` | recent_tail | False | 159 | 0.510 | 0.703 | -0.208 | 36.346 | INELIGIBLE |

## Portfolio

Survivors: none.
Exam portfolio: 0 trades, 0.000/source-day, stress PF None, average 0.000R, drawdown 0.000R.

## Interpretation

Neither fixed ranker passed the full chronological firewall. V1 is rejected without tuning.

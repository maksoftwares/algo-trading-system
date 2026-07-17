# XAUUSD Independent Specialists V1 Result

Campaign decision: **NO_SPECIALIST_SURVIVOR**

Research only. This result does not authorize model training, EA consumption, demo orders, or live orders.

## Specialist Decisions

| Specialist | Train | Validation | Internal test | Exam | Decision |
|---|---:|---:|---:|---:|---|
| `R1_H1_TREND_PULLBACK_LONG_V1` | FAIL | INELIGIBLE | INELIGIBLE | INELIGIBLE | REJECT |
| `R2_H1_TREND_PULLBACK_SHORT_V1` | FAIL | INELIGIBLE | INELIGIBLE | INELIGIBLE | REJECT |
| `R3_H1_COMPRESSION_BREAK_RETEST_V1` | FAIL | INELIGIBLE | INELIGIBLE | INELIGIBLE | REJECT |
| `R4_M15_SESSION_EXPANSION_V1` | FAIL | INELIGIBLE | INELIGIBLE | INELIGIBLE | REJECT |
| `R5_M30_CHOP_ROTATION_V1` | FAIL | INELIGIBLE | INELIGIBLE | INELIGIBLE | REJECT |

## Stage Metrics

- `R1_H1_TREND_PULLBACK_LONG_V1` / `train`: 75 trades, 0.060/source-day, stress PF 0.415, average -0.478R, drawdown 37.714R.
- `R1_H1_TREND_PULLBACK_LONG_V1` / `validation`: 39 trades, 0.063/source-day, stress PF 0.981, average -0.013R, drawdown 10.368R.
- `R1_H1_TREND_PULLBACK_LONG_V1` / `internal_test`: 43 trades, 0.069/source-day, stress PF 0.790, average -0.153R, drawdown 11.721R.
- `R1_H1_TREND_PULLBACK_LONG_V1` / `exam`: 64 trades, 0.103/source-day, stress PF 0.977, average -0.015R, drawdown 9.995R.
- `R2_H1_TREND_PULLBACK_SHORT_V1` / `train`: 67 trades, 0.054/source-day, stress PF 0.679, average -0.251R, drawdown 21.496R.
- `R2_H1_TREND_PULLBACK_SHORT_V1` / `validation`: 37 trades, 0.060/source-day, stress PF 0.794, average -0.145R, drawdown 10.294R.
- `R2_H1_TREND_PULLBACK_SHORT_V1` / `internal_test`: 38 trades, 0.061/source-day, stress PF 0.556, average -0.357R, drawdown 21.825R.
- `R2_H1_TREND_PULLBACK_SHORT_V1` / `exam`: 22 trades, 0.035/source-day, stress PF 0.896, average -0.071R, drawdown 6.975R.
- `R3_H1_COMPRESSION_BREAK_RETEST_V1` / `train`: 2 trades, 0.002/source-day, stress PF 1.674, average 0.377R, drawdown 0.000R.
- `R3_H1_COMPRESSION_BREAK_RETEST_V1` / `validation`: 2 trades, 0.003/source-day, stress PF 1.547, average 0.322R, drawdown 0.000R.
- `R3_H1_COMPRESSION_BREAK_RETEST_V1` / `internal_test`: 0 trades, 0.000/source-day, stress PF nan, average 0.000R, drawdown 0.000R.
- `R3_H1_COMPRESSION_BREAK_RETEST_V1` / `exam`: 0 trades, 0.000/source-day, stress PF nan, average 0.000R, drawdown 0.000R.
- `R4_M15_SESSION_EXPANSION_V1` / `train`: 0 trades, 0.000/source-day, stress PF nan, average 0.000R, drawdown 0.000R.
- `R4_M15_SESSION_EXPANSION_V1` / `validation`: 1 trades, 0.002/source-day, stress PF 0.000, average -1.091R, drawdown 0.000R.
- `R4_M15_SESSION_EXPANSION_V1` / `internal_test`: 1 trades, 0.002/source-day, stress PF inf, average 1.413R, drawdown 0.000R.
- `R4_M15_SESSION_EXPANSION_V1` / `exam`: 0 trades, 0.000/source-day, stress PF nan, average 0.000R, drawdown 0.000R.
- `R5_M30_CHOP_ROTATION_V1` / `train`: 48 trades, 0.039/source-day, stress PF 0.775, average -0.139R, drawdown 13.283R.
- `R5_M30_CHOP_ROTATION_V1` / `validation`: 38 trades, 0.061/source-day, stress PF 1.090, average 0.049R, drawdown 4.660R.
- `R5_M30_CHOP_ROTATION_V1` / `internal_test`: 31 trades, 0.050/source-day, stress PF 0.645, average -0.247R, drawdown 13.461R.
- `R5_M30_CHOP_ROTATION_V1` / `exam`: 38 trades, 0.061/source-day, stress PF 0.316, average -0.558R, drawdown 24.402R.

## Portfolio

Survivors: none.
Exam portfolio: 0 trades, 0.000/source-day, stress PF None, average 0.000R, drawdown 0.000R.

## Interpretation

No family passed the full chronological firewall. These definitions are rejected and will not be tuned in V1.

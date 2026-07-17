# XAUUSD Macro Composite Risk-State Portability V1 Result

Decision: **REJECT_MACRO_COMPOSITE_PORTABILITY**

Research only. No Python prediction, EA, demo, or live authorization is granted.

| Stage | Eligible | Trades | Trades/day | Stress PF | Avg R | Drawdown R | Top five removed R | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| replication_fit | True | 61 | 0.039 | 0.828 | -0.091 | 9.308 | -13.421 | FAIL |
| development | False | 67 | 0.072 | 0.650 | -0.221 | 13.697 | -22.658 | INELIGIBLE |
| exam | False | 31 | 0.053 | 1.230 | 0.089 | 3.288 | -5.132 | INELIGIBLE |

## Interpretation

The frozen archived rule did not pass the full chronological firewall. Later periods cannot rescue an earlier failure, and same-version tuning is forbidden.

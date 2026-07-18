# Five-Specialist MT5 Real-Tick Report

Window: 2026-04-01 through 2026-06-30. Symbol: XAUUSD. Timeframe: M5. Size: fixed 0.01 lot. Starting deposit: $1,000.

| Specialist | MT5 validation mode | Trades | Net P&L | PF | Max equity DD |
|---|---|---:|---:|---:|---:|
| R1_UPTREND | NATIVE_MT5_TWO_COMPONENT_AGGREGATE | 0 | $0.00 | 0.00 | $0.00 (0.00%) |
| R2_DOWNTREND | MT5_REAL_TICK_EXECUTION_SCHEDULE_REPLAY | 2 | $130.57 | 3.95 | $114.08 (9.17%) |
| R3_COMPRESSION | MT5_REAL_TICK_EXECUTION_SCHEDULE_REPLAY | 2 | -$3.88 | 0.85 | $66.73 (6.28%) |
| R4_CHOP | MT5_REAL_TICK_EXECUTION_SCHEDULE_REPLAY | 0 | $0.00 | 0.00 | $0.00 (0.00%) |
| R5_TRANSITION | MT5_REAL_TICK_EXECUTION_SCHEDULE_REPLAY | 2 | $54.24 | 8.07 | $28.47 (2.80%) |

## Combined MT5 Account Curve

The combined replay executed 6 trades and returned $180.93, with PF 3.31 and maximal equity drawdown $114.08 (8.81%).
Observed frequency was 6 trades across 65 weekdays, or 0.09 trades per weekday.

## Python/Dukascopy Reference vs MT5

| Specialist | Reference net | MT5 net | Difference |
|---|---:|---:|---:|
| R2_DOWNTREND | $149.29 | $130.57 | -$18.72 |
| R3_COMPRESSION | $20.22 | -$3.88 | -$24.10 |
| R4_CHOP | $0.00 | $0.00 | $0.00 |
| R5_TRANSITION | $23.08 | $54.24 | $31.16 |
| ALL_SPECIALISTS | $192.59 | $180.93 | -$11.66 |

## Scope

- Every report states `100% real ticks`.
- R1 is native MQL5 signal generation; both R1 components produced zero trades.
- R2-R5 are frozen Python-signal schedule replays through MT5 execution, not native MQL5 signal parity.
- Six replay signals opened and none were missed.
- The archived EX5 was compiled from the repository source with `0 errors, 0 warnings`.
- This small three-month sample is execution-portability evidence, not authorization for demo or live trading.

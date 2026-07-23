# EURUSD V1R Stage 0 Parity Result

Status: `STAGE0_PARITY_PASS_RECLAIM_NOT_RUN`

The corrected candidate reproduces the exact unmasked benchmark while
closing the startup, source/EX5, input-schema, leverage, symbol, fill,
SL/TP, stop-component, and order/deal evidence gaps.

| Gate | Pass |
|---|---:|
| candidate specific identity | PASS |
| compile zero errors zero warnings | PASS |
| source copy hash exact | PASS |
| source ex5 chain frozen | PASS |
| input schema exact | PASS |
| ini leverage 1 50 | PASS |
| report leverage 1 50 | PASS |
| environment leverage 50 | PASS |
| symbol specification complete | PASS |
| startup fail closed | PASS |
| signal count 2957 | PASS |
| decision count 2957 | PASS |
| trade count 1145 | PASS |
| aggregate metric parity | PASS |
| canonical signal decision trade parity | PASS |
| order action parity | PASS |
| failed attempts preserved | PASS |
| fill defined by entry deal | PASS |
| requested actual geometry complete | PASS |
| requested actual sl exact | PASS |
| requested actual tp exact | PASS |
| all entry exit deals in transaction log | PASS |
| stop component attribution complete | PASS |
| stop ceiling inventory complete | PASS |
| positive free margin | PASS |
| mt5 net exact | PASS |
| mt5 gross exact | PASS |
| mt5 equity drawdown exact | PASS |
| reclaim not implemented or run | PASS |
| tester only boundary | PASS |

## Canonical parity

- Signal rows: 2,957; mismatches: 0.
- Decision rows: 2,957; mismatches: 0.
- Trade rows: 1,145; mismatches: 0.
- Net: USD 77.26.
- Gross profit/loss: USD 779.61 / USD 702.35.
- Unrounded PF: 1.110002135687.
- MT5 maximal equity drawdown: 27.56 (2.68%).

## Boundary

This is a repaired retrospective research baseline only. No reclaim
source was created or run. No chart, demo, live, shadow, or broker-runtime
action was authorized or performed. Model 0 may contain generated ticks,
and DSR remains not assessable.

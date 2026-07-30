# EURUSD V1R immediate next-bar reclaim verdict

Status: `KILL_FAMILY`

The one permitted immediate-next-bar reclaim test failed multiple frozen fatal gates. The RSI/Bollinger close-fade family is closed. The candidate is not admitted to the protected H4 portfolio and is not authorized for shadow, demo, or live trading.

## Exact MT5 result

The candidate was frozen in git commit `7c94ae27` before its first compile and Strategy Tester run. MetaEditor compiled the source with zero errors and zero warnings. The isolated Capital.com MT5 test used the same `Model=0`, EURUSD history, 1:50 leverage, USD 1,000 deposit, 0.01 fixed lot, and 2022-07-01 through 2026-07-01 history as the repaired parent.

| Metric | Result | Frozen gate | Pass |
|---|---:|---:|---:|
| Trades | 599 | at least 400 | PASS |
| Trades per weekday in test span | 0.574 | diagnostic | — |
| Win rate | 57.60% | diagnostic | — |
| Payoff ratio | 0.769 | Stage 2 at least 0.90 | FAIL |
| Net P&L | $19.32 | positive | PASS |
| Profit factor | 1.0440 | at least 1.2100 | **FAIL** |
| Equity drawdown | $24.56 | at most $33.94 | PASS |
| +0.5 pip stressed net | -$15.39 | positive | **FAIL** |
| +0.5 pip stressed PF | 0.9661 | at least 1.15 | **FAIL** |
| +1.0 pip stressed net | -$45.34 | positive | **FAIL** |
| +1.0 pip stressed PF | 0.9028 | at least 1.00 | **FAIL** |
| Last-12-month trades | 172 | diagnostic | — |
| Last-12-month net | -$9.57 | positive implied by PF gate | **FAIL** |
| Last-12-month PF | 0.9192 | at least 1.22 | **FAIL** |
| Last-6-month trades | 103 | diagnostic | — |
| Last-6-month net | $9.32 | diagnostic | — |
| Last-6-month PF | 1.1529 | at least 1.20 | **FAIL** |

The cost stress uses the frozen MT5 symbol specification, actual 0.01-lot volume, 0.5 or 1.0 added round-trip pip, and 1.25 times any negative commission or swap.

## Calendar stability

| Exit year | Trades | Net P&L | PF | Gate |
|---|---:|---:|---:|---:|
| 2022 partial | 65 | $5.97 | 1.0904 | diagnostic |
| 2023 | 152 | $14.28 | 1.1338 | PF below 1.15 |
| 2024 | 146 | -$9.81 | 0.8977 | **FAIL: net not positive** |
| 2025 | 133 | -$0.44 | 0.9960 | **FAIL: net not positive** |
| 2026 H1 | 103 | $9.32 | 1.1529 | diagnostic |

The rule required positive net in 2023, 2024, and 2025 and PF of at least 1.15 in at least two of those years. It achieved zero qualifying years.

## Robustness

- Removing the largest winner leaves PF 1.0337 and $14.80, below the frozen PF 1.05 gate.
- Removing the best month leaves PF 1.0172, below the 1.15 gate.
- Removing the best six-hour entry session leaves PF 1.0061, below the 1.10 gate.
- Rolling 100-trade windows: 54% profitable, median PF 1.0100, versus required 65% and 1.15.
- Rolling 150-trade windows: 51.1% profitable, median PF 1.0002, versus required 75% and 1.20.
- Rolling 250-trade windows: 40% profitable, median PF 0.9894, versus required 90% and 1.25.
- Winner/loss concentration limits passed, but these do not rescue the fatal economic failures.

Bootstrap and D1 regime-coverage diagnostics are unnecessary for the decision because the conjunctive Stage 1 contract is already irreversibly failed by full-period, cost, recent-window, annual, removal, and rolling gates.

## Causal conclusion

Waiting for the next bar removed about half of the parent trades but did not improve accuracy or robustness. It reduced parent PF from 1.1100 to 1.0440 and reduced frequency from about 1.10 to 0.57 trades per weekday. The confirmation is therefore not informative enough to offset its delayed entry and cost burden.

Per the binding preregistration, no RSI threshold, Bollinger width, session mask, stop, target, multi-bar confirmation, or other rescue test is allowed. The family remains only as immutable research evidence.


# EURUSD Neutral inventory MT5 execution parity

## Result

`COMPILE_AND_FIXTURE_READY_RUNTIME_PARITY_BLOCKED_ACCOUNT_BOUNDARY`

The tester-only MQL5 execution kernel compiled with zero errors and zero
warnings. Its committed fixture contains seven deterministic cases covering
long and short target, stop, and time exits plus excess-spread rejection,
missing entry tick, and missing time-exit tick. Python tests regenerate every
expected row through the frozen production execution function.

The EA has no trade include or order, position-close, web-request, or broker
API. It refuses non-Strategy-Tester execution and refuses a tester state that
already contains a position.

## Runtime boundary

A one-shot local-only tester configuration used:

- `Login=0`;
- an empty server;
- local agents enabled;
- remote and cloud agents disabled;
- visual mode disabled;
- automatic terminal shutdown.

MT5 refused to start the tester because an account was not specified. No EA
fixture case therefore executed inside the Strategy Tester. The stored demo
login was not substituted, no account was accessed, and no order was possible.

Consequently:

- Python fixture parity: **passed**;
- MQL5 compilation: **passed, 0 errors / 0 warnings**;
- MQL5 source/EX5 hash lock: **available**;
- exact Strategy Tester runtime parity: **not verified**;
- controlled demo readiness: **false**;
- broker action: **none**.

Using an account merely to finish runtime parity requires explicit authorization
in a later task. It is not inferred from this research program.

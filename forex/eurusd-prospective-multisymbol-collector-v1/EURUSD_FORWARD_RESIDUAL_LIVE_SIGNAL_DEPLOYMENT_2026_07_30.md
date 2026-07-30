# EURUSD residual live-signal publisher deployment — 2026-07-30

## Result

The pre-outcome residual signal publisher is frozen and running unattended.
It emits the exact residual-regime decision during the 20:01-20:10 UTC window,
before the six-hour outcome exists.

It is disarmed and has no order path.

## Deployment gap corrected

The original residual evaluator is intentionally conservative: it waits for
the full six-hour path, observes both side outcomes, then writes a terminal
append-only research record. Although its side selection uses only prior
history, the record itself is not available at the intended 20:00 entry clock.

That terminal record cannot prove a demo trade could have been selected in
real time.

The live publisher now creates a separate immutable decision ledger before the
outcome. The later terminal evaluator remains independent and can be used to
check the published decision and resolve its economics.

## Causal publication

The publisher:

- runs from the system UTC clock with no as-of override;
- accepts publication only from 20:01 through 20:10 UTC;
- uses completed M5 intervals through 19:55 UTC;
- reconstructs training only from prior terminal residual records;
- rejects current-date or future outcome leakage;
- checks same-date M15 and daily ownership;
- applies the unchanged frozen regime and side-admission logic;
- records cash permanently if context is missing;
- records cash permanently if publication is late; and
- never includes an outcome or future-price field.

M15 signals are restricted to 06:00-09:45 UTC and the daily learner decides at
08:00 UTC, so same-date upstream ownership is known before the 20:00 residual
clock.

## Frozen boundary

The implementation was locked at `2026-07-30T08:45:03Z`, before the
`2026.08.01 00:00:00` UTC evidence floor. At lock time:

- post-floor feature rows: 0;
- terminal residual decisions: 0;
- live residual decisions: 0;
- eligible live signals: 0;
- historical backfill: prohibited; and
- demo-order authorization: false.

The lock covers the publisher config, protocol, runner, implementation, tests,
operations scripts, and the upstream residual-strategy lock.

## Prestart verification

Status: `WAITING_FORWARD_FLOOR`

- published decisions: 0;
- eligible signals: 0;
- cash decisions: 0; and
- `demo_order_authorized=false`.

Repository and deployed prestart outputs match:

| File | SHA-256 |
|---|---|
| `FORWARD_RESIDUAL_LIVE_SIGNALS.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `FORWARD_RESIDUAL_LIVE_SIGNAL_SUMMARY.json` | `00016f5a64eefe94aa6e8c97b1988b1412e6cb298b4c12117b9fe439243c28c6` |
| `FORWARD_RESIDUAL_LIVE_SIGNAL_SUMMARY.md` | `82ef771c5cb03f25042ab88d5bdfa9e09bb1f70ad1653ed8ec080c53223f4dae` |

Nine focused tests pass, including pre-floor refusal, pre-outcome publication,
prior-only regime histories, upstream veto, missing-data cash, late cash,
append-only mutation refusal, no-order/no-backfill guards, and hash-lock
verification. Ruff and both PowerShell parser checks pass.

## Unattended operation

Windows task: `Codex-EURUSD-Forward-Residual-Live-Signal`

- limited interactive principal;
- daily at 00:03 Dubai, corresponding to 20:03 UTC;
- maximum one concurrent instance;
- three automatic retries;
- ten-minute execution limit;
- first manual run result: 0;
- missed runs: 0; and
- next scheduled run at deployment: 2026-07-31 00:03 Dubai.

The pre-floor scheduled runs remain waiting. The first possible weekday
publication occurs only after the August evidence floor.

## Remaining execution work

This establishes that a decision exists at the executable clock. It does not
yet authorize demo orders.

Next, the immutable live decision must be joined to the independent terminal
outcome, checked for exact parity, exported through a disarmed MT5 shadow
bridge, and included in a live-only combined portfolio ledger. Demo ordering
remains forbidden until the full forward economic, frequency, parity, and soak
gates pass.

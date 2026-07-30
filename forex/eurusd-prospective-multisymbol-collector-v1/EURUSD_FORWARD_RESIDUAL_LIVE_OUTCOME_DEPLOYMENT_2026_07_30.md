# EURUSD residual live-outcome deployment — 2026-07-30

## Result

The raw-tick residual outcome adjudicator and pre-outcome selection-parity
monitor are frozen and running unattended.

Only the actual MT5 shadow receipt can produce executable P&L. The earlier
research entry is explicitly forbidden as a substitute.

## Frozen boundary

The implementation was re-locked at `2026-07-30T09:26:01Z`, before the
`2026.08.01 00:00:00` UTC evidence floor. At lock time:

- live published signals: 0;
- MT5 bridge receipts: 0;
- live outcomes: 0;
- raw tick artifacts: 0;
- selection parity rows: 0;
- order API calls: 0;
- historical backfill: prohibited; and
- demo-order authorization: false.

The lock covers the config, protocol, runner, adjudicator, tests, operations
scripts, bridge lock, and terminal residual-strategy lock.

## Exact live execution path

For an eligible MT5 shadow receipt:

1. Raw EURUSD broker ticks are requested from the captured entry through the
   six-hour horizon.
2. The one-second entry window must contain exactly one tick matching both the
   captured bid and ask.
3. The complete ordered tick payload is canonicalized, SHA-256 hashed, and
   stored immutably.
4. LONG exits are evaluated on bid and SHORT exits on ask.
5. Stop is checked before target.
6. A stop gap uses the first executable quote.
7. A target uses the target price.
8. Time exit requires a tick no more than 60 seconds before six hours.
9. Base and additional-0.5-pip stressed P&L are calculated at fixed 0.01 lot.

Zero or multiple matching entry ticks, an empty path, or an invalid time-exit
tick creates an invalid outcome. Nothing is imputed.

Friday 20:00 UTC receipts are non-evaluable cash because the six-hour window
crosses the weekly market close. They cannot enter future demo ordering or
live P&L.

The publisher now writes Friday market-closure cash before side selection.
That state receives self-terminal operational parity without waiting for a
research path that cannot exist after the weekly close.

## Selection parity

The immutable pre-outcome decision is compared with the later terminal
research record across:

- decision time;
- causal regime;
- eligible side;
- eligibility reason;
- prior training count;
- complete causal context; and
- regime-side statistics before selection.

Upstream-owned and missing-context cash states have exact terminal mappings.
A mismatch is permanent evidence and blocks admission.

## Admission

The live residual component needs at least 50 matched selections and 50
executable outcomes, with:

- zero selection mismatches;
- zero invalid outcomes;
- 45-60% wins;
- payoff at least 1.25;
- PF at least 1.15;
- stressed PF at least 1.05;
- best-5%-removed PF at least 1.00;
- both chronological halves above PF 1.00; and
- positive dollar P&L.

MT5 ordering parity and disarmed shadow soak remain mandatory external gates.

## Prestart verification

Status: `WAITING_MINIMUM_LIVE_EVIDENCE`

- published decisions: 0;
- MT5 receipts: 0;
- resolved live outcomes: 0;
- invalid outcomes: 0;
- selection parity rows: 0;
- selection mismatches: 0;
- order API calls: 0;
- position mutation attempts: 0; and
- `demo_order_authorized=false`.

Repository and deployed prestart outputs match:

| File | SHA-256 |
|---|---|
| `FORWARD_RESIDUAL_LIVE_OUTCOMES.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `FORWARD_RESIDUAL_SELECTION_PARITY.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `FORWARD_RESIDUAL_LIVE_OUTCOME_SUMMARY.json` | `9066fe6a41ed7c359dc9e4140c64fa58aa76bc7f6d8a616a64f0d627c6712f19` |
| `FORWARD_RESIDUAL_LIVE_OUTCOME_SUMMARY.md` | `d933eda5432e3d5b991070746f80cb2472ecbf03b20b989f8a56b630c7d88347` |

Ten focused tests pass. Ruff and both PowerShell parser checks pass.

## Unattended deployment

Windows task: `Codex-EURUSD-Forward-Residual-Live-Outcome`

- limited interactive principal;
- daily at 06:20 Dubai / 02:20 UTC;
- after the six-hour live horizon and terminal residual evaluator;
- before the 06:25 combined portfolio monitor;
- three retries;
- 20-minute execution limit;
- first manual run result: 0;
- missed runs: 0; and
- next scheduled run at deployment: 2026-07-31 06:20 Dubai.

## Remaining work

The residual pipeline can now produce defensible live selections, actual MT5
entry receipts, raw-tick outcomes, and selection parity.

The final combined admission ledger must next use these live outcomes—not the
research residual outcomes—alongside the protected M15 forward component.
Actual profitability and approximately one-trade-per-weekday frequency remain
unproven until sufficient August-forward observations accumulate.

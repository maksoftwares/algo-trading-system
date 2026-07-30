# EURUSD forward residual-regime deployment — 2026-07-30

## Result

The disarmed residual-regime specialist is frozen and running unattended
against the prospective demo collector. It cannot place orders.

This is the next evidence-producing step toward the approximately one-trade-
per-weekday goal. It does not yet prove that goal or qualify the combined
system for demo execution.

## Why the frequency goal is still unmet

The protected M15 chop/compression sleeve produced 106 trades over 522
weekdays, or 0.203 trades per weekday, with executable PF 1.411. Adding the
rejected daily learner raises the projected rate only to 0.216 per weekday.

The closest strictly causal historical frequency construction reached:

- 447 combined trades over 522 weekdays;
- 0.856 trades per weekday;
- 43.30% weekday coverage;
- 1.487 raw PF and 1.374 stressed PF; and
- 0.938 PF after removing its best 5% of trades.

It therefore met the minimum average-activity screen but did not reach one
trade per weekday, traded on fewer than half of weekdays, and did not retain
edge without its best 5% of outcomes. Its trailing segment was also too weak
for independent admission. Reusing more correlated signals from that same
family would increase trade count without establishing a new edge.

The missing component is an independently validated opportunity on weekdays
the protected system leaves empty.

## Frozen campaign

Campaign: `EURUSD_FORWARD_RESIDUAL_REGIME_V1`

The implementation was locked at `2026-07-30T08:20:07Z`, before the
`2026.08.01 00:00:00` UTC forward floor. At lock time:

- prospective post-floor feature rows: 0;
- residual decisions: 0;
- residual eligible trades: 0;
- historical backtesting: prohibited; and
- demo-order authorization: false.

The SHA-256 lock covers the config, protocol, runner, specialist, tests,
operations scripts, shared forward engine, and frozen M15 ownership
adjudicator.

## Regime and ownership design

The evaluator gets at most one 20:00 UTC opportunity on a weekday not already
owned by the M15 portfolio or daily learner. It assigns every complete residual
day to one of five causal regimes:

1. cross-pair compression;
2. broad EUR up;
3. broad EUR down;
4. short/long disagreement; or
5. mixed transition.

Each long or short regime expert learns only from its own prior fully resolved
forward observations. It starts with 20 residual warm-up days and fails to cash
unless the frozen expectation, PF, cost-stress, and recent-performance gates
all pass.

## Prestart verification

The frozen runner completed against the live ledger with:

- status: `WAITING_FORWARD_DATA`;
- complete weekdays: 0;
- residual decisions: 0;
- eligible trades: 0;
- incremental weekday coverage: 0.00%;
- admission: `WAITING_MINIMUM_EVIDENCE`; and
- `demo_order_authorized=false`.

The deployed prestart state has these immutable output hashes:

| File | SHA-256 |
|---|---|
| `FORWARD_RESIDUAL_DECISIONS.json` | `a5338d955b09046ec0b16f3a9625b7955c763aae07dc722e474e6078745f932f` |
| `FORWARD_RESIDUAL_SUMMARY.json` | `f1b31c746e24a6903126c5c9b49f8a36d8d23b4a745742d8131518fdc18268a6` |
| `FORWARD_RESIDUAL_SUMMARY.md` | `3e344b087e561f54a7448028236975cbf51908259ef464d81b82fb30524c6a40` |

Five focused tests passed, Ruff passed, and both PowerShell operations scripts
passed parser validation.

## Unattended deployment

Windows task: `Codex-EURUSD-Forward-Residual-Regime`

- principal: current interactive user, limited run level;
- trigger: 06:15 Dubai / 02:15 UTC daily;
- multiple instances: ignored;
- retry count: 3;
- execution limit: 15 minutes;
- first manual run: result 0 with zero missed runs; and
- next scheduled run at deployment: 2026-07-31 06:15 Dubai.

The schedule is 15 minutes after the prior day's maximum six-hour outcome
window. The operations wrapper verifies the frozen hashes, enforces an
append-only decision ledger, and rejects any unexpected order authorization.

## Remaining admission work

Deployment here means forward research collection, not demo ordering. The
combined system still requires:

- at least 160 complete prospective weekdays;
- at least 80 residual decisions and 50 eligible residual trades;
- at least 20% incremental weekday coverage;
- PF, payoff, stress, concentration, and chronological-half gates;
- combined portfolio frequency and weekday-coverage proof;
- MT5 signal and outcome parity; and
- disarmed demo-shadow soak.

Only a separately reviewed successor portfolio may authorize demo orders after
all of those checks pass.

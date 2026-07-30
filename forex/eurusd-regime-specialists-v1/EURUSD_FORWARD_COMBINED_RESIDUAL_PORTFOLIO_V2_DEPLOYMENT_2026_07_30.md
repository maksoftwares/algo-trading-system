# EURUSD combined residual forward portfolio v2 deployment — 2026-07-30

## Result

The residual-aware combined admission monitor is frozen and running
unattended. It measures the requested final portfolio rather than the earlier
two-component construction.

The monitor has no order path and cannot authorize demo orders.

## Why a successor was required

The original combined forward validator contained only:

- the protected M15 chop-plus-compression portfolio; and
- the frozen daily cross-pair learner.

The exact historical diagnostic rejected the daily learner as a frequency
sleeve. It produced only 34 trades over 2,571 post-warmup weekdays, PF 0.909,
and negative net R. The original validator therefore could not evaluate the new
residual-day specialist or determine whether the missing weekday coverage had
actually been recovered.

V2 retains the M15 and daily inputs, adds the frozen residual-regime component,
and gives both M15 sources priority over research components under overlap.

## Frozen target

The V2 portfolio is admitted only if it demonstrates:

- 160 complete prospective validation weekdays;
- at least 136 combined trades and 50 residual trades;
- 0.85 through 1.25 trades per complete weekday;
- at least 65% weekday trade coverage;
- 45% through 60% wins;
- payoff ratio at least 1.25;
- PF at least 1.15 and stressed PF at least 1.05;
- best-5%-removed PF at least 1.00;
- both chronological trade halves above PF 1.00;
- positive net P&L;
- maximum USD 75 closed-trade drawdown;
- maximum 40% single-month gross-profit share;
- M15 and residual component PF of at least 1.15;
- daily PF of at least 1.10 if that component contributes any trade;
- every participating component's independent economic, parity, and soak
  requirements; and
- combined MT5 ordering parity and disarmed demo soak.

The calendar denominator requires 240 valid prospective EURUSD M5 intervals
and terminal daily and residual decisions. Missing days are not imputed.

## Prestart boundary

The implementation was locked at `2026-07-30T08:35:09Z`, before the
`2026.08.01 00:00:00` UTC forward floor. At lock time:

- post-floor feature rows: 0;
- M15 terminal outcomes: 0;
- daily decisions: 0;
- residual decisions: 0;
- V2 portfolio decisions: 0;
- historical backtesting: prohibited; and
- demo-order authorization: false.

The lock covers the V2 contract, implementation, tests, operations scripts,
the unchanged V1 combination engine, and the upstream M15 and residual lock
receipts.

## Verification

The V2 prestart result is:

- status: `WAITING_MINIMUM_EVIDENCE`;
- complete validation weekdays: 0;
- combined trades: 0;
- trades per complete weekday: 0.000000;
- weekday coverage: 0.000000;
- component trade counts: M15 0, daily 0, residual 0; and
- `demo_order_authorized=false`.

Repository and deployed prestart outputs match:

| File | SHA-256 |
|---|---|
| `FORWARD_PORTFOLIO_LEDGER.json` | `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570` |
| `FORWARD_SUMMARY.json` | `1e9f4058c369bf0f5ab1f36c1adb3cea5280e70ec5ea64eaa2ad95df9eed2fc9` |
| `FORWARD_SUMMARY.md` | `d3f230de00becddca09c27466762f9b84dfd6e156a79d17ddf5932f5c87ed0e6` |

Ten focused tests pass, including:

- residual trade normalization and stress;
- both-learner warm-up boundary;
- dual-ledger terminal-day finalization;
- protected M15 risk priority;
- exact frequency/win/payoff/PF target acceptance;
- participating daily component admission;
- pre-warm-up refusal;
- append-only mutation refusal;
- no-order contract guards; and
- frozen hash verification.

Ruff and both PowerShell parser checks pass.

## Unattended operation

Windows task: `Codex-EURUSD-Forward-Combined-Residual-V2`

- limited interactive principal;
- daily at 06:25 Dubai / 02:25 UTC;
- ten minutes after the residual evaluator;
- maximum one concurrent instance;
- three automatic retries;
- 15-minute execution limit;
- first manual run result: 0;
- missed runs: 0; and
- next scheduled run at deployment: 2026-07-31 06:25 Dubai.

The task reads only append-only forward ledgers, verifies the V2 lock, writes
an append-only combined portfolio ledger, and fails if either summary layer
ever reports order authorization.

## Deployment meaning

The monitor and specialists are deployable for disarmed demo shadow research.
The portfolio is not deployable for demo orders today. A guarded demo-order
package may be created only after every frozen economic, frequency, parity,
and soak gate passes.

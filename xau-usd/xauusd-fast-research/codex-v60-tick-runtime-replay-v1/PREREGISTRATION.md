# V60 Tick Runtime Replay V1 Preregistration

Status: locked before inspecting replay outcomes.

## Purpose

Test whether the capital/reinitialization and flat re-baseline proposals survive
the deployed V60 execution controls when open-position equity is valued from
Dukascopy bid/ask ticks and the attached MT5 daily guardian is reproduced.

This package is read-only research. It does not authorize or modify MT5, the
demo account, runtime state, risk limits, ML, or live trading.

## Population

- Start from the frozen V60 price ledger.
- Keep entries on or after `2021-01-01T00:00:00Z`.
- Exclude `R5_TRANSITION`, which is not deployed.
- Do not pre-apply the V57 cooldown. Apply its 120-minute same-direction
  post-loss cooldown dynamically from losses actually accepted by each replay.
- Keep every other candidate. Runtime gates decide whether it is accepted.
- Resolve R1 initial risk from the native MT5 reconciliation:
  - stop exit: `entry - stop`;
  - target exit: `(target - entry) / 2`, because both R1 sources use 2R targets.

## Market Replay

- Source: raw Dukascopy XAUUSD bid/ask tick JSON.
- Runtime observation grid: UTC epoch-aligned 5-second cycles, matching the
  Python executor's configured poll period.
- At each cycle use the latest source tick at or before the cycle.
- Reject an entry when that source tick is older than the deployed 30-second
  limit.
- Retain each source trade's locked entry price, exit time, normal exit price,
  and fee-stressed P&L.
- Calibrate a static, causal cross-venue price offset at entry so Dukascopy
  changes value the source position without introducing a future price.
- Long positions mark to bid; short positions mark to ask.
- Emergency closes use the current adjusted bid/ask and the frozen open-cost
  field.
- Maintain separate account-realized P&L and V60-tracked closed P&L. MT5
  evidence shows the attached guardian's exit deal uses guardian magic
  `919200`; the deployed Python `closed_pnl()` filters only specialist magics.
  Guardian P&L therefore changes account equity but is absent from the V60
  closed-drawdown state.

## Event Ordering

At each 5-second cycle:

1. Reset the guardian when a new Dubai day is first observed.
2. Apply an eligible flat re-baseline.
3. Settle source exits due at or before the cycle.
4. Evaluate the daily guardian.
5. Refresh V60 equity and closed-P&L drawdown state.
6. Apply V60 floating or closed hard-stop emergency closes.
7. Process due candidates in `(scheduled time, source ID, trade ID)` order.

Exits therefore settle before same-cycle entries. Rejected candidates are
consumed, not deferred.

## Reproduced V60 Gates

- source maximum risk;
- entry halt from the guardian;
- closed-drawdown suspend/resume;
- floating and closed hard stops;
- account and directional concurrent initial risk;
- core, add-on, account, and source position caps;
- add-on concurrent risk;
- V57 post-loss cooldown;
- source, account, and add-on UTC-day quotas;
- duplicate add-on event;
- stale source tick;
- source spread-to-risk ratio.

Broker minimum-stop changes and historical broker order rejections are not
recoverable and are reported as limitations.

## Guardian

Reproduce the attached settings, converted at `3.6725 AED/USD`:

- arm and halt new entries at `+50 AED` daily equity P&L;
- use the `+100 AED` return floor after that level is reached;
- lock and close all simulated positions at `-100 AED`;
- after arming, lock and close if equity returns to the active floor;
- reset at midnight Dubai (`20:00 UTC`).

The guardian is observed on the same 5-second grid as the executor. Its real
timer is two seconds and has an unknowable phase relative to the Python process,
so this is a bounded timing approximation, not a claim of identical ordering
within a five-second interval.

Guardian exits count in account P&L, equity, win rate, and profit factor. They
do not count in the deployed V60 closed-P&L state because their broker deal
magic is not one of the specialist magics.

## Scenarios

Run each policy both without and with the guardian:

- deployed activation and starting equity: `$987.6623553437713`;
- deposit-only: `$3,000` starting equity with activation equity still
  `$987.6623553437713`;
- authorized-style state reinitialization at `$3,000`;
- state reinitialization at `$3,000` plus flat re-baseline after 14, 30, 60,
  or 90 days.

After confirming the broker's guardian-magic behavior, run one diagnostic
counterfactual at `$3,000`: attribute guardian exit P&L to the originating
specialist position. This is a test of the accounting defect's consequence,
not a deployed behavior or authorization.

### Position-origin repair verification amendment

Locked before rerunning the replay against the repaired runtime source:

- retain every original deployed and re-baseline scenario unchanged;
- relabel the position-origin behavior as the implemented repair;
- evaluate it at both the actual `$987.6623553437713` activation capital and
  the proposed `$3,000` funded/reinitialized capital;
- use each scenario's effective fractional risk caps, not only the nominal
  absolute caps, for the repair assessment;
- do not authorize deployment from this read-only replay.

A re-baseline resets only the closed-P&L policy peak and suspension state. It
does not erase lifetime drawdown evidence or the executor's running peak-equity
reference. This is the narrowest interpretation of the proposed resume change.

## Decision Rule

No proposal is demo-ready from this replay alone.

Reject a proposal if it:

- remains permanently suspended or hard-stopped;
- requires forgiving the floating-equity peak to function;
- breaches the nominal absolute `$300` closed or `$449.7675` floating safety
  evidence on the true lifetime path;
- materially depends on an unmodelled broker behavior;
- or loses the claimed economic advantage after runtime gates and guardian.

Any funding, state migration, or re-baseline remains a separate owner decision
and implementation review even if the replay is favorable.

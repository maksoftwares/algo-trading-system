# EURUSD Neutral prospective campaign orchestration V1.1 preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

This operational layer closes the gap between the frozen evidence captures and
prospective execution V2.1. It does not change the signal, regime, entry, risk,
target, hold, cost, frequency, or admission rules.

V1.1 supersedes the original orchestration lock before any prospective signal
or terminal trade existed. The original lock remains immutable. The only added
capability is ingestion of the separately frozen, late-known hindsight-oracle
evidence for admission measurement after terminal trade reconciliation.

The event-market parquet is created before its manifest and therefore cannot
contain the hash of that later manifest. The execution contract requires both
the normalized market snapshot hash and manifest hash. The orchestrator must
validate the manifest and every referenced raw, metadata, and normalized file,
then inject those two hashes in memory before constructing a signal. It never
rewrites source evidence.

The same validation applies to linked forecast/actual snapshots, five-market
Neutral ownership, and completed EURUSD trade paths. Relative references must
stay inside their declared evidence root. Missing, duplicated, drifted, or
tampered evidence fails closed.

The oracle loader validates its content-addressed manifest, exact 36-hour raw
EURUSD inventory, metadata linkage, completed M5 snapshot, label snapshot, and
referenced next-day ownership manifest and record. An oracle date is invisible
to evaluation until its frozen safe-known timestamp. A completed date with
fewer than four hindsight winners is a known negative date, not a reason to
retune. Only same-day/same-side matches to `NEUTRAL` oracle rows enter the
precision gate.

Four trades per day belongs only to the historical oracle definition. It is
not a prospective strategy-frequency requirement or admission gate. The
strategy may trade less often; profitability, cost robustness, drawdown, and
chronological evidence take priority, and oracle labels may never be used to
manufacture additional trades.

## Immutable state transitions

- One content-addressed signal record may exist per signal ID and exact event.
- A later source revision cannot replace a signal already reconstructed from
  the frozen earliest-admissible evidence rule.
- Cash signals become terminal `CASH_NO_TRADE` records without requesting a
  path.
- A non-cash signal without a complete 144-row path remains pending and is not
  written as a terminal trade.
- While an earlier non-cash outcome is pending, later non-cash signals remain
  blocked and are not written as terminal decisions.
- A signal entering at or before a prior position's exit is terminally skipped.
- A complete path is evaluated with the frozen bid/ask, spread, slippage,
  structural-stop, stop-first, 1.5R, and 12-hour rules.
- Existing signal and terminal-trade records must exactly match a fresh
  reconstruction. No overwrite or revision is permitted.
- Nullable oracle labels are attached in memory only after terminal trade
  reconciliation. They are never written into signal or trade records and may
  not alter evidence selection, entries, routing, risk, sizing, or exits.
- A trade remains unlabeled until its whole oracle date is safely known. Once
  that date is complete, absence of a same-day/same-side Neutral oracle row is
  recorded as `false`, including an oracle-unavailable date.

The processing command reads local evidence and writes only append-only
research ledgers. It makes no network request, loads no historical P&L, performs
no parameter search, and cannot place broker orders. Passing the eventual
prospective admission gates still authorizes research review only.

## Reproduction commands

From this package directory, with `src` on `PYTHONPATH`:

```powershell
python run_prospective_neutral_campaign_v1.py status
python run_prospective_neutral_campaign_v1.py process
```

`status` validates all evidence and immutable ledger records without writing.
`process` performs the same reconstruction and appends only newly terminal
signal/trade records plus a content-addressed process manifest. Network capture
remains in the separately frozen ownership, linked-actual, event-market, and
trade-path capture commands; processing never invokes those commands itself.

# EURUSD Neutral prospective operations planner preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_PROSPECTIVE_START_AND_FIRST_SIGNAL`

The planner is a local, read-only control layer for the frozen EURUSD Neutral
prospective campaign. It does not fetch data, write evidence, process a
signal, load historical P&L, change a parameter, or call a broker. It reports
which already locked command is due and the earliest safe time to run it.

The planner is bound to campaign orchestration V1.2 lock
`759f6cdda68ae2ee469c681524ce446c0448944c3c5fb35734b3fd88f7b4ce2e`
and exact hashes of every capture command it may print.

## Validated inputs

Every consensus manifest and its raw, metadata, and normalized references are
hash-validated before the calendar watchlist is used. The latest immutable raw
snapshot supplies the current CPI, PPI, and NFP event identities. Previously
captured forecast or actual rows preserve a target event after it leaves the
latest forward calendar window.

Actual, event-market, ownership, path, oracle, signal, and terminal-ledger
evidence is loaded through the frozen point-in-time campaign validators. Data
later than `as_of` is never made decision-visible.

## Frozen forecast polling cadence

Polling cadence depends only on time remaining to the scheduled release:

- at least 72 hours: every 24 hours;
- 6 to 72 hours: every 6 hours;
- 1 to 6 hours: every hour;
- 10 to 60 minutes: every 10 minutes; and
- 1 to 10 minutes: every minute.

If no admissible forecast exists by release minus 60 seconds, the event is
terminally reported `MISSED_NO_TRADE`. No historical backfill is suggested.

## Frozen safe actions

The planner reports, but never runs:

- append-only pre-release forecast capture;
- bounded rolling ownership-cache prewarm;
- event-date Neutral ownership capture after midnight plus 60 seconds;
- linked actual capture after release plus 60 seconds;
- three-bar cross-asset market capture after release plus 16 minutes;
- local campaign processing when a new immutable state is terminal;
- complete trade-path capture after entry plus 12 hours plus 60 seconds; and
- evaluation-only oracle capture after date midnight plus 36 hours plus
  60 seconds.

The rolling cache is checked only for the nearest upcoming target event. If
all safely completed hours are cached, the next check is scheduled for the
next hour end plus 60 seconds. If a safe gap exists, the planner prints the
bounded 120-request prewarm command.

## Fail-closed behavior

- Missing or hash-drifted immutable evidence stops planning.
- An ambiguous event identity stops planning.
- A missed forecast produces no-trade, not a late substitute.
- Actual, market, ownership, path, and oracle commands cannot become due
  before their safe times.
- No command is executed automatically.
- Four trades per day is not referenced by the planner.
- Profitability, PF, payoff, drawdown, and oracle similarity remain measured
  only by the frozen prospective campaign.

At the first live read-only run, all three target events were visible, no
forecast was populated, the campaign was still waiting for prospective start,
and the planner detected five newly safe ownership-cache symbol-hours. The
next forecast poll was scheduled for `2026-07-29T15:50:54Z`.

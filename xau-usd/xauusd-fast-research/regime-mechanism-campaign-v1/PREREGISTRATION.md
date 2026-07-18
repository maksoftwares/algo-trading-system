# XAUUSD Regime Mechanism Campaign V1 Preregistration

## Purpose

This campaign changes the research approach after the frozen R2 portability test
failed. It tests genuinely different mechanics for downtrend, compression, chop,
and transition states instead of making more small changes to one pullback rule.

## Information boundary

All data from 2010-01-01 through 2026-07-01 has already been exposed elsewhere in
the wider research program. The four chronological eras in this campaign are
therefore discovery robustness segments, not pristine holdouts. No result from
this package may be described as untouched out-of-sample evidence.

The campaign may nominate definitions for a separately locked raw-tick
confirmation. It cannot authorize model training, EA consumption, demo trading,
or live trading. A later candidate also requires prospective shadow evidence.

## Attempts

- Attempts: `11118` through `15117` inclusive.
- Total: 4,000.
- Regime owners: downtrend, compression, chop, transition.
- Five mechanics per regime and 200 deterministically sampled parameter sets per
  mechanic.
- The manifest is generated from this locked source before outcomes are scored.

## Screen execution

- Signals use only completed H1 and completed H4 information.
- Entry is the next available H1 executable open, ask for long and bid for short.
- A protective ATR stop is active from entry.
- Stops are checked before the fixed-horizon exit and same-bar ambiguity is
  resolved against the strategy.
- Long stops use bid prices; short stops use ask prices.
- Spread is paid through side-specific prices.
- Ticket cost, holding cost, and 0.05R stress slippage are deducted.
- A variant holds at most one position and takes at most four entries per UTC day.

This H1 screen is deliberately conservative but does not model tick-level stop
slippage. Any finalist must be replayed using the already verified raw Dukascopy
tick executor.

## Chronological robustness

Every variant is scored separately in 2010-2014, 2014-2018, 2018-2022, and
2022-2026. Economic nomination requires all four eras to pass the registered
minimum sample, PF, and average-R gates, plus whole-period PF, drawdown, and
top-winner-removal gates.

Daily one-sided p-values and Benjamini-Hochberg q-values are reported across all
4,000 attempts. Economic nomination and statistical support are reported
separately. No isolated high-PF, low-sample result is a survivor.

## Decision rule

The only positive V1 decision is `ECONOMIC_RAW_TICK_FINALISTS_FOUND`. This means
definitions may proceed to a new, frozen raw-tick package. It does not mean a
tradable specialist has been proven. If no variant passes, V1 remains a recorded
failed mechanism campaign and is not tuned after outcomes are opened.

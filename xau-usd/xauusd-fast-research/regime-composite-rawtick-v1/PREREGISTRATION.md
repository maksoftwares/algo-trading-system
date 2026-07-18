# XAUUSD Regime Composite Raw-Tick V1 Preregistration

## Purpose

The 4,000-attempt V1 mechanism campaign found no individual full survivor. A
post-outcome composite diagnostic then found two combinations that passed all
seven registered economic gates under conservative H1 execution:

- downtrend: origin attempts 11142 and 11266;
- compression: origin attempts 12183, 12222, and 12389.

This package freezes those exact combinations and checks whether their economics
survive chronological Dukascopy bid/ask tick execution.

## Selection bias

These composites were chosen after V1 outcomes were open. Fifteen downtrend
subsets and seven compression subsets were inspected. The raw-tick replay is an
execution-fidelity confirmation on already exposed history, not an independent
holdout. Its p-values are reported both raw and multiplied by the applicable
subset count. No result from this package can authorize training or trading.

## Candidate boundary

Candidate timestamps and frozen parameters are generated from the committed V1
manifest and causal completed H1/H4 features. The candidate parquet and its hash
are locked before raw outcomes are opened. Components and same-time priority are
fixed by ascending origin attempt number.

## Raw execution

- Entry is the first verified quote at or after the next H1 open, within 10
  minutes.
- Longs buy ask and stop/exit on bid. Shorts sell bid and stop/exit on ask.
- The H1 ATR stop distance is frozen before entry.
- A stop fills at the observed executable quote that first crosses it, including
  slippage and weekend gaps.
- If no stop occurs, exit is the first verified quote at or after the fixed
  horizon, allowing up to 96 hours for a weekend reopening.
- Ticket cost, holding cost, and 0.05R stress slippage are deducted.
- Each component holds one position at a time and takes at most four entries per
  UTC day. The composite then enforces one shared position at a time.

## Decision

`RAW_TICK_ECONOMIC_COMPOSITE_FOUND` requires every registered economic gate to
pass under raw execution. This is only an execution-qualified historical
candidate. Prospective shadow evidence, portfolio controls, and a later decision
are still required before any demo use.

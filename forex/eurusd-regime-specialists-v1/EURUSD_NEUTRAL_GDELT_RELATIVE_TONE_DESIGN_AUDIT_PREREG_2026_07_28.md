# EURUSD Neutral GDELT relative-tone design audit preregistration

Date: `2026-07-28`

Status: `FROZEN_BEFORE_HISTORICAL_GKG_TONE_INSPECTION`

The frozen GDELT coverage census passed every source-capacity gate. That
result permits this second, source-only audit. It does not permit EURUSD
price testing, oracle matching, a strategy claim, or broker activity.

## One frozen candidate transform

For each of the 24 census entry dates, reuse the exact strict central-bank
document filter and deduplicate by GKG document identifier. Parse only the
first component of `V2Tone`.

A date has source quorum only when both ECB and Fed documents come from at
least two unique sources and no source supplies more than half of either
side. Within each side, take the median tone per source and then the median
across sources. Define relative tone as ECB minus Fed.

The pooled dispersion is the median absolute deviation of all ECB and Fed
source-level scores on that date, floored at `0.5`. A candidate exists only
when absolute relative tone divided by that dispersion is at least `1.0`.
Positive relative tone maps to a hypothetical EURUSD long candidate and
negative relative tone maps to a hypothetical short candidate.

This mapping is an economic hypothesis, not evidence of return predictability.
The audit does not define entry execution, stops, targets, sizing, or a trade.

## Frozen source-only gates

The transform may proceed to a separately preregistered prospective expert
only if:

- at least 99% of strict documents have finite tone;
- at least eight sampled dates have two qualifying sources on both sides;
- at least six dates produce a candidate;
- at least two candidates occur in each direction; and
- neither direction exceeds 80% of candidates.

Failure closes the relative-tone lane without trying another formula.
Passing permits only a prospective strategy preregistration before its first
signal.

Historical EURUSD prices, returns, oracle rows, and P&L are forbidden. No
broker action is authorized.

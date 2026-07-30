# Frozen prospective data protocol

Protocol version: `EURUSD_PROSPECTIVE_MULTISYMBOL_V1`

Frozen forward floor: `2026-08-01 00:00:00 UTC`

## Purpose

The historical EURUSD search has produced one cost-surviving but sparse H4
edge. Repeated attempts to increase frequency on the same archive failed out of
sample. This protocol gathers new information without modifying the admitted
H4 sleeve or claiming that data collection itself creates an edge.

## Collection contract

1. Attach the compiled observer to the exact configured EURUSD M5 chart.
2. Use a demo account. A real-money account causes startup failure.
3. At startup, latch the current M5 open and do not collect a historical bar.
4. On each later native M5 transition, collect only the just-completed interval.
5. Query each source independently with an inclusive millisecond range from
   interval open through one millisecond before interval close.
6. Never forward-fill, interpolate, or substitute a missing source.
7. Preserve the raw CSV files. Any cleaning creates a derived file and leaves
   the original unchanged.
8. Strategy Tester rows are smoke-test rows and are never prospective evidence.
9. Live rows earlier than the frozen forward floor are refused.
10. No feature in this collector is a preauthorized trade signal.

## Frozen fields

For each source and interval, retain:

- broker-time and configured-UTC interval boundaries;
- source status and terminal error code;
- copied tick count and valid two-sided quote count;
- first and last source tick timestamps;
- first, last, high, and low bid;
- first, last, high, and low ask;
- minimum, mean, and maximum spread in source points;
- symbol digits and point size;
- current broker/UTC offset assumption;
- run, account, server, terminal build, and tester/demo scope metadata.

## Data tranches

- Tranche A: first 60 active collection days. It may be used for source-quality
  auditing and for defining at most one directional model family.
- Before looking at Tranche B outcomes, freeze that family, its features,
  thresholds, stop/target, costs, missing-data behavior, and kill criteria.
- Tranche B: next 60 active collection days. It is untouched validation.
- A failed Tranche B family is rejected. Its side may not be reversed post-hoc,
  and its threshold may not be tuned on Tranche B.

## Minimum admission gate for a new sleeve

A candidate cannot be added to demo ordering unless all of the following hold:

- at least 50 untouched Tranche B trades and at least 40 active validation days;
- exact bid/ask execution with entry and exit slippage assumptions;
- positive net expectancy and profit factor above 1.10 after base costs;
- positive expectancy under an additional 0.5 pip round-trip stress;
- payoff ratio at least 1.25;
- no single calendar month contributes more than 50% of total net profit;
- removing the five best trades leaves profit factor at least 1.00;
- no overlap or risk-budget conflict with the protected H4 sleeve;
- MT5 implementation parity and a separate shadow-demo soak pass.

These are admission floors, not a promise that the resulting sleeve will reach
one trade per day. Frequency is measured only after accepted sleeves are
combined.

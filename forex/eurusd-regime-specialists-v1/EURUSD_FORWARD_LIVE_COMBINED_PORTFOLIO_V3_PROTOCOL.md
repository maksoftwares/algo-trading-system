# EURUSD live-only combined forward portfolio v3 protocol

## Purpose

This is the final economic and frequency admission ledger for the requested
EURUSD portfolio. It combines only:

1. the unchanged protected M15 chop and compression outcomes; and
2. residual-regime outcomes produced from a pre-outcome signal, an exact MT5
   demo quote, and immutable raw broker ticks.

The research residual P&L ledger is prohibited as an input. The rejected daily
learner is also excluded: its historical diagnostic produced PF 0.909 and only
0.013 trade per weekday. This exclusion was made before the forward floor, not
after seeing V3 results.

V3 is an admission monitor, not an order router. It always writes
`demo_order_authorized=false`.

## Causal evidence chain

A residual weekday becomes final only when:

- the prospective EURUSD feature file contains at least 240 valid M5 intervals;
- the frozen publisher has an immutable terminal decision for that date;
- the publisher decision has a later selection-parity record;
- a published trade signal has a terminal live outcome;
- a resolved live outcome contains one exact entry-tick match and an immutable
  raw-tick digest; and
- no earlier M15 signal remains pending.

A cash publisher decision needs no outcome, but still counts in the calendar
denominator. Friday market-closure cash carries a self-terminal operational
parity record, so a nonexistent post-close six-hour path cannot freeze the
calendar. Missing days and missing ticks are not imputed.

Validation starts with the first terminal residual decision whose prior online
training count is at least 20. All accepted P&L comes from broker-observed
forward outcomes after `2026.08.01 00:00:00` UTC.

## Risk and ownership

M15 chop and compression retain priority. The residual trade is considered
after the protected sources. The portfolio permits at most three concurrent
positions and USD 15 of concurrent initial risk. More than 5% causal risk-cap
rejections fails admission.

M15 keeps its frozen sizing. Residual risk is fixed at 0.01 lot with an
eight-pip initial stop. No component deletion, reweighting, threshold change,
or force-trading on cash days is allowed.

## Frozen admission target

Admission requires all of:

- at least 160 complete prospective weekdays;
- at least 136 accepted trades, including 50 live residual trades;
- 0.85 through 1.25 trades per complete weekday;
- trades on at least 65% of complete weekdays;
- 45% through 60% wins;
- payoff ratio at least 1.25;
- PF at least 1.15;
- stressed PF at least 1.05 after another 0.5 pip per trade;
- best-5%-removed PF at least 1.00;
- both chronological trade halves above PF 1.00;
- positive net P&L;
- maximum USD 75 closed-trade drawdown;
- no month above 40% of gross positive P&L;
- M15 component PF at least 1.15;
- live residual component PF at least 1.15;
- zero invalid outcomes and zero residual selection mismatches;
- independent economic admission for both components;
- component MT5 parity and shadow soak; and
- combined MT5 ordering parity and combined disarmed-demo soak.

The last two combined execution checks remain false until a separate guarded
execution package produces that evidence. Economic success alone cannot enable
orders.

## Frozen prohibitions

Historical backfill, research-outcome substitution, daily-learner
participation, missing-data imputation, prior-ledger mutation, protected
component deletion, post-result tuning, and order routing are prohibited.

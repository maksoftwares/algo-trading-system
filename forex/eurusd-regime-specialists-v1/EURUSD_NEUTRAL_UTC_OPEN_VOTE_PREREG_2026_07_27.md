# EURUSD Neutral UTC-open cross-market vote preregistration

Frozen: 2026-07-27 16:55 UTC

Campaign: `eurusd-neutral-utc-open-vote-v1`

## Hypothesis

The hindsight oracle's dominant timing is an artifact of scanning each UTC
date from midnight, but that timing can still be challenged causally. A
single deterministic opening-auction specialist will enter at 00:00 UTC
only when completed pre-open EURUSD, EURGBP, EURJPY, and prior DXY-session
returns provide a three-of-four directional vote.

This is a deliberately narrow deterministic baseline. It is not ML, does
not use an oracle label to choose direction, does not rank future
candidates, and cannot stack four copies of the same daily opportunity.

All archived history is already development data. The annual windows are
chronological falsification, not pristine out-of-sample evidence.

## Frozen signal

For a potential 00:00 UTC entry:

1. The EURUSD regime state must be non-shock, non-compressed `NEUTRAL`
   using the latest fully completed hourly state.
2. EURUSD, EURGBP, and EURJPY use exact completed M5 bars through 23:55.
3. Each FX vote is the sign of the exact 60-minute mid-price return ending
   at 23:55. Both endpoints must exist exactly 60 minutes apart.
4. DXY is normally closed at 23:55. Its vote uses the negative sign of the
   latest completed, contiguous 60-minute DXY return whose endpoint is no
   later than 23:55 and no more than 240 minutes old.
5. All four votes must be nonzero.
6. Vote sum of at least +2 enters one EURUSD long; vote sum at most -2
   enters one short; a 2-2 tie remains cash.
7. Only one position and one entry per UTC date are allowed.

The DXY rule is an explicit prior-session handoff with a hard freshness
limit. It is not an unbounded forward-fill.

## Outcome-blind census

Before any target, stop, oracle-side, or P&L inspection for this rule:

- 655 Neutral 00:00 candidates existed;
- 464 had four valid nonzero votes;
- 314 passed three-of-four agreement;
- 157 were long and 157 were short;
- forward-window counts were 39 in 2023, 33 in 2024, 40 in 2025, and 23
  in 2026 H1.

The frozen census gate requires at least 300 total candidates, 30 in each
full forward year, and 15 in 2026 H1.

## Execution

- fixed 4-pip risk;
- 1.50R target;
- 12-hour maximum hold;
- exact bid/ask execution;
- 0.70-pip minimum retail spread;
- 0.10-pip adverse slippage per side;
- stop first when an M5 bar touches both stop and target;
- one open position and one trade per UTC date;
- 0.25 portfolio-R per position.

## Evaluation and rejection

The deterministic rule has no fitted parameter and no threshold selection.
Development is 2019-2022. Frozen forward windows are 2023, 2024, 2025, and
2026 H1.

Development and every forward window must reach the frozen sample,
45%-55% win-rate, 1.35-1.75 payoff, PF 1.10, and positive-expectancy gates.
Overall maximum drawdown must not exceed 30R. Net R must remain positive
after an extra half-pip round trip and after removing the largest 5% of
winners.

Behavioral admission additionally requires at least 25% exact oracle-match
precision, 2% exact recall, and 25% same-side precision within 15 minutes.
Oracle rows are evaluation-only and are loaded only after candidate
direction and execution outcomes have been generated.

Any failure rejects the expert. No post-outcome vote, horizon, freshness,
entry-time, direction, or gate repair is permitted.

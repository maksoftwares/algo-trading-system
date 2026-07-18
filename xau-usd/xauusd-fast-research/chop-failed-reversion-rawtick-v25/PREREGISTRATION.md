# Chop Failed-Reversion Raw-Tick V25 Preregistration

## Frozen origin

V24 attempt 39583 is the sole V25 hypothesis. It was selected after V24 outcomes
because it is the simpler of two overlapping economic finalists and has the more
stable era profile. Its frozen identity is:

- Variant `229111b27bb96c07`.
- H4 regime owner `CHOP`.
- Mechanic `CHOP_COUNTERFLOW_DUAL_WINDOW_ENVELOPE`.
- 1,986 raw signals and 131 M5-simulated trades.
- Window 384, z-score at least 1.0, variance-ratio horizon 4 at most 1.1,
  return autocorrelation at most -0.1, and absolute mean slope at most 0.35.
- Current or one-bar-old M15 state.
- Either the 3-bar or 12-bar M5 move is counter-directional or flat, while tick
  imbalance is at most -0.01 in the proposed trade direction.
- 1.0 latest-completed-H1 ATR stop, 2.0R target, and 12-hour hold.

No alternate V24 policy enters V25.

## Independent signal parity

V25 independently implements the frozen Boolean policy. Before raw outcomes are
opened, its signal mask, direction vector, signal count, and SHA-256 signal-stream
digest must equal V24 exactly. Candidate generation also requires contiguous M5
coverage through each scheduled 12-hour horizon.

## Raw-tick execution

- Verified free Dukascopy XAUUSD bid/ask ticks cover 2016-07-01 through
  2026-07-01; 120 complete frozen monthly manifests are locked.
- Entry uses the first executable quote at or after the next M5 open.
- Longs enter on ask and exit on bid; shorts enter on bid and exit on ask.
- The first chronological executable stop or target tick wins. Stop crossing fills
  at the observed quote; target crossing fills at the frozen target.
- If neither threshold is reached, exit uses the first executable quote at or
  after the scheduled 12-hour deadline.
- Spread, $0.30 ticket cost, $0.35 per 24-hour holding cost, and 0.05R stress
  slippage are deducted.
- One open position, a five-minute cooldown, and at most four trades per UTC day
  match V24's policy accounting.

## Frozen gates

The V24 economic gates remain unchanged: at least 100 trades and 15 per era,
total stress PF at least 1.25, every-era PF at least 1.10, every-era average at
least +0.02R, closed drawdown no more than 25R, and positive net R after removing
the five largest winners.

The raw-tick daily p-value and the conservative 1,000-policy adjusted p-value are
reported. Because the same historical price path selected the candidate, raw-tick
confirmation is not an independent holdout and cannot erase selection bias.

## Decision rule

An economic pass creates a raw-tick-confirmed historical CHOP candidate. It still
requires prospective shadow evidence and portfolio overlap testing. Failure
rejects attempt 39583 without parameter or gate changes. No result authorizes
training or trading; shock remains an abstain state.

# Chop Three-Mechanism Raw-Tick V26 Preregistration

## Frozen origin

V26 combines exactly three exposed V24 CHOP components. No parameter search is
authorized in this package:

- Attempt 39888: London z-expansion continuation, 116 raw signals and 49 M5
  trades, with V24 stress PF 1.785.
- Attempt 40193: all-session failed-reversion dual mode, 643 raw signals and 72
  M5 trades, with V24 stress PF 1.471.
- Attempt 39427: Asia tiered counterflow continuation, 189 raw signals and 44
  M5 trades, with V24 stress PF 1.584.

Every component uses the latest completed H4 CHOP state, completed M15/M5
features, a 1.0 latest-completed-H1 ATR stop, a 2.0R target, and a 12-hour hold.
The frozen component priority is 39888, 40193, then 39427. Exact duplicate
signal-time, direction, and geometry rows are retained only from the first
component. All remaining signals share one position, one cooldown, and one
four-trade UTC-day cap.

The exposed M5 reconstruction contains 125 composite trades, +42.831R, PF
1.611, minimum-era PF 1.394, minimum-era average +0.243R, and 8.305R closed
drawdown. These figures selected the composite and are not holdout evidence.

## Independent signal parity

V26 independently implements all three frozen Boolean policies. Before raw
outcomes are opened, each component's mask, direction vector, raw count, and
SHA-256 signal-stream digest must equal V24 exactly. Candidate generation also
requires contiguous M5 coverage through each scheduled 12-hour horizon. The
locked stream must contain 948 component raw signals, 588 contiguous component
candidates, 67 removed duplicates, and 521 unique raw-tick candidates. Spread
and risk eligibility are evaluated from the scheduled raw-tick entry quote.

## Raw-tick execution

- Verified free Dukascopy XAUUSD bid/ask ticks cover 2016-07-01 through
  2026-07-01; 120 complete frozen monthly manifests are locked.
- Entry uses the first executable quote at or after the next M5 open.
- Longs enter on ask and exit on bid; shorts enter on bid and exit on ask.
- The first chronological executable stop or target tick wins. Stop crossing
  fills at the observed quote; target crossing fills at the frozen target.
- If neither threshold is reached, exit uses the first executable quote at or
  after the scheduled 12-hour deadline.
- Spread, $0.30 ticket cost, $0.35 per 24-hour holding cost, and 0.05R stress
  slippage are deducted.
- One open position, a five-minute cooldown, and at most four trades per UTC day
  are applied to the combined stream.

## Frozen gates

The V24 gates remain unchanged: at least 100 trades and 15 per era, total stress
PF at least 1.25, every-era PF at least 1.10, every-era average at least +0.02R,
closed drawdown no more than 25R, and positive net R after removing the five
largest winners.

The raw-tick daily p-value and conservative 1,000-policy adjusted p-value are
reported. The raw-tick replay is an execution-quality confirmation on exposed
history, not an independent statistical holdout.

## Decision rule

An economic pass creates a raw-tick-confirmed historical CHOP specialist
candidate. It still requires prospective shadow evidence and shared-account
portfolio testing. Failure rejects this exact composite without parameter or
gate changes. No result authorizes training or trading; shock remains an
abstain state.
